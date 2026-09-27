"""
StaySafe - Message / Screenshot Scam Detector
-----------------------------------------------
Analyzes pasted text OR an uploaded screenshot for common scam patterns,
with a focus on scams seen in India (English + Hinglish):
  - Bank / KYC / PAN impersonation
  - OTP / PIN / CVV theft (only when someone ASKS for it)
  - Electricity disconnection scams
  - Courier / "digital arrest" / fake police scams
  - Task-based and fake job scams
  - Prize / lottery / advance-fee scams
  - Investment / trading scams
  - Remote access app requests (AnyDesk etc.)
  - "Hi mum, new number" family impersonation
  - Fake refunds and UPI "collect" tricks

It also recognises SAFE signals — e.g. a real bank OTP message that says
"do not share this OTP with anyone" — so genuine messages are not flagged.

Screenshot support uses OCR (Tesseract via pytesseract) to extract the text,
then runs it through the same rule engine as pasted text.
"""

import io
import re
import shutil
from flask import Blueprint, request, jsonify

message_scanner_bp = Blueprint("message_scanner", __name__)

try:
    import pytesseract
    from PIL import Image, ImageOps
    PYTESSERACT_INSTALLED = True
except ImportError:  # pragma: no cover
    PYTESSERACT_INSTALLED = False


def ocr_status() -> bool:
    """True only if both the Python package AND the Tesseract program exist."""
    if not PYTESSERACT_INSTALLED:
        return False
    cmd = pytesseract.pytesseract.tesseract_cmd
    return bool(shutil.which(cmd))


# ---------------------------------------------------------------------------
# SCAM PATTERN RULES
# Each rule: (label shown to user, list of regexes, weight)
# A rule counts once even if several of its patterns match.
# Text is lower-cased before matching.
# ---------------------------------------------------------------------------
LINK = r"(https?://|www\.|\b[a-z0-9-]+\.(?:xyz|top|club|click|live|icu|buzz|site|online|info|in|com|net|me|ly)/)"

RULES = [
    (
        "Asks you to share an OTP, PIN, CVV or password",
        [
            r"\b(share|send|tell|forward|give|provide|read out|confirm|batao|bata do|bhejo|bhej do)\b[^.\n]{0,40}\b(otp|one[- ]time (password|code)|verification code|cvv|upi pin|atm pin|card pin|mpin)\b",
            r"\b(share|send|tell|give)\b (me |us )?(your|the) (password|pin|login details|card details|card number)\b(?! (manager|tips|policy|rules))",
            r"\b(otp|verification code|cvv|mpin)\b[^.\n]{0,30}\b(share|send|tell|batao|bhejo|bhej do|forward)\b(?! (it )?with anyone)",
            r"\b(code|otp)\b[^.\n]{0,25}\b(you (just )?received|we (have )?sent|aaya hai|aya hai)\b",
        ],
        50,
    ),
    (
        "Asks for your UPI PIN to 'receive' money (you never need a PIN to receive)",
        [
            r"\b(enter|type|put|dalo|daalo)\b[^.\n]{0,20}\bupi pin\b",
            r"\bupi pin\b[^.\n]{0,40}\b(receive|get|credit|refund|cashback)\b",
            r"\b(scan|accept)\b[^.\n]{0,30}\b(qr|request)\b[^.\n]{0,40}\b(receive|get|refund|cashback|prize)\b",
        ],
        50,
    ),
    (
        "Bank / KYC / PAN impersonation",
        [
            r"\bre-?kyc\b", r"\bkyc\b[^.\n]{0,40}\b(update|pending|expire|verify|complete|block|suspend)",
            r"\b(account|a/c|khata|card|yono|net ?banking)\b[^.\n]{0,40}\b(will be |has been |is |ho jayega |hoga )?(blocked|suspended|frozen|deactivated|closed|band)\b",
            r"\b(update|link|verify)\b[^.\n]{0,20}\b(pan|aadhaar|aadhar)\b",
            r"\bverify your (account|bank|kyc|identity)\b",
        ],
        30,
    ),
    (
        "Electricity disconnection threat",
        [
            r"\b(electricity|bijli|power|light|eb)\b[^.\n]{0,60}\b(disconnect|disconnected|cut|kaat|kat|band)\b",
            r"\belectricity (officer|department)\b",
            r"\b(bill|bijli bill)\b[^.\n]{0,50}\b(not (been )?updated|update nahi)\b",
        ],
        35,
    ),
    (
        "Courier / customs / 'digital arrest' scam",
        [
            r"\bdigital arrest\b",
            r"\b(fedex|dhl|courier|parcel|package|shipment)\b[^\n]{0,100}\b(drugs|narcotics|illegal|seized|police|passports?|mdma)\b",
            r"\b(police|cbi|ncb|narcotics|crime branch|cyber ?crime|ed officer|enforcement directorate)\b[^\n]{0,80}\b(arrest|warrant|case|fir|video call|skype)\b",
            r"\barrest warrant\b",
        ],
        45,
    ),
    (
        "Impersonating government, police or tax department",
        [
            r"\b(income tax|it department)\b[^.\n]{0,40}\b(refund|notice|penalty)\b",
            r"\b(police|court) (verification|notice|summons)\b",
            r"\btrai\b[^.\n]{0,60}\b(disconnect|block|suspend)\b",
            r"\bpress \d\b[^.\n]{0,40}\b(officer|executive|agent|speak)\b",
            r"\b(sim|mobile number|number)\b[^.\n]{0,40}\b(will be |is )?(blocked|disconnected|deactivated|band)\b",
        ],
        30,
    ),
    (
        "Promises easy fixed daily/hourly earnings",
        [
            r"\b(earn|kamao|kamaye|income|salary)\b[^.\n]{0,40}(rs\.?|₹|inr)\s?\d[\d,]*\s*(/|per|a|daily|every)\s*(day|daily|hour|hr|task)",
        ],
        15,
    ),
    (
        "Task-based or fake job offer",
        [
            r"\b(lik(e|ing)|rat(e|ing)|review(ing)?|subscrib(e|ing))\b[^.\n]{0,40}\b(videos?|youtube|hotels?|products?|google maps)\b",
            r"\b(hiring|job offer|vacancy)\b[^\n]{0,120}\b(telegram|whatsapp)\b",
            r"\b(part[- ]time|work from home|ghar baithe)\b[^.\n]{0,80}\b(earn|daily|salary|income|kamao)\b",
            r"\b(registration|joining|security|training) (fee|deposit|charges?)\b",
        ],
        35,
    ),
    (
        "Prize, lottery or 'you have won' offer",
        [
            r"\byou (have |'ve )?(won|been selected)\b", r"\blottery\b", r"\blucky draw\b",
            r"\bkbc\b", r"\bjackpot\b", r"\bclaim (your )?(prize|reward|gift|cashback)\b",
            r"\bcongratulations\b[^.\n]{0,60}\b(won|winner|selected|reward|prize)\b",
            r"\b(inaam|lottery lagi)\b",
        ],
        30,
    ),
    (
        "Asks you to pay a fee to receive money",
        [
            r"\b(processing|delivery|release|clearance|tax|gst|handling) (fee|charges?)\b",
            r"\bpay\b[^.\n]{0,40}\b(to (receive|claim|release|unlock|withdraw))\b",
        ],
        30,
    ),
    (
        "Investment or trading scheme with unrealistic returns",
        [
            r"\bguaranteed (returns?|profit|income)\b", r"\bdouble your money\b",
            r"\b\d{2,3}\s?% (daily|weekly|monthly|returns?|profit)\b",
            r"\b(crypto|bitcoin|forex|stock|ipo)\b[^.\n]{0,40}\b(invest|profit|returns?|tips|signals?)\b",
            r"\bvip (group|trading)\b", r"\btrading (platform|signals?|app)\b",
        ],
        40,
    ),
    (
        "Asks you to install a remote access / screen sharing app",
        [
            r"\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid|screen ?share|remote access)\b",
            r"\b(download|install)\b[^.\n]{0,40}\b(apk|app from this link)\b",
            r"\.apk\b",
            r"\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid)\b[^\n]{0,80}\b(code|id|number)\b",
        ],
        45,
    ),
    (
        "Family member 'new number' / emergency money request",
        [
            r"\b(hi|hello)\s+(mum|mom|dad|mummy|papa|beta)\b[^\n]{0,120}\b(new number|lost my phone|phone (is )?broken)\b",
            r"\b(new number|lost my phone|phone (is )?broken)\b[^\n]{0,120}\b(send|transfer|pay|money|paise)\b",
            r"\b(urgent|emergency)\b[^.\n]{0,40}\b(send|transfer)\b[^.\n]{0,20}\b(money|paise|rs|₹)",
        ],
        30,
    ),
    (
        "Refund or cashback that needs you to click or fill a form",
        [
            r"\b(refund|cashback)\b[^.\n]{0,60}\b(click|link|form|claim|fill|apply)\b",
        ],
        25,
    ),
    (
        "Pressure / urgency language",
        [
            r"\bimmediately\b", r"\burgent(ly)?\b", r"\b(within|in) \d+ (hours?|hrs?|minutes?|mins?)\b",
            r"\bact now\b", r"\b(expire[sd]?|expiring) (today|soon|tonight)\b", r"\btoday itself\b",
            r"\btonight\b", r"\blast (chance|warning|reminder)\b", r"\bturant\b", r"\bjaldi\b", r"\baaj raat\b",
            r"\bfinal notice\b",
        ],
        10,
    ),
    (
        "Contains a shortened or unusual link",
        [
            r"\b(bit\.ly|tinyurl\.com|t\.ly|cutt\.ly|is\.gd|rb\.gy|shorturl\.at|tiny\.cc|ow\.ly|goo\.gl)/\S+",
            r"https?://\S+\.(xyz|top|club|click|live|icu|buzz|site|online|shop|rest|sbs|cfd|cyou|vip|support)\b",
            r"https?://\d{1,3}(\.\d{1,3}){3}",
        ],
        15,
    ),
    (
        "Asks you to call or message an unknown number",
        [
            r"\b(call|contact|whatsapp|message|sms)\b[^.\n]{0,30}(\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b",
            r"\b(contact|message|join)\b[^.\n]{0,20}\b(on |us on |me on )?telegram\b",
        ],
        10,
    ),
]


