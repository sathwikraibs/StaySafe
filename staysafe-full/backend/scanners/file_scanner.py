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

import io
import os
import re
import hashlib
import zipfile
import requests
from flask import Blueprint, request, jsonify

from scanners.risk_engine import log_scan

file_scanner_bp = Blueprint("file_scanner", __name__)

VIRUSTOTAL_API_KEY = os.environ.get("VT_API_KEY", "")

# Extensions that can execute code / run scripts
DANGEROUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".com", ".pif", ".vbs", ".vbe", ".js", ".jse",
    ".jar", ".msi", ".ps1", ".apk", ".dll", ".hta", ".wsf", ".lnk", ".reg", ".cpl",
    ".chm", ".iso", ".img", ".vhd", ".xll", ".appx", ".msix", ".sh",
}

# Extensions often used to smuggle macros
MACRO_RISK_EXTENSIONS = {".docm", ".xlsm", ".pptm", ".dotm", ".xlam"}

# Common "disguise" extensions people expect to be safe
COMMONLY_TRUSTED = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".mp3", ".mp4", ".txt", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".csv",
}

ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z"}

# What each file TYPE's content starts with ("magic bytes")
EXECUTABLE_KINDS = {"Windows program", "Linux program", "Android app", "Java program", "Windows shortcut", "script"}


def detect_real_type(data: bytes) -> str:
    """Identify what the file really is from its first bytes, ignoring its name."""
    head = data[:4096]
    if head.startswith(b"MZ"):
        return "Windows program"
    if head.startswith(b"\x7fELF"):
        return "Linux program"
    if head.startswith(b"%PDF"):
        return "PDF"
    if head.startswith(b"\x89PNG"):
        return "PNG image"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG image"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF image"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "WEBP image"
    if head.startswith(b"\x4c\x00\x00\x00\x01\x14\x02\x00"):
        return "Windows shortcut"
    if head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "old Office document"
    if head.startswith(b"Rar!"):
        return "RAR archive"
    if head.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z archive"
    if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()
        except Exception:
            return "ZIP archive"
        if "AndroidManifest.xml" in names or "classes.dex" in names:
            return "Android app"
        if "META-INF/MANIFEST.MF" in names and any(n.endswith(".class") for n in names):
            return "Java program"
        if any(n.startswith("word/") for n in names):
            return "Word document"
        if any(n.startswith("xl/") for n in names):
            return "Excel document"
        if any(n.startswith("ppt/") for n in names):
            return "PowerPoint document"
        return "ZIP archive"
    if head.startswith(b"#!") or re.match(rb"\s*(@echo off|powershell|Set\s+\w+\s*=\s*CreateObject)", head, re.IGNORECASE):
        return "script"
    return "unknown"


EXPECTED_TYPES = {
    ".pdf": {"PDF"}, ".png": {"PNG image"}, ".jpg": {"JPEG image"}, ".jpeg": {"JPEG image"},
    ".gif": {"GIF image"}, ".webp": {"WEBP image"}, ".docx": {"Word document"}, ".xlsx": {"Excel document"},
    ".pptx": {"PowerPoint document"}, ".doc": {"old Office document"}, ".xls": {"old Office document"},
    ".ppt": {"old Office document"}, ".zip": {"ZIP archive"}, ".apk": {"Android app"},
}


def _a(noun: str) -> str:
    return ("an " if noun[:1].lower() in "aeiou" else "a ") + noun


def get_extension(filename: str) -> str:
    name = filename.lower().rstrip(" .")
    return "." + name.rsplit(".", 1)[-1].strip() if "." in name else ""


def check_double_extension(filename: str) -> list:
    """Detects e.g. 'invoice.pdf.exe' or 'invoice.pdf      .exe' — looks safe, isn't."""
    parts = [p.strip() for p in filename.lower().rstrip(" .").split(".")]
    if len(parts) > 2:
        fake_ext = "." + parts[-2]
        real_ext = "." + parts[-1]
        if fake_ext in COMMONLY_TRUSTED and real_ext in DANGEROUS_EXTENSIONS:
            return [f"This file pretends to be a {fake_ext} file but is really a {real_ext} program — a common disguise trick"]
    return []


