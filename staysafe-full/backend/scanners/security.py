"""
TrustLight - Protection for the API itself
-----------------------------------------
- Fair-use limits per visitor, so nobody can use up the free daily quotas of the checking
  services (VirusTotal, Google, urlscan...) that every visitor shares.
- Only TrustLight's own website may call the API from a browser (CORS).
- Safe HTTP headers on every answer; scan results are never cached anywhere.
- The detailed status page and the screenshot self-test need a secret key (STATUS_KEY),
  so outsiders can't see which services are set up or run heavy tests.
- The link opener only ever connects to public internet addresses on normal web ports,
  checked at the moment of connecting (so a domain can't switch to an internal address).
"""

import hmac
import os
import re
import socket
import threading
import time
from collections import defaultdict, deque

from flask import jsonify, request

# --------------------------------------------------------------------------
# Who is calling
# --------------------------------------------------------------------------
def client_ip() -> str:
    """
    The visitor's address. Cloudflare / Render set these headers themselves (a visitor can't
    fake them through the proxy); X-Forwarded-For's last entry is the one the proxy added.
    """
    for header in ("CF-Connecting-IP", "True-Client-IP"):
        v = (request.headers.get(header) or "").strip()
        if v:
            return v[:64]
    xff = [p.strip() for p in (request.headers.get("X-Forwarded-For") or "").split(",") if p.strip()]
    if xff:
        return xff[-1][:64]
    return (request.remote_addr or "unknown")[:64]


# --------------------------------------------------------------------------
# Fair-use limits
# --------------------------------------------------------------------------
# path prefix -> (requests allowed, per seconds)
HEAVY = ("/api/scan-file", "/api/scan-screenshot", "/api/scan-qr")
LIMITS = {
    "heavy": (int(os.environ.get("LIMIT_HEAVY", "15")), 600),     # uploads: 15 per 10 minutes
    "scan": (int(os.environ.get("LIMIT_SCAN", "40")), 600),       # other checks: 40 per 10 minutes
    "global": (int(os.environ.get("LIMIT_GLOBAL", "900")), 3600),  # everyone together: 900 an hour
}
_hits: "defaultdict[tuple, deque]" = defaultdict(deque)
_lock = threading.Lock()
LIMIT_MESSAGE = "You've done a lot of checks in a short time. Please wait a few minutes and try again."


def _allow(key: tuple, limit: int, window: int) -> bool:
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        if len(_hits) > 20000:  # forget idle visitors
            for k in [k for k, v in _hits.items() if not v or now - v[-1] > 3600][:5000]:
                _hits.pop(k, None)
        return True


def check_rate_limit():
    """Flask before_request hook. Returns a 429 answer when a visitor is over the limit."""
    path = request.path or ""
    if not path.startswith("/api/") or request.method == "OPTIONS" or path == "/api/telegram/webhook":
        return None  # each Telegram chat is limited separately when its check runs
    counted = request.method == "POST" or path.startswith(("/api/file-report", "/api/check-network"))
    if not counted:
        return None
    ip = client_ip()
    kind = "heavy" if path.startswith(HEAVY) else "scan"
    limit, window = LIMITS[kind]
    if not _allow((kind, ip), limit, window):
        return jsonify({"error": LIMIT_MESSAGE}), 429
    glimit, gwindow = LIMITS["global"]
    if not _allow(("global",), glimit, gwindow):
        return jsonify({"error": LIMIT_MESSAGE}), 429
    return None


# --------------------------------------------------------------------------
# Which websites may call the API from a browser
# --------------------------------------------------------------------------
def allowed_origins() -> list:
    extra = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
    return extra + [
        "https://staysafe-tool.vercel.app",  # add preview or custom domains with ALLOWED_ORIGINS
        re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"),    # local development
    ]


# --------------------------------------------------------------------------
# Safe headers
# --------------------------------------------------------------------------
def add_security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if (request.path or "").startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"  # results can contain private messages
    return resp


# --------------------------------------------------------------------------
# Secret key for the detailed status page and the screenshot self-test
# --------------------------------------------------------------------------
def has_status_key() -> bool:
    key = os.environ.get("STATUS_KEY", "")
    given = request.args.get("key", "") or request.headers.get("X-Status-Key", "")
    return bool(key) and hmac.compare_digest(key.encode(), given.encode())


# --------------------------------------------------------------------------
# Uploaded files: never unpack more than a small amount (stops "zip bombs")
# --------------------------------------------------------------------------
ZIP_PART_LIMIT = 5 * 1024 * 1024


def safe_zip_read(z, name: str, limit: int = ZIP_PART_LIMIT) -> bytes:
    """Read one file from inside a zip, but never more than `limit` bytes of unpacked data."""
    info = z.getinfo(name)
    if info.file_size > limit:
        raise ValueError("part too large")
    with z.open(info) as f:
        return f.read(limit + 1)[:limit]


# Pictures: refuse images with absurd pixel counts (a tiny file that expands to gigabytes)
MAX_IMAGE_PIXELS = 40_000_000
try:
    from PIL import Image as _Image
    _Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
except Exception:  # pragma: no cover
    pass


# --------------------------------------------------------------------------
# The link opener may only connect to the public internet
# --------------------------------------------------------------------------
SAFE_PORTS = {80, 443, 8080, 8443}
_guard = threading.local()


def install_connection_guard(is_public_ip) -> None:
    """
    Wraps the low-level connect of the HTTP library. While `guarded_fetch()` is active in a
    thread, every connection is resolved and checked right before connecting, and only
    public addresses on normal web ports are allowed. This stops "DNS rebinding", where a
    domain answers with a public address when checked and an internal one when used.
    """
    import urllib3.util.connection as uc
    if getattr(uc, "_staysafe_guarded", False):
        return
    original = uc.create_connection

    def guarded(address, *args, **kwargs):
        if not getattr(_guard, "on", False):
            return original(address, *args, **kwargs)
        host, port = address
        if int(port) not in SAFE_PORTS:
            raise ConnectionError(f"blocked port {port}")
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        ips = [info[4][0] for info in infos]
        if not ips or not all(is_public_ip(ip) for ip in ips):
            raise ConnectionError("blocked non-public address")
        return original((ips[0], port), *args, **kwargs)

    uc.create_connection = guarded
    uc._staysafe_guarded = True


class guarded_fetch:
    """with guarded_fetch(): ...  -> connections inside only go to the public internet."""

    def __enter__(self):
        _guard.on = True
        return self

    def __exit__(self, *exc):
        _guard.on = False
        return False