# ---------------------------------------------------------------------------
# KANNADA (also covers much Tulu, which uses Kannada script) and HINDI rules.
# Same scam types as above, written in the native scripts. No \b here: word
# boundaries don't work reliably inside Indian scripts. Text is normalised first
# (zero-width joiners and Hindi nukta dots removed), so patterns omit them.
# ---------------------------------------------------------------------------
KN_ASK = r"(ಹ(ೇ|ೆ)?ಳಿ|ಹೇಳು|ಕಳುಹಿಸಿ|ಕಳಿಸಿ|ಕಳ್ಸಿ|ಶೇರ್ ಮಾಡಿ|ಕೊಡಿ|ತಿಳಿಸಿ|ಹಂಚಿಕೊಳ್ಳಿ|ಪನ್ಲೆ|ಕೊರ್ಲೆ|ಕಡಪುಡ್ಲೆ)"
HI_ASK = r"(बताएं|बताइए|बताओ|बता दो|बता दें|भेजें|भेजो|भेजिए|भेज दो|शेयर करें|शेयर करो|दें|दीजिए|दे दो)"
MONEY = r"(₹|rs\.?|ರೂ\.?|ರೂಪಾಯಿ|रु\.?|रुपये|रुपए)"
NUM = r"(\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}"

NATIVE_PATTERNS = {
    "Asks you to share an OTP, PIN, CVV or password": [
        r"(otp|ಒಟಿಪಿ|ಓಟಿಪಿ|pin|ಪಿನ್|cvv|ಪಾಸ್ವರ್ಡ್|ಕೋಡ್)[^.\n]{0,40}" + KN_ASK,
        r"(ಬಂದ|ಬಂದಿರುವ|ಬತ್ತಿನ)[^.\n]{0,12}(otp|ಒಟಿಪಿ|ಕೋಡ್)",
        r"(otp|ओटीपी|pin|पिन|cvv|पासवर्ड|कोड)[^।.\n]{0,40}" + HI_ASK,
        r"(आया|आए|आई|आया हुआ)[^।\n]{0,12}(otp|ओटीपी|कोड)",
    ],
    "Asks for your UPI PIN to 'receive' money (you never need a PIN to receive)": [
        r"(upi pin|ಯುಪಿಐ ಪಿನ್|यूपीआई पिन|upi पिन)[^.\n]{0,40}(ಪಡೆಯ|ಸ್ವೀಕರಿಸ|ಕ್ಯಾಶ್ಬ್ಯಾಕ್|ರಿಫಂಡ್|ಬರುತ್ತ|प्राप्त|पाने|मिलेगा|मिलेंगे|कैशबैक|रिफंड)",
        r"(ಪಡೆಯಲು|ಸ್ವೀಕರಿಸಲು|पाने के लिए|प्राप्त करने के लिए)[^.\n]{0,30}(ಪಿನ್|pin|पिन)",
    ],
    "Bank / KYC / PAN impersonation": [
        r"(ಖಾತೆ|ಅಕೌಂಟ್|ಕಾರ್ಡ್|ಬ್ಯಾಂಕ್)[^.\n]{0,40}(ಬ್ಲಾಕ್|ಬಂದ್ ಆಗ|ಸ್ಥಗಿತ|ನಿಷ್ಕ್ರಿಯ|ಫ್ರೀಜ್)",
        r"(kyc|ಕೆವೈಸಿ)[^.\n]{0,40}(ಅಪ್ಡೇಟ್|ಬಾಕಿ|ಪರಿಶೀಲ|ಪೂರ್ಣ|ಮಾಡಿ)",
        r"(ಪ್ಯಾನ್|pan|ಆಧಾರ್)[^.\n]{0,20}(ಲಿಂಕ್|ಅಪ್ಡೇಟ್|ಜೋಡಿಸ)",
        r"(खाता|खाते|अकाउंट|कार्ड|बैंक)[^।\n]{0,40}(बंद हो|बंद कर|ब्लॉक|निलंबित|फ्रीज)",
        r"(kyc|केवाईसी)[^।\n]{0,40}(अपडेट|लंबित|पूरा|करें|कराएं)",
        r"(पैन|pan|आधार)[^।\n]{0,20}(लिंक|अपडेट)",
    ],
    "Electricity disconnection threat": [
        r"(ಕರೆಂಟ್|ವಿದ್ಯುತ್|ಲೈಟ್|ಬೆಸ್ಕಾಂ|ಮೆಸ್ಕಾಂ|ಹೆಸ್ಕಾಂ|ಚೆಸ್ಕಾಂ|ಜೆಸ್ಕಾಂ)[^.\n]{0,60}(ಕಟ್|ಸ್ಥಗಿತ|ಕಡಿತ|ನಿಲ್ಲಿಸ)",
        r"(ಕರೆಂಟ್ ಬಿಲ್|ವಿದ್ಯುತ್ ಬಿಲ್)[^.\n]{0,50}(ಅಪ್ಡೇಟ್ ಆಗಿಲ್ಲ|ಬಾಕಿ|ಪಾವತಿಸಿಲ್ಲ)",
        r"(बिजली|लाइट|विद्युत)[^।\n]{0,60}(कट|काट|बंद कर|बंद हो)",
        r"(बिजली बिल|बिल)[^।\n]{0,50}(अपडेट नहीं|बकाया|जमा नहीं)",
    ],
    "Courier / customs / 'digital arrest' scam": [
        r"(ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್|डिजिटल अरेस्ट|डिजिटल गिरफ्तारी)",
        r"(ಪಾರ್ಸೆಲ್|ಕೊರಿಯರ್|पार्सल|कूरियर|कुरियर)[^\n]{0,100}(ಡ್ರಗ್ಸ್|ಮಾದಕ|ಪೊಲೀಸ್|ಅಕ್ರಮ|ವಶಪಡಿಸ|ड्रग्स|नशीले|पुलिस|अवैध|गैरकानूनी|जब्त)",
        r"(ಪೊಲೀಸ್|ಸಿಬಿಐ|cbi|ಕ್ರೈಂ ಬ್ರಾಂಚ್|पुलिस|सीबीआई|क्राइम ब्रांच|साइबर क्राइम)[^\n]{0,80}(ಅರೆಸ್ಟ್|ಬಂಧನ|ಬಂಧಿಸ|ವಾರಂಟ್|ವೀಡಿಯೊ ಕಾಲ್|ವಿಡಿಯೋ ಕಾಲ್|गिरफ्तार|वारंट|वीडियो कॉल|अरेस्ट)",
    ],
    "Impersonating government, police or tax department": [
        r"(ಆದಾಯ ತೆರಿಗೆ|ಇನ್ಕಮ್ ಟ್ಯಾಕ್ಸ್|आयकर|इनकम टैक्स)[^.\n]{0,40}(ರಿಫಂಡ್|ನೋಟಿಸ್|ದಂಡ|रिफंड|नोटिस|जुर्माना)",
        r"(ಸಿಮ್|ಮೊಬೈಲ್ ನಂಬರ್|ನಿಮ್ಮ ನಂಬರ್|सिम|मोबाइल नंबर|आपका नंबर)[^.\n]{0,40}(ಬ್ಲಾಕ್|ಸ್ಥಗಿತ|ಬಂದ್|बंद|ब्लॉक)",
    ],
    "Promises easy fixed daily/hourly earnings": [
        r"(ದಿನಕ್ಕೆ|ಪ್ರತಿದಿನ|ಗಂಟೆಗೆ|रोज|प्रतिदिन|रोजाना|प्रति दिन|हर दिन|घंटे)[^.\n]{0,30}" + MONEY + r"\s?\d",
        MONEY + r"\s?\d[\d,]*[^.\n]{0,25}(ದಿನಕ್ಕೆ|ಪ್ರತಿದಿನ|ಗಂಟೆಗೆ|रोज|प्रतिदिन|रोजाना|प्रति दिन)",
    ],
    "Task-based or fake job offer": [
        r"(ಲೈಕ್|ರಿವ್ಯೂ|ರೇಟಿಂಗ್|ಸಬ್ಸ್ಕ್ರೈಬ್|लाइक|रिव्यू|रेटिंग|सब्सक्राइब)[^.\n]{0,40}(ವೀಡಿಯೊ|ವಿಡಿಯೋ|ಯೂಟ್ಯೂಬ್|youtube|ಹೋಟೆಲ್|वीडियो|यूट्यूब|होटल)",
        r"(ನೋಂದಣಿ|ರಿಜಿಸ್ಟ್ರೇಶನ್|ತರಬೇತಿ|ಟ್ರೇನಿಂಗ್|ಸೆಕ್ಯುರಿಟಿ) ?(ಶುಲ್ಕ|ಫೀ|ಫೀಸ್|ಠೇವಣಿ)",
        r"(रजिस्ट्रेशन|पंजीकरण|ट्रेनिंग|सिक्योरिटी) ?(फीस|शुल्क|डिपॉजिट)",
        r"(ಮನೆಯಿಂದಲೇ|ಮನೆಯಲ್ಲೇ ಕುಳಿತು|ಪಾರ್ಟ್ ಟೈಮ್|घर बैठे|पार्ट टाइम)[^\n]{0,80}(ಗಳಿಸಿ|ಸಂಪಾದ|ಸಂಬಳ|ಆದಾಯ|कमाएं|कमाई|कमाइए|सैलरी|आय)",
    ],
    "Prize, lottery or 'you have won' offer": [
        r"(ಲಾಟರಿ|ಲಕ್ಕಿ ಡ್ರಾ|ನೀವು ಗೆದ್ದಿದ್ದೀರಿ|ಬಹುಮಾನ ಗೆದ್ದ|ಬಹುಮಾನ ಸಿಕ್ಕ|लॉटरी|लकी ड्रॉ|आपने जीत|इनाम जीत|इनाम मिला|केबीसी)",
        # "Congratulations ... ₹25 lakh" — also survives screenshot misreads of the prize words
        r"(ಅಭಿನಂದನೆ|बधाई)[^\n]{0,80}" + MONEY + r"\s?\d[\d,]*\s?(ಲಕ್ಷ|ಕೋಟಿ|लाख|करोड)",
    ],
    "Asks you to pay a fee to receive money": [
        r"(ಪ್ರೊ?ಸೆ?ಸಿಂಗ್|ಡೆಲಿವರಿ|ಕ್ಲಿಯರೆನ್ಸ್|ಜಿಎಸ್ಟಿ|ತೆರಿಗೆ|ಬಿಡುಗಡೆ) ?(ಶುಲ್ಕ|ಫೀ|ಫೀಸ್|ಚಾರ್ಜ್)",
        r"(प्र(ो)?स(े)?सिंग|डिलीवरी|क्लियरेंस|जीएसटी|टैक्स|रिलीज) ?(फीस|शुल्क|चार्ज)",
        r"(ಶುಲ್ಕ|ಫೀ|फीस|शुल्क|चार्ज)[^।.\n]{0,15}" + MONEY + r"\s?\d[^।.\n]{0,30}(ಕಳುಹಿಸಿ|ಕಳಿಸಿ|भेजें|भेजो|भेज दें|भेजिए)",
    ],
    "Investment or trading scheme with unrealistic returns": [
        r"(ಖಚಿತ|ಗ್ಯಾರಂಟಿ|ಗ್ಯಾರಂಟೀಡ್)[^.\n]{0,15}(ಲಾಭ|ರಿಟರ್ನ್|ಆದಾಯ)",
        r"(गारंटी|पक्का|निश्चित|गारंटीड)[^।\n]{0,15}(मुनाफा|रिटर्न|लाभ|कमाई)",
        r"(ಹಣ ಡಬಲ್|ದುಡ್ಡು ಡಬಲ್|पैसा डबल|पैसे डबल|रकम दोगुनी)",
        r"(ಕ್ರಿಪ್ಟೋ|ಟ್ರೇಡಿಂಗ್|ಷೇರು|क्रिप्टो|ट्रेडिंग|शेयर बाजार)[^.\n]{0,40}(ಲಾಭ|ಹೂಡಿಕೆ|ಟಿಪ್ಸ್|मुनाफ|निवेश|टिप्स)",
    ],
    "Asks you to install a remote access / screen sharing app": [
        r"(ಎನಿಡೆಸ್ಕ್|ಟೀಮ್ವೀವರ್|ಸ್ಕ್ರೀನ್ ಶೇರ್|एनीडेस्क|टीमव्यूअर|स्क्रीन शेयर)",
        r"(ಎಪಿಕೆ|एपीके)",
    ],
    "Family member 'new number' / emergency money request": [
        r"(ಹೊಸ ನಂಬರ್|ಫೋನ್ ಕಳೆದು|ಫೋನ್ ಹಾಳಾ|ಪೊಸ ನಂಬರ್|नया नंबर|फोन खो|फोन खराब|फोन टूट)[^\n]{0,120}(ಹಣ|ದುಡ್ಡು|ಕಳುಹಿಸ|ಪೈಸೆ|पैसे|पैसा|भेज)",
        r"(ಅಮ್ಮ|ಅಪ್ಪ|ಮಮ್ಮಿ|ಪಪ್ಪ|ಅಪ್ಪೆ|ಅಮ್ಮೆ|मम्मी|पापा|माँ|मां)[^\n]{0,60}(ಹೊಸ ನಂಬರ್|ಪೊಸ ನಂಬರ್|नया नंबर)",
    ],
    "Refund or cashback that needs you to click or fill a form": [
        r"(ರಿಫಂಡ್|ಕ್ಯಾಶ್ಬ್ಯಾಕ್|ಹಣ ವಾಪಸ್|रिफंड|कैशबैक|पैसे वापस)[^.\n]{0,60}(ಕ್ಲಿಕ್|ಲಿಂಕ್|ಫಾರ್ಮ್|क्लिक|लिंक|फॉर्म)",
    ],
    "Pressure / urgency language": [
        r"(ತಕ್ಷಣ|ಕೂಡಲೇ|ಇಂದೇ|ಇವತ್ತೇ|ಇಂದು ರಾತ್ರಿ|ಇವತ್ತು ರಾತ್ರಿ|ಕೊನೆಯ ಅವಕಾಶ|ಕೊನೆಯ ಎಚ್ಚರಿಕೆ|ತುರ್ತು|ತುರ್ತಾಗಿ|ಇತ್ತೆನೇ|ಬೇಗನೇ)",
        r"(तुरंत|फौरन|आज ही|आज रात|अंतिम चेतावनी|आखिरी मौका|जल्द से जल्द|घंटे के भीतर|घंटों में)",
    ],
    "Asks you to call or message an unknown number": [
        r"(ಕರೆ ಮಾಡಿ|ಸಂಪರ್ಕಿಸಿ|ವಾಟ್ಸಾಪ್|ಕಾಲ್ ಮಲ್ಪುಲೆ|कॉल करें|फोन करें|संपर्क करें|व्हाट्सएप)[^\n]{0,40}" + NUM,
        NUM + r"[^\n]{0,30}(ಗೆ ಕರೆ|ಕರೆ ಮಾಡಿ|ಸಂಪರ್ಕಿಸಿ|ಕಾಲ್ ಮಲ್ಪುಲೆ|पर कॉल|पर फोन|पर संपर्क)",
    ],
}
for _label, _patterns, _w in RULES:
    _patterns.extend(NATIVE_PATTERNS.get(_label, []))


