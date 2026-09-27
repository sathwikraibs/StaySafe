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

# Keep tests offline and fast: no DNS, WHOIS, page fetch, Safe Browsing or VirusTotal
url_scanner.OFFLINE = True

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
    "WhatsApp code": "Hi, I accidentally sent my WhatsApp code to you. Please send it back urgently",
    "WFH job": "Work from home job. Earn 5000 daily. No experience. Message on WhatsApp",
    "Challan": "You have a pending traffic challan of Rs 500. Pay now: echallan-parivahan.top",
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
    "Challan paid": "Your e-challan payment of Rs 500 is successful. Thank you",
    "Discount code": "Use code SAVE10, I sent the wrong code by mistake earlier",
}


def test_scam_messages_detected():
    for name, text in SCAM_MESSAGES.items():
        # the full check, including the links inside the message
        result = check_links_in_result(analyze_text(text))
        assert result["verdict"] == "SCAM_LIKELY", (name, result)


def test_genuine_messages_not_flagged():
    for name, text in GENUINE_MESSAGES.items():
        result = analyze_text(text)
        assert result["verdict"] == "LIKELY_SAFE", (name, result)


NEW_RULE_SAMPLES = {
    "Asks you to install an app from a link or file (APK)": "Hello, you are invited to our wedding. Please see the invitation card: wedding-card.apk",
    "Instant loan with no documents or checks": "Get instant loan of Rs 50,000 without documents. No CIBIL check",
    "Fake government scheme, Aadhaar, PAN or gas update": "PM Kisan: your installment is stopped. Update your KYC here: http://pmkisan-kyc.xyz",
    "Reward points or cashback that 'expire today'": "Your SBI credit card reward points worth Rs 7,850 expire today. Redeem now",
    "Threatens to share your photos or videos (blackmail)": "I have your video. Pay 20000 or I will make it viral and send to your family",
    "Asks for payment by gift card or crypto": "Buy 5 Google Play gift cards of Rs 2000 and send me the codes",
    "Asks for your Aadhaar, PAN or bank account details": "Please share your Aadhaar card and bank account number to receive the amount",
    "Asks you to keep it secret": "Do not tell anyone about this call, this is a confidential police matter",
    "Free recharge, data or gifts with a link": "Free 3 months Jio recharge for all users. Claim now: jio-free.xyz",
}
NEW_RULE_GENUINE = [
    "Download the Swiggy app from the Play Store to order",
    "Your loan EMI of Rs 5,400 is due on 5th. Pay via the HDFC app",
    "Please bring your Aadhaar card for the college admission tomorrow",
    "I got free data with my new Airtel plan",
]


def test_new_rules():
    for label, text in NEW_RULE_SAMPLES.items():
        result = analyze_text(text)
        assert label in result["patterns_detected"], (label, result["patterns_detected"])
        assert result["verdict"] != "LIKELY_SAFE", (label, result)
    for text in NEW_RULE_GENUINE:
        assert analyze_text(text)["verdict"] == "LIKELY_SAFE", text


