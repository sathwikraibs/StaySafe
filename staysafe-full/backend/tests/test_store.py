"""Long memory (Upstash Redis over HTTPS), with Redis faked in memory.
Run: python tests/test_store.py"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["UPSTASH_REDIS_REST_URL"] = "https://fake.upstash.io"
os.environ["UPSTASH_REDIS_REST_TOKEN"] = "t"
from scanners import store  # noqa: E402

DB, CALLS = {}, []


class _R:
    def __init__(self, d, code=200): self._d, self.status_code = d, code
    def json(self): return self._d


def fake_post(url, json=None, **kw):
    CALLS.append(json)
    if json[0] == "SET":
        DB[json[1]] = json[2]
        return _R({"result": "OK"})
    if json[0] == "GET":
        return _R({"result": DB.get(json[1])})
    return _R({"error": "unknown"})


store.requests.post = fake_post


def wait_writes():
    time.sleep(0.3)


def test_link_results_survive_a_restart():
    import scanners.url_scanner as us
    n = {"calls": 0}

    def call():
        n["calls"] += 1
        return {"status": "ok", "malicious": 5, "domain_malicious": 0}
    first = us._cached(("vt", "http://scam.example/x"), call)
    wait_writes()
    us._CACHE.clear()                                   # the server restarted
    second = us._cached(("vt", "http://scam.example/x"), call)
    assert n["calls"] == 1 and second == first
    assert not any("scam.example" in k for k in DB)     # keys are fingerprints, not the link


def test_skipped_checks_are_never_kept():
    import scanners.url_scanner as us
    before = len(DB)
    us._cached(("vt", "http://other.example/"), lambda: {"status": "skip", "error": True})
    us._cached(("vt", "http://busy.example/"), lambda: {us.NOT_CHECKED: True})
    wait_writes()
    assert len(DB) == before


def test_ai_verdict_kept_without_the_message():
    from scanners import ai_review
    ai_review.remember_verdict("k1", {"verdict": "scam", "category": "kyc", "confidence": 90, "provider": "x"})
    wait_writes()
    ai_review._cache.clear()
    got = ai_review.known_verdict("k1")
    assert got and got["verdict"] == "scam"
    stored = [c for c in CALLS if c[0] == "SET" and c[1].startswith("ss1:ai:")][-1]
    assert stored[4] == 7 * 86400 and "verdict" in stored[2]


def test_daily_allowances_survive_a_restart():
    from scanners.quota import quota
    q = quota("urlscan")
    q.reset()
    for _ in range(7):
        q.take()
    used = q._day_used
    assert used == 7
    store.save_quota_days()
    q.reset()                                           # the server restarted
    store.load_quota_days()
    assert q._day_used == used


def test_problems_never_break_a_check():
    def boom(*a, **k):
        raise TimeoutError
    store.requests.post = boom
    store._state["down_until"] = 0
    assert store.get("link", "x") is None
    t = time.time()
    assert store.get("link", "y") is None and time.time() - t < 0.1   # stops trying for a minute
    store.requests.post = fake_post
    store._state["down_until"] = 0


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
