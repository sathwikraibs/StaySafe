"""Telegram bot: checks arrive through the webhook and replies go back (Telegram is faked).
Run: python tests/test_telegram.py"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TELEGRAM_SCAN_BOT_TOKEN"] = "123:TEST"
import scanners.url_scanner as us  # noqa: E402
us.OFFLINE = True
import scanners.telegram_bot as tg  # noqa: E402
import app as appmod  # noqa: E402

sent = []


class _R:
    def __init__(self, data): self._d = data
    def json(self): return self._d


def fake_post(url, json=None, **kw):
    if url.endswith("/sendMessage"):
        sent.append(json)
    return _R({"ok": True, "result": {"username": "TestBot"}})


tg.requests.post = fake_post
tg.requests.get = lambda url, **kw: _R({"ok": True, "result": {"username": "TestBot"}})
client = appmod.app.test_client()
H = {"X-Telegram-Bot-Api-Secret-Token": tg._secret()}
_uid = [100]


def send(text, lang="en", chat=42):
    sent.clear()
    _uid[0] += 1
    upd = {"update_id": _uid[0], "message": {"message_id": 1, "chat": {"id": chat, "type": "private"},
                                             "from": {"language_code": lang}, "text": text}}
    r = client.post("/api/telegram/webhook", json=upd, headers=H)
    assert r.status_code == 200
    for _ in range(300):
        if sent:
            break
        time.sleep(0.1)
    assert sent, "no reply"
    return sent[-1]["text"]


def test_needs_the_secret():
    r = client.post("/api/telegram/webhook", json={"update_id": 1}, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"})
    assert r.status_code == 403


def test_start_and_language():
    assert "StaySafe" in send("/start")
    assert "हिन्दी" in send("/hi", chat=7)
    tg._LANG.clear()


def test_scam_message_number_and_upi():
    out = send("Dear customer your SBI account is blocked. Update KYC now at http://sbi-kyc-update.xyz or call 9876543210")
    assert "scam" in out.lower() or "careful" in out.lower(), out
    out = send("+92 300 1234567")
    assert "Foreign number" in out, out
    out = send("sbi.refund@ybl", lang="kn")
    assert "ಎಚ್ಚರ" in out and "refund" in out, out


def test_groups_are_ignored():
    sent.clear()
    client.post("/api/telegram/webhook", headers=H, json={"update_id": 999, "message": {
        "message_id": 1, "chat": {"id": -5, "type": "group"}, "text": "hello"}})
    time.sleep(1)
    assert not sent


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
    os._exit(1 if failed else 0)