KANNADA_HINDI_SCAMS = {
    "kn bank block": "ಆತ್ಮೀಯ ಗ್ರಾಹಕರೇ, ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ತಕ್ಷಣ KYC ಅಪ್‌ಡೇಟ್ ಮಾಡಿ",
    "kn OTP ask": "ನಿಮಗೆ ಬಂದ OTP ಯನ್ನು ತಕ್ಷಣ ಹೇಳಿ",
    "kn electricity": "ನಿಮ್ಮ ಕರೆಂಟ್ ಇಂದು ರಾತ್ರಿ 9:30 ಕ್ಕೆ ಕಟ್ ಆಗುತ್ತದೆ. ಈ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡಿ 9876543210",
    "kn lottery": "ಅಭಿನಂದನೆಗಳು! ನೀವು ಲಕ್ಕಿ ಡ್ರಾದಲ್ಲಿ ₹25 ಲಕ್ಷ ಗೆದ್ದಿದ್ದೀರಿ. ಪ್ರೊಸೆಸಿಂಗ್ ಶುಲ್ಕ ₹5000 ಕಟ್ಟಿ",
    "kn digital arrest": "ನಿಮ್ಮ ಪಾರ್ಸೆಲ್‌ನಲ್ಲಿ ಡ್ರಗ್ಸ್ ಸಿಕ್ಕಿದೆ. ಮುಂಬೈ ಪೊಲೀಸ್ ನಿಮ್ಮನ್ನು ಅರೆಸ್ಟ್ ಮಾಡುತ್ತಾರೆ. ವೀಡಿಯೊ ಕಾಲ್‌ಗೆ ಬನ್ನಿ",
    "kn task job": "ಮನೆಯಿಂದಲೇ ದಿನಕ್ಕೆ ₹3000 ಗಳಿಸಿ. ಯೂಟ್ಯೂಬ್ ವೀಡಿಯೊ ಲೈಕ್ ಮಾಡಿ. ನೋಂದಣಿ ಶುಲ್ಕ ₹500",
    "kn UPI PIN": "ಕ್ಯಾಶ್‌ಬ್ಯಾಕ್ ಪಡೆಯಲು ನಿಮ್ಮ UPI PIN ಹಾಕಿ",
    "kn new number": "ಅಮ್ಮಾ ಇದು ನನ್ನ ಹೊಸ ನಂಬರ್, ಫೋನ್ ಕಳೆದುಹೋಯಿತು. ತುರ್ತಾಗಿ 10000 ಹಣ ಕಳುಹಿಸಿ",
    "tulu bank + OTP": "ಈರೆನ ಖಾತೆ ಇನಿ ಬ್ಲಾಕ್ ಆಪುಂಡು. ಬೇಗನೇ OTP ಪನ್ಲೆ",
    "hi bank block": "आपका बैंक खाता आज बंद हो जाएगा। तुरंत KYC अपडेट करें",
    "hi OTP ask": "आपको आया हुआ OTP तुरंत बताइए",
    "hi electricity": "आपकी बिजली आज रात 9:30 बजे काट दी जाएगी। तुरंत इस नंबर पर कॉल करें 9876543210",
    "hi lottery": "बधाई हो! आपने लकी ड्रॉ में ₹25 लाख जीते हैं। प्रोसेसिंग फीस ₹5000 भेजें",
    "hi digital arrest": "आपके पार्सल में ड्रग्स मिले हैं। मुंबई पुलिस आपको गिरफ्तार करेगी। वीडियो कॉल पर आइए",
    "hi task job": "घर बैठे रोज ₹3000 कमाएं। यूट्यूब वीडियो लाइक करें। रजिस्ट्रेशन फीस ₹500",
    "hi new number": "मम्मी यह मेरा नया नंबर है, फोन खो गया। तुरंत 10000 पैसे भेज दो",
}

KANNADA_HINDI_GENUINE = {
    "kn bank OTP": "ನಿಮ್ಮ OTP 482913. ಇದನ್ನು ಯಾರಿಗೂ ಹೇಳಬೇಡಿ - SBI",
    "kn debit alert": "ನಿಮ್ಮ ಖಾತೆಯಿಂದ ₹250 ಕಡಿತವಾಗಿದೆ. ನೀವು ಮಾಡದಿದ್ದರೆ 1800111109 ಗೆ ಕರೆ ಮಾಡಿ",
    "kn family": "ಅಮ್ಮ, ಸಂಜೆ ಬರುವಾಗ ಹಾಲು ತನ್ನಿ",
    "kn bill": "ನಿಮ್ಮ ಕರೆಂಟ್ ಬಿಲ್ ₹450. ದಯವಿಟ್ಟು ಪಾವತಿಸಿ - ಮೆಸ್ಕಾಂ",
    "tulu OTP": "ಈರೆನ OTP 4829. ಏರೆಗ್‌ಲಾ ಕೊರೊಡ್ಚಿ",
    "hi bank OTP": "आपका OTP 482913 है। इसे किसी के साथ भी शेयर न करें - HDFC",
    "hi debit alert": "आपके खाते से ₹250 डेबिट हुए। अगर यह आपने नहीं किया तो 1800 पर कॉल करें",
    "hi school fee": "आपकी स्कूल फीस ₹5000 जमा करें - अंतिम तिथि 30 सितंबर",
    "hi family": "मम्मी, शाम को दूध ले आना",
}


def test_kannada_hindi_scams_detected():
    for name, text in KANNADA_HINDI_SCAMS.items():
        result = analyze_text(text)
        assert result["verdict"] == "SCAM_LIKELY", (name, result)


def test_kannada_hindi_genuine_not_flagged():
    for name, text in KANNADA_HINDI_GENUINE.items():
        result = analyze_text(text)
        assert result["verdict"] == "LIKELY_SAFE", (name, result)


def test_unsupported_language_is_not_called_safe():
    result = analyze_text("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন")  # Bengali — no built-in rules yet
    assert result["verdict"] == "UNCERTAIN", result


