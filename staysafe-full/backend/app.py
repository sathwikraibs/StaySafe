"""
StaySafe - Main Flask App
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from PIL import Image
from werkzeug.exceptions import HTTPException

from scanners.url_scanner import url_scanner_bp, link_check_status
from scanners.message_scanner import message_scanner_bp, ocr_status, ocr_languages
from scanners.risk_engine import risk_engine_bp
from scanners.qr_scanner import qr_scanner_bp, qr_status
from scanners.incident_wizard import incident_wizard_bp
from scanners.file_scanner import file_scanner_bp
from scanners.password_checker import password_checker_bp
from scanners.network_checker import network_checker_bp
from scanners.email_analyzer import email_analyzer_bp
from scanners.knowledge_base import knowledge_base_bp
from scanners.contact import contact_bp, contact_status
from scanners.number_check import number_check_bp
from scanners.reports import reports_bp
from scanners.telegram_bot import telegram_bp, telegram_status
from scanners.selftest import selftest_bp
from scanners.assistant import assistant_bp, assistant_ready
from scanners.translator import translation_status
from scanners.ai_review import ai_status
from scanners.quota import quota_status
from scanners.security import (check_rate_limit, allowed_origins, add_security_headers,
                               has_status_key)

MAX_UPLOAD_MB = 20

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
# Only StaySafe's own website may call the API from a browser
CORS(app, origins=allowed_origins())
app.before_request(check_rate_limit)
app.after_request(add_security_headers)

app.register_blueprint(url_scanner_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(message_scanner_bp)
app.register_blueprint(risk_engine_bp)
app.register_blueprint(qr_scanner_bp)
app.register_blueprint(incident_wizard_bp)
app.register_blueprint(file_scanner_bp)
app.register_blueprint(password_checker_bp)
app.register_blueprint(network_checker_bp)
app.register_blueprint(email_analyzer_bp)
app.register_blueprint(knowledge_base_bp)
app.register_blueprint(number_check_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(telegram_bp)
app.register_blueprint(selftest_bp)

# Start downloading the free public scam-link lists in the background
from scanners.url_scanner import ensure_feeds  # noqa: E402
ensure_feeds()
from scanners import store as _store  # noqa: E402
_store.start_background()   # today's used allowances survive restarts
import threading as _th  # noqa: E402
_th.Thread(target=__import__("scanners.tulu_lexicon", fromlist=["latin_available"]).latin_available, daemon=True).start()


@app.route("/")
def home():
    # Public view: just "is it running". Full details need ?key=<STATUS_KEY> (set on Render).
    if not has_status_key():
        return {"status": "StaySafe API running", "ocr": ocr_status(), "qr": qr_status()}
    return {
        "status": "StaySafe API running",
        "ocr": ocr_status(),
        "ocr_languages": ocr_languages() if ocr_status() else "",
        "qr": qr_status(),
        "translation": translation_status(),
        "ai_review": ai_status(),
        "connection": {"proxycheck_key": bool(os.environ.get("PROXYCHECK_KEY")),
                       "ipinfo": bool(os.environ.get("IPINFO_TOKEN")),
                       "abuseipdb": bool(os.environ.get("ABUSEIPDB_KEY"))},
        "link_checks": link_check_status(),
        "allowances": quota_status(),
        "contact_form": contact_status(),
        "assistant": assistant_ready(),
        "telegram_bot": telegram_status(),
        "long_memory": _store.status(),
        "tulu_lexicon": __import__("scanners.tulu_lexicon", fromlist=["status"]).status(),
        "phone_reputation": __import__("scanners.number_check", fromlist=["ipqs_status"]).ipqs_status(),
        "max_upload_mb": MAX_UPLOAD_MB,
    }


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": f"That file is too big. Please upload something under {MAX_UPLOAD_MB} MB."}), 413


@app.errorhandler(Image.DecompressionBombError)
def image_bomb(_e):
    return jsonify({"error": "That picture is too large to read. Please send a normal screenshot or photo."}), 400


@app.errorhandler(HTTPException)
def http_error(e):
    return jsonify({"error": e.description or e.name}), e.code


@app.errorhandler(Exception)
def unexpected_error(e):
    app.logger.exception("Unhandled error")
    return jsonify({"error": "Something went wrong on our side. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
