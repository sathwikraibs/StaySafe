"""Tests for how every AI part of the site behaves when services are busy, used up, cut off or off-topic.
Run: python tests/test_ai.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scanners.url_scanner as url_scanner  # noqa: E402
url_scanner.OFFLINE = True
import requests  # noqa: E402
from app import app  # noqa: E402
from scanners import assistant, groq_client, llm_pool, translator, ai_review  # noqa: E402
from scanners.quota import QUOTAS  # noqa: E402

c = app.test_client()
REAL_POST = requests.post
KEYS = ("STATUS_KEY", "GROQ_API_KEY", "GEMINI_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_AI_TOKEN", "MISTRAL_API_KEY",
        "OPENROUTER_API_KEY", "GEMINI_MODEL")


class R:
    def __init__(self, status=200, data=None, text=""):
        self.status_code, self._data, self.headers = status, data, {}
        self.text = text or (json.dumps(data) if data is not None else "")

    def json(self):
        return self._data


def gemini_ok(text, finish="STOP"):
    return R(200, {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": text}]}}]})


def openai_ok(text, finish="stop"):
    return R(200, {"choices": [{"finish_reason": finish, "message": {"content": text}}], "usage": {"total_tokens": 500}})


def fresh(**env):
    for k in KEYS:
        os.environ.pop(k, None)
    os.environ.update(env)
    for q in QUOTAS.values():
        q.reset()
    translator._GEMINI.update(model=None)
    translator._GEMINI_GONE.clear()
    translator._GEMINI_DAY_DONE.clear()
    translator._GEMINI_EXTRA.clear()
    translator._GEMINI_COOL.clear()
    translator._paused_until["gemini"] = 0
    groq_client._models.clear()
    groq_client._gone.clear()
    llm_pool._gone.clear()
    llm_pool._paused.clear()
    assistant._answers.clear()
    assistant._ip_hits.clear()
    assistant._answer_model["name"] = None
    assistant._answer_gone.clear()
    ai_review._cache.clear()
    translator.time.sleep = lambda s: None       # no real waiting in tests


def use(fake):
    requests.post = fake


BODY = {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}


# ---- Gemini: shared by translation, message review and the Helper -------------------------
def test_gemini_moves_to_the_next_free_model_when_one_is_used_up_for_the_day():
    fresh(GEMINI_API_KEY="g")
    first, second = translator.GEMINI_MODELS[0], translator.GEMINI_MODELS[1]
    calls = []

    def fake(url, **kw):
        calls.append(url)
        if f"/{first}:" in url:
            return R(429, {"error": {"message": "Quota exceeded for metric: GenerateRequestsPerDayPerProjectPerModel-FreeTier"}})
        return gemini_ok('{"ok": 1}')
    use(fake)
    assert translator.gemini_generate(BODY) == '{"ok": 1}'
    assert f"/{second}:" in calls[1] and not QUOTAS["gemini"].status()["day_closed"]
    calls.clear()
    assert translator.gemini_generate(BODY) and f"/{first}:" not in calls[0]     # the used-up one is skipped today


def test_gemini_stops_for_the_day_only_when_every_model_is_used_up():
    fresh(GEMINI_API_KEY="g")
    use(lambda url, **kw: R(429, {"error": {"message": "limit per day reached (daily)"}}))
    assert translator.gemini_generate(BODY) is None
    assert QUOTAS["gemini"].status()["day_closed"]


def test_gemini_high_demand_is_waited_out_not_a_ten_minute_pause():
    fresh(GEMINI_API_KEY="g")
    n = []

    def fake(url, **kw):
        n.append(url)
        return R(503, {"error": {"message": "This model is currently experiencing high demand."}}) if len(n) == 1 else gemini_ok("fine")
    use(fake)
    assert translator.gemini_generate(BODY) == "fine" and len(n) == 2 and n[0] == n[1]   # same model, asked again
    assert translator._available("gemini")
    # busy twice: the next model answers
    fresh(GEMINI_API_KEY="g")
    n.clear()
    use(lambda url, **kw: (n.append(url), R(503, {"error": {"message": "busy"}}) if len(n) <= 2 else gemini_ok("next"))[1])
    assert translator.gemini_generate(BODY) == "next" and n[2] != n[0] and translator._available("gemini")


def test_gemini_follows_googles_replacement_hint_and_never_returns_a_cut_off_answer():
    fresh(GEMINI_API_KEY="g", GEMINI_MODEL="")
    os.environ.pop("GEMINI_MODEL")
    saved = list(translator.GEMINI_MODELS)
    translator.GEMINI_MODELS[:] = ["gemini-old-lite"]
    calls = []
    try:
        def fake(url, **kw):
            calls.append(url)
            if "gemini-old-lite" in url:
                return R(404, {"error": {"message": "models/gemini-old-lite is no longer available to new users. "
                                                    "Please update your code to use models/gemini-new-lite for the latest"}})
            return gemini_ok("hello")
        use(fake)
        assert translator.gemini_generate(BODY) == "hello" and "gemini-new-lite" in calls[1]
        use(lambda url, **kw: gemini_ok('{"reply": "half', finish="MAX_TOKENS"))
        assert translator.gemini_generate(BODY) is None
    finally:
        translator.GEMINI_MODELS[:] = saved


def test_a_bad_request_does_not_switch_gemini_off_for_hours():
    fresh(GEMINI_API_KEY="g")
    use(lambda url, **kw: R(400, {"error": {"message": "Request contains an invalid argument."}}))
    assert translator.gemini_generate(BODY) is None and translator._available("gemini")
    use(lambda url, **kw: R(400, {"error": {"message": "API key not valid. Please pass a valid API key."}}))
    assert translator.gemini_generate(BODY) is None and not translator._available("gemini")


# ---- The extra free services ------------------------------------------------------------------
def test_extra_services_answer_skip_cut_off_answers_and_respect_limits():
    fresh(CLOUDFLARE_ACCOUNT_ID="acct", CLOUDFLARE_AI_TOKEN="t", MISTRAL_API_KEY="m")
    seen = []

    def fake(url, json=None, **kw):
        seen.append((url, json.get("model"), "response_format" in json))
        if "cloudflare" in url and json["model"] == "@cf/openai/gpt-oss-120b":
            return openai_ok('{"reply": "cut', finish="length")      # cut off: try the next model
        if "cloudflare" in url and "response_format" in json:
            return R(400, text="response_format is not supported for this model")
        return openai_ok('{"reply": "Call 1930."}')
    use(fake)
    out = llm_pool.chat("cloudflare", [{"role": "user", "content": "x"}])
    assert out == '{"reply": "Call 1930."}' and "ai/v1/chat/completions" in seen[0][0]
    assert seen[-1][2] is False                         # asked again without JSON mode
    use(lambda url, **kw: R(429, text="you have used up your daily free allocation of 10,000 neurons"))
    assert llm_pool.chat("mistral", [{"role": "user", "content": "x"}]) is None
    assert QUOTAS["mistral"].status()["day_closed"]
    use(lambda url, **kw: R(401, text="bad key"))
    assert llm_pool.chat("cloudflare", [{"role": "user", "content": "x"}]) is None and not llm_pool.ready("cloudflare")
    assert llm_pool.chat("openrouter", [{"role": "user", "content": "x"}]) is None    # no key: not used


# ---- The Helper --------------------------------------------------------------------------------
def test_cut_off_or_broken_answer_is_never_shown_the_next_service_answers():
    fresh(GROQ_API_KEY="k", CLOUDFLARE_ACCOUNT_ID="a", CLOUDFLARE_AI_TOKEN="t")

    def fake(url, json=None, **kw):
        if "groq.com" in url:
            return openai_ok('{"understood": "lost money", "reply": "Please call 1930 and')   # broken JSON
        return openai_ok('{"kind": "safety", "reply": "Please call 1930 now.", "actions": ["incident"]}')
    use(fake)
    d = c.post("/api/assistant", json={"message": "someone took my money after I shared OTP", "lang": "en"}).get_json()
    assert d["reply"] == "Please call 1930 now." and "{" not in d["reply"], d


def test_code_in_an_answer_is_replaced_by_the_safety_only_line():
    fresh(GROQ_API_KEY="k")
    use(lambda url, **kw: openai_ok(json.dumps({"kind": "safety", "reply": "```python\nprint('hello')\n```"})))
    d = c.post("/api/assistant", json={"message": "how do I block a scam number", "lang": "en"}).get_json()
    assert d["reply"] == assistant.OFF_TOPIC["en"] and d["kind"] == "other", d


def test_off_topic_questions_get_the_safety_only_line_in_the_visitors_language():
    fresh(GROQ_API_KEY="k", GEMINI_API_KEY="g")
    sent = []
    use(lambda url, **kw: (sent.append(url), openai_ok('{"kind": "other", "reply": "My girlfriend is..."}'))[1])
    d = c.post("/api/assistant", json={"message": "nimma favourite cinema yavudu heli", "lang": "kn"}).get_json()
    assert d["reply"] in (assistant.OFF_TOPIC["kn-latn"], assistant.OFF_TOPIC["kn"]) and d["actions"] == [], d
    # clearly off-topic: answered at once, no AI used at all
    sent.clear()
    for q, lang, want in (("write me a python code for calculator", "en", "en"),
                          ("tell me your girlfriend name", "en", "en"),
                          ("ನಿಮ್ಮ girlfriend ಹೆಸರು ಏನು", "kn", "kn")):
        d = c.post("/api/assistant", json={"message": q, "lang": lang}).get_json()
        assert d["reply"] == assistant.OFF_TOPIC[want] and d["kind"] == "other", (q, d)
    assert sent == []
    # but a real problem that mentions a girlfriend is answered
    use(lambda url, **kw: openai_ok('{"kind": "safety", "reply": "Tell her not to pay. Call 1930."}'))
    d = c.post("/api/assistant", json={"message": "my girlfriend got a scam call asking money", "lang": "en"}).get_json()
    assert "1930" in d["reply"]


def test_small_talk_is_answered_normally():
    fresh(GROQ_API_KEY="k")
    use(lambda url, **kw: openai_ok('{"kind": "smalltalk", "reply": "Hi! I am StaySafe\'s AI assistant, an automatic helper."}'))
    d = c.post("/api/assistant", json={"message": "who are you", "lang": "en"}).get_json()
    assert "StaySafe" in d["reply"] and d["kind"] == "smalltalk"


def test_the_helper_answers_when_groq_and_gemini_are_both_used_up():
    fresh(GROQ_API_KEY="k", GEMINI_API_KEY="g", MISTRAL_API_KEY="m")
    for name in groq_client.CHAT_MODELS:
        groq_client.model(name).requests.close_day()
    QUOTAS["gemini"].close_day()
    QUOTAS["gemini_answers"].close_day()
    urls = []
    use(lambda url, **kw: (urls.append(url), openai_ok('{"kind": "safety", "reply": "ಕರೆ ಕಡಿತಗೊಳಿಸಿ, ಹಣ ಕೊಡಬೇಡಿ."}'))[1])
    d = c.post("/api/assistant", json={"message": "ಪೊಲೀಸ್ ಅಂತ ಕರೆ ಬಂತು ಏನು ಮಾಡಲಿ", "lang": "kn"}).get_json()
    assert "ಹಣ" in d["reply"] and all("mistral" in u for u in urls), (urls, d)


# ---- Message review ------------------------------------------------------------------------------
def test_message_review_uses_the_next_free_service():
    fresh(CLOUDFLARE_ACCOUNT_ID="a", CLOUDFLARE_AI_TOKEN="t")
    use(lambda url, **kw: openai_ok('{"verdict": "scam", "category": "bank", "confidence": 90}'))
    out = ai_review.review("Dear customer your SBI account is blocked, update KYC now at http://sbi-kyc.xyz")
    assert out and out["verdict"] == "scam" and out["provider"] == "cloudflare"


def test_gemini_reads_the_day_limit_from_the_error_details_and_a_busy_minute_moves_to_the_next_model():
    fresh(GEMINI_API_KEY="g")
    first = translator.GEMINI_MODELS[0]
    day_body = {"error": {"code": 429, "message": "You exceeded your current quota. limit: 20, model: x. Please retry in 30s.",
                          "details": [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}}
    use(lambda url, **kw: R(429, day_body) if f"/{first}:" in url else gemini_ok("next"))
    assert translator.gemini_generate(BODY) == "next"
    assert translator._GEMINI_DAY_DONE.get(first) == translator._gemini_day_key()      # rests until Google's day ends
    assert QUOTAS["gemini"].status()["paused_for_s"] == 0                                # the others keep working
    fresh(GEMINI_API_KEY="g")
    minute_body = {"error": {"code": 429, "message": "Resource exhausted. Please retry in 20s.",
                             "details": [{"violations": [{"quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"}]}]}}
    use(lambda url, **kw: R(429, minute_body) if f"/{first}:" in url else gemini_ok("next"))
    assert translator.gemini_generate(BODY) == "next" and first in translator._GEMINI_COOL
    assert QUOTAS["gemini"].status()["paused_for_s"] == 0


def test_replacement_hint_ending_a_sentence_is_read_correctly():
    m = translator._REPLACEMENT.search("is no longer available. Please use models/gemini-3.1-flash-lite.")
    assert m.group(1) == "gemini-3.1-flash-lite"


def test_forced_model_rests_for_the_day_too():
    fresh(GEMINI_API_KEY="g", GEMINI_MODEL="gemini-only")
    calls = []
    use(lambda url, **kw: (calls.append(url), R(429, {"error": {"message": "per day limit reached"}}))[1])
    assert translator.gemini_generate(BODY) is None and len(calls) == 1
    assert translator.gemini_generate(BODY) is None and len(calls) == 1          # not asked again today
    os.environ.pop("GEMINI_MODEL")


def test_no_call_is_started_that_could_run_past_the_time_limit():
    import time as _t
    fresh(GEMINI_API_KEY="g", GROQ_API_KEY="k", MISTRAL_API_KEY="m")
    calls = []
    use(lambda url, **kw: (calls.append(url), gemini_ok("x"))[1])
    soon = _t.time() + 5
    assert translator.gemini_generate(BODY, deadline=soon) is None
    assert llm_pool.chat("mistral", [{"role": "user", "content": "x"}], deadline=soon) is None
    assert groq_client.chat([{"role": "user", "content": "x"}], finish_by=soon) is None
    assert calls == []
    # and every request's own time limit is cut to what is left
    seen = []
    use(lambda url, timeout=None, **kw: (seen.append(timeout), gemini_ok("x"))[1])
    assert translator.gemini_generate(BODY, timeout=30, deadline=_t.time() + 20) == "x" and seen[0] <= 18.1


def test_scam_victims_mentioning_a_code_are_answered_not_turned_away():
    for q in ("he asked me to give the code he sent on my phone", "someone on instagram said send me the code",
              "they told me to send the verification code"):
        assert not assistant.clearly_off_topic(q), q


def test_normal_answers_are_never_mistaken_for_code():
    for good in ("Call 1930 now.<br>Then call your bank.", "They may return your money; do not pay any fee.",
                 "If your phone doesn't function properly (it keeps restarting), reset it.",
                 'The SMS says "Alert": 5000 debited. It is fake.', "From today as a rule, never share OTP.",
                 "[#1] [#2] [#3] [#4] are scam numbers, block them.", "<b>Don't pay.</b> Call 1930."):
        assert not assistant.looks_like_code(good), good
    out = assistant.finish({"reply": "Call 1930 now.<br>Then call your bank.", "kind": "safety", "actions": []}, "x", "en")
    assert out["reply"] == "Call 1930 now.\nThen call your bank."
    assert assistant._parse('{"reply": "hi", "actions": 1}')["actions"] == []
    assert assistant._parse('Report on "Sanchar Saathi" and use "Chakshu".')["reply"].startswith("Report")


# ---- Protective DNS (Cloudflare 1.1.1.2, Quad9) ------------------------------------------------
def _dns_answer(query: bytes, rcode=0, ips=()):
    import struct as st
    header = st.pack(">HHHHHH", 0, 0x8180 | rcode, 1, len(ips), 0, 0)
    question = query[12:]
    answers = b"".join(b"\xc0\x0c" + st.pack(">HHIH", 1, 1, 60, 4) + bytes(int(x) for x in ip.split(".")) for ip in ips)
    return header + question + answers


def test_protective_dns_reads_both_services_answers():
    import base64 as b64
    from scanners import protective_dns as pd
    fresh()

    def fake_for(cf_ips, q9_rcode, q9_ips=("93.184.216.34",)):
        def get(url, params=None, **kw):
            q = b64.urlsafe_b64decode(params["dns"] + "=" * (-len(params["dns"]) % 4))
            class Resp:
                status_code = 200
                content = _dns_answer(q, 0, cf_ips) if "cloudflare" in url else _dns_answer(q, q9_rcode, () if q9_rcode else q9_ips)
            return Resp()
        return get
    real_get = requests.get
    try:
        requests.get = fake_for(("0.0.0.0",), 3)
        out = pd.check("bad-site.xyz", True)
        assert out["status"] == "fail" and out["blocked_by"] == ["Cloudflare", "Quad9"], out
        requests.get = fake_for(("0.0.0.0",), 0)
        assert pd.check("maybe.xyz", True)["status"] == "warn"
        requests.get = fake_for(("93.184.216.34",), 0)
        assert pd.check("example.com", True)["status"] == "pass"
        # the website really doesn't exist: Quad9's "no such website" is not a block
        requests.get = fake_for((), 3)
        assert pd.check("gone.xyz", False)["status"] == "pass"
        # neither service reachable: not checked, never a false alarm
        requests.get = lambda *a, **k: (_ for _ in ()).throw(requests.ConnectionError())
        assert pd.check("x.xyz", True)["status"] == "skip"
    finally:
        requests.get = real_get
    assert pd.parse_answer(_dns_answer(pd.build_query("a.b.com"), 0, ("1.2.3.4", "0.0.0.0")))["ips"] == ["1.2.3.4", "0.0.0.0"]


def test_self_test_can_check_one_chosen_service_and_never_affects_visitors():
    fresh(GROQ_API_KEY="k", CLOUDFLARE_ACCOUNT_ID="a", CLOUDFLARE_AI_TOKEN="t", STATUS_KEY="sk")
    urls = []
    use(lambda url, **kw: (urls.append(url), openai_ok('{"kind": "safety", "reply": "Call 1930 now."}'))[1])
    d = c.get("/api/assistant/selftest?key=sk&case=16&via=cloudflare").get_json()
    assert d["results"][0]["answered_by"] == "cloudflare" and all("cloudflare" in u for u in urls), (urls, d["results"])
    assert assistant._until.__dict__.get("only") is None
    urls.clear()
    c.post("/api/assistant", json={"message": "is this call a scam", "lang": "en"})
    assert "groq.com" in urls[0]                     # visitors use the normal order again
    os.environ.pop("STATUS_KEY")


def test_openrouter_busy_model_hands_over_to_its_next_free_model():
    fresh(OPENROUTER_API_KEY="o")
    models = []

    def fake(url, json=None, **kw):
        models.append(json["model"])
        if len(models) == 1:
            return R(429, text='{"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"is temporarily rate-limited upstream"}}}')
        return openai_ok('{"reply": "ok"}')
    use(fake)
    assert llm_pool.chat("openrouter", [{"role": "user", "content": "x"}]) == '{"reply": "ok"}'
    assert len(models) == 2 and models[0] != models[1] and QUOTAS["openrouter"].status()["paused_for_s"] == 0


def test_google_share_link_is_judged_by_the_page_it_opens_not_by_lists_of_the_whole_service():
    import numpy as np
    import scanners.url_scanner as u
    import scanners.protective_dns as pd
    saved = {k: getattr(u, k) for k in ("OFFLINE", "resolve_host", "whois_age_days", "whois_details", "cert_details",
                                        "first_certificate_days", "check_virustotal", "check_safe_browsing",
                                        "check_abusech", "check_urlscan", "check_server_abuse", "ensure_feeds",
                                        "ensure_big_feeds", "popularity_rank", "fetch_page")}
    saved_pd, saved_big, saved_feeds = pd.check, dict(u._BIG), dict(u._FEEDS)
    try:
        u.OFFLINE = False
        u.resolve_host = lambda h: {"exists": True, "ips": ["142.250.1.1"]}
        u.whois_age_days = lambda d: 3000
        u.whois_details = lambda d: {}
        u.cert_details = lambda h: {}
        u.first_certificate_days = lambda h: 3000
        u.check_virustotal = lambda url, d, *_: {"status": "ok", "malicious": 0, "domain_malicious": 0}
        u.check_safe_browsing = lambda urls: {"listed": False, "threats": []}
        u.check_abusech = lambda url, h: {"status": "pass"}
        u.check_urlscan = lambda h: {"status": "pass"}
        u.check_server_abuse = lambda ip: {}
        pd.check = lambda h, e: {"status": "pass"}
        u.ensure_feeds = lambda: None
        u.ensure_big_feeds = lambda: None
        u._FEEDS.update(urls={"x": "OpenPhish"}, hosts={})
        u._BIG.update(domains={"Phishing.Database": np.array([u._fingerprint("share.google")], dtype=np.uint64)}, links={})
        u.popularity_rank = lambda d: 50 if d == "thehindu.com" else None

        def opens(dest):
            return lambda url: {"ok": True, "final_url": dest if "share.google" in url else url, "hops": [dest],
                                "ssl_error": False, "title": "", "has_password": "login" in dest,
                                "text": "SBI login" if "login" in dest else "news", "download": None,
                                "blocked": False, "error": None}
        u.fetch_page = opens("https://www.thehindu.com/news/national/story/article1.ece")
        r = u.scan_url("https://share.google/k3IgCe77g1Gp4rhsH")
        assert r["verdict"] == "SAFE" and r["details"]["final_url"].startswith("https://www.thehindu.com"), r
        u.fetch_page = opens("https://sbi-reward-claim.xyz/login")
        assert u.scan_url("https://share.google/k3IgCe77g1Gp4rhsH")["verdict"] == "DANGEROUS"
    finally:
        for k, v in saved.items():
            setattr(u, k, v)
        pd.check = saved_pd
        u._BIG.clear(); u._BIG.update(saved_big)
        u._FEEDS.clear(); u._FEEDS.update(saved_feeds)


# ---- PhishStats and the Play Store check -------------------------------------------------------
def test_phishstats_exact_link_fails_other_pages_warn_and_quiet_when_unreachable():
    import scanners.url_scanner as u
    fresh()
    u._CACHE.clear() if hasattr(u, "_CACHE") else None
    real_get, offline = requests.get, u.OFFLINE
    try:
        u.OFFLINE = False
        rows = [{"url": "https://pay-sbi-kyc.xyz/login", "host": "pay-sbi-kyc.xyz", "score": 7.5}]
        requests.get = lambda url, **kw: R(200, rows)
        assert u.check_phishstats("https://pay-sbi-kyc.xyz/login", "pay-sbi-kyc.xyz") == {"status": "fail", "source": "PhishStats"}
        assert u.check_phishstats("https://pay-sbi-kyc.xyz/other", "pay-sbi-kyc.xyz")["status"] == "warn"
        requests.get = lambda url, **kw: R(200, [])
        assert u.check_phishstats("https://example-shop.in/", "example-shop.in")["status"] == "pass"
        requests.get = lambda url, **kw: (_ for _ in ()).throw(requests.ConnectionError())
        assert u.check_phishstats("https://other.in/", "other.in")["status"] == "skip"
    finally:
        requests.get, u.OFFLINE = real_get, offline


def test_bank_named_app_that_is_not_on_the_play_store_is_flagged():
    import io as _io
    import zipfile as _zip
    import scanners.url_scanner as u
    from scanners import apk_check
    fresh()
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w") as z:
        z.writestr("AndroidManifest.xml", b"x")
    real_get, real_manifest, offline = requests.get, apk_check.read_manifest, u.OFFLINE
    try:
        u.OFFLINE = False
        apk_check._play_cache.clear()
        apk_check.read_manifest = lambda b: {"package": "com.sbi.kyc.update", "permissions": ["android.permission.READ_SMS"]}
        requests.get = lambda url, **kw: R(404, text="not found")
        out = apk_check.analyze_apk("SBI KYC.apk", buf.getvalue())
        assert out["findings"][0].startswith("This app uses the name of a bank") and "com.sbi.kyc.update" in out["findings"][0]
        apk_check._play_cache.clear()
        requests.get = lambda url, **kw: R(200, text="<html>")
        out2 = apk_check.analyze_apk("SBI KYC.apk", buf.getvalue())
        assert not any("Play Store exists" in f or "no app called" in f for f in out2["findings"]) and out2["score"] < out["score"]
    finally:
        requests.get, apk_check.read_manifest, u.OFFLINE = real_get, real_manifest, offline


def test_connection_check_warns_about_services_open_to_the_internet_only_on_home_broadband():
    import scanners.url_scanner as u
    from scanners import network_checker as nc
    fresh()
    real_get, real_lookup, real_abuse, real_tor, offline = requests.get, nc.lookup_ip, nc.abuse_report, nc.is_tor_exit, u.OFFLINE
    try:
        u.OFFLINE = False
        nc._IP_CACHE.clear()
        nc.abuse_report = lambda ip: {}
        nc.is_tor_exit = lambda ip: False
        home = {"status": "success", "city": "Mangaluru", "regionName": "Karnataka", "country": "India", "isp": "BSNL",
                "timezone": "Asia/Kolkata", "proxy": False, "hosting": False, "mobile": False}
        nc.lookup_ip = lambda ip: home
        requests.get = lambda url, **kw: R(200, {"ports": [23, 80], "vulns": ["CVE-2023-1", "CVE-2023-2"]})
        out = nc.analyze_ip("117.200.1.2", "Asia/Kolkata")
        assert any(c["id"] == "net_exposed" and c["status"] == "warn" and "Telnet" in c["value"] for c in out["checks"])
        assert any("2 known security holes" in f for f in out["findings"])
        nc._IP_CACHE.clear()
        nc.lookup_ip = lambda ip: dict(home, mobile=True)          # mobile data: shared address, not checked
        calls = []
        requests.get = lambda url, **kw: (calls.append(url), R(200, {"ports": [23]}))[1]
        out = nc.analyze_ip("106.200.1.2", "Asia/Kolkata")
        assert calls == [] and not any(c["id"] == "net_exposed" for c in out["checks"])
    finally:
        requests.get, nc.lookup_ip, nc.abuse_report, nc.is_tor_exit, u.OFFLINE = real_get, real_lookup, real_abuse, real_tor, offline


# ---- Language quality ----------------------------------------------------------------------------
def test_site_language_decides_when_words_could_be_tulu_or_kannada():
    assert assistant.language_hint("ಫೋನ್ ಹ್ಯಾಕ್", "tcy") == ("tcy", "kannada")
    assert assistant.language_hint("enna phone hack aand dada malpodu", "kn") == ("tcy", "latin")
    assert assistant.language_hint("nanna account hack aagide", "tcy") == ("kn", "latin")   # clearly Kannada
    assert assistant.language_hint("my phone is hacked", "tcy") == (None, None)
    p = assistant.system_prompt("tcy", "", None, "phone hack")
    assert "Indian-language words in English letters, is most likely Tulu" in p


def test_tulu_answers_lose_kannada_only_words_and_kannada_answers_get_a_careful_proofread():
    assert assistant.tulu_polish("ನಿಮ್ಮ ಖಾತೆ ಬ್ಲಾಕ್ ಆಂಡ್ ಅಥವಾ OTP ಮತ್ತು PIN ಕೊರೊಡ್ಚಿ.") == "ಇರೆನ ಖಾತೆ ಬ್ಲಾಕ್ ಆಂಡ್ ಅತ್ತಂಡ OTP ಬೊಕ್ಕ PIN ಕೊರೊಡ್ಚಿ."
    assert assistant.tulu_polish("Nimma OTP korodchi") == "Irena OTP korodchi"
    fresh(GEMINI_API_KEY="g")
    original = "ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ ಮತ್ತು cybercrime.gov.in ನಲ್ಲಿ ದೂರು ನೀಡಿ."
    corrected = "ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ ಮತ್ತು cybercrime.gov.in ನಲ್ಲಿ ದೂರು ನೀಡಿರಿ."
    use(lambda url, **kw: gemini_ok(json.dumps({"text": corrected}, ensure_ascii=False)))
    assert assistant.proofread(original, "kn") == corrected
    # a "correction" that changes a number, the language or the length a lot is refused
    for bad in (corrected.replace("1930", "1903"), "Call 1930 now and file a complaint at cybercrime.gov.in.", "ಕರೆ ಮಾಡಿ."):
        use(lambda url, b=bad, **kw: gemini_ok(json.dumps({"text": b}, ensure_ascii=False)))
        assert assistant.proofread(original, "kn") == original, bad
    assert assistant.proofread("Ittene 1930 g call malpule", "kn") == "Ittene 1930 g call malpule"   # not Kannada script


def test_country_sites_and_very_popular_sites_are_not_called_fakes_but_tricks_still_are():
    import scanners.url_scanner as u
    saved = dict(u._TRANCO["ranks"])
    try:
        u._TRANCO["ranks"].clear()
        u._TRANCO["ranks"].update({"google.ro": 219, "kotaku.com": 882, "telegraf.com.ua": 1741, "blogspot.com": 40})
        for good in ("https://google.de/", "https://www.amazon.co.jp/", "https://google.ro/", "https://kotaku.com/",
                     "https://telegraf.com.ua/"):
            r = u.scan_url(good)
            assert r["verdict"] == "SAFE", (good, r["risk_score"], r["findings"])
        for bad in ("https://paypal-login.blogspot.com/", "https://g00gle.ro/", "https://kotak-kyc.com/",
                    "https://xkqzvbtrwplm.com/", "https://cafe-shop.com/wp-includes/paypal/signin/index.php"):
            r = u.scan_url(bad)
            assert r["verdict"] != "SAFE", (bad, r["risk_score"], r["findings"])
    finally:
        u._TRANCO["ranks"].clear(); u._TRANCO["ranks"].update(saved)


def test_blurry_screenshot_gets_a_second_reading_from_the_backup_reader():
    import io
    from PIL import Image
    import scanners.message_scanner as ms
    saved = (ms._tesseract_conf, ms._tesseract, ms._ocr_space, ms.ocr_languages, ms._detect_script)
    try:
        ms.ocr_languages = lambda: "eng"
        ms._detect_script = lambda img: ""
        ms._tesseract_conf = lambda img, lang, cfg, t: ("Y0ur S8l acc0unt w1ll b3 bl0ck", 40)
        ms._tesseract = lambda img, lang, cfg, t: ""
        ms._ocr_space = lambda b: "Your SBI account will be blocked today. Update KYC now"
        buf = io.BytesIO(); Image.new("RGB", (400, 200), "white").save(buf, "PNG")
        assert ms.extract_text_from_image(buf.getvalue()).startswith("Your SBI account")
        # a clear reading is kept, and the backup isn't asked
        ms._tesseract_conf = lambda img, lang, cfg, t: ("Your parcel is out for delivery today", 88)
        ms._ocr_space = lambda b: (_ for _ in ()).throw(AssertionError("backup should not be used"))
        assert ms.extract_text_from_image(buf.getvalue()).startswith("Your parcel")
    finally:
        ms._tesseract_conf, ms._tesseract, ms._ocr_space, ms.ocr_languages, ms._detect_script = saved


def test_tulu_and_kannada_word_lists_help_when_built_in_words_are_not_enough():
    from scanners import tulu_lexicon as tl
    from scanners.assistant import kannada_script_hint
    saved = dict(tl._lex)
    try:
        tl._lex.update(loaded=True,
                       tcy={"ಉಂಡು": 5000, "ಬೊಕ್ಕ": 4000, "ಇಜ್ಜಿ": 3000, "ಪೈಸೆ": 900, "ಬ್ಯಾಂಕ್": 500, "ಏರ್": 2000, "ಕಡಪುಡುಲೆ": 300},
                       kn={"ಇದೆ": 90000, "ಮತ್ತು": 120000, "ಇಲ್ಲ": 50000, "ಮಾಡಿ": 30000, "ಬ್ಯಾಂಕ್": 4000, "ನಿಮ್ಮ": 60000,
                           "ಕಳುಹಿಸಿ": 8000})
        tl._lex.update(tcy_total=sum(tl._lex["tcy"].values()), kn_total=sum(tl._lex["kn"].values()))
        assert tl.lean("ಏರ್ ಪೈಸೆ ಕಡಪುಡುಲೆ ಬ್ಯಾಂಕ್")[0] == "tcy"
        assert tl.lean("ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಕಳುಹಿಸಿ")[0] == "kn"
        assert tl.lean("ಬ್ಯಾಂಕ್")[0] is None                         # a shared word says nothing
        assert kannada_script_hint("ಏರ್ ಪೈಸೆ ಕಡಪುಡುಲೆ") in ("tcy", None)
        slips = tl.kannada_only_words("ಈ ಮೆಸೇಜ್ ಮೋಸ ಉಂಡು ಮತ್ತು ನಿಮ್ಮ ಬ್ಯಾಂಕ್‌ಗ್ ಕಾಲ್ ಮಾಡಿ")
        assert "ಮತ್ತು" in slips and "ನಿಮ್ಮ" in slips and "ಉಂಡು" not in slips and "ಬ್ಯಾಂಕ್‌ಗ್" not in slips, slips
    finally:
        tl._lex.clear(); tl._lex.update(saved)


def test_without_word_lists_nothing_changes():
    from scanners import tulu_lexicon as tl
    saved = dict(tl._lex)
    try:
        tl._lex.update(loaded=True, tcy={}, kn={}, tcy_total=0, kn_total=0)
        assert tl.lean("ಏರ್ ಪೈಸೆ ಕಡಪುಡುಲೆ") == (None, 0.0) and tl.kannada_only_words("ಮತ್ತು ನಿಮ್ಮ") == []
    finally:
        tl._lex.clear(); tl._lex.update(saved)


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    real_sleep = translator.time.sleep
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
        finally:
            requests.post = REAL_POST
            translator.time.sleep = real_sleep
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
