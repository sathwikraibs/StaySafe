"""
StaySafe - "Who is this?" check for a phone number or a UPI ID
------------------------------------------------------------------
Works offline, no API. Nobody can tell who owns a number from the number alone, so the
check combines three things:

1. What the number or ID itself shows: a foreign country often used for scam calls, a number
   that cannot exist, a personal mobile number pretending to be a bank, a UPI ID with words
   like "refund" or "customercare" in it, a UPI handle that no common app uses.
2. What the person tells us happened (optional): who the caller said they were and what they
   asked for. "Pay a fee to receive money", "share your OTP" and "stay on a video call with
   the police" are scams whoever is calling.
3. Facts that hold for everyone: since 1 January 2026 banks must make service and
   transaction calls from numbers starting with 1600 (TRAI); 140 numbers are adverts;
   1930 is the national cyber-crime helpline.

The result always points to the government's own lookup (cybercrime.gov.in, "Report and
Check Suspect"), which searches numbers and UPI IDs reported by victims.
"""

import os
import re

import requests
from flask import Blueprint, jsonify, request

from scanners.ledger import Ledger
from scanners.sender_check import _country_of

number_check_bp = Blueprint("number_check", __name__)

# --- Official numbers people often ask about -----------------------------------------------
HELPLINES = {
    "1930": "the national cyber-crime helpline",
    "112": "the national emergency number",
    "100": "the police emergency number",
    "101": "the fire service emergency number",
    "102": "the ambulance number",
    "108": "the emergency ambulance number",
    "1098": "the child helpline",
    "181": "the women's helpline",
    "1091": "the women's helpline",
    "14567": "Elder Line, the helpline for senior citizens",
    "1915": "the National Consumer Helpline",
    "139": "the railway enquiry and help number",
    "1947": "the Aadhaar (UIDAI) helpline",
}

# Country codes often seen in scam calls and WhatsApp messages to India (job, investment,
# "customer care" scams) and in one-ring "call me back" scams that charge you per minute
SCAM_CALL_COUNTRIES = {"92", "84", "62", "254", "855", "60", "63", "856", "95", "880", "234", "233", "977", "94"}
CALLBACK_SCAM_COUNTRIES = {"225", "232", "373", "381", "216", "222", "243", "882", "883", "870", "881"}