# ---------------------------------------------------------------------------
# TAMIL, TELUGU, MALAYALAM and MARATHI rules — so the most common scams are
# caught even when no translation is available (the ₹0 fallback).
# ---------------------------------------------------------------------------
MORE_NATIVE_PATTERNS = {
    "Asks you to share an OTP, PIN, CVV or password": [
        r"(otp|ஓடிபி|pin|பின்|cvv|கடவுச்சொல்|குறியீடு)[^.\n]{0,40}(சொல்லுங்கள்|சொல்லுங்க|சொல்லவும்|அனுப்புங்கள்|அனுப்பவும்|பகிரவும்|பகிருங்கள்|கொடுங்கள்|தெரிவிக்கவும்)",
        r"(வந்த|பெற்ற)[^.\n]{0,12}(otp|ஓடிபி|குறியீடு)",
        r"(otp|ఓటీపీ|pin|పిన్|cvv|పాస్వర్డ్|కోడ్)[^.\n]{0,40}(చెప్పండి|చెప్పు|పంపండి|పంపు|షేర్ చేయండి|ఇవ్వండి|తెలియజేయండి)",
        r"(వచ్చిన)[^.\n]{0,12}(otp|ఓటీపీ|కోడ్)",
        r"(otp|ഒടിപി|pin|പിൻ|cvv|പാസ്വേഡ്|കോഡ്)[^.\n]{0,40}(പറയൂ|പറയുക|അയക്കൂ|അയയ്ക്കുക|ഷെയർ ചെയ്യൂ|നൽകൂ|നൽകുക)",
        r"(വന്ന|ലഭിച്ച)[^.\n]{0,12}(otp|ഒടിപി|കോഡ്)",
        r"(otp|ओटीपी|pin|पिन|cvv|पासवर्ड|कोड)[^।.\n]{0,40}(सांगा|पाठवा|शेअर करा|द्या)",
        r"(आलेला|आलेले)[^।\n]{0,12}(otp|ओटीपी|कोड)",
    ],
    "Asks for your UPI PIN to 'receive' money (you never need a PIN to receive)": [
        r"(upi pin|யுபிஐ பின்)[^.\n]{0,40}(பெற|கேஷ்பேக்|ரீஃபண்ட்|பணம் வர)",
        r"(upi pin|యూపీఐ పిన్)[^.\n]{0,40}(పొంద|క్యాష్బ్యాక్|రీఫండ్|డబ్బు వస్తుంది)",
        r"(upi pin|യുപിഐ പിൻ)[^.\n]{0,40}(ലഭിക്ക|സ്വീകരി|ക്യാഷ്ബാക്ക്|റീഫണ്ട്)",
    ],
    "Bank / KYC / PAN impersonation": [
        r"(கணக்கு|அக்கவுண்ட்|கார்டு|வங்கி)[^.\n]{0,40}(முடக்க|தடை|பிளாக்|நிறுத்த|மூடப்)",
        r"(kyc|கேஒய்சி)[^.\n]{0,40}(புதுப்பி|அப்டேட்|நிலுவை|சரிபார்)",
        r"(பான்|pan|ஆதார்)[^.\n]{0,20}(இணை|புதுப்பி|அப்டேட்|லிங்க்)",
        r"(ఖాతా|అకౌంట్|కార్డ్|బ్యాంక్)[^.\n]{0,40}(బ్లాక్|నిలిపి|స్తంభింప|మూసివేయ|ఫ్రీజ్)",
        r"(kyc|కేవైసీ)[^.\n]{0,40}(అప్డేట్|పెండింగ్|పూర్తి|ధృవీకరి)",
        r"(పాన్|pan|ఆధార్)[^.\n]{0,20}(లింక్|అప్డేట్)",
        r"(അക്കൗണ്ട്|കാർഡ്|ബാങ്ക്)[^.\n]{0,40}(ബ്ലോക്ക്|മരവിപ്പി|റദ്ദാക്ക|നിർത്ത)",
        r"(kyc|കെവൈസി)[^.\n]{0,40}(അപ്ഡേറ്റ്|പുതുക്ക|പൂർത്തിയാക്ക)",
        r"(പാൻ|pan|ആധാർ)[^.\n]{0,20}(ലിങ്ക്|അപ്ഡേറ്റ്)",
        r"(खाते|अकाउंट|कार्ड|बँक)[^।\n]{0,40}(बंद होईल|बंद केले|ब्लॉक|गोठव)",
    ],
    "Electricity disconnection threat": [
        r"(மின்சார|மின் இணைப்பு|கரண்ட்)[^.\n]{0,60}(துண்டிக்க|நிறுத்த|கட்)",
        r"(కరెంట్|విద్యుత్|పవర్)[^.\n]{0,60}(కట్|నిలిపి|డిస్కనెక్ట్)",
        r"(വൈദ്യുതി|കറന്റ്|കെഎസ്ഇബി)[^.\n]{0,60}(വിച്ഛേദി|കട്ട്|നിർത്ത)",
        r"(वीज|लाईट|महावितरण)[^।\n]{0,60}(कापली|कापण्यात|कट|खंडित|बंद)",
    ],
    "Courier / customs / 'digital arrest' scam": [
        r"(டிஜிட்டல் கைது|டிஜிட்டல் அரெஸ்ட்|డిజిటల్ అరెస్ట్|ഡിജിറ്റൽ അറസ്റ്റ്)",
        r"(பார்சல்|கூரியர்)[^\n]{0,100}(போதை|போலீஸ்|காவல்|சட்டவிரோத)",
        r"(போலீஸ்|காவல்துறை|சிபிஐ|cbi)[^\n]{0,80}(கைது|வாரண்ட்|வீடியோ கால்)",
        r"(పార్సెల్|కొరియర్)[^\n]{0,100}(డ్రగ్స్|మత్తు|పోలీస్|అక్రమ)",
        r"(పోలీస్|సీబీఐ|cbi)[^\n]{0,80}(అరెస్ట్|వారెంట్|వీడియో కాల్)",
        r"(പാർസൽ|കൊറിയർ)[^\n]{0,100}(മയക്കുമരുന്ന്|ഡ്രഗ്സ്|പോലീസ്|നിയമവിരുദ്ധ)",
        r"(പോലീസ്|സിബിഐ|cbi)[^\n]{0,80}(അറസ്റ്റ്|വാറണ്ട്|വീഡിയോ കോൾ)",
    ],
    "Prize, lottery or 'you have won' offer": [
        r"(லாட்டரி|லக்கி டிரா|நீங்கள் வென்று|பரிசு வென்ற|பரிசு பெற்ற)",
        r"(లాటరీ|లక్కీ డ్రా|మీరు గెలుచుకున్నారు|బహుమతి గెలుచ)",
        r"(ലോട്ടറി|ലക്കി ഡ്രോ|നിങ്ങൾ നേടി|സമ്മാനം നേടി)",
        r"(लॉटरी|तुम्ही जिंकला|बक्षीस जिंक)",
    ],
    "Asks you to pay a fee to receive money": [
        r"(செயலாக்க|டெலிவரி|ஜிஎஸ்டி) ?(கட்டணம்|சார்ஜ்)",
        r"(ప్రాసెసింగ్|డెలివరీ|జీఎస్టీ) ?(ఫీజు|రుసుము|చార్జ్)",
        r"(പ്രോസസ്സിംഗ്|ഡെലിവറി|ജിഎസ്ടി) ?(ഫീസ്|ചാർജ്)",
        r"(प्रोसेसिंग|डिलिव्हरी) ?(फी|शुल्क)",
    ],
    "Promises easy fixed daily/hourly earnings": [
        r"(தினமும்|ஒரு நாளைக்கு|தினசரி|రోజుకు|ప్రతిరోజు|రోజూ|ദിവസവും|പ്രതിദിനം|दररोज|रोज)[^.\n]{0,30}" + MONEY + r"\s?\d",
    ],
    "Task-based or fake job offer": [
        r"(வீட்டிலிருந்தே|பகுதி நேர)[^\n]{0,80}(சம்பாதி|வருமானம்|சம்பளம்)",
        r"(லைக்|ரிவ்யூ|ரேட்டிங்)[^.\n]{0,40}(வீடியோ|யூடியூப்|youtube)",
        r"(பதிவு|பயிற்சி) ?கட்டணம்",
        r"(ఇంటి నుండే|పార్ట్ టైమ్)[^\n]{0,80}(సంపాదించ|జీతం|ఆదాయం)",
        r"(లైక్|రివ్యూ|రేటింగ్)[^.\n]{0,40}(వీడియో|యూట్యూబ్|youtube)",
        r"(రిజిస్ట్రేషన్|ట్రైనింగ్) ?(ఫీజు|రుసుము)",
        r"(വീട്ടിലിരുന്ന്|പാർട്ട് ടൈം)[^\n]{0,80}(സമ്പാദി|ശമ്പളം|വരുമാനം)",
        r"(ലൈക്ക്|റിവ്യൂ|റേറ്റിംഗ്)[^.\n]{0,40}(വീഡിയോ|യൂട്യൂബ്|youtube)",
        r"(രജിസ്ട്രേഷൻ|ട്രെയിനിംഗ്) ?ഫീസ്",
        r"(घरबसल्या|पार्ट टाइम)[^\n]{0,80}(कमवा|पगार|उत्पन्न)",
    ],
    "Investment or trading scheme with unrealistic returns": [
        r"(உத்தரவாத|கியாரண்டி)[^.\n]{0,15}(லாபம்|வருமானம்)", r"பணம் இரட்டிப்பு",
        r"(గ్యారంటీ|హామీ)[^.\n]{0,15}(లాభం|రాబడి)", r"డబ్బు రెట్టింపు",
        r"(ഉറപ്പായ|ഗ്യാരണ്ടി)[^.\n]{0,15}(ലാഭം|റിട്ടേൺ)", r"പണം ഇരട്ടി",
        r"(खात्रीशीर|हमखास)[^।\n]{0,15}(नफा|परतावा)",
    ],
    "Asks you to install a remote access / screen sharing app": [
        r"(எனிடெஸ்க்|டீம்வியூவர்|ஸ்கிரீன் ஷேர்|ఎనీడెస్క్|టీమ్వ్యూయర్|స్క్రీన్ షేర్|എനിഡെസ്ക്|ടീംവ്യൂവർ|സ്ക്രീൻ ഷെയർ)",
    ],
    "Family member 'new number' / emergency money request": [
        r"(புதிய எண்|போன் தொலை)[^\n]{0,120}(பணம்|அனுப்ப)",
        r"(కొత్త నంబర్|ఫోన్ పోయింది)[^\n]{0,120}(డబ్బు|పంప)",
        r"(പുതിയ നമ്പർ|ഫോൺ നഷ്ടപ്പെട്ടു)[^\n]{0,120}(പണം|അയക്ക)",
        r"(नवीन नंबर|फोन हरवला)[^\n]{0,120}(पैसे|पाठव)",
    ],
    "Refund or cashback that needs you to click or fill a form": [
        r"(ரீஃபண்ட்|கேஷ்பேக்|பணம் திரும்ப)[^.\n]{0,60}(கிளிக்|லிங்க்|இணைப்பை)",
        r"(రీఫండ్|క్యాష్బ్యాక్)[^.\n]{0,60}(క్లిక్|లింక్)",
        r"(റീഫണ്ട്|ക്യാഷ്ബാക്ക്)[^.\n]{0,60}(ക്ലിക്ക്|ലിങ്ക്)",
    ],
    "Pressure / urgency language": [
        r"(உடனே|உடனடியாக|இன்றே|இன்று இரவு|கடைசி வாய்ப்பு|அவசர)",
        r"(వెంటనే|తక్షణమే|ఈరోజే|ఈ రాత్రి|చివరి అవకాశం|అత్యవసర)",
        r"(ഉടൻ|ഉടനടി|ഇന്ന് തന്നെ|ഇന്ന് രാത്രി|അവസാന അവസരം|അടിയന്തര)",
        r"(ताबडतोब|लगेच|आजच|आज रात्री|शेवटची संधी)",
    ],
    "Asks you to call or message an unknown number": [
        r"(அழைக்கவும்|தொடர்பு கொள்ளவும்|கால் செய்|కాల్ చేయండి|సంప్రదించండి|വിളിക്കുക|ബന്ധപ്പെടുക|कॉल करा|संपर्क करा)[^\n]{0,40}" + NUM,
        NUM + r"[^\n]{0,30}(அழைக்கவும்|தொடர்பு|కి కాల్|కాల్ చేయండి|വിളിക്കുക|ബന്ധപ്പെടുക|वर कॉल करा|वर संपर्क)",
    ],
}

