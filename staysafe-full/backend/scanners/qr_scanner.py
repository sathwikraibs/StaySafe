"""
StaySafe - QR Code Safety Scanner
------------------------------------
User uploads a QR code image. We decode it, and if it contains a URL,
run it through the SAME risk engine as the URL scanner (no duplicate logic).
If it's not a URL (e.g. plain UPI string), we do basic UPI-specific checks.

Requires:
    pip install opencv-python pyzbar
    (pyzbar also needs the system lib zbar0 -- see note below)

Register with:
    from qr_scanner import qr_scanner_bp
    app.register_blueprint(qr_scanner_bp)
"""

import re
import io
import numpy as np
from flask import Blueprint, request, jsonify

from scanners.url_scanner import scan_url
from scanners.risk_engine import log_scan

qr_scanner_bp = Blueprint("qr_scanner", __name__)

try:
    import cv2
    from pyzbar.pyzbar import decode as decode_qr
    QR_LIB_AVAILABLE = True
except ImportError:
    QR_LIB_AVAILABLE = False


def analyze_upi_string(upi_data: str) -> dict:
    """
    Basic checks for UPI payment QR strings, e.g.:
    upi://pay?pa=merchant@upi&pn=MerchantName&am=100
    """
    findings = []
    score = 0

    pa_match = re.search(r"pa=([^&]+)", upi_data)
    am_match = re.search(r"am=([^&]+)", upi_data)
    pn_match = re.search(r"pn=([^&]+)", upi_data)

    payee = pa_match.group(1) if pa_match else None
    amount = am_match.group(1) if am_match else None
    payee_name = pn_match.group(1) if pn_match else None

    if not payee:
        findings.append("QR does not contain a valid UPI payee ID")
        score += 20

    if amount:
        findings.append(f"QR requests a pre-filled amount of ₹{amount} — verify this matches what you expect to pay")
        score += 10

    findings.append("Reminder: you never need to enter your UPI PIN to RECEIVE money — only to send it")

    verdict = "CAUTION" if score >= 20 else "SAFE"
    return {
        "qr_type": "upi_payment",
        "payee": payee,
        "payee_name": payee_name,
        "amount": amount,
        "risk_score": score,
        "verdict": verdict,
        "findings": findings,
    }


@qr_scanner_bp.route("/api/scan-qr", methods=["POST"])
def scan_qr_route():
    if not QR_LIB_AVAILABLE:
        return jsonify({
            "error": "QR libraries not installed. Run: pip install opencv-python pyzbar "
                     "(Linux also needs: sudo apt install libzbar0)"
        }), 500

    if "image" not in request.files:
        return jsonify({"error": "Missing 'image' file in form-data"}), 400

    file = request.files["image"]
    try:
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        decoded = decode_qr(img)
    except Exception as e:
        return jsonify({"error": f"Could not process image: {str(e)}"}), 400

    if not decoded:
        return jsonify({"error": "No QR code found in this image"}), 400

    qr_data = decoded[0].data.decode("utf-8")

    if qr_data.startswith("upi://"):
        result = analyze_upi_string(qr_data)
        result["raw_data"] = qr_data
        log_scan("qr_upi", result)
        return jsonify(result)

    if qr_data.startswith(("http://", "https://")):
        result = scan_url(qr_data)
        result["qr_type"] = "url"
        log_scan("qr_url", result)
        return jsonify(result)

    # Neither a URL nor a UPI string — just return the raw decoded content
    return jsonify({
        "qr_type": "unknown",
        "raw_data": qr_data,
        "risk_score": 5,
        "verdict": "SAFE",
        "findings": ["QR contains plain text/data, not a link or payment request"],
    })