# --- UPI ------------------------------------------------------------------------------------
UPI_ID = re.compile(r"^[A-Za-z0-9.\-_]{2,256}@[A-Za-z][A-Za-z0-9]{1,64}$")
UPI_HANDLES = {
    # apps
    "okaxis": "Google Pay", "oksbi": "Google Pay", "okhdfcbank": "Google Pay", "okicici": "Google Pay",
    "ybl": "PhonePe", "ibl": "PhonePe", "axl": "PhonePe",
    "paytm": "Paytm", "ptyes": "Paytm", "ptaxis": "Paytm", "pthdfc": "Paytm", "ptsbi": "Paytm",
    "apl": "Amazon Pay", "yapl": "Amazon Pay", "rapl": "Amazon Pay",
    "upi": "BHIM", "waaxis": "WhatsApp", "wahdfcbank": "WhatsApp", "wasbi": "WhatsApp", "waicici": "WhatsApp",
    "jupiteraxis": "Jupiter", "freecharge": "Freecharge", "ikwik": "MobiKwik", "fam": "FamPay",
    "slc": "slice", "sliceaxis": "slice", "superyes": "super.money", "naviaxis": "Navi", "yesg": "Groww",
    "axisb": "CRED", "timecosmos": "Times Pay", "abfspay": "Aditya Birla", "kbaxis": "Kiwi", "tapicici": "Tata Neu",
    "pingpay": "Ping Pay", "airtel": "Airtel Payments Bank", "jio": "Jio Payments Bank", "postbank": "India Post Payments Bank",
    # banks
    "sbi": "State Bank of India", "hdfcbank": "HDFC Bank", "icici": "ICICI Bank", "axisbank": "Axis Bank",
    "kotak": "Kotak Mahindra Bank", "kmbl": "Kotak Mahindra Bank", "pnb": "Punjab National Bank",
    "boi": "Bank of India", "barodampay": "Bank of Baroda", "cnrb": "Canara Bank", "unionbank": "Union Bank of India",
    "unionbankofindia": "Union Bank of India", "idfcbank": "IDFC FIRST Bank", "idfcfirst": "IDFC FIRST Bank",
    "indus": "IndusInd Bank", "rbl": "RBL Bank", "yesbank": "Yes Bank", "fbl": "Federal Bank", "federal": "Federal Bank",
    "aubank": "AU Small Finance Bank", "idbi": "IDBI Bank", "mahb": "Bank of Maharashtra", "indianbank": "Indian Bank",
    "iob": "Indian Overseas Bank", "uco": "UCO Bank", "cbin": "Central Bank of India", "dbs": "DBS Bank",
    "hsbc": "HSBC", "sc": "Standard Chartered", "citi": "Citibank", "kvb": "Karur Vysya Bank", "kbl": "Karnataka Bank",
    "equitas": "Equitas Small Finance Bank", "ujjivan": "Ujjivan Small Finance Bank", "jkb": "J&K Bank",
    "dlb": "Dhanlaxmi Bank", "tjsb": "TJSB Bank", "psb": "Punjab & Sind Bank", "csbpay": "CSB Bank",
    "esaf": "ESAF Small Finance Bank", "suryoday": "Suryoday Small Finance Bank",
}
# Words a real person's or shop's UPI ID has no reason to contain, but fake "official" ones do
UPI_ROLE_WORDS = re.compile(
    r"(refund|cashback|cash\.?back|reward|prize|lottery|lucky|winner|kyc|helpdesk|help\.?desk|customer\.?care|"
    r"cust\.?care|care\.?desk|support|helpline|service\.?cent|unblock|reactivat|verif|govt|gov\b|rbi|npci|"
    r"police|cbi|customs|court|penalty|challan|income\.?tax|incometax|electricity|bescom|"
    r"subsidy|pmkisan|grant)", re.IGNORECASE)

# --- What the person tells us -------------------------------------------------------------
CLAIMS = {"bank", "official", "delivery", "company", "family", "unknown"}
ASKS = {"pay_to_get", "otp", "app", "video", "nothing"}


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def classify_input(value: str) -> str:
    v = (value or "").strip()
    if "@" in v and UPI_ID.match(v.replace(" ", "")):
        return "upi"
    d = _digits(v)
    if d and len(d) >= 3 and re.fullmatch(r"[\d\s+\-().]{3,25}", v):
        return "phone"
    return "unknown"


def _indian_type(local: str) -> str:
    """'mobile', 'landline' or '' (unknown), from Google's numbering data when available."""
    try:
        import phonenumbers
        n = phonenumbers.parse("+91" + local, None)
        t = phonenumbers.number_type(n)
        if t == phonenumbers.PhoneNumberType.FIXED_LINE:
            return "landline"
        if t in (phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE):
            return "mobile"
    except Exception:
        pass
    return ""


