"""
StaySafe - Long memory for check results (survives restarts)
---------------------------------------------------------------
The server's own memory is wiped every time it restarts (each update, and whenever the free
server sleeps). Results that cost a limited free allowance (VirusTotal, urlscan, the AI second
opinion...) are also kept here, in a small free online database (Upstash Redis, reached over
HTTPS), so the same scam link, file or forwarded message is never paid for twice.

What is kept: only answers about LINKS, FILES and WEBSITES, plus the AI's verdict on a
message. Keys are one-way fingerprints (SHA-256), so the database never holds anyone's
message, and nothing in it says who checked what.

Setup: on Upstash create a free Redis database (no card), then on Render add
    UPSTASH_REDIS_REST_URL   = https://....upstash.io
    UPSTASH_REDIS_REST_TOKEN = ....
Without them everything still works, just without the long memory.

Free plan: 500,000 commands a month. We spend at most STORE_DAILY_LIMIT (default 15,000) a
day and simply stop using the long memory for the rest of the day if that is reached.
"""

import hashlib
import json
import os
import threading
import time

import requests

PREFIX = "ss1:"
TIMEOUT = 2.5          # never let the long memory slow a check down much
_state = {"problem": None, "hits": 0, "misses": 0, "writes": 0, "down_until": 0.0}
_lock = threading.Lock()


def _conf():
    url = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip()
    return (url, token) if url.startswith("https://") and token else (None, None)


def enabled() -> bool:
    return _conf()[0] is not None


def _fingerprint(ns: str, key) -> str:
    raw = key if isinstance(key, str) else json.dumps(key, sort_keys=True, default=str)
    return PREFIX + ns + ":" + hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:40]


def _command(cmd: list, cost: int = 1):
    """Run one Redis command. None on any problem (the caller then carries on without it)."""
    return command(cmd, cost)[1]


def key(ns: str, k) -> str:
    return _fingerprint(ns, k)


def command(cmd: list, cost: int = 1):
    """(worked, result). worked is False on any problem; result can be None for a Redis 'nil'."""
    url, token = _conf()
    if not url or time.time() < _state["down_until"]:
        return False, None
    from scanners.quota import quota
    if not quota("store").take(wait=0, cost=cost):
        return False, None
    try:
        r = requests.post(url, json=cmd, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
        if r.status_code == 401:
            _state["problem"] = "token not accepted"
            _state["down_until"] = time.time() + 3600
            return False, None
        if r.status_code == 429:
            _state["problem"] = "free allowance used"
            _state["down_until"] = time.time() + 3600
            return False, None
        data = r.json()
        if "error" in data:
            _state["problem"] = str(data["error"])[:80]
            return False, None
        _state["problem"] = None
        _state["working"] = True
        return True, data.get("result")
    except Exception as e:  # noqa: BLE001
        _state["problem"] = type(e).__name__
        _state["down_until"] = time.time() + 60   # unreachable: don't keep every check waiting
        return False, None


def get(ns: str, key):
    raw = _command(["GET", _fingerprint(ns, key)])
    if raw is None:
        with _lock:
            _state["misses"] += 1
        return None
    try:
        value = json.loads(raw)
    except Exception:
        return None
    with _lock:
        _state["hits"] += 1
    return value


def put(ns: str, key, value, ttl_seconds: int) -> None:
    """Keep a value for ttl_seconds. Done in the background so the visitor never waits for it."""
    if not enabled() or not ttl_seconds or ttl_seconds <= 0:
        return
    try:
        raw = json.dumps(value, separators=(",", ":"), default=str)
    except Exception:
        return
    if len(raw) > 60_000:
        return

    def work():
        if _command(["SET", _fingerprint(ns, key), raw, "EX", int(ttl_seconds)]) is not None:
            with _lock:
                _state["writes"] += 1
    threading.Thread(target=work, daemon=True).start()


# --- Daily allowances survive restarts too -------------------------------------------------
_QUOTA_KEY = PREFIX + "quota-days"


def load_quota_days() -> None:
    """After a restart, remember how much of each daily allowance was already used today."""
    raw = _command(["GET", _QUOTA_KEY])
    if not raw:
        return
    try:
        saved = json.loads(raw)
    except Exception:
        return
    from scanners.quota import QUOTAS
    now = time.time()
    for name, (day_key, used) in saved.items():
        q = QUOTAS.get(name)
        if not q or not q.per_day or name == "store":
            continue
        with q._lock:
            q._roll_day(now)
            if q._day_key == day_key and used > q._day_used:
                q._day_used = int(used)


def save_quota_days() -> None:
    from scanners.quota import QUOTAS
    snap = {}
    for name, q in QUOTAS.items():
        if q.per_day and name != "store":
            with q._lock:
                q._roll_day(time.time())
                if q._day_used:
                    snap[name] = [q._day_key, q._day_used]
    if snap:
        _command(["SET", _QUOTA_KEY, json.dumps(snap), "EX", 2 * 86400])


_started = {"done": False}


def start_background() -> None:
    """Load today's usage once, then save it every 10 minutes."""
    if _started["done"] or not enabled():
        return
    _started["done"] = True

    def loop():
        ok, pong = command(["PING"])
        _state["working"] = bool(ok and pong == "PONG")
        load_quota_days()
        while True:
            time.sleep(600)
            save_quota_days()
    threading.Thread(target=loop, daemon=True).start()


def status() -> dict:
    return {"configured": enabled(), "working": _state.get("working", False), "problem": _state["problem"], "hits": _state["hits"],
            "misses": _state["misses"], "writes": _state["writes"]}
