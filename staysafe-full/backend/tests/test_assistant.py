"""Tests for the automatic assistant. Run: python tests/test_assistant.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scanners.url_scanner as url_scanner  # noqa: E402
url_scanner.OFFLINE = True
from app import app  # noqa: E402
from scanners import assistant  # noqa: E402
from scanners.quota import QUOTAS  # noqa: E402

c = app.test_client()
seen = []


def fake(reply_obj, status=200):
    class R:
        status_code = status
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": json.dumps(reply_obj)}}]}

    def post(url, **kw):
        seen.append(kw.get("json"))
        return R()
    return post


def setup(reply_obj):
    seen.clear()
    assistant._ip_hits.clear()
    for q in QUOTAS.values():
        q.reset()
    os.environ["GROQ_API_KEY"] = "k"
    assistant.requests.post = fake(reply_obj)


def test_answers_with_safe_steps_and_buttons():
    setup({"reply": "Please call 1930 now and your bank. Report at cybercrime.gov.in.", "urgent": True,
           "actions": ["incident", "person", "hack-the-planet"]})
    r = c.post("/api/assistant", json={"message": "sir money cut from acount what do", "lang": "en"})
    d = r.get_json()
    assert r.status_code == 200 and d["urgent"] and d["actions"] == ["incident", "person"], d
    assert "cybercrime.gov.in" in d["reply"]


def test_personal_numbers_never_leave_and_come_back_in_reply():
    setup({"reply": "Don't share the OTP. Block card [#1] with your bank.", "urgent": True, "actions": []})
    r = c.post("/api/assistant", json={"message": "my card 4111 1111 1111 1111 otp 482913 given", "lang": "en"})
    sent = json.dumps(seen[0])
    assert "4111 1111 1111 1111" not in sent and "482913" not in sent
    assert "4111 1111 1111 1111" in r.get_json()["reply"]          # the visitor's own number put back for them


def test_unknown_links_and_long_dashes_are_removed():
    setup({"reply": "Visit https://evil-refund.xyz/claim or sancharsaathi.gov.in — now", "urgent": False, "actions": []})
    d = c.post("/api/assistant", json={"message": "fraud call came", "lang": "en"}).get_json()
    assert "evil-refund" not in d["reply"] and "sancharsaathi.gov.in" in d["reply"] and "—" not in d["reply"]


def test_reply_language_and_history_are_sent():
    setup({"reply": "ಸರಿ", "urgent": False, "actions": []})
    c.post("/api/assistant", json={"message": "ನನ್ನ ಹಣ ಹೋಯ್ತು", "lang": "kn",
                                   "history": [{"role": "user", "text": "hi"}, {"role": "assistant", "text": "Hello"}]})
    msgs = seen[0]["messages"]
    assert "Reply in Kannada" in msgs[0]["content"] and len(msgs) == 4 and "<visitor>" in msgs[-1]["content"]


def test_not_available_and_flood_limits():
    for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_AI_TOKEN"):
        os.environ.pop(k, None)
    assert c.get("/api/assistant/status").get_json() == {"available": False}
    assert c.post("/api/assistant", json={"message": "hello there"}).status_code == 503
    setup({"reply": "ok", "urgent": False, "actions": []})
    codes = [c.post("/api/assistant", json={"message": "question"}, headers={"CF-Connecting-IP": "203.0.113.77"}).status_code
             for _ in range(7)]
    assert codes[:6] == [200] * 6 and codes[6] == 429, codes


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