def check_phone(value: str, claim: str, findings: list, led: Ledger, checks: list) -> dict:
    raw = re.sub(r"[^\d+]", "", value.strip())
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    d = _digits(raw)
    info = {"kind": "phone", "number": value.strip(), "number_type": "unknown", "country": None}
    score = 0

    local = d[2:] if raw.startswith("+91") or (len(d) == 12 and d.startswith("91")) else d
    if local.startswith("0") and len(local) in (11, 12):
        local = local[1:]

    if not raw.startswith("+") or raw.startswith("+91") or (len(d) == 12 and d.startswith("91")):
        if local in HELPLINES:
            info["number_type"] = "helpline"
            findings.append(f"This is {HELPLINES[local]}. It is a real government number")
            checks.append({"id": "num_type", "status": "pass", "value": local})
            return {"score": 0, "info": info}
        if re.fullmatch(r"1600\d{6}", local):
            info["number_type"] = "bank_1600"
            findings.append("Numbers starting with 1600 are given only to banks, insurance and other money "
                            "companies for service calls. Still, never share an OTP or PIN on a call")
            checks.append({"id": "num_type", "status": "pass", "value": "1600"})
        elif re.fullmatch(r"140\d{7}", local):
            info["number_type"] = "promo_140"
            findings.append("Numbers starting with 140 are used only for adverts and sales calls. A bank "
                            "or office will not call you about your account from a 140 number")
            checks.append({"id": "num_type", "status": "info", "value": "140"})
            if claim in ("bank", "official"):
                score += led.note(findings, 25)
        elif re.fullmatch(r"18[06]0\d{4,7}", local):
            info["number_type"] = "toll_free"
            findings.append("Toll-free number (1800 or 1860). Real companies use these, but scammers also put "
                            "fake 'customer care' numbers online. Take the number from the official app, "
                            "website or the back of your card")
            checks.append({"id": "num_type", "status": "info", "value": local[:4]})
        elif re.fullmatch(r"[6-9]\d{9}", local) and _indian_type(local) != "landline":
            info["number_type"] = "mobile"
            checks.append({"id": "num_type", "status": "info", "value": "mobile"})
            if claim == "bank":
                findings.append("Says they are from a bank but called from a personal mobile number. Since "
                                "January 2026 banks must make service calls from numbers starting with 1600")
                score += led.note(findings, 35)
            elif claim == "official":
                findings.append("Says they are from the police, a court or a government office but used a "
                                "personal mobile number. Officials never ask for money or details on such calls")
                score += led.note(findings, 30)
            else:
                findings.append("This is an ordinary Indian mobile number. Anyone can get one, so the number "
                                "alone can't tell you who is calling")
        elif re.fullmatch(r"[2-8]\d{9}", local):
            info["number_type"] = "landline"
            checks.append({"id": "num_type", "status": "info", "value": "landline"})
            findings.append("This looks like an Indian landline number. Scammers can also fake the number "
                            "shown on your phone, so check it on the official website")
        else:
            info["number_type"] = "invalid"
            findings.append("This is not a real Indian phone number (wrong number of digits). Calls and "
                            "messages showing numbers like this are often faked")
            score += led.note(findings, 20)
            checks.append({"id": "num_type", "status": "warn", "value": None})
        return {"score": score, "info": info}

    # Foreign number
    country = _country_of(raw)
    code = next((c for c in (raw[1:4], raw[1:3], raw[1:2]) if c in SCAM_CALL_COUNTRIES | CALLBACK_SCAM_COUNTRIES), None)
    info["number_type"] = "foreign"
    info["country"] = country
    if not country and not code:
        findings.append("This is not a real phone number (the country code or length is wrong). Numbers "
                        "like this are often faked")
        score += led.note(findings, 20)
        checks.append({"id": "num_type", "status": "warn", "value": None})
        return {"score": score, "info": info}
    shown = country or f"+{code}"
    if code in CALLBACK_SCAM_COUNTRIES:
        findings.append(f"Foreign number ({shown}) of a kind used in 'missed call' scams: calling back can "
                        "cost a lot per minute. Don't call back")
        score += led.note(findings, 30)
    elif code in SCAM_CALL_COUNTRIES:
        findings.append(f"Foreign number ({shown}). Numbers from this country are very often used for job, "
                        "investment and 'customer care' scams in India")
        score += led.note(findings, 30)
    else:
        findings.append(f"Foreign number ({shown}). Be careful if you don't know anyone there")
        score += led.note(findings, 15)
    if claim in ("bank", "official", "delivery"):
        findings.append("Says they are from an Indian bank, office or courier but uses a foreign number. Real ones don't")
        score += led.note(findings, 30)
    checks.append({"id": "num_type", "status": "warn", "value": shown})
    return {"score": score, "info": info}


