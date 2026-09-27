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

# Signals that a message is a genuine notification, not a scam
SAFE_SIGNALS = [
    r"\b(do not|don't|dont|never)\s+share\b",
    r"\bnever (ask|asks) for (your )?(otp|pin|password|cvv)\b",
    r"\bkisi (ke saath|se bhi|ko bhi)\b[^.\n]{0,30}\b(share na|mat)\b",
    r"\bif (this was )?not (done by )?you\b",
]

HIGH_RISK_LABELS = {r[0] for r in RULES if r[2] >= 30}


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "SCAM_LIKELY"
    if score >= 25:
        return "SUSPICIOUS"
    return "LIKELY_SAFE"


def _normalise(text: str) -> str:
    text = text.lower()
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

    return {
        "text_analyzed": text,
        "risk_score": score,
        "verdict": verdict_from_score(score),
        "patterns_detected": findings,
        "safe_signals": notes,
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

    result["links_checked"] = checked
    result["risk_score"] = min(100, result["risk_score"] + extra_score)
    result["verdict"] = verdict_from_score(result["risk_score"])
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


def extract_text_from_image(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    prepared = _prepare_for_ocr(img)
    text = pytesseract.image_to_string(prepared, config="--psm 6", timeout=40)
    if len(text.strip()) < 10:
        # try automatic page layout as a fallback
        text = pytesseract.image_to_string(prepared, timeout=40)
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

    result = check_links_in_result(analyze_text(text))

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

    result = check_links_in_result(analyze_text(extracted_text))

    from scanners.risk_engine import log_scan
    log_scan("screenshot", result)

    return jsonify(result)
