"""
Tests for the careful use of free services (quota.py) and the one-request Gemini check.
Run from the backend folder:  python tests/test_quota.py
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scanners.url_scanner as url_scanner  # noqa: E402
url_scanner.OFFLINE = True
from scanners.quota import Quota  # noqa: E402


def test_waits_for_next_free_slot_instead_of_skipping():
    q = Quota("t", per_minute=2, per_day=100, window=1.0)
    assert q.take() and q.take()
    t = time.time()
    assert q.take(wait=3)                      # third call waits for the window to free up
    assert 0.7 <= time.time() - t <= 2.5
    assert q.status()["used_today"] == 3


def test_gives_up_when_wait_would_be_too_long():
    q = Quota("t", per_minute=1, per_day=100, window=5.0)
    assert q.take()
    t = time.time()
    assert not q.take(wait=0.5)
    assert time.time() - t < 0.2               # doesn't even sleep when it can't make it


def test_daily_cap_is_never_passed_and_keeps_reserve_for_important_calls():
    q = Quota("t", per_minute=None, per_day=20)
    for _ in range(19):
        assert q.take(priority="high")
    assert not q.take(priority="normal")       # last 5% kept for decisive calls
    assert q.take(priority="high")
    assert not q.take(priority="high")         # hard cap


def test_low_priority_is_spread_over_the_day():
    q = Quota("t", per_minute=None, per_day=1000)
    q.day_offset = -((time.time()) % 86400)    # pretend it's just after midnight
    used = 0
    while q.take(priority="low"):
        used += 1
    assert 100 <= used <= 200, used            # about 15% early in the day
    assert q.take(priority="normal")           # normal calls still go


def test_service_saying_too_many_pauses_and_then_resumes():
    q = Quota("t", per_minute=10, per_day=100, window=1.0)
    q.cool_down(0.6)
    assert not q.take(wait=0.1)
    assert q.take(wait=1.5)
    q.close_day()
    assert not q.take(wait=5, priority="high")


def test_many_threads_never_exceed_the_minute_limit():
    q = Quota("t", per_minute=3, per_day=100, window=1.0, max_waiters=20)
    stamps, lock = [], threading.Lock()

    def worker():
        if q.take(wait=4):
            with lock:
                stamps.append(time.time())

    threads = [threading.Thread(target=worker) for _ in range(9)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert len(stamps) == 9
    stamps.sort()
    for i in range(len(stamps) - 3):
        assert stamps[i + 3] - stamps[i] >= 0.95, stamps


def test_combined_gemini_request_fills_all_three_answers_with_one_call():
    import json
    from scanners import gemini_combo, translator, ai_review
    from scanners.quota import quota
    calls = []

    class Resp:
        status_code = 200

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": json.dumps({
                "source_language": "kn", "english": "Your SBI account will be blocked today. Call [#1] now",
                "translation": "आपका SBI खाता आज बंद हो जाएगा। अभी [#1] पर कॉल करें",
                "verdict": "scam", "category": "bank", "confidence": 90})}]}}]}

    real_post, real_key = translator.requests.post, os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = "test"
        translator.requests.post = lambda *a, **k: (calls.append(1), Resp())[1]
        text = "ನಿಮ್ಮ SBI ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ಈಗಲೇ 9876543210 ಗೆ ಕರೆ ಮಾಡಿ"
        before = quota("gemini").status()["used_today"]
        assert gemini_combo.prefetch(text, "hi")
        assert len(calls) == 1 and quota("gemini").status()["used_today"] == before + 1
        en = translator.cached_translation(text, "en")
        hi = translator.cached_translation(text, "hi")
        assert "9876543210" in en["text"] and "9876543210" in hi["text"]      # numbers put back
        assert ai_review.review(text)["verdict"] == "scam"                      # no new request
        assert translator.translate(text, "en")["provider"] == "gemini" and len(calls) == 1
        # nothing left to ask: no second request
        assert not gemini_combo.prefetch(text, "hi") and len(calls) == 1
    finally:
        translator.requests.post = real_post
        if real_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = real_key


def test_limit_refusal_is_not_remembered_as_an_answer():
    from scanners.url_scanner import _cached, NOT_CHECKED
    n = {"calls": 0}

    def call():
        n["calls"] += 1
        return {"status": "skip", NOT_CHECKED: True} if n["calls"] == 1 else {"status": "pass"}

    assert _cached(("urlscan", "t.example"), call)["status"] == "skip"
    assert _cached(("urlscan", "t.example"), call)["status"] == "pass"   # asked again, not cached
    assert _cached(("urlscan", "t.example"), call)["status"] == "pass" and n["calls"] == 2


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