MORE_LANGUAGE_SCAMS = {
    "ta bank": "உங்கள் வங்கி கணக்கு இன்று முடக்கப்படும். உடனே KYC புதுப்பிக்கவும்",
    "ta otp": "உங்களுக்கு வந்த OTP ஐ உடனே சொல்லுங்கள்",
    "te bank": "మీ బ్యాంక్ ఖాతా ఈరోజు బ్లాక్ అవుతుంది. వెంటనే KYC అప్డేట్ చేయండి",
    "te arrest": "మీ పార్సెల్‌లో డ్రగ్స్ ఉన్నాయి. పోలీస్ మిమ్మల్ని అరెస్ట్ చేస్తారు. వీడియో కాల్‌కు రండి",
    "ml otp": "നിങ്ങൾക്ക് വന്ന OTP ഉടൻ പറയൂ",
    "ml power": "നിങ്ങളുടെ വൈദ്യുതി ഇന്ന് രാത്രി വിച്ഛേദിക്കും. ഉടൻ 9876543210 വിളിക്കുക",
    "mr bank": "तुमचे बँक खाते आज बंद होईल. ताबडतोब KYC अपडेट करा",
    "mr otp": "तुम्हाला आलेला OTP लगेच सांगा",
}
MORE_LANGUAGE_GENUINE = {
    "ta otp": "உங்கள் OTP 482913. இதை யாருடனும் பகிர வேண்டாம் - SBI",
    "te otp": "మీ OTP 482913. దీన్ని ఎవరితోనూ షేర్ చేయవద్దు - SBI",
    "ml otp": "നിങ്ങളുടെ OTP 482913. ഇത് ആരുമായും പങ്കിടരുത് - SBI",
    "mr otp": "तुमचा OTP 482913 आहे. तो कोणालाही सांगू नका - SBI",
}


def test_tamil_telugu_malayalam_marathi_without_translation():
    for name, text in MORE_LANGUAGE_SCAMS.items():
        assert analyze_text(text)["verdict"] == "SCAM_LIKELY", name
    for name, text in MORE_LANGUAGE_GENUINE.items():
        assert analyze_text(text)["verdict"] == "LIKELY_SAFE", name


def test_hidden_link_gets_a_tip():
    result = check_links_in_result(analyze_text("Your KYC is pending. Click here to update now"))
    assert any("Copy link" in n for n in result["notes"]), result


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


# ---- Live-style link checks, with the internet lookups replaced by fakes
def _online(dns=True, age=900, gsb=False, vt=None, page=None):
    """Run scan_url as if online. page = dict of fetch_page fields to override."""
    saved = {k: getattr(url_scanner, k) for k in
             ("OFFLINE", "resolve_host", "whois_age_days", "check_safe_browsing", "check_virustotal", "fetch_page")}
    base_page = {"ok": True, "final_url": None, "hops": [], "status": 200, "ssl_error": False, "title": "Welcome",
                 "has_password": False, "text": "welcome to our shop", "download": None, "blocked": False, "error": None}

    def fake_page(url):
        out = dict(base_page, **(page or {}))
        out["final_url"] = out["final_url"] or url
        return out

    url_scanner.OFFLINE = False
    url_scanner.resolve_host = lambda host: {"exists": dns, "ips": ["93.184.216.34"] if dns else []}
    url_scanner.whois_age_days = lambda domain: age
    url_scanner.check_safe_browsing = lambda urls: {"listed": gsb, "threats": ["SOCIAL_ENGINEERING"] if gsb else []}
    url_scanner.check_virustotal = lambda url, domain: vt or {"status": "ok", "malicious": 0, "suspicious": 0,
                                                             "harmless": 60, "engines": 90, "domain_malicious": 0}
    url_scanner.fetch_page = fake_page
    url_scanner.ensure_feeds = lambda: None  # no downloads in tests
    if not url_scanner._FEEDS["urls"]:
        url_scanner._FEEDS["urls"] = {"example.invalid/x": "test"}
    try:
        return lambda u: url_scanner.scan_url(u)
    finally:
        pass


def _restore():
    import importlib
    importlib.reload(url_scanner)
    url_scanner.OFFLINE = True


def _scan_online(url, **kw):
    try:
        return _online(**kw)(url)
    finally:
        _restore()


def test_website_that_does_not_exist_is_risky():
    r = _scan_online("https://my-free-gift-card.com", dns=False, age=None, vt={"status": "not_found"},
                     page={"ok": False, "error": "no_dns"})
    assert r["verdict"] == "DANGEROUS", r
    assert any(c["id"] == "exists" and c["status"] == "fail" for c in r["checks"]), r["checks"]