# Malayalam "chillu" letters can be typed two ways; store both texts and patterns one way
CHILLU = {"ൺ": "ണ്", "ൻ": "ന്", "ർ": "ര്", "ൽ": "ല്", "ൾ": "ള്"}


def _unify_chillu(text: str) -> str:
    for atomic, seq in CHILLU.items():
        text = text.replace(atomic, seq)
    return text


for _label, _patterns, _w in RULES:
    _patterns.extend(_unify_chillu(p).replace("‍", "").replace("‌", "")
                     for p in MORE_NATIVE_PATTERNS.get(_label, []))

# Signals that a message is a genuine notification, not a scam
SAFE_SIGNALS = [
    r"\b(do not|don't|dont|never)\s+share\b",
    r"\bnever (ask|asks) for (your )?(otp|pin|password|cvv)\b",
    r"\bkisi (ke saath|se bhi|ko bhi)\b[^.\n]{0,30}\b(share na|mat)\b",
    r"\bif (this was )?not (done by )?you\b",
    # Kannada / Tulu: "don't tell/share with anyone"
    r"ಯಾರಿಗೂ[^.\n]{0,15}(ಹೇಳಬೇಡಿ|ಹಂಚಿಕೊಳ್ಳಬೇಡಿ|ಕೊಡಬೇಡಿ|ಶೇರ್ ಮಾಡಬೇಡಿ|ತಿಳಿಸಬೇಡಿ)",
    r"(ಹಂಚಿಕೊಳ್ಳಬೇಡಿ|ಶೇರ್ ಮಾಡಬೇಡಿ|ಕೊರೊಡ್ಚಿ|ಪನೊಡ್ಚಿ)",
    r"(ನೀವು ಮಾಡಿಲ್ಲದಿದ್ದರೆ|ನೀವು ಮಾಡದಿದ್ದರೆ)",
    # Hindi: "don't share with anyone"
    r"(किसी को भी|किसी के साथ|किसी से)[^।\n]{0,20}(न|ना|मत) ",
    r"(न|ना|मत) (बताएं|बताइए|बताओ|शेयर करें|शेयर करो|दें)",
    r"(यदि|अगर) (यह )?(आपने नहीं|आपके द्वारा नहीं)",
    # Tamil, Telugu, Malayalam, Marathi: "don't share / tell anyone"
    r"(யாருடனும்|யாரிடமும்)[^.\n]{0,20}(பகிர வேண்டாம்|சொல்ல வேண்டாம்|பகிராதீர்கள்)",
    r"(ఎవరితోనూ|ఎవరికీ)[^.\n]{0,20}(షేర్ చేయవద్దు|చెప్పవద్దు|పంచుకోవద్దు)",
    _unify_chillu(r"(ആരുമായും|ആരോടും)[^.\n]{0,20}(പങ്കിടരുത്|പറയരുത്|ഷെയർ ചെയ്യരുത്)"),
    r"(कोणालाही|कोणासोबतही)[^।\n]{0,20}(सांगू नका|शेअर करू नका|देऊ नका)",
]

