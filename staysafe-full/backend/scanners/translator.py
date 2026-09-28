"""
StaySafe - Translation with a ₹0 fallback chain
-------------------------------------------------
Used for two things:
  1. CHECKING: messages in a language our rules don't cover are translated to
     English so the same explainable rules can check them (the rules still decide).
  2. EXPLAINING: "What this message says" in the visitor's language.

Providers are tried in order, and each one switches itself off automatically
when it runs out. Nothing here can ever create a bill:

  1. Google Cloud Translation  (TRANSLATE_API_KEY). Best quality.
     Keep the Google project on the free trial (never "Upgrade") and set a daily
     quota in Google Cloud; when Google refuses (quota reached, trial ended,
     billing off), we stop calling it for a while.
  2. MyMemory (free, no card, no key). 5,000 chars/day, or 50,000 with an email
     in MYMEMORY_EMAIL. When it says the daily quota is used, we stop for the day.
  3. Nothing left → the result falls back to StaySafe's own built-in rules
     (English, Hinglish, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi).

TRANSLATE_DAILY_CHAR_LIMIT (default 15,000) is an extra per-day cap on Google
inside this server. (It resets if the server restarts, which is why the real
guarantee is Google's own quota + staying on the free trial.)
"""

import os
import re
import threading
import time
from collections import OrderedDict
from datetime import date

import requests

GOOGLE_URL = "https://translation.googleapis.com/language/translate/v2"
MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MAX_CHARS = 1500           # longest message we translate
MYMEMORY_CHUNK_BYTES = 450  # MyMemory accepts max 500 bytes per request
DAILY_LIMIT = int(os.environ.get("TRANSLATE_DAILY_CHAR_LIMIT", "15000"))

# Neither Google's API nor MyMemory offers Tulu; Tulu readers read Kannada script.
TARGET_FALLBACK = {"tcy": "kn"}

_lock = threading.Lock()
_cache: "OrderedDict[tuple, dict]" = OrderedDict()
_usage = {"day": date.today(), "chars": 0}
_paused_until = {"google": 0.0, "mymemory": 0.0}   # provider -> unix time it may be tried again
_problem = {"google": None, "mymemory": None}


def _google_key() -> str:
    # Only a key added on purpose for translation. The Safe Browsing key is never reused here,
    # so Google Translate can't be switched on by accident (keeps the site at ₹0).
    return os.environ.get("TRANSLATE_API_KEY", "")


def _pause(provider: str, seconds: float, reason: str) -> None:
    _paused_until[provider] = time.time() + seconds
    _problem[provider] = reason


def _available(provider: str) -> bool:
    return time.time() >= _paused_until[provider]


def translation_status() -> dict:
    return {
        "enabled": True,  # MyMemory needs no key, so translation is always attempted
        "google": {
            "configured": bool(_google_key()),
            "active": bool(_google_key()) and _available("google"),
            "problem": _problem["google"],
            "chars_today": _usage["chars"],
            "daily_limit": DAILY_LIMIT,
        },
        "mymemory": {"active": _available("mymemory"), "problem": _problem["mymemory"],
                     "email_set": bool(os.environ.get("MYMEMORY_EMAIL"))},
    }


def _reserve_google(chars: int) -> bool:
    with _lock:
        today = date.today()
        if _usage["day"] != today:
            _usage["day"], _usage["chars"] = today, 0
        if _usage["chars"] + chars > DAILY_LIMIT:
            return False
        _usage["chars"] += chars
        return True


# ---------------------------------------------------------------------------
# Language of a text, guessed from its script (needed by MyMemory)
# ---------------------------------------------------------------------------
SCRIPT_RANGES = [
    ((0x0C80, 0x0CFF), "kn"), ((0x0900, 0x097F), "hi"), ((0x0B80, 0x0BFF), "ta"),
    ((0x0C00, 0x0C7F), "te"), ((0x0D00, 0x0D7F), "ml"), ((0x0980, 0x09FF), "bn"),
    ((0x0A80, 0x0AFF), "gu"), ((0x0A00, 0x0A7F), "pa"), ((0x0B00, 0x0B7F), "or"),
    ((0x0600, 0x06FF), "ur"),
]
MARATHI_HINTS = ("आहे", "होईल", "तुमचे", "तुमच्या", "करा", "नाही", "सांगा")


