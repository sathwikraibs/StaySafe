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
    assert seen[0]["model"] == groq_client.CHAT_MODELS[1]


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


def test_tulu_in_kannada_script_is_recognised_not_taken_for_kannada():
    from scanners.assistant import kannada_script_hint, language_hint, system_prompt
    assert kannada_script_hint("ಎಂಕ್ ಒಂಜಿ ಮೆಸೇಜ್ ಬತ್ತ್ಂಡ್, ಲಾಟರಿ ಬತ್ತ್ಂಡ್ ಪಂಡ್ದ್, ದುಡ್ಡು ಕಟ್ಟೊಡು ಪನ್ಪೆರ್") == "tcy"
    assert kannada_script_hint("ನನಗೆ ಒಂದು ಕರೆ ಬಂತು, ಪೊಲೀಸ್ ಅಂತ ಹೇಳಿ ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್ ಮಾಡ್ತೀವಿ ಅಂದ್ರು, ಏನು ಮಾಡಲಿ") == "kn"
    assert language_hint("enna whatsapp hack aand, dada malpodu") == ("tcy", "latin")
    assert language_hint("someone hacked my whatsapp") == (None, None)
    p = system_prompt("tcy", "", ("tcy", "kannada"))
    assert "Tulu written in Kannada script" in p and "The site is set to Tulu" in p
    setup({"reply": "ok", "urgent": False, "actions": []})
    c.post("/api/assistant", json={"message": "ಎಂಕ್ ಒಂಜಿ ಮೆಸೇಜ್ ಬತ್ತ್ಂಡ್, ದುಡ್ಡು ಕಟ್ಟೊಡು ಪನ್ಪೆರ್", "lang": "en"})
    assert "most likely Tulu written in Kannada script" in seen[0]["messages"][0]["content"]


def test_one_language_rule_and_no_button_names_in_the_instructions():
    from scanners.assistant import system_prompt
    p = system_prompt("en")
    assert "Never start or mix in English sentences" in p and "Never write the button names" in p
    t = system_prompt("tcy")
    assert "ಪೈಸೆ ಕೊರೊಡ್ಚಿ" in t and "paise korodchi" in t and "-odchi means DON'T" in t


def test_better_gemini_model_answers_indian_languages_and_steps_aside_when_busy():
    setup({"reply": "ok", "urgent": False, "actions": []})
    QUOTAS["gemini_answers"].reset()
    assistant._answer_model["name"] = None
    assistant._answer_gone.clear()
    assistant._answer_extra.clear()
    assistant.ANSWER_MODELS[:] = ["gemini-2.5-flash", "gemini-flash-latest"]
    os.environ["GEMINI_API_KEY"] = "g"
    calls = []

    def make(status, url, text=""):
        class R:
            status_code = status
            headers = {}

            def json(self):
                body = json.dumps({"reply": "ಗಾಬರಿ ಆವೊಡ್ಚಿ. ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ.", "urgent": True, "actions": []},
                                  ensure_ascii=False)
                return {"candidates": [{"content": {"parts": [{"text": "thinking...", "thought": True}, {"text": body}]}}]}
        R.text = text
        return R()

    try:
        # first better model doesn't exist: the next one answers; its thoughts are never shown
        def post(url, **kw):
            calls.append(url)
            if "gemini-2.5-flash:" in url:
                return make(404, url)
            return make(200, url)
        groq_client.requests.post = post
        d = c.post("/api/assistant", json={"message": "ಎಂಕ್ ಒಂಜಿ ಕಾಲ್ ಬತ್ತ್ಂಡ್, ದುಡ್ಡು ಪೋಂಡು", "lang": "tcy"}).get_json()
        assert "gemini-flash-latest" in calls[1] and "ಇತ್ತೆನೇ" in d["reply"] and "thinking" not in d["reply"], (calls, d)
        assert assistant._answer_model["name"] == "gemini-flash-latest"
        # busy (429): that model rests, and the usual Gemini model answers instead
        calls.clear()
        assistant._answers.clear()

        def busy(url, **kw):
            calls.append(url)
            return make(429, url, "rate limit per minute") if "gemini-flash-latest" in url else make(200, url)
        groq_client.requests.post = busy
        d = c.post("/api/assistant", json={"message": "ಎಂಕ್ ಒಂಜಿ ಮೆಸೇಜ್ ಬತ್ತ್ಂಡ್, ಲಾಟರಿ ಪನ್ಪೆರ್", "lang": "tcy"}).get_json()
        assert d.get("reply") and QUOTAS["gemini_answers"].status()["paused_for_s"] > 0, (calls, d)
    finally:
        os.environ.pop("GEMINI_API_KEY", None)
        QUOTAS["gemini_answers"].reset()