HIGH_RISK_LABELS = {r[0] for r in RULES if r[2] >= 30}


# ---------------------------------------------------------------------------
# LANGUAGE COVERAGE — be honest when a message is in a script we can't check well
# ---------------------------------------------------------------------------
NOTE_OTHER_SCRIPT = (
    "This message is mostly in a language our checks can't read yet (we check English, Hinglish, Kannada, "
    "Hindi, Tamil, Telugu, Malayalam and Marathi). We couldn't fully check it — be careful, and never share "
    "OTPs, PINs or passwords."
)
NOTE_NEW_SCRIPT = (
    "Our checks for messages written in Indian-language scripts are new and may miss some scams — stay careful."
)
NOTE_TRANSLATED_CHECK = (
    "We also checked an automatic English translation of this message. Translations can miss details — stay careful."
)
NOTE_HIDDEN_LINK = (
    "This message asks you to click a link, but the link itself isn't visible here — it may be hidden "
    "behind words like 'click here'. Press and hold the link, choose 'Copy link', and paste it into Check a Link."
)

HIDDEN_LINK_PHRASES = re.compile(
    r"(click here|tap here|click (on )?(the )?(below |above )?link|tap (on )?(the )?link|click (the |this )?button|"
    r"click below|link below|ಇಲ್ಲಿ ಕ್ಲಿಕ್|ಇಲ್ಲಿ ಒತ್ತಿ|ಕೆಳಗಿನ ಲಿಂಕ್|ಲಿಂಕ್ ಕ್ಲಿಕ್|ಲಿಂಕ್ ಒತ್ತಿ|ಮುಲ್ಪ ಕ್ಲಿಕ್|"
    r"यहाँ क्लिक|यहां क्लिक|यहाँ टैप|यहां टैप|नीचे दिए (गए )?लिंक|लिंक पर क्लिक|इस लिंक)",
)