def test_google_blocklist_hit_is_always_risky():
    r = _scan_online("https://normal-looking-shop.com/offer", gsb=True)
    assert r["verdict"] == "DANGEROUS" and r["risk_score"] >= 90, r


def test_virustotal_hits_are_risky():
    r = _scan_online("https://normal-looking-shop.com", vt={"status": "ok", "malicious": 7, "suspicious": 1,
                                                          "harmless": 50, "engines": 90, "domain_malicious": 0})
    assert r["verdict"] == "DANGEROUS", r


def test_short_link_to_fake_bank_page_is_risky():
    r = _scan_online("https://bit.ly/abc123", page={"final_url": "https://sbi-rewards-kyc.top/login",
                                                   "hops": ["https://sbi-rewards-kyc.top/login"]})
    assert r["verdict"] == "DANGEROUS", r
    assert any(c["id"] == "redirect" and c["status"] == "warn" for c in r["checks"])


def test_fake_login_page_is_risky():
    r = _scan_online("https://secure-portal-7731.com/", page={"has_password": True, "title": "HDFC Bank NetBanking",
                                                            "text": "hdfc bank login customer id password"})
    assert r["verdict"] == "DANGEROUS", r


def test_brand_new_website_is_not_called_safe():
    r = _scan_online("https://best-deals-store.com", age=9)
    assert r["verdict"] != "SAFE", r


def test_misspelled_brand_names_are_risky():
    for u in ("https://amazom.in", "https://flipkarrt.com", "https://whatsaap.com/join"):
        r = _scan_online(u)
        assert r["verdict"] == "DANGEROUS", (u, r)


def test_words_that_look_like_brands_are_fine():
    for u in ("https://tomato.com", "https://www.apply.com", "https://kodak.com", "https://japan-guide.com"):
        r = _scan_online(u)
        assert r["verdict"] == "SAFE", (u, r)


def test_normal_old_website_is_safe():
    r = _scan_online("https://www.example-bakery.in/menu", age=3000)
    assert r["verdict"] == "SAFE", r
    assert all(c["status"] in ("pass", "info") for c in r["checks"]), r["checks"]


def test_broken_certificate_is_not_safe():
    r = _scan_online("https://some-shop.com", page={"ok": False, "ssl_error": True, "error": "ssl"})
    assert r["verdict"] != "SAFE", r


def test_link_that_downloads_an_app_is_risky():
    r = _scan_online("https://get-rewards.com/app", page={"download": "apk"})
    assert r["verdict"] == "DANGEROUS", r


def test_public_scam_list_hit_is_risky():
    try:
        scan = _online(age=2000)
        url_scanner._FEEDS["urls"] = {"normal-shop-offers.com/win": "OpenPhish"}
        url_scanner._FEEDS["hosts"] = {"normal-shop-offers.com": "OpenPhish"}
        r = scan("https://normal-shop-offers.com/win")
        assert r["verdict"] == "DANGEROUS", r
        r2 = scan("https://normal-shop-offers.com/other")
        assert any(c["id"] == "feeds" and c["status"] == "warn" for c in r2["checks"]), r2
    finally:
        _restore()


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


# ---------------------------------------------------------------------------
# Translation (Google Cloud Translation is replaced by a fake — no internet needed)
# ---------------------------------------------------------------------------
import scanners.translator as translator  # noqa: E402
from scanners.message_scanner import add_translation  # noqa: E402

FAKE_TRANSLATIONS = {
    ("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন", "en"):
        ("Your bank account will be blocked today. Update KYC immediately", "bn"),
    ("ನಿಮಗೆ ಬಂದ OTP ಯನ್ನು ತಕ್ಷಣ ಹೇಳಿ", "en"): ("Tell me the OTP you received immediately", "kn"),
    ("Your SBI account will be blocked today. Update KYC now", "kn"):
        ("ನಿಮ್ಮ SBI ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ಈಗಲೇ KYC ಅಪ್‌ಡೇಟ್ ಮಾಡಿ", "en"),
}


