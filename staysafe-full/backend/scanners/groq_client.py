"""
StaySafe - Careful use of Groq's free plan
------------------------------------------
Groq's free plan limits EACH MODEL separately, in four ways (published free-plan numbers for
the text models we use, Sep 2026):

    requests per minute 30 · requests per day 1,000 · tokens per minute 8,000 · tokens per day 200,000

Tokens (pieces of words, both the question and the answer) run out long before requests do:
one assistant answer with our instructions and a short conversation uses roughly 1,500 to 3,000
tokens. So we:

  1. keep a separate allowance per model for requests AND tokens (minute and day);
  2. estimate each call's tokens before sending, then correct the count with the real number
     Groq reports back;
  3. read Groq's own x-ratelimit headers after every answer, so our counts always match
     Groq's (and pick up the real limits for this account automatically);
  4. when a model's minute is full, wait for the next free slot (the visitor sees "thinking"),
     and when its day is used up, move on to the next model: every model has its own
     allowance, so five models give about five times the capacity;
  5. give the best model a little more "thinking" when there's plenty of allowance left today,
     and less when it's running low, so the site keeps answering around the clock.

No card is ever added to Groq, so none of this can cost anything; when everything is used up
Groq just says no and the Helper uses the other free options.
"""

import os
import re
import threading
import time

import requests

from scanners.quota import Quota, _env_int

URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq's day for these limits is a rolling 24 hours; a UTC day plus the header sync keeps us inside it.
DEFAULT = {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000}

# Best first for the assistant (quality and languages), cheapest first for quick yes/no reviews.
CHAT_MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "qwen/qwen3.8-27b", "openai/gpt-oss-20b",
               "llama-3.1-8b-instant"]
REVIEW_MODELS = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"]

_models: dict = {}
_lock = threading.Lock()
_problem = {"last": None}
_gone: set = set()   # model names Groq says don't exist (any more) for this account


class _Model:
    def __init__(self, name):
        tag = re.sub(r"[^A-Z0-9]", "_", name.upper())
        self.name = name
        # Requests and tokens each have a minute and a day allowance. We keep 5% below Groq's.
        self.requests = Quota(f"groq:{name}", _env_int(f"GROQ_RPM_{tag}", DEFAULT["rpm"] - 2),
                              _env_int(f"GROQ_RPD_{tag}", int(DEFAULT["rpd"] * 0.95)), max_waiters=8)
        self.tokens = Quota(f"groq-tokens:{name}", _env_int(f"GROQ_TPM_{tag}", int(DEFAULT["tpm"] * 0.95)),
                            _env_int(f"GROQ_TPD_{tag}", int(DEFAULT["tpd"] * 0.95)), max_waiters=8)

    def left_today(self) -> float:
        s = self.tokens.status()
        return 1.0 - (s["used_today"] / s["per_day"]) if s["per_day"] else 1.0


def model(name) -> _Model:
    with _lock:
        if name not in _models:
            _models[name] = _Model(name)
        return _models[name]


def configured() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def estimate_tokens(messages, max_tokens) -> int:
    """A careful guess: Latin text is about 4 characters a token, Indian scripts about 1 a token."""
    total = 0
    for m in messages:
        text = m.get("content") or ""
        latin = sum(1 for ch in text if ord(ch) < 0x0250)
        total += latin / 3.6 + (len(text) - latin) * 1.1 + 6
    return int(total) + max_tokens


def _seconds(value) -> float:
    """Groq reset times look like '7.66s', '2m59.56s' or '1h2m3s'."""
    if not value:
        return 0.0
    total = 0.0
    for num, unit in re.findall(r"([\d.]+)(ms|h|m|s)", str(value)):
        total += float(num) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]
    return total


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _sync(m: _Model, headers) -> None:
    m.requests.sync(day_limit=_int(headers.get("x-ratelimit-limit-requests")),
                    day_remaining=_int(headers.get("x-ratelimit-remaining-requests")))
    m.tokens.sync(minute_limit=_int(headers.get("x-ratelimit-limit-tokens")),
                  minute_remaining=_int(headers.get("x-ratelimit-remaining-tokens")),
                  minute_reset_s=_seconds(headers.get("x-ratelimit-reset-tokens")))


def _extras(name: str, effort: str) -> dict:
    """Model-specific options: how much it may 'think' before answering."""
    if name.startswith("openai/gpt-oss"):
        return {"reasoning_effort": effort, "include_reasoning": False}
    if name.startswith("qwen/"):
        return {"reasoning_format": "hidden"}
    return {}


def chat(messages, models=None, max_tokens=600, json_mode=True, wait=20.0, priority="normal",
         effort="medium", temperature=0.3):
    """
    Ask Groq, trying each model in turn within its own free allowance.
    Returns {"text", "model"} or None.
    """
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return None
    deadline = time.time() + wait
    for name in (models or CHAT_MODELS):
        if name in _gone:
            continue
        m = model(name)
        # Running low today? Think less, so the allowance lasts until tomorrow.
        this_effort = effort
        if effort != "low" and m.left_today() < 0.35:
            this_effort = "low"
        est = estimate_tokens(messages, max_tokens + (900 if this_effort == "high" else 500 if this_effort == "medium" else 150))
        left = max(0.0, deadline - time.time())
        if not m.requests.take(wait=left, priority=priority):
            continue
        if not m.tokens.take(wait=max(0.0, deadline - time.time()), priority=priority, cost=est):
            m.requests.refund()
            continue
        body = {"model": name, "temperature": temperature, "max_tokens": max_tokens, "messages": messages,
                **_extras(name, this_effort)}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            r = requests.post(URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=30)
            if r.status_code == 400 and any(w in r.text.lower() for w in ("reasoning", "include_reasoning", "response_format", "json")):
                # this model doesn't take one of the options: ask once more without them
                for k in ("reasoning_effort", "include_reasoning", "reasoning_format", "response_format"):
                    body.pop(k, None)
                r = requests.post(URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=30)
        except Exception as e:
            _problem["last"] = f"{name}: {type(e).__name__}"
            m.tokens.refund(est)
            continue
        _sync(m, getattr(r, "headers", None) or {})
        if r.status_code == 200:
            try:
                data = r.json()
                text = data["choices"][0]["message"].get("content") or ""
                used = int((data.get("usage") or {}).get("total_tokens") or est)
            except Exception:
                continue
            m.tokens.adjust(used - est)
            _problem["last"] = None
            if text.strip():
                return {"text": text, "model": name}
            continue
        m.tokens.refund(est)
        body_text = str(getattr(r, "text", ""))[:400].lower()
        if r.status_code == 429:
            hdr = getattr(r, "headers", None) or {}
            retry = _seconds(hdr.get("retry-after")) or _int(hdr.get("retry-after")) or 60
            if "per day" in body_text or "tpd" in body_text or "rpd" in body_text:
                m.tokens.close_day() if "token" in body_text else m.requests.close_day()
            else:
                m.tokens.cool_down(float(retry))
            _problem["last"] = f"{name}: limit reached"
            continue
        if r.status_code in (400, 404) and ("model" in body_text and ("not" in body_text or "decommission" in body_text)):
            _gone.add(name)
            continue
        if r.status_code in (401, 403):
            _problem["last"] = "key rejected"
            return None
        _problem["last"] = f"{name}: HTTP {r.status_code}"
    return None


def status() -> dict:
    with _lock:
        names = list(_models)
    return {"configured": configured(), "problem": _problem["last"], "unavailable_models": sorted(_gone),
            "models": {n: {"requests": model(n).requests.status(), "tokens": model(n).tokens.status()} for n in names}}
