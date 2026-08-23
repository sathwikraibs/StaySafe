"""
StaySafe - Message / Screenshot Scam Detector
-----------------------------------------------
Analyzes pasted text OR an uploaded screenshot for common scam patterns:
  - Bank/KYC impersonation
  - OTP/PIN theft attempts
  - Prize/lottery/advance-fee scams
  - Job scams
  - Investment/crypto scams
  - Urgency + credential-harvesting language

Screenshot support uses OCR (pytesseract) to extract text first,
then runs it through the same rule engine as pasted text.

Register with:
    from message_scanner import message_scanner_bp
    app.register_blueprint(message_scanner_bp)
"""

import re
import io
from flask import Blueprint, request, jsonify

message_scanner_bp = Blueprint("message_scanner", __name__)

# Optional OCR — only needed for screenshot uploads
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# ---------------------------------------------------------------------------
# SCAM PATTERN RULES
# Each rule: (label, regex list, weight)
# ---------------------------------------------------------------------------
RULES = [
    (
        "Urgency language",
        [r"\bimmediately\b", r"\burgent\b", r"\bwithin \d+ hours?\b",
         r"\bact now\b", r"\bexpire[sd]? today\b", r"\bsuspend(ed)?\b"],
        15,
    ),
    (
        "Requests OTP/PIN",
        [r"\botp\b", r"\bone[- ]time password\b", r"\bpin\b(?!\w)", r"\bcvv\b"],
        30,
    ),
    (
        "Bank/KYC impersonation",
        [r"\bkyc\b", r"\baccount (will be |is )?(blocked|suspended|frozen)\b",
         r"\bverify your (account|bank|kyc)\b", r"\bre-?kyc\b"],
        25,
    ),
    (
        "Prize / lottery / advance-fee scam",
        [r"\byou (have )?won\b", r"\blottery\b", r"\bclaim your (prize|reward)\b",
         r"\bprocessing fee\b", r"\bpay .* to (receive|claim)\b"],
        30,
    ),
    (
        "Suspicious link present",
        [r"https?://\S+", r"\bbit\.ly/\S+", r"\btinyurl\.com/\S+"],
        10,
    ),
    (
        "Job scam",
        [r"\bwork from home\b.*\b(earn|salary)\b", r"\bregistration fee\b",
         r"\btraining fee\b", r"\bpart[- ]time job\b.*\bdaily payment\b"],
        20,
    ),
    (
        "Investment/crypto scam",
        [r"\bguaranteed returns?\b", r"\bdouble your money\b",
         r"\bcrypto(currency)? investment\b", r"\btrading (platform|signal)\b"],
        25,
    ),
    (
        "Remote access / screen sharing request",
        [r"\banydesk\b", r"\bteamviewer\b", r"\bscreen ?share\b", r"\bremote access\b"],
        30,
    ),
    (
        "Impersonating government/police",
        [r"\bdigital arrest\b", r"\bcyber ?crime (branch|cell)\b",
         r"\bincome tax (notice|department)\b", r"\bpolice (verification|notice)\b"],
        30,
    ),
    (
        "Payment request framed as refund",
        [r"\brefund\b.*\b(claim|process)\b", r"\benter (your )?upi pin\b.*\breceive\b"],
        25,
    ),
]


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "SCAM_LIKELY"
    if score >= 20:
        return "SUSPICIOUS"
    return "LIKELY_SAFE"


def analyze_text(text: str) -> dict:
    text_lower = text.lower()
    findings = []
    score = 0

    for label, patterns, weight in RULES:
        for pattern in patterns:
            if re.search(pattern, text_lower):
                findings.append(label)
                score += weight
                break  # only count each rule once

    score = min(100, score)

    return {
        "text_analyzed": text,
        "risk_score": score,
        "verdict": verdict_from_score(score),
        "patterns_detected": findings,
    }


# ---------------------------------------------------------------------------
# ROUTE 1 — paste text directly (SMS / WhatsApp / email body)
# ---------------------------------------------------------------------------
@message_scanner_bp.route("/api/scan-message", methods=["POST"])
def scan_message_route():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    result = analyze_text(text)

    from scanners.risk_engine import log_scan
    log_scan("message", result)

    return jsonify(result)


# ---------------------------------------------------------------------------
# ROUTE 2 — upload a screenshot (OCR extracts text, then same analysis)
# ---------------------------------------------------------------------------
@message_scanner_bp.route("/api/scan-screenshot", methods=["POST"])
def scan_screenshot_route():
    if not OCR_AVAILABLE:
        return jsonify({
            "error": "OCR not installed on server. Run: pip install pytesseract pillow, "
                     "and install the tesseract-ocr system package."
        }), 500

    if "image" not in request.files:
        return jsonify({"error": "Missing 'image' file in form-data"}), 400

    file = request.files["image"]
    try:
        img = Image.open(io.BytesIO(file.read()))
        extracted_text = pytesseract.image_to_string(img).strip()
    except Exception as e:
        return jsonify({"error": f"Could not process image: {str(e)}"}), 400

    if not extracted_text:
        return jsonify({"error": "No readable text found in the image"}), 400

    result = analyze_text(extracted_text)

    from scanners.risk_engine import log_scan
    log_scan("screenshot", result)

    return jsonify(result)
