"""
StaySafe - "Report as scam": StaySafe's own list, built by its users
-----------------------------------------------------------------------
People who were targeted can report a link, phone number or UPI ID. When enough different
people report the same one, everybody who checks it later sees "Reported as a scam by N
StaySafe users", without spending any outside allowance.

Kept in the long memory (store.py), as fingerprints only: the database holds a count per
fingerprint, never the link, number or ID itself, and never who reported it.

Protection against misuse (someone reporting a real business to harm it):
- one report per person per item (by network address fingerprint), for 90 days
- at most REPORTS_PER_DAY reports a day from one address
- nothing shows until REPORT_THRESHOLD different people agree
- official numbers (helplines, 1600 bank numbers), the world's most visited websites,
  official brand sites and shared hosting services can't be reported
- reports fade: each item's count is kept 90 days after its latest report
"""

import hashlib
import re
import threading
import time

from flask import Blueprint, jsonify, request

from scanners import store

reports_bp = Blueprint("reports", __name__)

REPORT_THRESHOLD = 3
REPORTS_PER_DAY = 20
KEEP = 90 * 86400
KINDS = ("link", "number", "upi")

_cache = {}           # (kind, norm) -> (time, count): checks reuse a fresh count for a minute
_cache_lock = threading.Lock()


def normalize(kind: str, value: str):
    """Canonical form, plus a wider 'site' form for links. None if it can't be reported."""
    value = (value or "").strip()[:500]
    if not value:
        return None, None
    if kind == "upi":
        v = value.replace(" ", "").lower()
        return (v, None) if re.fullmatch(r"[\w.\-]{2,256}@[a-z][a-z0-9]{1,64}", v) else (None, None)
    if kind == "number":
        raw = re.sub(r"[^\d+]", "", value)
        if raw.startswith("00"):
            raw = "+" + raw[2:]
        d = re.sub(r"\D", "", raw)
        if raw.startswith("+91") or (len(d) == 12 and d.startswith("91")):
            d = d[2:]
        elif len(d) == 11 and d.startswith("0"):
            d = d[1:]
        if len(d) < 6 or len(d) > 15:
            return None, None
        from scanners.number_check import HELPLINES
        if d in HELPLINES or re.fullmatch(r"1600\d{6}", d):
            return None, None            # official numbers can't be reported
        return ("+" + d if raw.startswith("+") and not raw.startswith("+91") else d), None
    if kind == "link":
        from scanners import url_scanner as us
        try:
            url = us.normalize_url(value)
            host = (us.urlparse(url).hostname or "").lower()
        except Exception:
            return None, None
        if not host:
            return None, None
        reg = host if us.is_ip(host) else us.registered_domain(host)
        hosting = any(host == h or host.endswith("." + h) for h in us.FREE_HOSTING)
        trusted = reg in us.TRUSTED_DOMAINS or host.endswith((".gov.in", ".nic.in", ".bank.in"))
        popular = (us.popularity_rank(reg) or 10**9) <= 20_000
        shared = hosting or reg in us.OFFICIAL_SHORTENERS or reg in us.SHORTENER_DOMAINS
        if (trusted or popular) and not hosting:
            return None, None            # real, well-known websites can't be reported
        page = url.split("#")[0].rstrip("/").lower()
        return page, (None if shared or popular else reg)
    return None, None


def _count_key(kind, norm):
    return ("count", kind, norm)


def report_count(kind: str, value: str) -> int:
    """How many different people reported this (the link's whole website counts too)."""
    if not store.enabled():
        return 0
    norm, site = normalize(kind, value)
    if not norm:
        return 0
    best = 0
    for k, n in ((kind, norm), ("site", site)):
        if not n:
            continue
        with _cache_lock:
            hit = _cache.get((k, n))
        if hit and time.time() - hit[0] < 60:
            c = hit[1]
        else:
            got = store.get("report", _count_key(k, n))
            c = int(got) if isinstance(got, (int, float)) else 0
            with _cache_lock:
                _cache[(k, n)] = (time.time(), c)
                if len(_cache) > 5000:
                    _cache.clear()
        best = max(best, c)
    return best


def community_signal(kind: str, value: str):
    """(finding, points) when enough people reported it, else None."""
    n = report_count(kind, value)
    if n < REPORT_THRESHOLD:
        return None
    points = 50 if n >= 10 else (35 if n >= 5 else 25)
    return f"Reported as a scam by {n} StaySafe users", points


def _reporter_id() -> str:
    from scanners.security import client_ip
    return hashlib.sha256(("reporter:" + client_ip()).encode()).hexdigest()[:24]


def add_report(kind: str, value: str) -> dict:
    if kind not in KINDS:
        return {"ok": False, "reason": "invalid"}
    if not store.enabled():
        return {"ok": False, "reason": "unavailable"}
    norm, site = normalize(kind, value)
    if not norm:
        return {"ok": False, "reason": "not_reportable"}
    who = _reporter_id()
    day = int(time.time() // 86400)
    ok, daily = store.command(["INCR", store.key("report", ("day", who, day))])
    if not ok or not isinstance(daily, int):
        return {"ok": False, "reason": "unavailable"}
    if daily == 1:
        store.command(["EXPIRE", store.key("report", ("day", who, day)), 2 * 86400])
    if daily > REPORTS_PER_DAY:
        return {"ok": False, "reason": "limit"}
    # one report per person per item
    ok, first = store.command(["SET", store.key("report", ("by", kind, norm, who)), "1", "NX", "EX", KEEP])
    if not ok:
        return {"ok": False, "reason": "unavailable"}
    if first is None:
        return {"ok": True, "already": True}
    for k, n in ((kind, norm), ("site", site)):
        if not n:
            continue
        ck = store.key("report", _count_key(k, n))
        _ok, c = store.command(["INCR", ck])
        store.command(["EXPIRE", ck, KEEP])
        if isinstance(c, int):
            with _cache_lock:
                _cache[(k, n)] = (time.time(), c)
    return {"ok": True, "already": False}


@reports_bp.route("/api/report", methods=["POST"])
def report_route():
    data = request.get_json(silent=True) or {}
    kind = str(data.get("kind", ""))
    value = str(data.get("value", ""))[:500]
    if kind not in KINDS or not value.strip():
        return jsonify({"ok": False, "reason": "invalid"}), 400
    return jsonify(add_report(kind, value))
