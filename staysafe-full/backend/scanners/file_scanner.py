"""
StaySafe - File / Download Scanner
--------------------------------------
User uploads a file before opening it. We:
  1. Compute its SHA-256 hash
  2. Check that hash against VirusTotal's database
  3. Run local heuristics: double extensions, risky extensions, macro-enabled docs

We do NOT execute or sandbox the file. That's out of scope for a
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
    """Detects e.g. 'invoice.pdf.exe' or 'invoice.pdf      .exe'. Looks safe, isn't."""
    parts = [p.strip() for p in filename.lower().rstrip(" .").split(".")]
    if len(parts) > 2:
        fake_ext = "." + parts[-2]
        real_ext = "." + parts[-1]
        if fake_ext in COMMONLY_TRUSTED and real_ext in DANGEROUS_EXTENSIONS:
            return [f"This file pretends to be a {fake_ext} file but is really a {real_ext} program. A common disguise trick"]
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
        findings.append(f"File type '{ext}' can run code on your device. Only open it if you fully trust the sender")
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
        findings.append(f"This file is named like a '{ext or 'no extension'}' file but is actually {_a(real_type)}. Do NOT open it")
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
            findings.append("This PDF " + ", ".join(risky) + ". Normal documents rarely need this")
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


VT_API = "https://www.virustotal.com/api/v3"


def _vt_date(ts):
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
    except Exception:
        return ""


def _engine_list(results: dict) -> list:
    """Every security company's verdict, dangerous ones first (like VirusTotal's Detection tab)."""
    order = {"malicious": 0, "suspicious": 1, "harmless": 2, "undetected": 3}
    engines = [{"name": name, "category": (v or {}).get("category", ""), "result": (v or {}).get("result") or ""}
               for name, v in (results or {}).items()]
    engines = [e for e in engines if e["category"] in order]
    engines.sort(key=lambda e: (order.get(e["category"], 9), e["name"].lower()))
    return engines[:90]


def _vt_summary(stats: dict, results: dict, attrs: dict, sha256: str) -> dict:
    malicious, suspicious = stats.get("malicious", 0), stats.get("suspicious", 0)
    total = sum(v for k, v in stats.items() if k in ("malicious", "suspicious", "undetected", "harmless"))
    label = ((attrs or {}).get("popular_threat_classification") or {}).get("suggested_threat_label", "")
    return {
        "state": "found",
        "malicious": malicious,
        "suspicious": suspicious,
        "undetected": stats.get("undetected", 0),
        "harmless": stats.get("harmless", 0),
        "total": total,
        "engines": _engine_list(results),
        "threat_label": label,
        "type_description": (attrs or {}).get("type_description", ""),
        "first_seen": _vt_date((attrs or {}).get("first_submission_date")),
        "last_analysis": _vt_date((attrs or {}).get("last_analysis_date")),
        "times_submitted": (attrs or {}).get("times_submitted"),
        "names": ((attrs or {}).get("names") or [])[:5],
        "tags": ((attrs or {}).get("tags") or [])[:6],
        "reputation": (attrs or {}).get("reputation"),
        "link": f"https://www.virustotal.com/gui/file/{sha256}",
    }


def _vt_scoring(vt: dict) -> dict:
    """Turn a VirusTotal summary into score, findings and the check line."""
    mal, sus = vt.get("malicious", 0), vt.get("suspicious", 0)
    if mal > 0:
        return {"status": "fail", "value": f"{mal}/{vt.get('total') or '?'}", "score": 60 if mal >= 2 else 40,
                "findings": [f"{mal} security engines flagged this exact file as malicious"]}
    if sus > 0:
        return {"status": "warn", "value": f"{sus}/{vt.get('total') or '?'}", "score": 25,
                "findings": [f"{sus} security engines flagged this file as suspicious"]}
    return {"status": "pass", "value": vt.get("total") or None, "score": 0,
            "findings": ["No security engines flagged this file"]}


