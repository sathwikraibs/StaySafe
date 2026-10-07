"""'Who is this?' check for phone numbers and UPI IDs.
Run: python tests/test_number_check.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanners.number_check import check_number  # noqa: E402


def v(value, claim="", ask=""):
    return check_number(value, claim, ask)["verdict"]


def test_official_and_ordinary_numbers_are_not_alarming():
    assert check_number("1930")["details"]["number_type"] == "helpline"
    assert v("1930") == "SAFE"
    assert v("98765 43210") == "SAFE"
    assert v("+91 98765 43210") == "SAFE"
    assert v("1600 123 456", "bank") == "SAFE"
    assert v("1800 1234") == "SAFE"          # short toll-free numbers exist (e.g. banks)
    assert v("1800 425 3800") == "SAFE"
    assert check_number("1800 1234")["details"]["number_type"] == "toll_free"


def test_bank_calling_from_a_mobile_or_foreign_number_is_flagged():
    assert v("98765 43210", "bank") == "CAUTION"
    assert v("140 123 4567", "bank") == "CAUTION"
    assert v("+1 202 555 0143", "bank") == "CAUTION"
    assert v("+92 300 1234567") == "CAUTION"
    assert v("+225 01 02 03 04 05") == "CAUTION"


def test_what_they_asked_for_decides_when_it_is_a_scam():
    assert v("98765 43210", "company", "pay_to_get") == "DANGEROUS"
    assert v("98765 43210", "bank", "otp") == "DANGEROUS"
    assert v("98765 43210", "official", "video") == "DANGEROUS"
    assert v("98765 43210", "unknown", "app") == "DANGEROUS"
    assert v("1930", "", "otp") == "DANGEROUS"   # the number shown can be faked
    assert v("ravi@okaxis", "family", "pay_to_get") == "DANGEROUS"


def test_upi_ids():
    r = check_number("ravi.kumar@okaxis")
    assert r["verdict"] == "SAFE" and r["details"]["app"] == "Google Pay" and r["findings"]
    assert v("sbi.refund@ybl") == "CAUTION"
    assert v("customercare.amazon@axl") == "CAUTION"
    assert any("not one we know" in f for f in check_number("shop@xyzpay")["findings"])
    assert check_number("not a number")["error"]


def test_every_finding_has_a_translation():
    import re
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fe = os.path.join(os.path.dirname(here), "frontend", "src", "i18n")
    samples = []
    for args in [("1930",), ("98765 43210", "bank"), ("98765 43210", "official"), ("98765 43210",), ("080 2222 3333",),
                 ("1600123456",), ("1401234567", "bank"), ("18001234567",), ("12345",), ("+92 300 1234567", "company"),
                 ("+225 0102030405",), ("+44 7911 123456",), ("sbi.refund@ybl",), ("9876543210@paytm",), ("xy@xyzpay",),
                 ("98765 43210", "family", "pay_to_get"), ("98765 43210", "", "otp"), ("98765 43210", "", "app"),
                 ("98765 43210", "", "video")]:
        samples += check_number(*args)["findings"]
    for lang in ("hi", "kn", "tcy"):
        src = open(os.path.join(fe, f"content-{lang}.ts"), encoding="utf-8").read()
        keys = re.findall(r'^\s*"((?:[^"\\]|\\.)*)":', src, re.M)
        pats = [re.compile("^" + re.sub(r"\\\{\w+\\\}", ".+?", re.escape(k.replace('\\"', '"'))) + "$") for k in keys]
        missing = [f for f in samples if not any(p.match(f) for p in pats)]
        assert not missing, (lang, missing[:3])


def test_phone_reputation_when_configured():
    import scanners.number_check as nc

    class _R:
        def __init__(self, d): self._d = d
        def json(self): return self._d
    saved = nc.requests.get
    try:
        os.environ["IPQS_API_KEY"] = "k"
        nc.requests.get = lambda url, **kw: _R({"success": True, "recent_abuse": True, "VOIP": True, "fraud_score": 90})
        r = check_number("98765 12345", "bank")
        assert r["findings"][0] == "This number has recently been linked to fraud or spam calls", r["findings"]
        assert any("VOIP" in f for f in r["findings"]) and r["verdict"] == "DANGEROUS", r
        # official numbers are never looked up
        nc.requests.get = lambda url, **kw: (_ for _ in ()).throw(AssertionError("looked up"))
        assert check_number("1930")["verdict"] == "SAFE"
    finally:
        nc.requests.get = saved
        os.environ.pop("IPQS_API_KEY", None)


def test_rbi_alert_list():
    import scanners.url_scanner as us
    us.OFFLINE = True
    from scanners import rbi_alert
    assert rbi_alert.domain_hit("hi.octafx.com", "octafx.com", True) == "OctaFX"
    assert rbi_alert.domain_hit("www.exness.com", "exness.com", True) == "Exness"
    assert rbi_alert.domain_hit("zerodha.com", "zerodha.com", True) is None
    r = us.scan_url("https://quotex.com/en/sign-up")
    assert r["verdict"] == "DANGEROUS" and "RBI's Alert List" in r["findings"][0], r["findings"]
    assert rbi_alert.names_in_text("Join our Olymp Trade VIP group, 90% profit daily", True) == ["Olymp Trade"]
    assert rbi_alert.names_in_text("Deposit on XM and copy my trades", True) == ["XM"]
    assert rbi_alert.names_in_text("XM radio is playing my favourite song", True) == []
    assert rbi_alert.names_in_text("I trust trade unions to fight for us", True) == []
    from scanners.message_scanner import analyze_text, add_entity_checks
    m = add_entity_checks(analyze_text("Earn 5000 daily with Binomo. Join now"))
    assert any("Binomo" in p and "RBI" in p for p in m["patterns_detected"]), m["patterns_detected"]


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
