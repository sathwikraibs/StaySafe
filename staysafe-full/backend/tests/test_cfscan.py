"""Cloudflare URL Scanner, with Cloudflare faked.
Run: python tests/test_cfscan.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["CLOUDFLARE_ACCOUNT_ID"] = "acct"
os.environ["CLOUDFLARE_SCAN_TOKEN"] = "tok"
import scanners.url_scanner as us  # noqa: E402

us.OFFLINE = False
us.time.sleep = lambda s: None
SENT = []


class _R:
    def __init__(self, code, data=None): self.status_code, self._d = code, data
    def json(self): return self._d


def make(polls_before_ready, malicious):
    state = {"n": 0}

    def post(url, json=None, **kw):
        SENT.append(json["url"])
        return _R(200, {"uuid": "abc"})

    def get(url, **kw):
        state["n"] += 1
        if state["n"] <= polls_before_ready:
            return _R(404)
        return _R(200, {"verdicts": {"overall": {"malicious": malicious, "categories": [{"name": "Phishing"}]}}})
    us.requests.post, us.requests.get = post, get


def test_harmful_page_is_found():
    us._CACHE.clear()
    make(2, True)
    r = us.check_cloudflare_scan("http://new-bank-login.example/verify")
    assert r == {"status": "fail", "categories": ["Phishing"]}, r


def test_personal_details_are_not_sent():
    us._CACHE.clear()
    make(0, False)
    us.check_cloudflare_scan("http://x.example/reset?email=ravi@gmail.com&t=1")
    assert SENT[-1] == "http://x.example/reset", SENT[-1]
    us.check_cloudflare_scan("http://y.example/p?lang=en")
    assert SENT[-1] == "http://y.example/p?lang=en"


def test_slow_scan_is_picked_up_next_time():
    us._CACHE.clear()
    us._CF_PENDING.clear()
    make(10**12, True)
    first = us.check_cloudflare_scan("http://slow.example/a", wait=1)
    assert first["status"] == "skip"
    n = len(SENT)
    make(0, True)
    second = us.check_cloudflare_scan("http://slow.example/a", wait=5)
    assert second["status"] == "fail" and len(SENT) == n      # same scan, not a new one


def test_otx_reports():
    us._CACHE.clear()
    os.environ["OTX_API_KEY"] = "k"
    us.requests.get = lambda url, **kw: _R(200, {"pulse_info": {"pulses": [
        {"name": "SBI phishing kit domains", "tags": ["phishing", "india"]},
        {"name": "Fake KYC smishing", "tags": []}]}})
    r = us.check_otx("sbi-kyc-update.xyz")
    assert r["status"] == "warn" and r["pulses"] == 2 and r["what"] == "phishing", r
    us._CACHE.clear()
    us.requests.get = lambda url, **kw: _R(200, {"pulse_info": {"pulses": [{"name": "Top sites list", "tags": ["alexa"]}]}})
    assert us.check_otx("someshop.in")["status"] == "pass"
    us._CACHE.clear()
    us.requests.get = lambda url, **kw: _R(200, {"validation": [{"source": "majestic"}], "pulse_info": {"pulses": [
        {"name": "phishing", "tags": []}]}})
    assert us.check_otx("bigsite.com")["status"] == "pass"


if __name__ == "__main__":
    failed = 0
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("test_"))
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