def check_virustotal_hash(sha256: str) -> dict:
    """Look the file up on VirusTotal by its fingerprint only (the file itself is not sent)."""
    if not VIRUSTOTAL_API_KEY:
        return {"status": "skip", "score": 0, "findings": [], "vt": {"state": "off"}}
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    try:
        resp = requests.get(f"{VT_API}/files/{sha256}", headers=headers, timeout=8)
        if resp.status_code == 404:
            return {"status": "info", "score": 5,
                    "findings": ["This exact file hasn't been seen by VirusTotal before. Treat with normal caution"],
                    "vt": {"state": "not_found", "link": f"https://www.virustotal.com/gui/file/{sha256}"}}
        if resp.status_code == 429:
            return {"status": "skip", "score": 0, "findings": [], "vt": {"state": "busy"}}
        attrs = resp.json()["data"]["attributes"]
        vt = _vt_summary(attrs.get("last_analysis_stats", {}), attrs.get("last_analysis_results", {}), attrs, sha256)
        return {**_vt_scoring(vt), "vt": vt}
    except Exception:
        return {"status": "skip", "score": 0, "findings": [], "error": True, "vt": {"state": "error"}}


def upload_to_virustotal(filename: str, data: bytes, sha256: str) -> dict:
    """
    Only when the visitor ticks 'let VirusTotal scan the file itself'. Sends the file, then
    checks back up to 3 times (15 s apart) so we stay inside the free 4-lookups-a-minute limit.
    """
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    if len(data) > 32 * 1024 * 1024:
        return {"state": "too_big"}
    try:
        up = requests.post(f"{VT_API}/files", headers=headers, files={"file": (filename, data)}, timeout=60)
        if up.status_code == 429:
            return {"state": "busy"}
        analysis_id = up.json()["data"]["id"]
    except Exception:
        return {"state": "error"}
    import time as _t
    for _ in range(3):
        _t.sleep(15)
        try:
            a = requests.get(f"{VT_API}/analyses/{analysis_id}", headers=headers, timeout=10).json()["data"]["attributes"]
        except Exception:
            continue
        if a.get("status") == "completed":
            return _vt_summary(a.get("stats", {}), a.get("results", {}), {}, sha256)
    return {"state": "queued", "link": f"https://www.virustotal.com/gui/file/{sha256}"}


def check_known_good(sha256: str) -> dict:
    """
    CIRCL hashlookup (free, no key): is this exact file a known genuine one, e.g. from the US
    NIST software library (NSRL), Windows or Linux installers? {'known': bool, 'source': str}
    """
    import scanners.url_scanner as _us
    if _us.OFFLINE:
        return {"known": False}
    try:
        resp = requests.get(f"https://hashlookup.circl.lu/lookup/sha256/{sha256}", timeout=5,
                            headers={"Accept": "application/json", "User-Agent": "StaySafe/2.0"})
        if resp.status_code != 200:
            return {"known": False}
        data = resp.json()
    except Exception:
        return {"known": False}
    trust = data.get("hashlookup:trust", 50)
    if isinstance(trust, (int, float)) and trust < 50:
        return {"known": False}
    source = data.get("ProductName") or data.get("FileName") or data.get("source") or "NSRL"
    return {"known": True, "source": str(source)[:60]}


def check_malwarebazaar(sha256: str) -> dict:
    """
    MalwareBazaar (abuse.ch, free key ABUSECH_AUTH_KEY): is this exact file a known malware
    sample? Very strong evidence when found. {'found': bool, 'signature': str}
    """
    import os
    import scanners.url_scanner as _us
    key = os.environ.get("ABUSECH_AUTH_KEY", "")
    if _us.OFFLINE or not key:
        return {"found": False}
    try:
        resp = requests.post("https://mb-api.abuse.ch/api/v1/", data={"query": "get_info", "hash": sha256},
                             headers={"Auth-Key": key, "User-Agent": "StaySafe/2.0"}, timeout=8)
        data = resp.json()
    except Exception:
        return {"found": False}
    if data.get("query_status") != "ok" or not data.get("data"):
        return {"found": False}
    item = data["data"][0] or {}
    return {"found": True, "signature": str(item.get("signature") or item.get("file_type") or "malware")[:60]}


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "DANGEROUS"
    if score >= 20:
        return "CAUTION"
    return "SAFE"


