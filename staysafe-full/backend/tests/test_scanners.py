"""
StaySafe checker tests — real-world scam and genuine samples.

Run from the backend folder (no internet or API keys needed):
    python tests/test_scanners.py          # plain Python, prints a report
    python -m pytest tests                 # if you have pytest installed
"""
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scanners.url_scanner as url_scanner  # noqa: E402

# Keep tests offline and fast: skip the live WHOIS lookup
url_scanner.analyze_domain_age = lambda host: {"score": 0, "findings": []}

from scanners.message_scanner import analyze_text, check_links_in_result, extract_links  # noqa: E402
from scanners.url_scanner import scan_url  # noqa: E402
from scanners.file_scanner import check_extension_risk, check_content  # noqa: E402
from scanners.password_checker import analyze_strength  # noqa: E402
from scanners.qr_scanner import analyze_upi_string  # noqa: E402

DANGER = ("DANGEROUS", "SCAM_LIKELY")
SAFE = ("SAFE", "LIKELY_SAFE")

# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
SCAM_MESSAGES = {
    "KYC block": "Dear customer your SBI account will be blocked today. Update PAN immediately: http://sbi-kyc.xyz",
    "OTP request": "Share the code you just received to confirm your delivery",
    "OTP by phone": "Sir I am calling from HDFC, please tell me the OTP you received to stop the transaction",
    "Hinglish electricity": "Aapka bijli connection aaj raat 9:30 baje kaat diya jayega. Turant is number par call karein 9876543210",
    "Electricity": "Dear consumer, your electricity power will be disconnected tonight at 9.30pm because your previous month bill was not updated. Please immediately contact our electricity officer 9876543210",
    "Task job": "Hi, we are hiring for Amazon. Earn Rs 3000/day by liking YouTube videos. Contact on Telegram",
    "Digital arrest": "Your FedEx parcel contains illegal drugs. Mumbai police will arrest you. Join Skype video call now",
    "Lottery": "Congratulations! You have won Rs 25,00,000 in KBC lucky draw. Pay processing fee of Rs 5000 to claim your prize",
    "AnyDesk": "To process your refund please install AnyDesk and share the 9 digit code",
    "UPI PIN": "You have received cashback of Rs 2000. Enter your UPI PIN to receive the amount",
    "Hi mum": "Hi mum, this is my new number, my phone is broken. Can you send 15000 urgently for rent?",
    "Investment": "Join our VIP trading group, guaranteed returns of 30% monthly. Crypto investment tips daily",
    "TRAI": "TRAI notice: your mobile number will be blocked in 2 hours. Press 9 to speak to officer",
    "Tax refund": "Income tax refund of Rs 15,490 approved. Click http://bit.ly/itr-refund to update your account details",
}

GENUINE_MESSAGES = {
    "Bank OTP": "Your OTP for login is 482913. Do not share this OTP with anyone. -HDFC Bank",
    "Amazon OTP": "482913 is your Amazon OTP. Do not share it with anyone.",
    "Pin photo": "Can you pick up milk on the way home? Also pin the photo in the group",
    "Order shipped": "Your Amazon order has been shipped. Track: https://amazon.in/track",
    "Work urgency": "Urgent: team meeting moved to 3pm, please join",
    "Refund done": "Your refund of Rs 499 has been processed to your original payment method.",
    "Debit alert": "Rs 250.00 debited from A/c XX1234 on 27-09-26 to VPA swiggy@icici. If not done by you, call 18002586161 - SBI",
    "Friend": "bro send me the notes pdf pls, exam tomorrow",
    "Plan expiry": "Your Jio plan expires in 3 days. Recharge at https://www.jio.com to continue enjoying services.",
    "Share code": "I will share the code on github tonight",
    "Customs delay": "My parcel from Amazon is delayed by customs",
    "Wifi": "Can you share the wifi password?",
}


def test_scam_messages_detected():
    for name, text in SCAM_MESSAGES.items():
        result = analyze_text(text)
        assert result["verdict"] == "SCAM_LIKELY", (name, result)


def test_genuine_messages_not_flagged():
    for name, text in GENUINE_MESSAGES.items():
        result = analyze_text(text)
        assert result["verdict"] == "LIKELY_SAFE", (name, result)