def script_mix(text: str) -> dict:
    """Share of letters in: latin, supported Indian scripts (Kannada, Devanagari), other scripts."""
    counts = {"latin": 0, "supported": 0, "other": 0}
    for ch in text:
        if not ch.isalpha():
            continue
        code = ord(ch)
        if ch.isascii():
            counts["latin"] += 1
        elif (0x0900 <= code <= 0x097F or 0x0C80 <= code <= 0x0CFF or 0x0B80 <= code <= 0x0BFF
              or 0x0C00 <= code <= 0x0C7F or 0x0D00 <= code <= 0x0D7F):
            counts["supported"] += 1
        else:
            counts["other"] += 1
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "SCAM_LIKELY"
    if score >= 25:
        return "SUSPICIOUS"
    return "LIKELY_SAFE"


def _normalise(text: str) -> str:
    text = text.lower()
    # zero-width joiners (common in Kannada words like ಅಪ್‌ಡೇಟ್) and Hindi nukta dots
    text = text.replace("\u200c", "").replace("\u200d", "").replace("\u093c", "")
    text = _unify_chillu(text)
    text = text.replace("’", "'").replace("₹", "₹")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def analyze_text(text: str) -> dict:
    text_norm = _normalise(text)
    findings = []
    score = 0

    for label, patterns, weight in RULES:
        hits = sum(1 for p in patterns if re.search(p, text_norm))
        if hits:
            findings.append(label)
            score += weight
            if hits >= 2 and weight >= 30:
                score += 10  # several independent signs of the same scam type

    # A plain link on its own is normal, but links in a threatening message are a red flag
    has_link = re.search(LINK, text_norm) is not None
    high_risk_hits = [f for f in findings if f in HIGH_RISK_LABELS]
    if has_link and high_risk_hits:
        findings.append("Contains a link inside a threatening or too-good-to-be-true message")
        score += 15

    # Pressure + a high-risk ask together is a classic scam combo
    if "Pressure / urgency language" in findings and high_risk_hits:
        score += 10

    safe_hits = [p for p in SAFE_SIGNALS if re.search(p, text_norm)]
    notes = []
    if safe_hits:
        otp_label = RULES[0][0]
        # A genuine OTP SMS says "do not share this OTP" — that alone shouldn't count as asking for it
        asks_to_share_with_sender = re.search(
            r"\b(share|send|tell|forward|give)\b[^.\n]{0,40}\b(otp|code|pin)\b[^.\n]{0,20}\b(with (me|us)|to (me|us)|here)\b",
            text_norm,
        )
        if otp_label in findings and not asks_to_share_with_sender:
            findings.remove(otp_label)
            score -= RULES[0][2]
        score -= 15
        notes.append("Contains a genuine-looking safety warning (e.g. 'do not share your OTP')")

    score = max(0, min(100, score))
    verdict = verdict_from_score(score)

    info = []
    mix = script_mix(text)
    if not findings:
        if mix["other"] > 0.4:
            verdict = "UNCERTAIN"  # don't tell people it's safe when we couldn't read it
            info.append(NOTE_OTHER_SCRIPT)
        elif mix["supported"] > 0.4:
            info.append(NOTE_NEW_SCRIPT)

    return {
        "text_analyzed": text,
        "risk_score": score,
        "verdict": verdict,
        "patterns_detected": findings,
        "safe_signals": notes,
        "notes": info,
    }