def check_extension_risk(filename: str) -> tuple:
    findings = []
    score = 0

    if "‮" in filename:
        findings.append("The file name contains a hidden character that reverses the text to disguise its real type")
        score += 50
        filename = filename.replace("‮", "")

    ext = get_extension(filename)

    if ext in DANGEROUS_EXTENSIONS:
        findings.append(f"File type '{ext}' can run code on your device — only open it if you fully trust the sender")
        score += 30

    if ext in MACRO_RISK_EXTENSIONS:
        findings.append(f"File type '{ext}' can contain macros, which are often used to install malware")
        score += 25

    disguise = check_double_extension(filename)
    if disguise:
        findings.extend(disguise)
        score += 35

    return score, findings


def check_content(filename: str, data: bytes) -> tuple:
    """Look INSIDE the file: does it match its name, and does it hide anything risky?"""
    findings = []
    score = 0
    ext = get_extension(filename)
    real_type = detect_real_type(data)

    if real_type in EXECUTABLE_KINDS and ext not in DANGEROUS_EXTENSIONS:
        findings.append(f"This file is named like a '{ext or 'no extension'}' file but is actually {_a(real_type)} — do NOT open it")
        score += 60
    elif ext in EXPECTED_TYPES and real_type != "unknown" and real_type not in EXPECTED_TYPES[ext]:
        findings.append(f"The file's name says '{ext}' but its contents are {_a(real_type)}")
        score += 20

    if real_type == "PDF":
        lowered = data[:5_000_000]
        risky = [label for token, label in (
            (b"/JavaScript", "runs JavaScript"),
            (b"/Launch", "tries to launch other programs"),
            (b"/EmbeddedFile", "has files hidden inside it"),
        ) if token in lowered]
        risky = sorted(set(risky))
        if risky:
            findings.append("This PDF " + ", ".join(risky) + " — normal documents rarely need this")
            score += 30

    if real_type in ("Word document", "Excel document", "PowerPoint document", "ZIP archive"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                infos = z.infolist()
                names = [i.filename for i in infos]
                if any(n.lower().endswith("vbaproject.bin") for n in names):
                    findings.append("This Office document contains macros (hidden programs)")
                    score += 35
                    if ext in (".docx", ".xlsx", ".pptx"):
                        findings.append(f"'{ext}' files normally can't contain macros, so this one has been tampered with")
                        score += 15
                if real_type == "ZIP archive":
                    inner_risky = [n for n in names if get_extension(n) in DANGEROUS_EXTENSIONS]
                    if inner_risky:
                        shown = ", ".join(n.rsplit("/", 1)[-1] for n in inner_risky[:3])
                        findings.append(f"This ZIP contains program files that can run code: {shown}")
                        score += 40
                    if any(i.flag_bits & 0x1 for i in infos):
                        findings.append("This ZIP is password-protected, a trick used to hide malware from scanners")
                        score += 15
        except Exception:
            pass

    if real_type == "old Office document" and (b"VBA" in data or b"_VBA_PROJECT" in data):
        findings.append("This Office document contains macros (hidden programs)")
        score += 35

    return score, findings, real_type


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
        return jsonify({"error": "Please choose a file to check."}), 400

    file = request.files["file"]
    filename = file.filename or "unknown"

    file_bytes = file.read()
    if not file_bytes:
        return jsonify({"error": "This file is empty."}), 400

    sha256 = hashlib.sha256(file_bytes).hexdigest()

    ext_score, ext_findings = check_extension_risk(filename)
    content_score, content_findings, real_type = check_content(filename, file_bytes)
    vt_result = check_virustotal_hash(sha256)

    total_score = min(100, ext_score + content_score + vt_result["score"])
    all_findings = ext_findings + content_findings + vt_result["findings"]
    if not all_findings:
        all_findings = ["No warning signs found in this file's name or contents"]

    result = {
        "filename": filename,
        "sha256": sha256,
        "detected_type": real_type,
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings,
    }

    log_scan("file", result)
    return jsonify(result)
