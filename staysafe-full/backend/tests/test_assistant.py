"""Tests for the automatic assistant. Run: python tests/test_assistant.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scanners.url_scanner as url_scanner  # noqa: E402
url_scanner.OFFLINE = True
from app import app  # noqa: E402
from scanners import assistant, groq_client  # noqa: E402
from scanners.quota import QUOTAS  # noqa: E402

c = app.test_client()
seen = []


def fake(reply_obj, status=200, headers=None, usage=900):
    class R:
        status_code = status
        text = ""

        def __init__(self):
            self.headers = headers or {}

        def json(self):
            return {"choices": [{"message": {"content": json.dumps(reply_obj, ensure_ascii=False)}}],
                    "usage": {"total_tokens": usage}}

    def post(url, **kw):
        seen.append(kw.get("json"))
        return R()
    return post


def setup(reply_obj):
    seen.clear()
    assistant._ip_hits.clear()
    assistant._answers.clear()
    groq_client._models.clear()
    groq_client._gone.clear()
    for q in QUOTAS.values():
        q.reset()
    os.environ["GROQ_API_KEY"] = "k"
    groq_client.requests.post = fake(reply_obj)


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
    assert "use Kannada" in msgs[0]["content"] and len(msgs) == 4 and "<visitor>" in msgs[-1]["content"]


def test_not_available_and_flood_limits():
    for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_AI_TOKEN"):
        os.environ.pop(k, None)
    assert c.get("/api/assistant/status").get_json() == {"available": False}
    assert c.post("/api/assistant", json={"message": "hello there"}).status_code == 503
    setup({"reply": "ok", "urgent": False, "actions": []})
    codes = [c.post("/api/assistant", json={"message": "question"}, headers={"CF-Connecting-IP": "203.0.113.77"}).status_code
             for _ in range(7)]
    assert codes[:6] == [200] * 6 and codes[6] == 429, codes


def test_groq_limits_learned_from_headers_and_real_tokens_counted():
    setup({"reply": "ok", "urgent": False, "actions": []})
    groq_client.requests.post = fake({"reply": "ok", "urgent": False, "actions": []}, usage=1234, headers={
        "x-ratelimit-limit-requests": "1000", "x-ratelimit-remaining-requests": "990",
        "x-ratelimit-limit-tokens": "6000", "x-ratelimit-remaining-tokens": "4000", "x-ratelimit-reset-tokens": "7.5s"})
    c.post("/api/assistant", json={"message": "is this call a scam", "lang": "en"})
    m = groq_client.model(seen[0]["model"])
    assert m.requests.status()["used_today"] >= 10                   # Groq said 10 used today
    assert m.tokens.status()["per_minute"] == 6000                    # learned the real per-minute limit
    assert m.tokens.status()["used_today"] == 1234                    # real tokens, not our guess
    assert seen[0].get("reasoning_effort") == "medium" and seen[0]["model"] == "openai/gpt-oss-120b"


def test_moves_to_next_model_when_one_is_used_up_today():
    setup({"reply": "ok", "urgent": False, "actions": []})
    groq_client.model("openai/gpt-oss-120b").tokens.close_day()
    c.post("/api/assistant", json={"message": "is this call a scam", "lang": "en"})
    assert seen[0]["model"] == "llama-3.3-70b-versatile"


def test_thinks_less_when_allowance_runs_low():
    setup({"reply": "ok", "urgent": False, "actions": []})
    m = groq_client.model("openai/gpt-oss-120b")
    m.tokens.take(priority="high", cost=1)
    m.tokens._day_used = int(m.tokens.per_day * 0.8)
    c.post("/api/assistant", json={"message": "is this call a scam", "lang": "en"})
    assert seen[0].get("reasoning_effort") == "low"


def test_kannada_question_gets_kannada_answer():
    setup({"reply": "Please call 1930", "urgent": True, "actions": []})
    replies = iter([{"reply": "Please call 1930", "urgent": True, "actions": []},
                    {"reply": "ದಯವಿಟ್ಟು ಈಗಲೇ 1930 ಗೆ ಕರೆ ಮಾಡಿ", "urgent": True, "actions": []}])

    def post(url, **kw):
        seen.append(kw.get("json"))
        return fake(next(replies))(url, **kw)
    groq_client.requests.post = post
    d = c.post("/api/assistant", json={"message": "ನನ್ನ ಹಣ ಹೋಯ್ತು ಏನು ಮಾಡಲಿ", "lang": "en"}).get_json()
    assert "ಕರೆ" in d["reply"], d


def test_same_question_is_answered_from_memory():
    setup({"reply": "It is a scam.", "urgent": False, "actions": []})
    for _ in range(3):
        c.post("/api/assistant", json={"message": "is digital arrest real", "lang": "en"})
    assert len(seen) == 1


def test_indian_language_answers_go_to_gemini_first_english_to_groq():
    setup({"reply": "ok", "urgent": False, "actions": []})
    os.environ["GEMINI_API_KEY"] = "g"
    urls = []

    class R:
        status_code = 200
        headers = {}
        text = ""

        def __init__(self, url):
            self.url = url

        def json(self):
            body = json.dumps({"reply": "ಕರೆ ಕಡಿತಗೊಳಿಸಿ, ಹಣ ಕೊಡಬೇಡಿ.", "urgent": False, "actions": []}, ensure_ascii=False)
            if "generativelanguage" in self.url:
                return {"candidates": [{"content": {"parts": [{"text": body}]}}]}
            return {"choices": [{"message": {"content": json.dumps({"reply": "Hang up.", "urgent": False, "actions": []})}}],
                    "usage": {"total_tokens": 800}}

    def post(url, **kw):
        urls.append(url)
        return R(url)
    groq_client.requests.post = post
    try:
        d = c.post("/api/assistant", json={"message": "ಪೊಲೀಸ್ ಕರೆ ಬಂತು ಏನು ಮಾಡಲಿ", "lang": "kn"}).get_json()
        assert "generativelanguage" in urls[0] and "ಕರೆ" in d["reply"], (urls, d)
        urls.clear()
        c.post("/api/assistant", json={"message": "police called me what to do", "lang": "en"})
        assert "groq.com" in urls[0], urls
    finally:
        os.environ.pop("GEMINI_API_KEY", None)


def test_tulu_or_kannada_unsure_asks_then_uses_the_chosen_language():
    setup({"reply": "Is this Tulu or Kannada?", "urgent": False, "actions": [], "ask_language": True, "language": "kn"})
    d = c.post("/api/assistant", json={"message": "yenk ondu message bandh", "lang": "en"}).get_json()
    assert d["ask_language"] is True
    assert "Tulu words" in seen[0]["messages"][0]["content"]
    setup({"reply": "ಈ ಮೆಸೇಜ್ ಮೋಸ ಆದುಪ್ಪು", "urgent": False, "actions": [], "ask_language": True})
    d = c.post("/api/assistant", json={"message": "yenk ondu message bandh", "lang": "en", "reply_lang": "tcy"}).get_json()
    assert d["ask_language"] is False                                   # already chosen: never asks again
    assert "always reply in Tulu" in seen[0]["messages"][0]["content"]


def test_kannada_or_hindi_in_english_letters_goes_to_the_indian_language_writer():
    from scanners.assistant import _looks_indic_in_latin
    assert _looks_indic_in_latin("nanna account inda hana hoytu enu maadli")
    assert _looks_indic_in_latin("yenk paisa ponda dada malpu")
    assert _looks_indic_in_latin("mera paisa kat gaya kya karo")
    assert not _looks_indic_in_latin("someone called me about my bank account")


def test_tulu_in_english_letters_is_recognised_and_hinted():
    from scanners.assistant import latin_language_hint
    assert latin_language_hint("yenk onji call battund, OTP kender, yan korde, ipo duddu poyind") == "tcy"
    assert latin_language_hint("nanage ondu call banthu enu madli") == "kn"
    assert latin_language_hint("mera paisa kat gaya kya karu") == "hi"
    assert latin_language_hint("someone called me about my bank") is None
    setup({"reply": "ok", "understood": "They gave the OTP and lost money", "urgent": True, "actions": []})
    c.post("/api/assistant", json={"message": "yenk onji call battund, OTP kender, yan korde, ipo duddu poyind", "lang": "en"})
    assert "most likely Tulu" in seen[0]["messages"][0]["content"]


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
