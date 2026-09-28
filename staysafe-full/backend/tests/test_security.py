"""
StaySafe security tests: fair-use limits, allowed websites, safe headers, hidden status
details, the link opener's address guard, zip bombs and long inputs.

Run from the backend folder (no internet needed):
    python tests/test_security.py
"""
import io
import os
import socket
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scanners.url_scanner as url_scanner  # noqa: E402

url_scanner.OFFLINE = True
os.environ["STATUS_KEY"] = "test-key-123"

from app import app  # noqa: E402
from scanners import security  # noqa: E402

client = app.test_client()


def _fresh_limits():
    security._hits.clear()


def test_status_page_hides_details_without_key():
    body = client.get("/").get_json()
    assert set(body) == {"status", "ocr", "qr"}, body
    full = client.get("/?key=test-key-123").get_json()
    assert "link_checks" in full and "translation" in full
    assert set(client.get("/?key=wrong").get_json()) == {"status", "ocr", "qr"}


def test_ocr_self_test_needs_key():
    assert client.get("/api/ocr-check").status_code == 404


def test_security_headers():
    r = client.get("/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    r = client.post("/api/scan-message", json={"text": "hello"})
    assert r.headers["Cache-Control"] == "no-store"


def test_only_staysafe_site_can_call_from_browser():
    ok = client.post("/api/scan-message", json={"text": "hi"}, headers={"Origin": "https://staysafe-tool.vercel.app"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "https://staysafe-tool.vercel.app"
    bad = client.post("/api/scan-message", json={"text": "hi"}, headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in bad.headers
    copy = client.post("/api/scan-message", json={"text": "hi"}, headers={"Origin": "https://staysafe-copy.vercel.app"})
    assert "Access-Control-Allow-Origin" not in copy.headers
    trick = client.post("/api/scan-message", json={"text": "hi"}, headers={"Origin": "https://staysafe-x.vercel.app.evil.com"})
    assert "Access-Control-Allow-Origin" not in trick.headers


def test_fair_use_limit_returns_429():
    _fresh_limits()
    old = security.LIMITS["scan"]
    security.LIMITS["scan"] = (3, 600)
    try:
        h = {"CF-Connecting-IP": "203.0.113.9"}
        codes = [client.post("/api/scan-message", json={"text": "hi"}, headers=h).status_code for _ in range(4)]
        assert codes[:3] == [200, 200, 200] and codes[3] == 429, codes
        # another visitor is not affected
        assert client.post("/api/scan-message", json={"text": "hi"}, headers={"CF-Connecting-IP": "203.0.113.10"}).status_code == 200
        # reading the scam library is never limited
        assert client.get("/api/scam-library", headers=h).status_code == 200
    finally:
        security.LIMITS["scan"] = old
        _fresh_limits()


def test_guard_blocks_private_addresses_and_odd_ports():
    import urllib3.util.connection as uc
    real = socket.getaddrinfo
    try:
        socket.getaddrinfo = lambda host, port, *a, **k: [(2, 1, 6, "", ("127.0.0.1", port))]
        with security.guarded_fetch():
            for addr in (("rebind.example", 443), ("x.example", 22)):
                try:
                    uc.create_connection(addr, timeout=1)
                    raise AssertionError(f"connection to {addr} was allowed")
                except ConnectionError:
                    pass
        socket.getaddrinfo = lambda host, port, *a, **k: [(2, 1, 6, "", ("169.254.169.254", port))]
        with security.guarded_fetch():
            try:
                uc.create_connection(("meta.example", 80), timeout=1)
                raise AssertionError("cloud metadata address was allowed")
            except ConnectionError:
                pass
    finally:
        socket.getaddrinfo = real
    assert not url_scanner._public_ip("::ffff:127.0.0.1")
    assert not url_scanner._public_ip("10.0.0.5") and url_scanner._public_ip("8.8.8.8")


def test_zip_bomb_is_not_unpacked():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("AndroidManifest.xml", b"\0" * (30 * 1024 * 1024))
        z.writestr("classes.dex", b"dex")
    from scanners.apk_check import analyze_apk
    t = time.time()
    out = analyze_apk("x.apk", buf.getvalue())
    assert out["package"] == "" and time.time() - t < 2
    with zipfile.ZipFile(buf) as z:
        try:
            security.safe_zip_read(z, "AndroidManifest.xml", 1024)
            raise AssertionError("big part was read")
        except ValueError:
            pass


def test_huge_picture_is_refused_politely():
    from PIL import Image
    assert Image.MAX_IMAGE_PIXELS == security.MAX_IMAGE_PIXELS


def test_long_inputs_are_capped():
    _fresh_limits()
    r = client.post("/api/check-password", json={"password": "a" * 5000})
    assert r.status_code == 400
    r = client.post("/api/check-password", json={"password": ["x"]})
    assert r.status_code == 400
    t = time.time()
    r = client.post("/api/scan-message", json={"text": "click http://a.co " * 20000})
    assert r.status_code == 200 and time.time() - t < 20
    r = client.post("/api/incident-plan", json={"incident_type": {"a": 1}})
    assert r.status_code in (400, 404)
    _fresh_limits()


def test_page_text_strip_is_fast_on_hostile_html():
    html = "<script>" * 30000 + "x" * 100000
    t = time.time()
    url_scanner._strip_blocks(html)
    url_scanner._page_title("<title>" * 50000)
    assert time.time() - t < 1
    assert url_scanner._strip_blocks("a<script>bad()</script>b<style>x{}</style>c").replace(" ", "") == "abc"
    assert url_scanner._page_title("<html><TITLE> Pay  now </title>") == "Pay now"


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
