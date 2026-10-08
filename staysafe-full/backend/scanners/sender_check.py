"""
TrustLight - Who sent the message, and which phone numbers it asks you to contact
-----------------------------------------------------------------------------------
Works offline, no API.

1. SMS sender. Since 6 May 2025 (TRAI), every business SMS in India comes from a registered
   sender like "AX-HDFCBK-S": 2 letters for the operator and circle, the company's 6-letter
   code, and a letter for the kind of message:
       -S service   -T transactional (OTPs, bank alerts)   -G government   -P promotional (ads)
   So a "bank" or "electricity office" message from a normal mobile number, from a foreign
   number, or sent as an advert (-P) while talking about your account, is a scam sign.

2. Phone numbers inside the message. Asking you to call or WhatsApp a foreign number is a
   classic sign of job, investment and "customer care" scams.

Uses Google's libphonenumber (the "phonenumbers" package) when installed, for exact country
names; otherwise a built-in list of common country codes.
"""

import re

try:
    import phonenumbers
    from phonenumbers import geocoder
except Exception:  # optional
    phonenumbers = None

# Words that mean "this message claims to come from an organisation"
ORG_CLAIM = re.compile(
    r"\b(bank|sbi|hdfc|icici|axis bank|kotak|canara|pnb|bank of baroda|union bank|yono|net ?banking|kyc|"
    r"credit card|debit card|paytm|phonepe|google pay|amazon|flipkart|jio|airtel|bsnl|customer care|"
    r"electricity|bescom|mseb|tneb|tangedco|kseb|lpg|indane|income tax|epfo|uidai|"
    r"police|cbi|customs|court|rto|e-?challan|fastag|traffic police|fedex|dhl|india post|bluedart|"
    r"government|govt|ministry|pm kisan|lic|insurance)\b",
    re.IGNORECASE,
)
ACCOUNT_THREAT = re.compile(
    r"\b(kyc|pan|aadhaa?r|account|a/c|card|net ?banking|yono)\b[^.\n]{0,50}"
    r"\b(block|blocked|suspend|suspended|expire|expired|update|verify|deactivat|close|band)",
    re.IGNORECASE,
)

# Registered business sender: XX-ABCDEF with an optional -S/-T/-G/-P ending
HEADER = re.compile(r"^\s*([A-Z]{2})-([A-Z0-9]{3,9})(?:-([STGP]))?\s*$")
INDIAN_MOBILE = re.compile(r"^(?:\+?91[\s-]?|0)?([6-9]\d{4}[\s-]?\d{5})$")
ANY_NUMBER = re.compile(r"^\+?[\d\s\-()]{7,20}$")

COMMON_CODES = {  # used when the phonenumbers package isn't installed
    "1": "USA/Canada", "44": "UK", "971": "UAE", "966": "Saudi Arabia", "974": "Qatar", "965": "Kuwait",
    "968": "Oman", "973": "Bahrain", "92": "Pakistan", "880": "Bangladesh", "977": "Nepal", "94": "Sri Lanka",
    "62": "Indonesia", "84": "Vietnam", "63": "Philippines", "60": "Malaysia", "65": "Singapore", "66": "Thailand",
    "855": "Cambodia", "856": "Laos", "95": "Myanmar", "86": "China", "852": "Hong Kong", "7": "Russia",
    "234": "Nigeria", "233": "Ghana", "254": "Kenya", "27": "South Africa", "20": "Egypt", "90": "Turkey",
    "49": "Germany", "33": "France", "61": "Australia", "64": "New Zealand", "81": "Japan", "82": "South Korea",
}

FOREIGN_IN_TEXT = re.compile(r"(?:\+|\b00)(?!91)(\d{1,3})[\s-]?\d[\d\s-]{6,14}\d")
WA_LINK = re.compile(r"wa\.me/(\+?\d{8,15})", re.IGNORECASE)


def _country_of(number: str):
    """'+84 912 345 678' -> 'Vietnam'. None for Indian or unknown numbers."""
    raw = re.sub(r"[^\d+]", "", number)
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    if not raw.startswith("+"):
        raw = "+" + raw
    if raw.startswith("+91"):
        return None
    if phonenumbers is not None:
        try:
            parsed = phonenumbers.parse(raw, None)
            if not phonenumbers.is_possible_number(parsed):
                return None
            # the main country for the code (+44 is the UK, not Guernsey)
            region = phonenumbers.region_code_for_country_code(parsed.country_code)
            try:
                name = geocoder._region_display_name(region, "en", None, None)
            except Exception:
                name = ""
            name = name or geocoder.country_name_for_number(parsed, "en")
            return name or f"+{parsed.country_code}"
        except Exception:
            return None
    for size in (3, 2, 1):
        code = raw[1:1 + size]
        if code in COMMON_CODES:
            return COMMON_CODES[code]
    return None


def classify_sender(sender: str) -> dict:
    """{'kind': 'header'|'indian_mobile'|'foreign'|'unknown', 'suffix', 'country'}"""
    s = (sender or "").strip()
    if not s:
        return {"kind": "unknown"}
    m = HEADER.match(s.upper())
    if m and not s.replace("-", "").isdigit():
        return {"kind": "header", "suffix": m.group(3), "code": m.group(2)}
    compact = re.sub(r"[\s()-]", "", s)
    if INDIAN_MOBILE.match(compact):
        return {"kind": "indian_mobile"}
    if ANY_NUMBER.match(s) and (compact.startswith("+") or compact.startswith("00")):
        country = _country_of(compact)
        if country:
            return {"kind": "foreign", "country": country}
    return {"kind": "unknown"}


def find_sender_in_text(text: str) -> str:
    """Screenshots usually show the sender at the top: 'VM-SBIINB-S' or '+91 98765 43210'."""
    for line in (text or "").splitlines()[:4]:
        line = line.strip()
        if HEADER.match(line.upper()) or (ANY_NUMBER.match(line) and len(re.sub(r"\D", "", line)) >= 10):
            return line
    return ""


def sender_signals(sender: str, text: str, claims_org: bool = False) -> dict:
    """Findings, score and safe notes from who sent the message."""
    out = {"findings": [], "score": 0, "safe": [], "sender": sender, "kind": "unknown"}
    info = classify_sender(sender)
    out["kind"] = info["kind"]
    claims_org = claims_org or ORG_CLAIM.search(text or "") is not None
    if info["kind"] == "indian_mobile" and claims_org:
        out["findings"].append(
            "Claims to be from a bank, company or government office, but was sent from a personal mobile "
            "number. Real ones use a registered sender name like AX-HDFCBK-S")
        out["score"] += 30
    elif info["kind"] == "foreign":
        out["findings"].append(f"Sent from a foreign phone number ({info['country']})")
        out["score"] += 30 if claims_org else 20
    elif info["kind"] == "header":
        if info.get("suffix") == "P" and ACCOUNT_THREAT.search(text or ""):
            out["findings"].append(
                "Sent as an advert (the sender name ends in -P) but talks about your account. Real bank "
                "alerts come from senders ending in -S or -T")
            out["score"] += 20
        elif info.get("suffix") in ("S", "T", "G"):
            out["safe"].append("Sent from a registered business sender. Still check any link before opening it")
    return out


def foreign_numbers_in_text(text: str) -> list:
    """Countries of foreign phone numbers the message asks you to contact."""
    countries = []
    for m in list(FOREIGN_IN_TEXT.finditer(text or "")) + list(WA_LINK.finditer(text or "")):
        country = _country_of(m.group(0) if m.re is FOREIGN_IN_TEXT else m.group(1))
        if country and country not in countries:
            countries.append(country)
    return countries