class _FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self._payload = status, payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def _use_fake_google(status=200, mymemory="ok", google_message="Cloud Translation API has not been used in project"):
    """Fake Google (POST) and MyMemory (GET). calls = list of (provider, text, target)."""
    calls = []

    def fake_post(url, params=None, json=None, timeout=None):
        calls.append(("google", json["q"], json["target"]))
        if status != 200:
            return _FakeResponse(status, {"error": {"message": google_message}})
        text, src = FAKE_TRANSLATIONS.get((json["q"], json["target"]), (json["q"], "en"))
        return _FakeResponse(200, {"data": {"translations": [{"translatedText": text, "detectedSourceLanguage": src}]}})

    def fake_get(url, params=None, timeout=None):
        src, target = params["langpair"].split("|")
        calls.append(("mymemory", params["q"], target))
        if mymemory == "quota":
            return _FakeResponse(200, {"responseStatus": 429, "responseData": {"translatedText":
                "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY"}})
        text, _ = FAKE_TRANSLATIONS.get((params["q"], target), (params["q"], src))
        return _FakeResponse(200, {"responseStatus": 200, "responseData": {"translatedText": text}})

    os.environ["TRANSLATE_API_KEY"] = "test-key"
    translator.requests.post = fake_post
    translator.requests.get = fake_get
    translator._cache.clear()
    translator._paused_until.update(google=0.0, mymemory=0.0)
    translator._problem.update(google=None, mymemory=None)
    translator._usage["chars"] = 0
    return calls


def test_translation_lets_us_check_other_languages():
    _use_fake_google()
    result = add_translation(analyze_text("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন"), "en")  # Bengali
    assert result["verdict"] == "SCAM_LIKELY", result
    assert result["translation"]["from"] == "bn" and "blocked" in result["translation"]["text"]


def test_kannada_message_explained_in_english():
    _use_fake_google()
    result = add_translation(analyze_text("ನಿಮಗೆ ಬಂದ OTP ಯನ್ನು ತಕ್ಷಣ ಹೇಳಿ"), "en")
    assert result["verdict"] == "SCAM_LIKELY"
    assert result["translation"]["to"] == "en" and "OTP" in result["translation"]["text"]


def test_english_message_explained_in_kannada_and_tulu():
    for ui in ("kn", "tcy"):  # Tulu isn't in Google's API, so Tulu readers get Kannada
        calls = _use_fake_google()
        result = add_translation(analyze_text("Your SBI account will be blocked today. Update KYC now"), ui)
        assert result["translation"]["to"] == "kn", (ui, result)
        assert calls == [("google", "Your SBI account will be blocked today. Update KYC now", "kn")]


def test_english_message_on_english_site_costs_nothing():
    calls = _use_fake_google()
    result = add_translation(analyze_text("Your order has shipped"), "en")
    assert calls == [] and "translation" not in result


def test_google_quota_or_trial_end_falls_back_to_free_mymemory():
    for status, message in ((429, "Quota exceeded for quota metric 'Characters per day'"),
                            (403, "Billing account for project is disabled / trial ended")):
        calls = _use_fake_google(status=status, google_message=message)
        result = add_translation(analyze_text("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন"), "en")
        assert result["verdict"] == "SCAM_LIKELY", (status, result)
        assert result["translation"]["provider"] == "mymemory"
        # Google is now paused: the next message goes straight to the free fallback
        calls.clear()
        translator._cache.clear()
        add_translation(analyze_text("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন"), "en")
        assert all(c[0] == "mymemory" for c in calls), calls


def test_everything_used_up_falls_back_to_built_in_rules():
    _use_fake_google(status=429, mymemory="quota", google_message="Quota exceeded")
    bengali = add_translation(analyze_text("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন"), "en")
    assert bengali["verdict"] == "UNCERTAIN" and "translation" not in bengali  # honest, not "safe"
    translator._cache.clear()
    tamil = add_translation(analyze_text(MORE_LANGUAGE_SCAMS["ta bank"]), "en")
    assert tamil["verdict"] == "SCAM_LIKELY"  # built-in Tamil rules still work
    assert translator._problem["mymemory"]  # MyMemory paused itself for the day


def test_without_google_key_mymemory_still_translates():
    _use_fake_google()
    os.environ.pop("TRANSLATE_API_KEY"); os.environ.pop("GSB_API_KEY", None)
    result = add_translation(analyze_text("আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই KYC আপডেট করুন"), "en")
    assert result["translation"]["provider"] == "mymemory" and result["verdict"] == "SCAM_LIKELY"


def test_daily_limit_protects_free_tier():
    calls = _use_fake_google()
    translator._usage["chars"] = translator.DAILY_LIMIT  # pretend today's Google budget is used up
    result = add_translation(analyze_text("ನಿಮಗೆ ಬಂದ OTP ಯನ್ನು ತಕ್ಷಣ ಹೇಳಿ"), "en")
    assert not any(c[0] == "google" for c in calls)  # Google not called at all
    assert result["verdict"] == "SCAM_LIKELY"  # native rules still work


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