def check_upi(value: str, findings: list, led: Ledger, checks: list) -> dict:
    upi = value.strip().replace(" ", "")
    name, _, handle = upi.rpartition("@")
    handle_l = handle.lower()
    info = {"kind": "upi", "upi": upi, "app": UPI_HANDLES.get(handle_l)}
    score = 0
    if info["app"]:
        checks.append({"id": "upi_handle", "status": "pass", "value": info["app"]})
        findings.append(f"This UPI ID is on {info['app']}. Before you pay, check that the name your UPI app shows "
                        "is the person or shop you expect")
    else:
        findings.append(f"The part after @ ({handle}) is not one we know from common UPI apps or banks. "
                        "Check the spelling, or ask the person to share a QR from their app")
        score += led.note(findings, 15)
        checks.append({"id": "upi_handle", "status": "warn", "value": handle})

    role = UPI_ROLE_WORDS.search(name)
    if role:
        findings.append(f"The UPI ID contains '{role.group(0)}'. Real refunds, rewards and offices never ask you "
                        "to pay a UPI ID like this")
        score += led.note(findings, 40)
        checks.append({"id": "upi_words", "status": "fail", "value": role.group(0)})
    else:
        checks.append({"id": "upi_words", "status": "pass", "value": None})

    if re.fullmatch(r"(\+?91)?[6-9]\d{9}", name):
        findings.append("This UPI ID is made from a mobile number, so it belongs to a person, not a company or office")
        checks.append({"id": "upi_person", "status": "info", "value": None})
    return {"score": score, "info": info}


_IPQS_PROBLEM = {"last": None}


def phone_reputation(e164: str) -> dict:
    """
    IPQualityScore phone check (optional IPQS_API_KEY): has this number recently been used for
    fraud or spam, and is it an internet (VOIP) number? Answers are kept 7 days.
    {'status': 'ok'|'skip', 'abuse': bool, 'voip': bool, 'fraud_score': int}
    """
    key = os.environ.get("IPQS_API_KEY", "").strip()
    if not key or not e164:
        return {"status": "skip"}
    from scanners import store
    kept = store.get("ipqs", e164)
    if isinstance(kept, dict) and kept.get("status") == "ok":
        return kept
    from scanners.quota import quota
    if not quota("ipqs").take(wait=3):
        return {"status": "skip"}
    try:
        r = requests.get(f"https://www.ipqualityscore.com/api/json/phone/{key}/{e164.lstrip('+')}",
                         params={"strictness": 1}, timeout=8)
        data = r.json()
    except Exception as e:  # noqa: BLE001
        _IPQS_PROBLEM["last"] = type(e).__name__
        return {"status": "skip"}
    if not data.get("success"):
        _IPQS_PROBLEM["last"] = str(data.get("message") or "error")[:80]
        if "quota" in str(data.get("message", "")).lower() or "credits" in str(data.get("message", "")).lower():
            quota("ipqs").close_day()
        return {"status": "skip"}
    _IPQS_PROBLEM["last"] = None
    out = {"status": "ok", "abuse": bool(data.get("recent_abuse") or data.get("spammer")),
           "voip": bool(data.get("VOIP")), "fraud_score": int(data.get("fraud_score") or 0)}
    store.put("ipqs", e164, out, 7 * 86400)
    return out


def ipqs_status() -> dict:
    return {"configured": bool(os.environ.get("IPQS_API_KEY")), "problem": _IPQS_PROBLEM["last"]}


def context_signals(claim: str, ask: str, kind: str, findings: list, led: Ledger, checks: list) -> int:
    score = 0
    if ask == "pay_to_get":
        findings.append("They asked you to pay first to get money, a job, a prize, a loan or a refund. "
                        "That is always a scam: you never pay to receive money")
        score += led.note(findings, 60)
    elif ask == "otp":
        findings.append("They asked for an OTP, PIN, CVV or password. No real bank, company or office ever "
                        "asks for these")
        score += led.note(findings, 60)
    elif ask == "app":
        findings.append("They asked you to install an app or share your screen. That lets them see your OTPs "
                        "and control your phone")
        score += led.note(findings, 55)
    elif ask == "video":
        findings.append("They want you to stay on a video call or move money to a 'safe account' to avoid "
                        "arrest. This is the 'digital arrest' scam: police never do this")
        score += led.note(findings, 70)
    if claim == "family" and ask in ("pay_to_get", "nothing", ""):
        findings.append("A relative or friend writing from a new number and asking for money is a common "
                        "trick. Call them on their old number before you pay")
        score += led.note(findings, 25 if ask == "pay_to_get" else 15)
    if ask in ASKS and ask != "nothing":
        checks.append({"id": "num_ask", "status": "fail", "value": ask})
    return score