def test_tulu_dont_on_a_must_do_step_is_corrected():
    # first answer says "don't file a complaint"; the AI is asked once to fix it
    replies = [{"reply": "ಉಂದು ಮೋಸ. 1. ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಲ್ಪೊಡ್ಚಿ. 2. cybercrime.gov.in ಡ್ ದೂರು ಕೊರೊಡ್ಚಿ.", "urgent": False, "actions": []},
               {"reply": "ಉಂದು ಮೋಸ. 1. ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಲ್ಪೊಡ್ಚಿ. 2. cybercrime.gov.in ಡ್ ದೂರು ಕೊರ್ಲೆ.", "urgent": False, "actions": []}]
    setup(replies[0])
    sent = []

    class R:
        status_code = 200
        headers = {}
        text = ""

        def __init__(self, obj):
            self.obj = obj

        def json(self):
            return {"choices": [{"message": {"content": json.dumps(self.obj, ensure_ascii=False)}}], "usage": {"total_tokens": 900}}

    def post(url, **kw):
        sent.append(kw["json"])
        return R(replies[min(len(sent) - 1, 1)])
    groq_client.requests.post = post
    d = c.post("/api/assistant", json={"message": "ಎಂಕ್ ಒಂಜಿ ಮೆಸೇಜ್ ಬತ್ತ್ಂಡ್", "lang": "en"}).get_json()
    assert len(sent) == 2 and "ದೂರು ಕೊರ್ಲೆ" in d["reply"] and "ಕ್ಲಿಕ್ ಮಲ್ಪೊಡ್ಚಿ" in d["reply"], (len(sent), d)
    # still wrong after asking: fixed in place, other "don't"s untouched
    from scanners.assistant import _fix_dont
    assert _fix_dont("Ittene 1930 g call malpodchi. OTP yereglaa panodchi.") == "Ittene 1930 g call malpule. OTP yereglaa panodchi."


def test_phrases_are_sent_only_for_the_languages_needed():
    from scanners.assistant import system_prompt
    en = system_prompt("en", "", None, "my bank called me")
    assert "ಪೈಸೆ ಕೊರೊಡ್ಚಿ" not in en and "कॉल काट" not in en
    assert "ಪೈಸೆ ಕೊರೊಡ್ಚಿ" in system_prompt("en", "", ("tcy", "latin"), "yenk call battund")
    assert "कॉल काट" in system_prompt("en", "", ("hi", "latin"), "mera paisa gaya")


def test_tulu_asked_but_kannada_answered_is_rewritten_in_tulu():
    kannada = {"reply": "ಗಾಬರಿ ಆಗಬೇಡಿ. ನಿಮ್ಮ ವಾಟ್ಸಾಪ್ ಹ್ಯಾಕ್ ಆಗಿದೆ. ಸೆಟ್ಟಿಂಗ್‌ಗೆ ಹೋಗಿ ಲಾಗ್ ಔಟ್ ಮಾಡಿ, ನಿಮ್ಮ ಸ್ನೇಹಿತರಿಗೆ ಹೇಳಿ.", "urgent": False, "actions": []}
    tulu = {"reply": "ಗಾಬರಿ ಆವೊಡ್ಚಿ. ಸೆಟ್ಟಿಂಗ್‌ಗ್ ಪೋದು ಲಾಗ್ ಔಟ್ ಮಲ್ಪುಲೆ, ಇರೆನ ಫ್ರೆಂಡ್‌ಲೆಗ್ ಪನ್ಲೆ.", "urgent": False, "actions": []}
    setup(kannada)
    sent = []

    class R:
        status_code = 200
        headers = {}
        text = ""

        def __init__(self, obj):
            self.obj = obj

        def json(self):
            return {"choices": [{"message": {"content": json.dumps(self.obj, ensure_ascii=False)}}], "usage": {"total_tokens": 900}}

    def post(url, **kw):
        sent.append(kw["json"])
        return R(kannada if len(sent) == 1 else tulu)
    groq_client.requests.post = post
    d = c.post("/api/assistant", json={"message": "enna whatsapp hack aand, dada malpodu", "lang": "en", "reply_lang": "tcy"}).get_json()
    assert len(sent) == 2 and "ಮಲ್ಪುಲೆ" in d["reply"], (len(sent), d)
    assert "(not Kannada)" in sent[0]["messages"][0]["content"] and "same letters they typed" in sent[0]["messages"][0]["content"]


