"""
StaySafe - Main Flask App
"""
from flask import Flask
from flask_cors import CORS
from scanners.url_scanner import url_scanner_bp
from scanners.message_scanner import message_scanner_bp
from scanners.risk_engine import risk_engine_bp
from scanners.qr_scanner import qr_scanner_bp
from scanners.incident_wizard import incident_wizard_bp
from scanners.file_scanner import file_scanner_bp
from scanners.password_checker import password_checker_bp
from scanners.network_checker import network_checker_bp
from scanners.email_analyzer import email_analyzer_bp
from scanners.knowledge_base import knowledge_base_bp

app = Flask(__name__)
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

@app.route("/")
def home():
    return {"status": "StaySafe API running"}

if __name__ == "__main__":
    app.run(debug=True, port=5000)
