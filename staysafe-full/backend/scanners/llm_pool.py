"""
TrustLight - More free AI services, as backups
---------------------------------------------
Groq and Google Gemini do most of the work. These add more free capacity, so the Helper and
the message review keep answering when those two are busy or used up for the day. Each one
is used only if its key is set on Render, and each stays inside its own free limit (quota.py
style: wait for a free slot, keep a reserve, believe the service when it says "too many").

All of them are free with no card (checked Sep 2026):

  Cloudflare Workers AI   CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_AI_TOKEN
                          10,000 "neurons" a day (roughly 100 to 300 answers). Resets 00:00 UTC.
  Mistral                 MISTRAL_API_KEY    free plan (phone number check at sign-up)
  OpenRouter              OPENROUTER_API_KEY only the ":free" models: 50 requests a day, 20 a minute

They all speak the same "chat completions" format, so one function talks to all of them.
Nothing here can cost money: without a card, a used-up allowance just answers "no".
"""

import os
import re
import threading
import time

import requests

from scanners.quota import Quota, QUOTAS


def _cloudflare_url():
    acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    return f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/v1/chat/completions"


def _models(env, default):
    return [m.strip() for m in os.environ.get(env, default).split(",") if m.strip()]


# name -> settings. "chat" models answer the Helper (quality and languages first);
# "review" models give the short scam / not-scam opinion (small and quick first).
PROVIDERS = {
    "cloudflare": {
        "ready": lambda: bool(os.environ.get("CLOUDFLARE_ACCOUNT_ID") and os.environ.get("CLOUDFLARE_AI_TOKEN")),
        "url": _cloudflare_url,
        "key": lambda: os.environ.get("CLOUDFLARE_AI_TOKEN", ""),
        "chat": lambda: _models("CLOUDFLARE_CHAT_MODELS", "@cf/openai/gpt-oss-120b,@cf/google/gemma-4-26b-a4b-it,@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
        "review": lambda: _models("CLOUDFLARE_REVIEW_MODELS", "@cf/openai/gpt-oss-20b,@cf/openai/gpt-oss-120b,@cf/meta/llama-3.1-8b-instruct"),
        "quota": QUOTAS["cloudflare"],
    },
    "mistral": {
        "ready": lambda: bool(os.environ.get("MISTRAL_API_KEY")),
        "url": lambda: "https://api.mistral.ai/v1/chat/completions",
        "key": lambda: os.environ.get("MISTRAL_API_KEY", ""),
        "chat": lambda: _models("MISTRAL_CHAT_MODELS", "mistral-medium-latest,mistral-small-latest"),
        "review": lambda: _models("MISTRAL_REVIEW_MODELS", "mistral-small-latest"),
        "quota": QUOTAS["mistral"],
    },
    "openrouter": {
        "ready": lambda: bool(os.environ.get("OPENROUTER_API_KEY")),
        "url": lambda: "https://openrouter.ai/api/v1/chat/completions",
        "key": lambda: os.environ.get("OPENROUTER_API_KEY", ""),
        "chat": lambda: _models("OPENROUTER_CHAT_MODELS", "qwen/qwen3.8-27b:free,nvidia/nemotron-3-super-120b-a12b:free"),
        "review": lambda: _models("OPENROUTER_REVIEW_MODELS", "qwen/qwen3.8-27b:free"),
        "quota": QUOTAS["openrouter"],
    },
}

_lock = threading.Lock()
_gone: dict = {}        # provider -> set of model names it doesn't offer
_problem: dict = {}     # provider -> last problem (for the status page)
_paused: dict = {}      # provider -> time until which it is not used (wrong key etc.)


def ready(name: str) -> bool:
    p = PROVIDERS.get(name)
    return bool(p and p["ready"]() and time.time() >= _paused.get(name, 0))


def _day_limit(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in ("per day", "daily", "per-day", "neurons", "free-models-per-day"))


def _time_for_call(deadline, cap: float) -> float:
    if deadline is None:
        return cap
    left = deadline - time.time() - 2
    return min(cap, left) if left >= 6 else 0.0


def chat(name: str, messages, kind: str = "chat", max_tokens: int = 1500, json_mode: bool = True,
         wait: float = 20.0, temperature: float = 0.3, priority: str = "normal", deadline=None):
    """Ask one provider. Returns the answer text, or None (then the next service is tried).
    Never runs past `deadline` (a time.time() value)."""
    if not ready(name):
        return None
    if deadline is not None:
        wait = max(0.0, min(wait, deadline - time.time() - 15))
    p = PROVIDERS[name]
    q: Quota = p["quota"]
    if not q.take(wait=wait, priority=priority):
        return None
    gone = _gone.setdefault(name, set())
    headers = {"Authorization": f"Bearer {p['key']()}", "Content-Type": "application/json"}
    if name == "openrouter":
        headers.update({"HTTP-Referer": "https://staysafe-tool.vercel.app", "X-Title": "TrustLight"})
    for model in [m for m in p[kind]() if m not in gone]:
        body = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if name == "openrouter":
            # free models "think" first; keep that short and out of the answer, and leave room for the reply
            body["reasoning"] = {"effort": "low", "exclude": True}
            body["max_tokens"] = max(max_tokens, 4000)
        t = _time_for_call(deadline, 40)
        if not t:
            return None
        try:
            r = requests.post(p["url"](), headers=headers, json=body, timeout=t)
            if r.status_code in (400, 422) and json_mode and re.search(r"response_format|json", r.text, re.I):
                body.pop("response_format", None)      # this model can't be asked for JSON: ask plainly
                t = _time_for_call(deadline, 40)
                if not t:
                    return None
                r = requests.post(p["url"](), headers=headers, json=body, timeout=t)
        except Exception as e:
            _problem[name] = f"{model}: {type(e).__name__}"
            continue                        # timed out or no connection: try the next model
        text = str(getattr(r, "text", ""))[:300]
        if r.status_code == 200:
            try:
                choice = r.json()["choices"][0]
                out = (choice.get("message") or {}).get("content") or ""
            except Exception:
                _problem[name] = f"{model}: answer could not be read"
                continue
            if isinstance(out, list):       # some services send the answer in parts
                out = "".join(part.get("text", "") for part in out if isinstance(part, dict))
            if choice.get("finish_reason") == "length" or not str(out).strip():
                _problem[name] = f"{model}: answer was {'cut off' if choice.get('finish_reason') == 'length' else 'empty'}"
                continue                    # cut off or empty: never show half an answer
            _problem[name] = None
            return str(out)
        _problem[name] = f"{model}: HTTP {r.status_code} {text[:160]}"
        if r.status_code in (401, 403):
            _paused[name] = time.time() + 6 * 3600      # key wrong or not allowed: check again later
            return None
        if r.status_code == 429:
            if _day_limit(text):
                q.close_day()           # the whole account's day is used up
                return None
            if re.search(r"upstream|provider returned error|temporarily", text, re.I):
                continue                # only this model is busy at its source: try the next model
            q.cool_down(60)
            return None
        if r.status_code in (400, 404) and re.search(r"model|not found|does not exist|no endpoints", text, re.I):
            gone.add(model)                 # not offered (any more): try the next model
            continue
        if r.status_code >= 500:
            continue                        # busy: try the next model
        return None
    return None


def status() -> dict:
    return {name: {"configured": p["ready"](), "problem": _problem.get(name),
                   "models_not_offered": sorted(_gone.get(name, set())),
                   "allowance": p["quota"].status()} for name, p in PROVIDERS.items()}