def test_links_found_in_messages():
    links = extract_links("Track at amazon.in/track or www.sbi-kyc.xyz/login. Mail a@b.com at 9.30pm (http://bit.ly/x)")
    assert links == ["https://amazon.in/track", "https://www.sbi-kyc.xyz/login", "http://bit.ly/x"], links


def test_dangerous_link_makes_message_risky():
    result = check_links_in_result(analyze_text("Your parcel is waiting. Confirm address at amaz0n-delivery.com/track"))
    assert result["verdict"] == "SCAM_LIKELY", result
    assert result["links_checked"][0]["verdict"] == "DANGEROUS"


def test_real_link_keeps_message_safe():
    result = check_links_in_result(analyze_text("Your Amazon order has shipped. Track: https://amazon.in/track"))
    assert result["verdict"] == "LIKELY_SAFE", result


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------
PHISHING_URLS = [
    "https://sbi-kyc-update.in/login",
    "https://amaz0n-offers.com",
    "https://paypal.com.secure-login.verify-account.ru/x",
    "https://hdfc-netbanking-verify.xyz",
    "https://rewards-paytm.top/claim",
    "https://sbi-kyc.vercel.app",
]
REAL_URLS = [
    "https://google.com",
    "https://www.amazon.in/deal",
    "https://netbanking.hdfcbank.com/login",
    "https://onlinesbi.sbi",
    "https://www.irctc.co.in",
    "https://github.com/sathwikraibs/StaySafe",
    "https://staysafe-tool.vercel.app",
]


def test_phishing_urls_flagged():
    for url in PHISHING_URLS:
        result = scan_url(url)
        assert result["verdict"] == "DANGEROUS", (url, result)


def test_real_urls_safe():
    for url in REAL_URLS:
        result = scan_url(url)
        assert result["verdict"] == "SAFE", (url, result)


def test_ip_address_no_fake_subdomain_warning():
    result = scan_url("http://192.168.1.5/login")
    assert not any("sub-domain" in f for f in result["findings"]), result


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
def _zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return buf.getvalue()


def _file_score(name, data):
    ext_score, _ = check_extension_risk(name)
    content_score, _, real_type = check_content(name, data)
    return min(100, ext_score + content_score), real_type


def test_program_disguised_as_photo():
    score, real_type = _file_score("photo.jpg", b"MZ\x90\x00" + b"\x00" * 100)
    assert real_type == "Windows program" and score >= 50


def test_apk_disguised_as_pdf():
    score, real_type = _file_score("Payment.pdf", _zip({"AndroidManifest.xml": "x", "classes.dex": "x"}))
    assert real_type == "Android app" and score >= 50


def test_double_extension_with_spaces():
    score, _ = _file_score("invoice.pdf      .exe", b"MZ")
    assert score >= 50


def test_zip_with_program_inside():
    score, _ = _file_score("docs.zip", _zip({"Invoice.pdf.exe": "MZ"}))
    assert score >= 40


def test_docx_with_macros():
    score, _ = _file_score("report.docx", _zip({"word/document.xml": "<x/>", "word/vbaProject.bin": "x"}))
    assert score >= 50


def test_real_image_is_safe():
    score, real_type = _file_score("photo.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    assert real_type == "JPEG image" and score == 0


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def test_weak_passwords():
    for pw in ["Password@123", "Qwerty@12345", "P@ssw0rd2024!", "India@123", "Adm1n#2023"]:
        assert analyze_strength(pw)["strength_label"] == "Weak", pw


def test_strong_passwords():
    for pw in ["T7#kq9!Lm2&vZx", "blue-Mango-river-42"]:
        assert analyze_strength(pw)["strength_label"] == "Strong", pw


# ---------------------------------------------------------------------------
# UPI QR
# ---------------------------------------------------------------------------
def test_fake_refund_upi_qr():
    result = analyze_upi_string("upi://pay?pa=9876543210@ybl&pn=Refund%20Desk&am=15000&tn=Cashback%20refund")
    assert result["verdict"] == "DANGEROUS", result


def test_normal_shop_upi_qr():
    result = analyze_upi_string("upi://pay?pa=shop@okaxis&pn=Ravi%20Stores")
    assert result["verdict"] == "SAFE", result


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
