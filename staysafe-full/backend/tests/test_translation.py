"""Translation flow with the outside services replaced by fakes (no network, no keys used)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask  # noqa: E402

import scanners.translator as tr  # noqa: E402
import scanners.message_scanner as ms  # noqa: E402

KANNADA = "ನಿಮ್ಮ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ತಕ್ಷಣ ಈ ಲಿಂಕ್ ಒತ್ತಿ"
KANGLISH = "nimma account block aagide, ivattu link open maadi KYC update maadi illandre hana hogutte"


class Fake:
    """Stands in for Google / Gemini / Bhashini / MyMemory and records what was asked."""

    def __init__(self, google=None, gemini=None):
        self.google, self.gemini, self.calls = google, gemini, []

    def install(self):
        tr._cache.clear()
        tr._google = lambda text, target: self._call("google", text, target)
        tr._gemini = lambda text, target, *a, **k: self._call("gemini", text, target)
        tr._bhashini = lambda text, target: None
        tr._mymemory = lambda text, target: None
        return self

    def _call(self, name, text, target):
        self.calls.append((name, target))
        fn = getattr(self, name)
        return fn(text, target) if fn else None


def _app():
    app = Flask(__name__)
    app.add_url_rule("/api/translate", view_func=ms.translate_route, methods=["POST"])
    return app.test_client()


def test_kannada_to_english_uses_google():
    f = Fake(google=lambda t, to: {"text": "Your account will be blocked today. Press this link now",
                                   "from": "kn", "to": to, "provider": "google"}).install()
    out = tr.translate(KANNADA, "en")
    assert out["from"] == "kn" and out["text"].startswith("Your account")
    assert f.calls == [("google", "en")]


def test_same_language_costs_nothing():
    f = Fake().install()
    out = tr.translate(KANNADA, "kn")
    assert out["text"] == KANNADA and out["to"] == "kn" and f.calls == []


def test_romanized_goes_to_gemini_first_and_rejects_unchanged():
    # the word lists are downloaded when the server is built; stand in for them here
    real = tr._romanized, tr._romanized_language
    tr._romanized = lambda t: t == KANGLISH
    tr._romanized_language = lambda t: "kn"
    try:
        _romanized_case()
    finally:
        tr._romanized, tr._romanized_language = real


def _romanized_case():
    # Google can't read Kanglish: it calls it English and sends it back unchanged
    f = Fake(google=lambda t, to: {"text": t, "from": "en", "to": to, "provider": "google"},
             gemini=lambda t, to: {"text": "Your account is blocked, open the link today and update KYC "
                                           "or the money will go", "from": "kn", "to": to, "provider": "gemini"}).install()
    out = tr.translate(KANGLISH, "en")
    assert out and out["provider"] == "gemini" and out["from"] == "kn"
    assert f.calls[0] == ("gemini", "en")
    # Gemini busy: Google's unchanged answer must not count as a translation
    f = Fake(google=lambda t, to: {"text": t, "from": "en", "to": to, "provider": "google"}).install()
    assert tr.translate(KANGLISH, "en") is None
    # Google translates it but calls it English: the language is filled in from the word lists
    Fake(google=lambda t, to: {"text": "ನಿಮ್ಮ ಖಾತೆ ಬ್ಲಾಕ್ ಆಗಿದೆ", "from": "en", "to": to, "provider": "google"}).install()
    out = tr.translate(KANGLISH, "hi")
    assert out["from"] == "kn"


def test_tulu_falls_back_to_kannada_without_error():
    client = _app()
    Fake().install()                       # Gemini (the only one that writes Tulu) is down
    r = client.post("/api/translate", json={"text": KANNADA, "to": "tcy"})
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["to"] == "kn" and body["text"] == KANNADA
    # an English message asked for in Tulu: Kannada translation instead, still no error
    Fake(google=lambda t, to: {"text": "ನಿಮ್ಮ ಖಾತೆ ಬ್ಲಾಕ್ ಆಗಿದೆ", "from": "en", "to": to, "provider": "google"}).install()
    r = client.post("/api/translate", json={"text": "Your account is blocked", "to": "tcy"})
    assert r.status_code == 200 and r.get_json()["to"] == "kn"


def test_tulu_from_gemini():
    Fake(gemini=lambda t, to: {"text": "ಈರೆನ ಖಾತೆ ಬ್ಲಾಕ್ ಆತ್ಂಡ್", "from": "en", "to": to, "provider": "gemini"}).install()
    r = _app().post("/api/translate", json={"text": "Your account is blocked", "to": "tcy"})
    assert r.status_code == 200 and r.get_json() == {"text": "ಈರೆನ ಖಾತೆ ಬ್ಲಾಕ್ ಆತ್ಂಡ್", "from": "en", "to": "tcy"}


def test_route_errors():
    Fake().install()
    c = _app()
    assert c.post("/api/translate", json={"text": "", "to": "kn"}).status_code == 400
    assert c.post("/api/translate", json={"text": "hi", "to": "fr"}).status_code == 400
    assert c.post("/api/translate", json={"text": "Your account is blocked", "to": "hi"}).status_code == 503


def test_personal_details_never_sent():
    seen = []

    def google(t, to):
        seen.append(t)
        return {"text": t.replace("Call", "ಕರೆ ಮಾಡಿ"), "from": "en", "to": to, "provider": "google"}
    Fake(google=google).install()
    out = tr.translate("Call 9876543210 and share OTP 482913", "kn")
    assert "9876543210" not in seen[0] and "9876543210" in out["text"]


def test_message_result_shows_translation_on_other_language_site():
    Fake(google=lambda t, to: {"text": "Your account will be blocked today", "from": "kn", "to": to,
                               "provider": "google"}).install()
    res = ms.add_translation(ms.analyze_text(KANNADA), "en")
    assert res.get("translation", {}).get("from") == "kn"
    # Kannada message on the Kannada site: nothing to translate, no request made
    f = Fake().install()
    res = ms.add_translation(ms.analyze_text(KANNADA), "kn")
    assert "translation" not in res and all(c[1] != "kn" for c in f.calls)


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    ok = 0
    for t in tests:
        try:
            t(); ok += 1; print("PASS ", t.__name__)
        except Exception as e:
            import traceback; traceback.print_exc()
            print("FAIL ", t.__name__, repr(e))
    print(f"\n{ok}/{len(tests)} tests passed")