def guess_language(text: str) -> str:
    counts = {}
    for ch in text:
        code = ord(ch)
        for (lo, hi), lang in SCRIPT_RANGES:
            if lo <= code <= hi:
                counts[lang] = counts.get(lang, 0) + 1
                break
    if not counts:
        return "en"
    lang = max(counts, key=counts.get)
    if lang == "hi" and any(h in text for h in MARATHI_HINTS):
        return "mr"
    return lang


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
def _google(text: str, target: str):
    key = _google_key()
    if not key or not _available("google") or not _reserve_google(len(text)):
        return None
    try:
        resp = requests.post(GOOGLE_URL, params={"key": key},
                             json={"q": text, "target": target, "format": "text"}, timeout=8)
    except Exception:
        return None
    if resp.status_code == 200:
        try:
            item = resp.json()["data"]["translations"][0]
            return {"text": item["translatedText"], "from": item.get("detectedSourceLanguage", ""),
                    "to": target, "provider": "google"}
        except Exception:
            return None
    try:
        msg = resp.json().get("error", {}).get("message", "") or f"HTTP {resp.status_code}"
    except Exception:
        msg = f"HTTP {resp.status_code}"
    low = msg.lower()
    if resp.status_code == 429 or "quota" in low or "rate limit" in low:
        _pause("google", 6 * 3600, "Daily limit reached. Using the free fallback for now")
    elif resp.status_code in (401, 403) or "billing" in low or "api key" in low or "disabled" in low:
        # Trial ended / billing off / key wrong: stop calling Google, re-try occasionally
        _pause("google", 24 * 3600, msg[:200])
    else:
        _pause("google", 10 * 60, msg[:200])
    return None


def _chunks(text: str, limit: int):
    """Split text into pieces of at most `limit` UTF-8 bytes, preferring sentence ends."""
    pieces, current = [], ""
    for part in text.replace("\n", "\n ").split(" "):
        candidate = (current + " " + part).strip() if current else part
        if len(candidate.encode("utf-8")) <= limit:
            current = candidate
        else:
            if current:
                pieces.append(current)
            while len(part.encode("utf-8")) > limit:  # one very long "word"
                cut = limit // 3
                pieces.append(part[:cut])
                part = part[cut:]
            current = part
    if current:
        pieces.append(current)
    return pieces


def _same_text(a: str, b: str) -> bool:
    norm = lambda s: re.sub(r"[\W_]+", "", (s or "").lower())
    return bool(norm(a)) and norm(a) == norm(b)


def _looks_like_translation(source: str, translated: str, target: str) -> bool:
    """Reject empty, unchanged or wildly short/long results."""
    if not translated or _same_text(source, translated):
        return False
    if target == "en":
        letters = len(re.findall(r"[A-Za-z]", translated))
        src_letters = len(re.findall(r"\w", source))
        if letters < 2 or not (0.25 <= letters / max(src_letters, 1) <= 5):
            return False
    return True


def _pick_mymemory(piece: str, data: dict, target: str):
    """
    MyMemory mixes its machine translation with "similar sentences" people saved before.
    Those near matches are sentences about something else, so we only accept:
      1. a saved human translation of exactly this text, or
      2. the machine translation (created-by "MT!") of exactly this text.
    """
    matches = data.get("matches") or []
    exact_human = [m for m in matches
                   if m.get("created-by") != "MT!" and _same_text(m.get("segment", ""), piece)
                   and float(m.get("match") or 0) >= 0.99]
    machine = [m for m in matches if m.get("created-by") == "MT!"
               and (not m.get("segment") or _same_text(m.get("segment", ""), piece))]
    for m in exact_human + machine:
        text = (m.get("translation") or "").strip()
        if _looks_like_translation(piece, text, target):
            return text
    if not matches:
        # older answer format without the list: trust it only when MyMemory is sure
        best = data.get("responseData") or {}
        text = (best.get("translatedText") or "").strip()
        if float(best.get("match") or 0) >= 0.85 and _looks_like_translation(piece, text, target):
            return text
    return None


def _mymemory(text: str, target: str):
    if not _available("mymemory"):
        return None
    source = guess_language(text)
    if source == target:
        return None
    params_base = {"langpair": f"{source}|{target}"}
    if os.environ.get("MYMEMORY_EMAIL"):
        params_base["de"] = os.environ["MYMEMORY_EMAIL"]
    out = []
    for piece in _chunks(text, MYMEMORY_CHUNK_BYTES):
        try:
            resp = requests.get(MYMEMORY_URL, params={**params_base, "q": piece}, timeout=8)
            data = resp.json()
        except Exception:
            return None
        translated = (data.get("responseData") or {}).get("translatedText") or ""
        status = str(data.get("responseStatus", resp.status_code))
        if status == "429" or data.get("quotaFinished") or "MYMEMORY WARNING" in translated.upper():
            _pause("mymemory", 6 * 3600, "Free daily limit used. Try again later")
            return None
        if status != "200" or not translated:
            return None
        picked = _pick_mymemory(piece, data, target)
        if not picked:
            # Only a "similar sentence" from someone else's memory came back. That is often
            # about something different, so showing nothing is better than showing it.
            return None
        out.append(picked)
    return {"text": " ".join(out), "from": source, "to": target, "provider": "mymemory"}


def translate(text: str, target: str):
    """
    Translate `text` into `target` ("en", "kn", ...). Returns
    {"text", "from", "to", "provider"} or None when no free translation is available.
    """
    text = (text or "").strip()[:MAX_CHARS]
    target = TARGET_FALLBACK.get(target, target)
    if not text:
        return None

    cache_key = (text, target)
    with _lock:
        if cache_key in _cache:
            _cache.move_to_end(cache_key)
            return _cache[cache_key]

    result = _google(text, target) or _mymemory(text, target)
    if result:
        with _lock:
            _cache[cache_key] = result
            while len(_cache) > 500:
                _cache.popitem(last=False)
    return result
