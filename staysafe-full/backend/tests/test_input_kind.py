"""Wrong-section detection: each check notices input that belongs to another tool."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scanners.input_kind import kind_of, wrong_tool  # noqa: E402
from scanners.email_analyzer import scan_email  # noqa: E402


def test_kinds():
    assert kind_of("https://sbi.in/x") == "link"
    assert kind_of("sbi-kyc.in") == "link"
    assert kind_of("a@b.com") == "email_address"
    assert kind_of("name@okaxis") == "upi"
    assert kind_of("+91 98765 43210") == "phone"
    assert kind_of("From: a@b.com\nTo: c@d.com\nSubject: hi\n\nbody") == "email_source"
    assert kind_of("Your account will be blocked http://x.in") == "message"


def test_wrong_tool_per_section():
    assert wrong_tool("https://x.in", "email") == "link"
    assert wrong_tool("https://x.in", "message") == "link"
    assert wrong_tool("https://x.in", "link") is None
    assert wrong_tool("a@b.com", "link") == "email"
    assert wrong_tool("9876543210", "link") == "number"
    assert wrong_tool("Your account is blocked, click http://x.in", "link") is None   # the link inside is checked
    assert wrong_tool("hello", "number") is None                                       # let the number check explain
    assert wrong_tool("1930", "number") is None
    assert wrong_tool("Dear customer your bank account will be blocked today", "number") == "message"


def test_email_checker_only_takes_emails():
    r = scan_email({"raw_email": "https://sbi-yono-kyc.in/update"})
    assert r.get("wrong_tool") == "link" and "error" in r
    assert "error" in scan_email({"raw_email": "Dear customer your account is blocked"})
    assert scan_email({"raw_email": "9876543210"}).get("wrong_tool") == "number"
    assert "error" in scan_email({"body": "click http://x.in"})                      # no sender
    assert scan_email({"sender_email": "http://x.in", "body": "hi"}).get("wrong_tool") == "link"
    assert "error" in scan_email({"sender_email": "a@b.com", "body": ""})
    assert scan_email({"body": "https://sbi-kyc.in/update"}).get("wrong_tool") == "link"      # link in the message box
    assert scan_email({"body": "name@okaxis"}).get("wrong_tool") == "number"
    full = "From: SBI <alerts@sbi-kyc.xyz>\nTo: me@gmail.com\nSubject: KYC\n\nUpdate KYC at http://sbi-kyc.xyz now"
    assert "error" not in scan_email({"body": full})                                       # whole email pasted in the box


if __name__ == "__main__":
    import scanners.url_scanner as us
    us.OFFLINE = True
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    ok = 0
    for t in tests:
        try:
            t(); ok += 1; print("PASS ", t.__name__)
        except Exception as e:
            print("FAIL ", t.__name__, repr(e))
    print(f"\n{ok}/{len(tests)} tests passed")
