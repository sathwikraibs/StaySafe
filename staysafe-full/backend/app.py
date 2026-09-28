"""
StaySafe - Main Flask App
"""
from flask import Flask, jsonify
from flask_cors import CORS
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
from scanners.translator import translation_status
from scanners.ai_review import ai_status

MAX_UPLOAD_MB = 20

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
CORS(app)  # allows your Vercel frontend (different domain) to call this API

app.register_blueprint(url_scanner_bp)
app.register_blueprint(message_scanner_bp)
app.register_blueprint(risk_engine_bp)
app.register_blueprint(qr_scanner_bp)
app.register_blueprint(incident_wizard_bp)
app.register_blueprint(file_scanner_bp)
app.register_blueprint(password_checker_bp)
app.register_blueprint(network_checker_bp)
app.register_blueprint(email_analyzer_bp)
app.register_blueprint(knowledge_base_bp)

# Start downloading the free public scam-link lists in the background
from scanners.url_scanner import ensure_feeds  # noqa: E402
ensure_feeds()


@app.route("/")
def home():
    # Open this URL after deploying: "ocr" and "qr" should both be true.
    return {
        "status": "StaySafe API running",
        "ocr": ocr_status(),
        "ocr_languages": ocr_languages() if ocr_status() else "",
        "qr": qr_status(),
        "translation": translation_status(),
        "ai_review": ai_status(),
        "link_checks": link_check_status(),
        "max_upload_mb": MAX_UPLOAD_MB,
    }


@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": f"That file is too big. Please upload something under {MAX_UPLOAD_MB} MB."}), 413


@app.errorhandler(HTTPException)
def http_error(e):
    return jsonify({"error": e.description or e.name}), e.code


@app.errorhandler(Exception)
def unexpected_error(e):
    app.logger.exception("Unhandled error")
    return jsonify({"error": "Something went wrong on our side. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