# ---------------------------------------------------------------------------
# LINK CHECK — every link in the message gets the full link scanner
# (structure rules + domain age + Google Safe Browsing + VirusTotal)
# ---------------------------------------------------------------------------
MAX_LINKS_CHECKED = 3

URL_IN_TEXT = re.compile(
    r"(?<![@\w.])("
    r"https?://[^\s<>\"'()]+"
    r"|www\.[^\s<>\"'()]+"
    r"|(?:[a-z0-9-]+\.)+(?:com|in|net|org|info|xyz|top|club|click|live|icu|buzz|site|online|shop|store|"
    r"rest|sbs|cfd|cyou|vip|support|me|ly|co|io|app|link|tk|ml|ga|cf|gq|ru|cn|sbi)(?:/[^\s<>\"'()]*)?"
    r")",
    re.IGNORECASE,
)


def extract_links(text: str) -> list:
    """Find links in the text (with or without http://), de-duplicated, in order."""
    links = []
    for match in URL_IN_TEXT.finditer(text):
        link = match.group(1).rstrip(".,;:!?)]}'\"")
        if not link.lower().startswith(("http://", "https://")):
            link = "https://" + link
        if link.lower() not in (l.lower() for l in links):
            links.append(link)
    return links


def check_links_in_result(result: dict) -> dict:
    """Run the full link scanner on up to 3 links and fold the results into the verdict."""
    from scanners.url_scanner import scan_url

    links = extract_links(result.get("text_analyzed", ""))
    checked = []
    extra_score = 0
    for link in links[:MAX_LINKS_CHECKED]:
        try:
            link_result = scan_url(link)
        except Exception:
            continue
        checked.append({
            "url": link,
            "verdict": link_result["verdict"],
            "risk_score": link_result["risk_score"],
            "findings": link_result["findings"],
        })
        reason = next((f for f in link_result["findings"] if "Could not" not in f), "")
        if link_result["verdict"] == "DANGEROUS":
            result["patterns_detected"].append(
                f"The link {link} looks dangerous" + (f": {reason}" if reason else "")
            )
            extra_score = max(extra_score, 50)
        elif link_result["verdict"] == "CAUTION":
            result["patterns_detected"].append(
                f"The link {link} looks suspicious" + (f": {reason}" if reason else "")
            )
            extra_score = max(extra_score, 20)

    if len(links) > MAX_LINKS_CHECKED:
        result["patterns_detected"].append(
            f"This message has {len(links)} links; we checked the first {MAX_LINKS_CHECKED}"
        )

    if not links and HIDDEN_LINK_PHRASES.search(_normalise(result.get("text_analyzed", ""))):
        result.setdefault("notes", []).append(NOTE_HIDDEN_LINK)

    result["links_checked"] = checked
    result["risk_score"] = min(100, result["risk_score"] + extra_score)
    if extra_score or result.get("verdict") != "UNCERTAIN":
        result["verdict"] = verdict_from_score(result["risk_score"])
    return result