def test_a_failed_fix_up_keeps_the_first_answer_and_waits_stay_within_the_time_budget():
    import time as _t
    kannada = {"reply": "ನಿಮ್ಮ ವಾಟ್ಸಾಪ್ ಹ್ಯಾಕ್ ಆಗಿದೆ. ಲಾಗ್ ಔಟ್ ಮಾಡಿ, ನಿಮ್ಮ ಸ್ನೇಹಿತರಿಗೆ ಹೇಳಿ.", "urgent": False, "actions": []}
    setup(kannada)
    n = []

    class Bad:
        status_code = 500
        headers = {}
        text = "server error"

    class Good:
        status_code = 200
        headers = {}
        text = ""

        def json(self):
            return {"choices": [{"message": {"content": json.dumps(kannada, ensure_ascii=False)}}], "usage": {"total_tokens": 900}}

    def post(url, **kw):
        n.append(url)
        return Good() if len(n) == 1 else Bad()
    groq_client.requests.post = post
    d = c.post("/api/assistant", json={"message": "enna whatsapp hack aand", "lang": "en", "reply_lang": "tcy"}).get_json()
    assert d.get("reply") == kannada["reply"], d          # better than nothing
    assistant._until.end = _t.time() + 40
    try:
        assert assistant._wait() <= 5.1
    finally:
        assistant._until.end = None
    assert assistant._wait() == assistant.WAIT


def test_retired_better_model_hands_over_to_the_one_google_names_and_emails_are_never_shown():
    setup({"reply": "ok", "urgent": False, "actions": []})
    QUOTAS["gemini_answers"].reset()
    assistant._answer_model["name"] = None
    assistant._answer_gone.clear()
    assistant._answer_extra.clear()
    saved = list(assistant.ANSWER_MODELS)
    assistant.ANSWER_MODELS[:] = ["gemini-old-flash"]
    os.environ["GEMINI_API_KEY"] = "g"
    calls = []

    class R:
        def __init__(self, status, text=""):
            self.status_code, self.text, self.headers = status, text, {}

        def json(self):
            body = json.dumps({"reply": "Ittene 1930 g call malpule. Email support@fakehelp.com or help@ now.", "urgent": True,
                               "actions": []})
            return {"candidates": [{"content": {"parts": [{"text": body}]}}]}

    def post(url, **kw):
        calls.append(url)
        if "gemini-old-flash" in url:
            return R(404, '{"error": {"message": "This model models/gemini-old-flash is no longer available to new users. '
                          'Please update your code to use models/gemini-9-flash for the latest features"}}')
        return R(200)
    groq_client.requests.post = post
    try:
        d = c.post("/api/assistant", json={"message": "yenk call battund, duddu poyind", "lang": "tcy"}).get_json()
        assert "gemini-9-flash" in calls[1] and assistant._answer_model["name"] == "gemini-9-flash", calls
        assert "@" not in d["reply"] and "1930" in d["reply"], d
    finally:
        assistant.ANSWER_MODELS[:] = saved
        assistant._answer_extra.clear()
        assistant._answer_model["name"] = None
        os.environ.pop("GEMINI_API_KEY", None)
        QUOTAS["gemini_answers"].reset()


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
