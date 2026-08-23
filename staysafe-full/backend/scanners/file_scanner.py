"""
StaySafe - File / Download Scanner
--------------------------------------
User uploads a file before opening it. We:
  1. Compute its SHA-256 hash
  2. Check that hash against VirusTotal's database
  3. Run local heuristics: double extensions, risky extensions, macro-enabled docs

We do NOT execute or sandbox the file — that's out of scope for a
student project and genuinely risky to run server-side. Hash lookup +
heuristics is the safe, defensible approach.

Register with:
    from file_scanner import file_scanner_bp
    app.register_blueprint(file_scanner_bp)
"""

import os
import re
import hashlib
import requests
from flask import Blueprint, request, jsonify

from scanners.risk_engine import log_scan

file_scanner_bp = Blueprint("file_scanner", __name__)

VIRUSTOTAL_API_KEY = os.environ.get("VT_API_KEY", "")

# Extensions that can execute code / run scripts
DANGEROUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".com", ".pif", ".vbs", ".js",
    ".jar", ".msi", ".ps1", ".apk", ".dll", ".hta", ".wsf",
}

# Extensions often used to smuggle macros
MACRO_RISK_EXTENSIONS = {".docm", ".xlsm", ".pptm"}

# Common "disguise" extensions people expect to be safe
COMMONLY_TRUSTED = {".pdf", ".jpg", ".jpeg", ".png", ".mp3", ".mp4", ".txt", ".docx", ".xlsx"}


def check_double_extension(filename: str) -> list:
    """Detects e.g. invoice.pdf.exe -- looks safe, isn't."""
    findings = []
    parts = filename.lower().split(".")
    if len(parts) > 2:
        # second-to-last extension looks like a trusted type, last is dangerous
        fake_ext = "." + parts[-2]
        real_ext = "." + parts[-1]
        if fake_ext in COMMONLY_TRUSTED and real_ext in DANGEROUS_EXTENSIONS:
            findings.append(
                f"This file looks like a {fake_ext} file but is actually {real_ext} — a common disguise trick"
            )
    return findings


def check_extension_risk(filename: str) -> tuple:
    findings = []
    score = 0
    ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext in DANGEROUS_EXTENSIONS:
        findings.append(f"File type '{ext}' can run code on your device — only open if you fully trust the source")
        score += 30

    if ext in MACRO_RISK_EXTENSIONS:
        findings.append(f"File type '{ext}' supports macros, which can be used to run malicious code")
        score += 20

    findings.extend(check_double_extension(filename))
    if any("disguise" in f for f in findings[-1:]):
        score += 35

    return score, findings


def check_virustotal_hash(sha256: str) -> dict:
    if not VIRUSTOTAL_API_KEY:
        return {"score": 0, "findings": [], "skipped": "No VirusTotal API key configured"}

    endpoint = f"https://www.virustotal.com/api/v3/files/{sha256}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    try:
        resp = requests.get(endpoint, headers=headers, timeout=8)
        if resp.status_code == 404:
            return {
                "score": 5,
                "findings": ["This exact file hasn't been seen by VirusTotal before — treat with normal caution"],
            }

        stats = resp.json()["data"]["attributes"]["last_analysis_stats"]
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)

        if malicious > 0:
            return {"score": 60, "findings": [f"{malicious} security engines flagged this exact file as malicious"]}
        if suspicious > 0:
            return {"score": 25, "findings": [f"{suspicious} security engines flagged this file as suspicious"]}
        return {"score": 0, "findings": ["No security engines flagged this file"]}
    except Exception:
        return {"score": 0, "findings": ["VirusTotal file check failed"], "error": True}


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "DANGEROUS"
    if score >= 20:
        return "CAUTION"
    return "SAFE"


@file_scanner_bp.route("/api/scan-file", methods=["POST"])
def scan_file_route():
    if "file" not in request.files:
        return jsonify({"error": "Missing 'file' in form-data"}), 400

    file = request.files["file"]
    filename = file.filename or "unknown"

    file_bytes = file.read()
    if not file_bytes:
        return jsonify({"error": "Empty file"}), 400

    sha256 = hashlib.sha256(file_bytes).hexdigest()

    ext_score, ext_findings = check_extension_risk(filename)
    vt_result = check_virustotal_hash(sha256)

    total_score = min(100, ext_score + vt_result["score"])
    all_findings = ext_findings + vt_result["findings"]

    result = {
        "filename": filename,
        "sha256": sha256,
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings,
    }

    log_scan("file", result)
    return jsonify(result)