@file_scanner_bp.route("/api/file-report/<sha256>", methods=["GET"])
def file_report_route(sha256):
    """'Check again' after a file was sent to VirusTotal."""
    if not re.fullmatch(r"[0-9a-f]{64}", sha256 or ""):
        return jsonify({"error": "Unknown file."}), 400
    r = check_virustotal_hash(sha256)
    return jsonify({"virustotal": r.get("vt", {}), "status": r.get("status"), "findings": r.get("findings", [])})


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
    md5 = hashlib.md5(file_bytes).hexdigest()
    sha1 = hashlib.sha1(file_bytes).hexdigest()

    ext_score, ext_findings = check_extension_risk(filename)
    content_score, content_findings, real_type = check_content(filename, file_bytes)
    apk = {"findings": [], "score": 0, "package": "", "permissions": []}
    if real_type == "Android app":
        from scanners.apk_check import analyze_apk
        apk = analyze_apk(filename, file_bytes)
        content_findings = content_findings + apk["findings"]
        content_score += apk["score"]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(3) as pool:
        known_f = pool.submit(check_known_good, sha256)
        bazaar_f = pool.submit(check_malwarebazaar, sha256)
        vt_result = check_virustotal_hash(sha256)
        known = known_f.result()
        bazaar = bazaar_f.result()
    # The visitor agreed to let VirusTotal scan the file itself (only if it has never been seen)
    if request.form.get("vt_upload") == "1" and vt_result.get("vt", {}).get("state") == "not_found":
        uploaded = upload_to_virustotal(filename, file_bytes, sha256)
        if uploaded.get("state") == "found":
            vt_result = {**_vt_scoring(uploaded), "vt": uploaded}
        else:
            vt_result["vt"] = uploaded

    total_score = min(100, ext_score + content_score + vt_result["score"])
    all_findings = ext_findings + content_findings + vt_result["findings"]
    vt_flagged = (vt_result.get("vt", {}) or {}).get("malicious", 0) or 0
    if bazaar.get("found"):
        all_findings.insert(0, f"This exact file is a known malware sample on MalwareBazaar ({bazaar['signature']}). Delete it")
        total_score = max(total_score, 95)
        known = {"known": False}
    if known.get("known") and vt_flagged == 0:
        # exactly the same file as a known genuine program: small warning signs don't matter
        total_score = min(total_score, 10)
        all_findings.insert(0, f"This exact file is on a public list of known genuine software ({known['source']})")
    if not all_findings:
        all_findings = ["No warning signs found in this file's name or contents"]

    type_bad = [f for f in content_findings if f.startswith(("This file is named like", "The file's name says"))]
    hidden = [f for f in content_findings if f not in type_bad]
    ext = get_extension(filename)
    checks = [
        {"id": "file_vt", "status": vt_result.get("status", "skip"), "value": vt_result.get("value")},
        {"id": "file_type", "status": ("fail" if any("do not" in f.lower() for f in type_bad) else "warn") if type_bad else "pass",
         "value": real_type if real_type != "unknown" else None},
        {"id": "file_hidden", "status": "fail" if hidden else "pass", "value": len(hidden)},
        {"id": "file_name", "status": "fail" if ext_score >= 35 else ("warn" if ext_score else "pass"), "value": ext or None},
    ]
    if known.get("known"):
        checks.insert(0, {"id": "file_known", "status": "pass", "value": known.get("source")})
    if bazaar.get("found"):
        checks.insert(0, {"id": "file_bazaar", "status": "fail", "value": bazaar["signature"]})
    if real_type == "Android app":
        checks.insert(1, {"id": "file_apk", "status": "fail" if apk["score"] >= 35 else ("warn" if apk["score"] else "pass"),
                          "value": len(apk["permissions"])})

    result = {
        "filename": filename,
        "size": len(file_bytes),
        "checks": checks,
        "sha256": sha256,
        "md5": md5,
        "sha1": sha1,
        "virustotal": vt_result.get("vt", {}),
        "detected_type": real_type,
        "apk": {"package": apk["package"], "permissions": apk["permissions"]} if real_type == "Android app" else None,
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings,
    }

    log_scan("file", result)
    return jsonify(result)
