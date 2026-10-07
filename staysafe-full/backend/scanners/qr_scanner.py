"""
StaySafe - QR Code Safety Scanner
------------------------------------
User uploads a photo/screenshot of a QR code. We decode it and:
  - URL      -> run it through the SAME checks as the link scanner
  - UPI      -> payment-specific checks (a QR can only SEND your money, never receive)
  - anything else -> show the raw content

Decoding uses pyzbar (needs the system library libzbar0, installed by the
Dockerfile) and falls back to OpenCV's built-in QR detector, so QR scanning
still works even if zbar is missing.
"""

import re
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
from flask import Blueprint, request, jsonify

from scanners.url_scanner import scan_url
from scanners.risk_engine import log_scan

qr_scanner_bp = Blueprint("qr_scanner", __name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:  # pragma: no cover
    CV2_AVAILABLE = False

try:
    from pyzbar.pyzbar import decode as zbar_decode
    ZBAR_AVAILABLE = True
except Exception:  # ImportError, or OSError when libzbar is missing
    ZBAR_AVAILABLE = False


def qr_status() -> bool:
    return CV2_AVAILABLE


# ---------------------------------------------------------------------------
# DECODING
# ---------------------------------------------------------------------------
def _variants(img):
    """Yield progressively 'cleaned up' versions of the image to improve decode rates."""
    yield img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    yield gray
    h, w = gray.shape[:2]
    if max(h, w) < 800:
        yield cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    elif max(h, w) > 2000:
        scale = 1600 / max(h, w)
        yield cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    yield cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
    yield cv2.bitwise_not(gray)  # dark-mode / inverted codes


def decode_qr_image(image_bytes: bytes):
    """Returns the decoded text of the first QR code found, or None."""
    file_bytes = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("not an image")

    detector = cv2.QRCodeDetector()
    for variant in _variants(img):
        if ZBAR_AVAILABLE:
            try:
                results = zbar_decode(variant)
                if results:
                    return results[0].data.decode("utf-8", errors="replace")
            except Exception:
                pass
        try:
            data, _points, _ = detector.detectAndDecode(variant)
            if data:
                return data
        except cv2.error:
            pass
    return None


# ---------------------------------------------------------------------------
# UPI CHECKS
# ---------------------------------------------------------------------------
SCAM_NOTE_WORDS = re.compile(
    r"(refund|cashback|prize|reward|lottery|won|winner|kyc|verify|verification|receive|gift|bonus|claim|customer ?care|support)",
    re.IGNORECASE,
)


def analyze_upi_string(upi_data: str) -> dict:
    """
    Checks a UPI payment QR string, e.g.
    upi://pay?pa=merchant@okaxis&pn=Merchant%20Name&am=100&tn=note
    """
    findings = []
    score = 0
    from scanners.ledger import Ledger
    led = Ledger()

    parsed = urlparse(upi_data)
    params = {k.lower(): unquote(v[0]) for k, v in parse_qs(parsed.query).items()}

    payee = params.get("pa")
    payee_name = params.get("pn")
    amount = params.get("am")
    note = params.get("tn", "")

    if not payee or not re.fullmatch(r"[\w.\-]{2,256}@[A-Za-z][\w]{1,64}", payee):
        findings.append("This QR does not contain a valid UPI payee ID")
        score += led.note(findings, 30)
    elif re.match(r"^\d{10}@", payee):
        findings.append(f"Payment goes to a personal phone-number UPI ID ({payee}), not a registered business")
        score += led.note(findings, 10)

    if not payee_name:
        findings.append("The QR doesn't show who you are paying (no payee name)")
        score += led.note(findings, 10)

    if amount:
        try:
            value = float(amount)
            findings.append(f"This QR will pre-fill an amount of ₹{value:,.2f}. Check it matches what you expect to pay")
            score += led.note(findings, 10)
            if value >= 10000:
                findings.append("That is a large amount for a QR payment. Double-check before paying")
                score += led.note(findings, 10)
        except ValueError:
            findings.append("The amount in this QR is not a valid number")
            score += led.note(findings, 15)

    if note and SCAM_NOTE_WORDS.search(note):
        findings.append(f"The payment note says “{note}”. Scammers use notes like this to make you think you'll RECEIVE money")
        score += led.note(findings, 40)

    if payee:
        try:
            from scanners.reports import community_signal
            sig = community_signal("upi", payee)
        except Exception:
            sig = None
        if sig:
            findings.insert(0, sig[0])
            score += led.note(findings, sig[1])

    findings.append("Remember: scanning a QR and entering your UPI PIN always SENDS money. You never scan a QR or enter a PIN to receive money.")

    score = min(100, score)
    verdict = "DANGEROUS" if score >= 50 else ("CAUTION" if score >= 20 else "SAFE")
    valid_id = bool(payee and re.fullmatch(r"[\w.\-]{2,256}@[A-Za-z][\w]{1,64}", payee))
    try:
        amount_value = float(amount) if amount else None
    except ValueError:
        amount_value = -1
    checks = [
        {"id": "upi_note", "status": "fail" if (note and SCAM_NOTE_WORDS.search(note)) else "pass", "value": note or None},
        {"id": "upi_id", "status": ("warn" if re.match(r"^\d{10}@", payee or "") else "pass") if valid_id else "fail",
         "value": payee or None},
        {"id": "upi_name", "status": "pass" if payee_name else "warn", "value": payee_name or None},
        {"id": "upi_amount", "status": "info" if amount_value is None else
            ("fail" if amount_value < 0 else ("warn" if amount_value >= 10000 else "info")),
         "value": f"{amount_value:,.2f}" if amount_value and amount_value > 0 else None},
    ]
    return {
        "checks": checks,
        "qr_type": "upi_payment",
        "payee": payee,
        "payee_name": payee_name,
        "amount": amount,
        "risk_score": score,
        "verdict": verdict,
        "findings": findings,
        "score_parts": led.result(score),
    }


# ---------------------------------------------------------------------------
# ROUTE
# ---------------------------------------------------------------------------
@qr_scanner_bp.route("/api/scan-qr", methods=["POST"])
def scan_qr_route():
    if not CV2_AVAILABLE:
        return jsonify({"error": "QR reading from a picture isn't available right now. Try the camera button instead."}), 503

    if "image" not in request.files:
        return jsonify({"error": "Please choose a photo of the QR code to upload."}), 400

    image_bytes = request.files["image"].read()
    if not image_bytes:
        return jsonify({"error": "The uploaded image was empty."}), 400

    try:
        qr_data = decode_qr_image(image_bytes)
    except Exception:
        return jsonify({"error": "We couldn't open this image. Please upload a PNG or JPG photo."}), 400

    if not qr_data:
        return jsonify({
            "error": "We couldn't find a QR code in this image. Try a clearer photo with the whole QR code visible."
        }), 400

    return jsonify(analyze_qr_data(qr_data))


def analyze_qr_data(qr_data: str) -> dict:
    """Check what a QR code contains (a link, a UPI payment or plain text)."""
    qr_data = qr_data.strip()
    lowered = qr_data.lower()

    if lowered.startswith("upi://"):
        result = analyze_upi_string(qr_data)
        result["raw_data"] = qr_data
        log_scan("qr_upi", result)
        return result

    if lowered.startswith(("http://", "https://", "www.")):
        url = qr_data if lowered.startswith("http") else "https://" + qr_data
        result = scan_url(url)
        result["qr_type"] = "url"
        result["raw_data"] = qr_data
        log_scan("qr_url", result)
        return result

    # Plain text (or Wi-Fi details, a contact card...). It can still hide a link or a scam
    # message, so it gets the message checks, including the full check of any link inside.
    from scanners.url_scanner import extract_url
    inner = extract_url(qr_data)
    if inner and not lowered.startswith(("wifi:", "begin:vcard", "mecard:")):
        url = inner if inner.lower().startswith("http") else "https://" + inner
        result = scan_url(url)
        result["qr_type"] = "url"
        result["raw_data"] = qr_data
        log_scan("qr_url", result)
        return result
    from scanners.message_scanner import analyze_text, finalize_parts, verdict_from_score as msg_verdict
    msg = analyze_text(qr_data)
    from scanners.message_scanner import add_entity_checks
    msg = add_entity_checks(msg, qr_data)
    if msg["patterns_detected"]:
        verdict = "DANGEROUS" if msg["risk_score"] >= 50 else ("CAUTION" if msg["risk_score"] >= 20 else "SAFE")
        result = {
            "qr_type": "text", "raw_data": qr_data, "risk_score": msg["risk_score"], "verdict": verdict,
            "findings": msg["patterns_detected"],
            "checks": [{"id": "qr_text", "status": "fail" if verdict == "DANGEROUS" else "warn", "value": None}],
            "score_parts": finalize_parts(msg)["score_parts"],
        }
        log_scan("qr_text", result)
        return result
    result = {
        "qr_type": "text",
        "raw_data": qr_data,
        "risk_score": 0,
        "verdict": "SAFE",
        "findings": ["This QR contains plain text, not a link or payment request"],
        "checks": [{"id": "qr_text", "status": "pass", "value": None}],
        "score_parts": [],
    }
    log_scan("qr_text", result)
    return result


@qr_scanner_bp.route("/api/scan-qr-text", methods=["POST"])
def scan_qr_text_route():
    """The phone's camera already read the QR code; we only check what's inside."""
    data = request.get_json(silent=True) or {}
    qr_data = str(data.get("data") or "").strip()[:4000]
    if not qr_data:
        return jsonify({"error": "We couldn't find a QR code in this image. Try a clearer photo with the whole QR code visible."}), 400
    return jsonify(analyze_qr_data(qr_data))