# ---------------------------------------------------------------------------
# TRANSLATION — understand other languages, and explain in the visitor's language
# ---------------------------------------------------------------------------
def request_language() -> str:
    """The website language the visitor is using (sent by the frontend as X-Lang)."""
    lang = (request.headers.get("X-Lang") or "en").strip().lower()
    return lang if re.fullmatch(r"[a-z]{2,3}", lang) else "en"


def add_translation(result: dict, ui_lang: str) -> dict:
    """
    1. If the message isn't mainly in English letters, check an English translation
       with the same rules and merge what it finds (the rules still decide).
    2. If the message's language differs from the website's, add
       result["translation"] = {"text", "from", "to"} so we can show what it says.
    """
    from scanners.translator import translate, TARGET_FALLBACK

    text = result.get("text_analyzed", "")
    mix = script_mix(text)
    non_latin = mix["supported"] + mix["other"]
    english = None

    if non_latin >= 0.2:
        english = translate(text, "en")
        if english and english["text"].strip():
            en_result = analyze_text(english["text"])
            for pattern in en_result["patterns_detected"]:
                if pattern not in result["patterns_detected"]:
                    result["patterns_detected"].append(pattern)
            was_unreadable = result.get("verdict") == "UNCERTAIN" or not result["patterns_detected"]
            result["risk_score"] = max(result["risk_score"], en_result["risk_score"])
            result["verdict"] = verdict_from_score(result["risk_score"])
            notes = [n for n in result.get("notes", []) if n not in (NOTE_OTHER_SCRIPT, NOTE_NEW_SCRIPT)]
            if was_unreadable or mix["other"] > 0.4:
                notes.append(NOTE_TRANSLATED_CHECK)
            result["notes"] = notes

    # "What this message says" in the visitor's language
    target = TARGET_FALLBACK.get(ui_lang, ui_lang)
    meaning = english if (english and target == "en") else None
    if meaning is None and text.strip():
        if non_latin >= 0.2 or target != "en":
            meaning = translate(text, target)
    if meaning and meaning.get("from") and meaning["from"].split("-")[0] != target \
            and meaning["text"].strip().lower() != text.strip().lower():
        result["translation"] = meaning
    return result


# ---------------------------------------------------------------------------
# OCR helpers
# ---------------------------------------------------------------------------
def _prepare_for_ocr(img):
    """Grayscale, fix phone photo rotation, upscale small screenshots, handle dark mode."""
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    w, h = img.size
    if max(w, h) < 1500:
        scale = 1500 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    elif max(w, h) > 4000:
        scale = 4000 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    # Dark-mode chat screenshots: light text on dark background -> invert
    histogram = img.histogram()
    total_pixels = img.size[0] * img.size[1]
    if sum(histogram[:100]) > total_pixels * 0.5:
        img = ImageOps.invert(img)
    return ImageOps.autocontrast(img)


_OCR_LANGS = None


def ocr_languages() -> str:
    """English plus Kannada and Hindi when their language packs are installed (see Dockerfile)."""
    global _OCR_LANGS
    if _OCR_LANGS is None:
        try:
            installed = set(pytesseract.get_languages(config=""))
        except Exception:
            installed = {"eng"}
        _OCR_LANGS = "+".join(l for l in ("eng", "kan", "hin") if l in installed) or "eng"
    return _OCR_LANGS


def extract_text_from_image(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    prepared = _prepare_for_ocr(img)
    langs = ocr_languages()
    text = pytesseract.image_to_string(prepared, lang=langs, config="--psm 6", timeout=60)
    if len(text.strip()) < 10:
        # try automatic page layout as a fallback
        text = pytesseract.image_to_string(prepared, lang=langs, timeout=60)
    return text.strip()


# ---------------------------------------------------------------------------
# ROUTE 1 — paste text directly (SMS / WhatsApp / email body)
# ---------------------------------------------------------------------------
@message_scanner_bp.route("/api/scan-message", methods=["POST"])
def scan_message_route():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Please paste the message you want to check."}), 400

    result = add_translation(analyze_text(text), request_language())
    result = check_links_in_result(result)

    from scanners.risk_engine import log_scan
    log_scan("message", result)

    return jsonify(result)


# ---------------------------------------------------------------------------
# ROUTE 2 — upload a screenshot (OCR extracts text, then same analysis)
# ---------------------------------------------------------------------------
@message_scanner_bp.route("/api/scan-screenshot", methods=["POST"])
def scan_screenshot_route():
    if not ocr_status():
        return jsonify({
            "error": "Screenshot reading is not set up on the server yet (Tesseract OCR is missing). "
                     "You can paste the message text instead."
        }), 503

    if "image" not in request.files:
        return jsonify({"error": "Please choose a screenshot to upload."}), 400

    image_bytes = request.files["image"].read()
    if not image_bytes:
        return jsonify({"error": "The uploaded image was empty."}), 400

    try:
        extracted_text = extract_text_from_image(image_bytes)
    except RuntimeError:
        return jsonify({"error": "Reading this image took too long. Try cropping it to just the message."}), 400
    except Exception:
        return jsonify({"error": "We couldn't open this image. Please upload a PNG or JPG screenshot."}), 400

    if len(extracted_text) < 5:
        return jsonify({
            "error": "We couldn't find readable text in this image. Try a clearer, uncropped screenshot, "
                     "or paste the message text instead."
        }), 400

    result = add_translation(analyze_text(extracted_text), request_language())
    result = check_links_in_result(result)

    from scanners.risk_engine import log_scan
    log_scan("screenshot", result)

    return jsonify(result)
