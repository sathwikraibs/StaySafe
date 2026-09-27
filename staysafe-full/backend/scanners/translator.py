"""
StaySafe - Translation (Google Cloud Translation, Basic v2)
------------------------------------------------------------
Used for two things:
  1. CHECKING: messages written mostly in a script our rules can't read
     (Tamil, Telugu, Malayalam, Bengali, ...) — and Kannada/Hindi too, as a
     second opinion — are translated to English so the same explainable rules
     can check them. The verdict still comes from the rules, never from AI.
  2. EXPLAINING: when the message is in a different language from the website,
     we show "What this message says" in the visitor's language.

Key: TRANSLATE_API_KEY (falls back to GSB_API_KEY if that key also has the
Cloud Translation API enabled). Without a key, everything still works —
translation is just skipped.

Free tier: 500,000 characters/month. TRANSLATE_DAILY_CHAR_LIMIT (default 15,000)
stops translating for the rest of the day once reached, so a busy day can't
run up a bill.
"""

import os
import threading
from collections import OrderedDict
from datetime import date

import requests

API_URL = "https://translation.googleapis.com/language/translate/v2"
MAX_CHARS = 2000  # longest message we'll translate
DAILY_LIMIT = int(os.environ.get("TRANSLATE_DAILY_CHAR_LIMIT", "15000"))

# Google's Cloud Translation API has no Tulu; Tulu readers read Kannada script.
TARGET_FALLBACK = {"tcy": "kn"}

_lock = threading.Lock()
_cache: "OrderedDict[tuple, dict]" = OrderedDict()
_usage = {"day": date.today(), "chars": 0}
_disabled_reason = None  # set if Google rejects the key (e.g. API not enabled)


def _api_key() -> str:
    return os.environ.get("TRANSLATE_API_KEY") or os.environ.get("GSB_API_KEY", "")


def translation_status() -> dict:
    return {
        "enabled": bool(_api_key()) and _disabled_reason is None,
        "problem": _disabled_reason,
        "chars_today": _usage["chars"],
        "daily_limit": DAILY_LIMIT,
    }


def _reserve(chars: int) -> bool:
    with _lock:
        today = date.today()
        if _usage["day"] != today:
            _usage["day"], _usage["chars"] = today, 0
        if _usage["chars"] + chars > DAILY_LIMIT:
            return False
        _usage["chars"] += chars
        return True


def translate(text: str, target: str):
    """
    Translate `text` into `target` (e.g. "en", "kn"). Returns
    {"text": ..., "from": "ta", "to": "en"} or None if unavailable.
    """
    global _disabled_reason
    key = _api_key()
    text = (text or "").strip()[:MAX_CHARS]
    target = TARGET_FALLBACK.get(target, target)
    if not key or not text or _disabled_reason:
        return None

    cache_key = (text, target)
    with _lock:
        if cache_key in _cache:
            _cache.move_to_end(cache_key)
            return _cache[cache_key]

    if not _reserve(len(text)):
        return None

    try:
        resp = requests.post(
            API_URL,
            params={"key": key},
            json={"q": text, "target": target, "format": "text"},
            timeout=8,
        )
        if resp.status_code in (400, 401, 403):
            # Key wrong, or Cloud Translation API not enabled for this key — stop trying
            msg = ""
            try:
                msg = resp.json().get("error", {}).get("message", "")
            except Exception:
                pass
            if resp.status_code != 400 or "API key" in msg:
                _disabled_reason = msg or f"HTTP {resp.status_code}"
            return None
        resp.raise_for_status()
        item = resp.json()["data"]["translations"][0]
        result = {
            "text": item["translatedText"],
            "from": item.get("detectedSourceLanguage", ""),
            "to": target,
        }
    except Exception:
        return None

    with _lock:
        _cache[cache_key] = result
        while len(_cache) > 500:
            _cache.popitem(last=False)
    return result
