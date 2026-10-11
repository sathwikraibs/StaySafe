"""
TrustLight - Ratings and reviews (their own section of the long-memory database)
-------------------------------------------------------------------------------
Every rating sent from the feedback card is kept here, apart from the check results:

    ss1:fb:stars    how many 1, 2, 3, 4 and 5 star ratings (kept forever, so the average is exact)
    ss1:fb:reviews  the latest 1,000 ratings: stars, words, topics, language, date, and whether the
                    person allowed their words to be shown to others (anonymous: no name, no contact)
    ss1:fb:hidden   reviews the owner hid (with the private link sent to Telegram)

Only reviews whose writer ticked "let others read my words" are ever shown on the website, with phone
numbers, emails, OTPs and long numbers removed and rude words kept off the page.
"""
import json
import re
import secrets
import threading
import time

from scanners import store

K_STARS, K_REVIEWS, K_HIDDEN = store.PREFIX + "fb:stars", store.PREFIX + "fb:reviews", store.PREFIX + "fb:hidden"
KEEP_REVIEWS = 1000
SHOW_REVIEWS = 12
_summary = {"at": 0.0, "value": None}
_lock = threading.Lock()

# kept off the public page (the rating still counts, and the owner still reads it in Telegram)
_RUDE = re.compile(r"\b(fuck\w*|shit\w*|bitch\w*|bastard|asshole|dick|chutiya\w*|madarchod|bhenchod|behenchod|"
                   r"bc|mc|gandu|harami|kutta|kutti|saala|saali|randi|bewakoof)\b", re.I)


def public_text(text: str) -> str:
    """The words as other visitors may see them: personal details removed."""
    from scanners.translator import mask_personal
    masked, _ = mask_personal(text or "")
    masked = re.sub(r"\[#\d+\]", "•••", masked)
    masked = re.sub(r"(?i)\b(otp|pin|cvv|password)\b\W{0,3}\S+", r"\1 •••", masked)
    return re.sub(r"\s+", " ", masked).strip()[:400]


def save(stars: int, topics: list, message: str, lang: str, source: str, share: bool):
    """Keep one rating. Returns (review id, private hide token) or (None, None) without the database."""
    if not store.enabled():
        return None, None
    rid, token = secrets.token_hex(4), secrets.token_urlsafe(9)
    record = {"id": rid, "token": token, "stars": stars, "topics": topics, "text": message[:1500], "lang": lang,
              "from": source, "share": bool(share and message.strip()), "at": int(time.time())}
    ok, _ = store.command(["HINCRBY", K_STARS, str(stars), 1])
    store.command(["LPUSH", K_REVIEWS, json.dumps(record, ensure_ascii=False)])
    store.command(["LTRIM", K_REVIEWS, 0, KEEP_REVIEWS - 1])
    with _lock:
        _summary["at"] = 0.0          # the next visitor sees the new numbers
    return (rid, token) if ok else (None, None)


def hide(rid: str, token: str) -> bool:
    """Hide one review from the website, using the private token from the Telegram message."""
    ok, raw = store.command(["LRANGE", K_REVIEWS, 0, KEEP_REVIEWS - 1])
    if not ok:
        return False
    for item in raw or []:
        try:
            r = json.loads(item)
        except Exception:
            continue
        if r.get("id") == rid and secrets.compare_digest(str(r.get("token", "")), token or ""):
            store.command(["SADD", K_HIDDEN, rid])
            with _lock:
                _summary["at"] = 0.0
            return True
    return False


def summary() -> dict:
    """Average, how many of each star, and the latest shared reviews. Remembered for 5 minutes."""
    with _lock:
        if _summary["value"] is not None and time.time() - _summary["at"] < 300:
            return _summary["value"]
    counts = {str(n): 0 for n in range(1, 6)}
    reviews = []
    if store.enabled():
        ok, raw = store.command(["HGETALL", K_STARS])
        if ok and raw:
            pairs = dict(zip(raw[::2], raw[1::2])) if isinstance(raw, list) else dict(raw)
            for k, v in pairs.items():
                if str(k) in counts:
                    counts[str(k)] = int(v or 0)
        ok_h, hidden = store.command(["SMEMBERS", K_HIDDEN])
        hidden = set(hidden or []) if ok_h else set()
        ok_r, raw = store.command(["LRANGE", K_REVIEWS, 0, 199])
        for item in (raw or []) if ok_r else []:
            try:
                r = json.loads(item)
            except Exception:
                continue
            text = public_text(r.get("text", ""))
            if not r.get("share") or r.get("id") in hidden or len(text) < 8 or _RUDE.search(text):
                continue
            reviews.append({"id": r["id"], "stars": int(r.get("stars", 0)), "text": text,
                            "lang": r.get("lang", "en"), "at": int(r.get("at", 0))})
            if len(reviews) >= SHOW_REVIEWS:
                break
    total = sum(counts.values())
    average = round(sum(int(k) * v for k, v in counts.items()) / total, 1) if total else 0.0
    value = {"count": total, "average": average, "stars": counts, "reviews": reviews}
    with _lock:
        _summary.update(at=time.time(), value=value)
    return value
