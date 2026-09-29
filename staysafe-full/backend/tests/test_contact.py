"""Tests for the "Talk to a person" form. Run: python tests/test_contact.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scanners.url_scanner as url_scanner  # noqa: E402
url_scanner.OFFLINE = True
from app import app  # noqa: E402
from scanners import contact  # noqa: E402

c = app.test_client()
sent = []


class R:
    status_code = 200

    def json(self):
        return {"ok": True}


def setup():
    sent.clear()
    contact._per_ip.clear()
    os.environ.update(TELEGRAM_BOT_TOKEN="t", TELEGRAM_CHAT_ID="1")
    contact.requests.post = lambda url, **kw: (sent.append((url, kw.get("json"))), R())[1]


def test_not_available_without_services():
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "RESEND_API_KEY", "CONTACT_EMAIL"):
        os.environ.pop(k, None)
    assert c.get("/api/contact/status").get_json() == {"available": False}
    assert c.post("/api/contact", json={"message": "help me please", "email": "a@b.co"}).status_code == 503


def test_message_reaches_telegram_with_sensitive_numbers_hidden():
    setup()
    r = c.post("/api/contact", json={"message": "I lost 5000. My card 4111 1111 1111 1111 and OTP 482913 given to 9876543210",
                                     "phone": "98765 43210", "lost": "yes", "lang": "kn", "topic": "lost_money", "name": "Ravi"})
    assert r.status_code == 200 and r.get_json()["ref"].startswith("SS-"), r.get_json()
    text = sent[0][1]["text"]
    assert "URGENT" in text and "Kannada" in text and "wa.me/919876543210" in text
    assert "4111" not in text and "482913" not in text and "9876543210" in text   # phone kept, card/OTP hidden


def test_needs_a_way_to_reply_and_valid_details():
    setup()
    assert c.post("/api/contact", json={"message": "hello there"}).status_code == 400
    assert c.post("/api/contact", json={"message": "hello there", "email": "not-an-email"}).status_code == 400
    assert c.post("/api/contact", json={"message": "hello there", "phone": "123"}).status_code == 400
    assert not sent


def test_bots_and_floods_are_stopped():
    setup()
    r = c.post("/api/contact", json={"message": "buy cheap stuff", "email": "a@b.co", "website": "http://spam"})
    assert r.status_code == 200 and not sent                      # silently dropped
    codes = [c.post("/api/contact", json={"message": "hello again", "email": "a@b.co"},
                    headers={"CF-Connecting-IP": "203.0.113.50"}).status_code for _ in range(6)]
    assert codes[:5] == [200] * 5 and codes[5] == 429, codes


def test_html_in_message_is_escaped():
    setup()
    c.post("/api/contact", json={"message": "<b>hi</b><script>x</script>", "email": "a@b.co"})
    assert "<script>" not in sent[0][1]["text"] and "&lt;script&gt;" in sent[0][1]["text"]


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