def _to_e164(value: str):
    raw = re.sub(r"[^\d+]", "", value or "")
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    d = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        return "+" + d if 8 <= len(d) <= 15 else None
    if len(d) == 11 and d.startswith("0"):
        d = d[1:]
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    return "+91" + d if len(d) == 10 else None


def check_number(value: str, claim: str = "", ask: str = "") -> dict:
    value = (value or "").strip()[:120]
    claim = claim if claim in CLAIMS else ""
    ask = ask if ask in ASKS else ""
    kind = classify_input(value)
    findings, checks = [], []
    led = Ledger()
    if kind == "upi":
        part = check_upi(value, findings, led, checks)
    elif kind == "phone":
        part = check_phone(value, claim, findings, led, checks)
    else:
        return {"error": "Please enter a phone number (like 98765 43210 or +91 98765 43210) or a UPI ID (like name@okaxis)."}
    score = part["score"] + context_signals(claim, ask, kind, findings, led, checks)
    # Phone reputation (recent fraud or spam, internet numbers)
    ntype = part["info"].get("number_type")
    if kind == "phone" and ntype in ("mobile", "landline", "foreign", "unknown"):
        e164 = _to_e164(value)
        rep = phone_reputation(e164) if e164 else {"status": "skip"}
        if rep.get("status") == "ok":
            if rep.get("abuse") or rep.get("fraud_score", 0) >= 85:
                findings.insert(0, "This number has recently been linked to fraud or spam calls")
                score += led.note(findings, 35)
                checks.append({"id": "num_reputation", "status": "fail", "value": None})
            else:
                checks.append({"id": "num_reputation", "status": "pass", "value": None})
            if rep.get("voip"):
                findings.append("This is an internet (VOIP) number. Scammers use these to hide who they are")
                score += led.note(findings, 20 if claim in ("bank", "official", "delivery") else 10)

    # StaySafe's own list: reported as a scam by its users (official numbers can't be reported)
    if part["info"].get("number_type") not in ("helpline", "bank_1600"):
        try:
            from scanners.reports import community_signal
            sig = community_signal("upi" if kind == "upi" else "number", value)
        except Exception:
            sig = None
        if sig:
            findings.insert(0, sig[0])
            score += led.note(findings, sig[1])
            checks.insert(0, {"id": "community", "status": "fail" if sig[1] >= 35 else "warn",
                              "value": int(re.search(r"\d+", sig[0]).group())})
    score = min(100, score)
    helpline = part["info"].get("number_type") == "helpline"
    verdict = "DANGEROUS" if score >= 50 else ("CAUTION" if score >= 20 else "SAFE")
    if not helpline:
        # The number alone never proves someone is genuine
        checks.append({"id": "num_registry", "status": "info", "value": None})
    return {
        "kind": kind,
        "value": value,
        "details": part["info"],
        "risk_score": score,
        "verdict": verdict,
        "findings": findings,
        "checks": checks,
        "score_parts": led.result(score),
    }


@number_check_bp.route("/api/check-number", methods=["POST"])
def check_number_route():
    data = request.get_json(silent=True) or {}
    value = str(data.get("value", ""))
    if not value.strip():
        return jsonify({"error": "Please enter a phone number or a UPI ID."}), 400
    result = check_number(value, str(data.get("claim", "")), str(data.get("ask", "")))
    if "error" in result:
        return jsonify(result), 400
    from scanners.risk_engine import log_scan
    log_scan("number", result)
    return jsonify(result)
