"""Tests for the "Talk to a person" form. Run: python tests/test_contact.py"""
import os
import re
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


def test_feedback_reaches_telegram_anonymously():
    setup()
    contact._fb_per_ip.clear()
    r = c.post("/api/feedback", json={"stars": 5, "topics": ["love", "idea", "nonsense"], "lang": "tcy", "from": "ai",
                                      "message": "Super app! Add WhatsApp sharing. My OTP 482913"})
    assert r.status_code == 200, r.get_json()
    text = sent[0][1]["text"]
    assert "⭐⭐⭐⭐⭐" in text and "5/5" in text and "Tulu" in text and "AI helper" in text
    assert "New idea" in text and "nonsense" not in text and "482913" not in text
    assert c.post("/api/feedback", json={"stars": 0}).status_code == 400
    assert c.post("/api/feedback", json={"stars": 9}).status_code == 400
    r = c.post("/api/feedback", json={"stars": 2})                       # stars alone are fine
    assert r.status_code == 200 and "☆☆☆" in sent[-1][1]["text"]


class FakeRedis:
    def __init__(self): self.h, self.l, self.s = {}, {}, {}
    def __call__(self, cmd, cost=1):
        op, key = cmd[0], cmd[1]
        if op == "HINCRBY":
            d = self.h.setdefault(key, {}); d[cmd[2]] = d.get(cmd[2], 0) + int(cmd[3]); return True, d[cmd[2]]
        if op == "HGETALL":
            d = self.h.get(key, {}); return True, [x for kv in d.items() for x in (kv[0], str(kv[1]))]
        if op == "LPUSH":
            self.l.setdefault(key, []).insert(0, cmd[2]); return True, len(self.l[key])
        if op == "LTRIM":
            self.l[key] = self.l.get(key, [])[cmd[2]:cmd[3] + 1]; return True, "OK"
        if op == "LRANGE":
            return True, self.l.get(key, [])[cmd[2]:cmd[3] + 1]
        if op == "SADD":
            self.s.setdefault(key, set()).add(cmd[2]); return True, 1
        if op == "SMEMBERS":
            return True, list(self.s.get(key, set()))
        return True, None


def test_ratings_are_kept_counted_and_only_shared_words_shown():
    from scanners import store, ratings
    setup(); contact._fb_per_ip.clear()
    fake = FakeRedis()
    saved = (store.enabled, store.command)
    store.enabled, store.command = (lambda: True), fake
    try:
        ratings._summary["at"] = 0
        c.post("/api/feedback", json={"stars": 5, "message": "Saved my mother from a KYC scam! Call me 9876543210", "share": True})
        c.post("/api/feedback", json={"stars": 4, "message": "Good but the bc translation is slow", "share": True})
        c.post("/api/feedback", json={"stars": 2, "message": "private: my bank details are wrong", "share": False})
        c.post("/api/feedback", json={"stars": 5})
        s = c.get("/api/feedback/summary").get_json()
        assert s["count"] == 4 and s["average"] == 4.0 and s["stars"]["5"] == 2, s
        words = [r["text"] for r in s["reviews"]]
        assert len(words) == 1 and "Saved my mother" in words[0] and "9876543210" not in words[0], words   # rude + private kept off
        tg = [m[1]["text"] for m in sent if "Hide this review" in m[1].get("text", "")]
        link = re.search(r'href="([^"]+)"', tg[0]).group(1).replace("&amp;", "&")
        rid, token = re.search(r"id=(\w+)&token=([\w-]+)", link).groups()
        assert c.get(f"/api/feedback/hide?id={rid}&token=wrong").status_code == 404
        assert c.get(f"/api/feedback/hide?id={rid}&token={token}").status_code == 200
        assert c.get("/api/feedback/summary").get_json()["reviews"] == []          # hidden from the page
        assert c.get("/api/feedback/summary").get_json()["count"] == 4             # still counted
    finally:
        store.enabled, store.command = saved


def test_feedback_goes_to_its_own_bot_when_set():
    setup(); contact._fb_per_ip.clear()
    os.environ.update(FEEDBACK_BOT_TOKEN="fbtoken", FEEDBACK_CHAT_ID="99")
    try:
        c.post("/api/feedback", json={"stars": 4, "message": "nice"})
        c.post("/api/contact", json={"message": "help me please", "email": "a@b.co"})
        fb = [u for u, j in sent if j and "new feedback" in j.get("text", "")]
        msg = [u for u, j in sent if j and "New message" in j.get("text", "")]
        assert fb and "botfbtoken" in fb[0] and [j for u, j in sent if "new feedback" in j.get("text", "")][0]["chat_id"] == "99"
        assert msg and "bott/" in msg[0]                     # "Write to us" keeps its own bot
    finally:
        os.environ.pop("FEEDBACK_BOT_TOKEN", None); os.environ.pop("FEEDBACK_CHAT_ID", None)


def test_feedback_falls_back_to_contact_bot_when_its_bot_fails():
    setup(); contact._fb_per_ip.clear()
    os.environ.update(FEEDBACK_BOT_TOKEN="broken", FEEDBACK_CHAT_ID="99")

    class Bad:
        status_code = 400

        def json(self):
            return {"ok": False}
    contact.requests.post = lambda url, **kw: (sent.append((url, kw.get("json"))), Bad() if "botbroken" in url else R())[1]
    try:
        r = c.post("/api/feedback", json={"stars": 5, "message": "good"})
        assert r.status_code == 200, r.get_json()
        urls = [u for u, j in sent if j and "new feedback" in j.get("text", "")]
        assert "botbroken" in urls[0] and "bott/" in urls[-1]      # tried its own bot, then the "Write to us" bot
    finally:
        os.environ.pop("FEEDBACK_BOT_TOKEN", None); os.environ.pop("FEEDBACK_CHAT_ID", None)


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
