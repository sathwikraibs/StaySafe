"""
TrustLight - File / Download Scanner
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
import threading
import time
import zipfile

from scanners.security import safe_zip_read
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
    ".xapk", ".apks", ".apkm", ".vhdx", ".url", ".scf", ".wsh", ".msp", ".application", ".appref-ms",
    ".settingcontent-ms", ".one", ".iqy", ".slk", ".website", ".mde", ".ade", ".gadget", ".psc1",
}

# Web pages and drawings that can carry scripts and login boxes when sent as files
WEB_EXTENSIONS = {".html", ".htm", ".shtml", ".xhtml", ".svg", ".mht", ".mhtml", ".xht"}

EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

# Extensions often used to smuggle macros
MACRO_RISK_EXTENSIONS = {".docm", ".xlsm", ".pptm", ".dotm", ".xlam"}

# Common "disguise" extensions people expect to be safe
COMMONLY_TRUSTED = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".mp3", ".mp4", ".txt", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".csv",
}

ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z"}

# What each file TYPE's content starts with ("magic bytes")
EXECUTABLE_KINDS = {"Windows program", "Linux program", "Android app", "Java program", "Windows shortcut", "script",
                    "disk image", "OneNote file"}


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
    if head.startswith(b"\xe4\x52\x5c\x7b\x8c\xd8\xa7\x4d"):
        return "OneNote file"
    if any(data[o:o + 5] == b"CD001" for o in (0x8001, 0x8801, 0x9001)) or data[:8] == b"conectix" or data[:8] == b"vhdxfile":
        return "disk image"
    if head.startswith(b"#!") or re.match(rb"\s*(@echo off|powershell|Set\s+\w+\s*=\s*CreateObject)", head, re.IGNORECASE):
        return "script"
    low = head.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if low.startswith((b"<!doctype html", b"<html", b"<head", b"<body", b"<script", b"<form", b"<meta", b"<iframe")) \
            or (low.startswith(b"<?xml") and b"<html" in head.lower()):
        return "web page"
    if low.startswith(b"<svg") or (low.startswith(b"<?xml") and b"<svg" in head.lower()):
        return "SVG image"
    if low.startswith(b"[internetshortcut]"):
        return "internet shortcut"
    return "unknown"


EXPECTED_TYPES = {
    ".pdf": {"PDF"}, ".png": {"PNG image"}, ".jpg": {"JPEG image"}, ".jpeg": {"JPEG image"},
    ".gif": {"GIF image"}, ".webp": {"WEBP image"}, ".docx": {"Word document"}, ".xlsx": {"Excel document"},
    ".pptx": {"PowerPoint document"}, ".doc": {"old Office document"}, ".xls": {"old Office document"},
    ".svg": {"SVG image", "web page"}, ".html": {"web page"}, ".htm": {"web page"},
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


def check_extension_risk(filename: str, led=None) -> tuple:
    findings = []
    score = 0

    if "‮" in filename:
        findings.append("The file name contains a hidden character that reverses the text to disguise its real type")
        score += (led.note(findings, 50) if led else 50)
        filename = filename.replace("‮", "")

    ext = get_extension(filename)

    if ext in DANGEROUS_EXTENSIONS:
        findings.append(f"File type '{ext}' can run code on your device. Only open it if you fully trust the sender")
        score += (led.note(findings, 30) if led else 30)

    if ext in MACRO_RISK_EXTENSIONS:
        findings.append(f"File type '{ext}' can contain macros, which are often used to install malware")
        score += (led.note(findings, 25) if led else 25)

    disguise = check_double_extension(filename)
    if disguise:
        findings.extend(disguise)
        score += (led.note(findings, 35) if led else 35)

    return score, findings


def check_content(filename: str, data: bytes, led=None) -> tuple:
    """Look INSIDE the file: does it match its name, and does it hide anything risky?"""
    findings = []
    score = 0
    ext = get_extension(filename)
    real_type = detect_real_type(data)

    if real_type in EXECUTABLE_KINDS and ext not in DANGEROUS_EXTENSIONS:
        findings.append(f"This file is named like a '{ext or 'no extension'}' file but is actually {_a(real_type)}. Do NOT open it")
        score += (led.note(findings, 60) if led else 60)
    elif ext in EXPECTED_TYPES and real_type != "unknown" and real_type not in EXPECTED_TYPES[ext]:
        findings.append(f"The file's name says '{ext}' but its contents are {_a(real_type)}")
        score += (led.note(findings, 20) if led else 20)

    def note(text, pts):
        nonlocal score
        findings.append(text)
        score += (led.note(findings, pts) if led else pts)

    if EICAR in data[:4096] and real_type != "ZIP archive":
        note("This is the standard antivirus test file (EICAR). It is harmless, but every security program treats it "
             "as a virus, so TrustLight does too", 90)

    if real_type == "PDF":
        # names can be hidden with #xx codes (/J#61vaScript is /JavaScript)
        raw = data[:5_000_000]
        lowered = re.sub(rb"#([0-9a-fA-F]{2})", lambda m: bytes([int(m.group(1), 16)]), raw)
        risky = [label for token, label in (
            (b"/JavaScript", "runs JavaScript"), (b"/JS", "runs JavaScript"),
            (b"/EmbeddedFile", "has files hidden inside it"),
        ) if token in lowered]
        risky = sorted(set(risky))
        auto = re.search(rb"/(OpenAction|AA)\b", lowered) is not None
        if b"/Launch" in lowered:
            note("This PDF tries to start another program on your computer when opened. Genuine documents never do this", 50)
        if risky:
            if auto and "runs JavaScript" in risky:
                risky = ["runs JavaScript as soon as it is opened" if r == "runs JavaScript" else r for r in risky]
            note("This PDF " + ", ".join(risky) + ". Normal documents rarely need this",
                 40 if "runs JavaScript as soon as it is opened" in risky else 30)

    if real_type in ("Word document", "Excel document", "PowerPoint document"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()[:2000]
                if any(n.lower().endswith("vbaproject.bin") for n in names):
                    note("This Office document contains macros (hidden programs)", 35)
                    if ext in (".docx", ".xlsx", ".pptx"):
                        note(f"'{ext}' files normally can't contain macros, so this one has been tampered with", 15)
                rels = b" ".join(safe_zip_read(z, n, 2 * 1024 * 1024) for n in names if n.endswith(".rels"))
                if re.search(rb'Type="[^"]*/(attachedTemplate|oleObject|frame|subDocument)"[^>]*Target="(https?:|file:|\\\\)', rels) or \
                        re.search(rb'Target="(https?:|file:|\\\\)[^"]*"[^>]*Type="[^"]*/(attachedTemplate|oleObject|frame|subDocument)"', rels):
                    note("This document downloads a hidden part from the internet when it is opened (a known trick to "
                         "run harmful code without macros)", 45)
                body = b" ".join(safe_zip_read(z, n, 4 * 1024 * 1024) for n in names
                                 if re.match(r"(word|xl|ppt)/[^/]+\.xml$", n) or n.startswith("xl/worksheets/"))[:20_000_000]
                if re.search(rb"\bDDE(AUTO)?\b", body):
                    note("This document can start other programs through a hidden command (DDE). Don't click 'Yes' "
                         "on any pop-up it shows", 45)
                embedded = [n for n in names if "/embeddings/" in n.lower() or n.lower().endswith(("olepackage.bin", ".exe", ".js", ".hta"))]
                if embedded:
                    inside = b" ".join(safe_zip_read(z, n, 4 * 1024 * 1024)[:4_000_000] for n in embedded[:5]).lower()
                    if re.search(rb"\.(exe|scr|bat|cmd|js|jse|vbs|vbe|hta|lnk|ps1|wsf|apk|msi)\b", inside) or inside.find(b"mz") == 0:
                        note("This document has a program hidden inside it. Never double-click pictures or icons in it", 50)
                    elif any(n.lower().endswith(".bin") for n in embedded):
                        note("This document has another file hidden inside it", 10)
        except Exception:
            pass

    if real_type == "ZIP archive":
        pts, texts = _inspect_zip(data, 0)
        for t, p in zip(texts, pts):
            note(t, p)

    if real_type == "old Office document" and (b"VBA" in data or b"_VBA_PROJECT" in data):
        note("This Office document contains macros (hidden programs)", 35)

    if real_type in ("web page", "SVG image") or (ext in WEB_EXTENSIONS and real_type == "unknown"):
        for t, p in _inspect_web_page(data[:3_000_000], real_type == "SVG image" or ext == ".svg"):
            note(t, p)

    if real_type == "OneNote file" or ext == ".one":
        inside = data[:20_000_000].lower()
        if re.search(rb"\.(hta|bat|cmd|exe|vbs|js|wsf|lnk|ps1|chm)\b", inside):
            note("This OneNote file has a program hidden behind a picture or button. Clicking it would install malware", 50)
        else:
            note("OneNote files sent by email or chat are a common way to hide programs. Don't click anything in it", 20)

    if real_type == "internet shortcut" or ext in (".url", ".website"):
        target = re.search(rb"(?im)^\s*url\s*=\s*(\S+)", data[:4096])
        if target and re.match(rb"(file:|\\\\|smb:)", target.group(1), re.I):
            note("This shortcut opens a file on another computer over the internet, a trick used to run programs", 45)

    if real_type == "disk image" and ext in (".iso", ".img", ".vhd", ".vhdx"):
        note("Disk image files sent by email or chat are used to sneak programs past Windows protection", 20)

    return score, findings, real_type


_PROGRAM_NAME = re.compile(r"\.(exe|scr|bat|cmd|com|pif|vbs|vbe|js|jse|jar|msi|ps1|hta|wsf|lnk|cpl|apk|dll|iso|img|one)$", re.I)


def _inspect_zip(data: bytes, depth: int):
    """What is inside a ZIP (and ZIPs inside it, two levels deep). Returns (points, texts)."""
    pts, texts = [], []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()[:2000]
            names = [i.filename for i in infos]
            programs = [n for n in names if _PROGRAM_NAME.search(n.rstrip(" ."))]
            if programs:
                shown = ", ".join(n.rsplit("/", 1)[-1] for n in programs[:3])
                texts.append(f"This archive contains program files that can run code: {shown}")
                pts.append(40)
            if any(check_double_extension(n.rsplit("/", 1)[-1]) or "\u202e" in n for n in names):
                texts.append("A file inside is disguised as a document or photo but is really a program")
                pts.append(30)
            if any(i.flag_bits & 0x1 for i in infos):
                texts.append("This archive is password-protected, a trick used to hide malware from scanners")
                pts.append(15 if not programs else 25)
            encrypted = any(i.flag_bits & 0x1 for i in infos)
            if encrypted:
                return pts, texts
            for i in infos:
                n = i.filename.lower()
                if i.file_size > 25 * 1024 * 1024 or i.is_dir():
                    continue
                if n.endswith((".apk", ".xapk", ".apks")) or n == "classes.dex":
                    inner = safe_zip_read(z, i.filename, 25 * 1024 * 1024)
                    if inner[:2] == b"PK":
                        from scanners.apk_check import analyze_apk
                        a = analyze_apk(i.filename.rsplit("/", 1)[-1], inner)
                        if a["score"]:
                            texts.append(f"This archive hides an Android app ({i.filename.rsplit('/', 1)[-1]}) that asks for risky "
                                         "permissions, like reading SMS OTPs or controlling the screen")
                            pts.append(min(60, a["score"]))
                    break
            budget = 60 * 1024 * 1024        # never unpack more than this in total (stops "zip bombs")
            for i in infos[:200]:
                if i.file_size > 25 * 1024 * 1024 or i.is_dir() or i.file_size > budget:
                    continue
                budget -= i.file_size
                head = safe_zip_read(z, i.filename, 25 * 1024 * 1024)
                if EICAR in head[:4096]:
                    texts.append("The archive contains the standard antivirus test file (EICAR), which every security program treats as a virus")
                    pts.append(90)
                    break
                if depth < 2 and head[:4] == b"PK\x03\x04" and not i.filename.lower().endswith((".docx", ".xlsx", ".pptx", ".apk", ".jar")):
                    p2, t2 = _inspect_zip(head, depth + 1)
                    if p2:
                        texts.append("Another archive is hidden inside this one, and it contains program files")
                        pts.append(max(p2) + 10)
                        break
                if head[:2] == b"MZ" and not _PROGRAM_NAME.search(i.filename):
                    texts.append(f"A file inside ({i.filename.rsplit('/', 1)[-1]}) is really a Windows program in disguise")
                    pts.append(50)
                    break
    except Exception:
        pass
    return pts, texts


def _inspect_web_page(data: bytes, svg: bool):
    """A web page or drawing sent as a file: login boxes, hidden downloads, instant redirects."""
    out = []
    text = data.decode("utf-8", "ignore")
    low = text.lower()
    if re.search(r"<input[^>]+type\s*=\s*[\"']?password", low):
        brand = re.search(r"(microsoft|outlook|office ?365|onedrive|sharepoint|adobe|docusign|wetransfer|dropbox|"
                          r"gmail|google|yahoo|webmail|sbi|hdfc|icici|axis|kotak|paytm|phonepe|bank|netbanking|"
                          r"aadhaa?r|income ?tax|whatsapp|instagram|facebook)", low)
        if brand:
            out.append((f"This file is a login page with a password box and uses the name '{brand.group(1).title()}'. "
                        "Login pages sent as files are almost always fake and send your password to criminals", 55))
        else:
            out.append(("This file is a login page with a password box. Login pages sent as files are almost always "
                        "fake and send your password to criminals", 55))
        if re.search(r"<input[^>]+value\s*=\s*[\"'][^\"'@\s]+@[^\"'\s]+\.[a-z]{2,}", low):
            out.append(("Your email address is already filled in, to make the fake page look personal", 10))
    elif re.search(r"<input[^>]+name\s*=\s*[\"']?(otp|pin|cvv|card|upi|aadhaa?r|pan)\b", low):
        out.append(("This file is a form asking for OTP, PIN, card or bank details. Never type them into a file", 45))
    if re.search(r"(new\s+blob\s*\(|createobjecturl|mssaveoropenblob|navigator\.mssaveblob)", low) and \
            re.search(r"(atob\s*\(|\.download\s*=|download\s*=)", low):
        out.append(("This file builds another file inside your browser and downloads it (HTML smuggling). "
                    "This is used to sneak malware past email protection", 55))
    elif re.search(r"(eval\s*\(\s*(atob|unescape|decodeuricomponent)|document\.write\s*\(\s*(unescape|atob|decodeuricomponent)|"
                   r"string\.fromcharcode\s*\((\s*\d+\s*,){20,})", low):
        out.append(("This file hides its real content with scrambled code", 30))
    redirect = re.search(r"http-equiv\s*=\s*[\"']?refresh[^>]+url\s*=\s*['\"]?https?://", low) or \
        re.search(r"(window|document|top|self)\.location(\.href)?\s*=\s*['\"`]https?://", low) or \
        re.search(r"location\.(replace|assign)\s*\(\s*['\"`]https?://", low)
    if redirect:
        out.append(("Opening this file sends you straight to a website, a way to get around link checks in email and chat", 20))
    if svg and re.search(r"<script|onload\s*=|javascript:", low):
        out.append(("This picture (SVG) contains a program (script). Real pictures don't need one", 35))
    return out


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


_VT_FOUND: dict = {}          # sha256 -> (time, result): known files, so repeat checks cost nothing
_VT_LOCK = threading.Lock()


def check_virustotal_hash(sha256: str) -> dict:
    """Look the file up on VirusTotal by its fingerprint only (the file itself is not sent)."""
    if not VIRUSTOTAL_API_KEY:
        return {"status": "skip", "score": 0, "findings": [], "vt": {"state": "off"}}
    from scanners.quota import quota
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    with _VT_LOCK:
        hit = _VT_FOUND.get(sha256)
    if hit and time.time() - hit[0] < 3 * 3600:
        return hit[1]
    from scanners import store
    kept = store.get("file", sha256)
    if isinstance(kept, dict) and kept.get("vt"):
        with _VT_LOCK:
            _VT_FOUND[sha256] = (time.time(), kept)
        return kept
    try:
        deadline = time.time() + 40   # the file's own VirusTotal result matters most: wait for a free slot
        for _attempt in range(2):
            if not quota("virustotal").take(wait=max(0.0, deadline - time.time()), priority="high"):
                return {"status": "skip", "score": 0, "findings": [], "vt": {"state": "busy"}}
            resp = requests.get(f"{VT_API}/files/{sha256}", headers=headers, timeout=8)
            if resp.status_code != 429:
                break
            quota("virustotal").cool_down(60)
        if resp.status_code == 404:
            return {"status": "info", "score": 5,
                    "findings": ["This exact file hasn't been seen by VirusTotal before. Treat with normal caution"],
                    "vt": {"state": "not_found", "link": f"https://www.virustotal.com/gui/file/{sha256}"}}
        if resp.status_code == 429:
            return {"status": "skip", "score": 0, "findings": [], "vt": {"state": "busy"}}
        attrs = resp.json()["data"]["attributes"]
        vt = _vt_summary(attrs.get("last_analysis_stats", {}), attrs.get("last_analysis_results", {}), attrs, sha256)
        out = {**_vt_scoring(vt), "vt": vt}
        with _VT_LOCK:
            _VT_FOUND[sha256] = (time.time(), out)
            if len(_VT_FOUND) > 500:
                _VT_FOUND.pop(next(iter(_VT_FOUND)))
        # A file's verdict rarely changes: harmful files are kept 30 days, others 3 days
        harmful = (vt.get("malicious") or 0) >= 1 if isinstance(vt, dict) else False
        store.put("file", sha256, out, (30 if harmful else 3) * 86400)
        return out
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
    from scanners.quota import quota
    if not quota("virustotal").take(wait=40, priority="high"):
        return {"state": "busy"}
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
        if not quota("virustotal").take(wait=20):
            continue
        try:
            a = requests.get(f"{VT_API}/analyses/{analysis_id}", headers=headers, timeout=10).json()["data"]["attributes"]
        except Exception:
            continue
        if a.get("status") == "completed":
            return _vt_summary(a.get("stats", {}), a.get("results", {}), {}, sha256)
    return {"state": "queued", "link": f"https://www.virustotal.com/gui/file/{sha256}"}


_LINK_IN_FILE = re.compile(rb"https?://[^\s<>\"'()\\\]\[{}]{4,300}", re.IGNORECASE)
_SKIP_LINK_HOSTS = ("schemas.openxmlformats.org", "schemas.microsoft.com", "www.w3.org", "purl.org", "ns.adobe.com",
                    "www.adobe.com/xap", "openoffice.org", "xml.org", "microsoft.com/office")


def extract_file_links(real_type: str, data: bytes, limit: int = 3) -> list:
    """Web links a PDF, Office document or text file would open when clicked (not internal XML names)."""
    raw = []
    try:
        if real_type in ("Word document", "Excel document", "PowerPoint document"):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist()[:400]:
                    if name.endswith(".rels"):
                        for m in re.finditer(rb'Target="(https?://[^"]+)"[^>]*TargetMode="External"', safe_zip_read(z, name)):
                            raw.append(m.group(1))
        elif real_type == "PDF":
            raw = [m.group(1) for m in re.finditer(rb"/URI\s*\(([^)]{4,300})\)", data[:8_000_000])]
        elif real_type in ("unknown", "script", "web page", "SVG image", "internet shortcut"):
            raw = _LINK_IN_FILE.findall(data[:2_000_000])
            # where a web page sends what you type, or where it jumps to, matters most
            first = re.findall(rb"(?:action\s*=\s*[\"']?|url\s*=\s*['\"]?|location(?:\.href)?\s*=\s*['\"`]|"
                               rb"(?:replace|assign)\s*\(\s*['\"`])(https?://[^\s\"'`<>)]{4,300})", data[:2_000_000], re.I)
            raw = first + [r for r in raw if r not in first]
    except Exception:
        return []
    out = []
    for r in raw:
        u = r.decode("utf-8", "ignore").strip().rstrip(".,;")
        if u.lower().startswith("http") and not any(h in u.lower() for h in _SKIP_LINK_HOSTS) and u not in out:
            out.append(u)
        if len(out) >= limit:
            break
    return out


def check_known_good(sha256: str) -> dict:
    """
    CIRCL hashlookup (free, no key): is this exact file a known genuine one, e.g. from the US
    NIST software library (NSRL), Windows or Linux installers? {'known': bool, 'source': str}
    """
    import scanners.url_scanner as _us
    from scanners.quota import quota
    if _us.OFFLINE or not quota("circl").take(wait=5):
        return {"known": False}
    try:
        resp = requests.get(f"https://hashlookup.circl.lu/lookup/sha256/{sha256}", timeout=5,
                            headers={"Accept": "application/json", "User-Agent": "TrustLight/2.0"})
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
    from scanners.quota import quota
    if _us.OFFLINE or not key or not quota("abusech").take(wait=5):
        return {"found": False}
    try:
        resp = requests.post("https://mb-api.abuse.ch/api/v1/", data={"query": "get_info", "hash": sha256},
                             headers={"Auth-Key": key, "User-Agent": "TrustLight/2.0"}, timeout=8)
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

    result = scan_file_bytes(filename, file_bytes, vt_upload=request.form.get("vt_upload") == "1")
    if file_bytes[:3] == b"\xff\xd8\xff" or file_bytes[:4] in (b"\x89PNG", b"RIFF"):
        try:
            from scanners.qr_scanner import decode_qr_image, CV2_AVAILABLE
            qr = decode_qr_image(file_bytes) if CV2_AVAILABLE and len(file_bytes) < 15_000_000 else None
        except Exception:
            qr = None
        if qr:
            result["qr_in_picture"] = qr[:2000]  # the website suggests Check a QR Code
    log_scan("file", result)
    return jsonify(result)


def scan_file_bytes(filename: str, file_bytes: bytes, vt_upload: bool = False, use_vt: bool = True) -> dict:
    """The whole file check (also used by the owner's live self-test)."""
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    md5 = hashlib.md5(file_bytes).hexdigest()
    sha1 = hashlib.sha1(file_bytes).hexdigest()

    from scanners.ledger import Ledger
    led = Ledger()
    ext_score, ext_findings = check_extension_risk(filename, led)
    content_score, content_findings, real_type = check_content(filename, file_bytes, led)
    apk = {"findings": [], "score": 0, "package": "", "permissions": []}
    if real_type == "Android app":
        from scanners.apk_check import analyze_apk
        apk = analyze_apk(filename, file_bytes)
        content_findings = content_findings + apk["findings"]
        content_score += apk["score"]
        for f in apk["findings"]:
            led.add(f, apk.get("points", {}).get(f, 0))
    from concurrent.futures import ThreadPoolExecutor
    from scanners.url_scanner import scan_url, LINK_POOL
    file_links = extract_file_links(real_type, file_bytes)
    link_futures = [(u, LINK_POOL.submit(scan_url, u)) for u in file_links]
    with ThreadPoolExecutor(3) as pool:
        known_f = pool.submit(check_known_good, sha256)
        bazaar_f = pool.submit(check_malwarebazaar, sha256)
        vt_result = check_virustotal_hash(sha256) if use_vt else {"status": "skip", "score": 0, "findings": [], "vt": {"state": "off"}}
        known = known_f.result()
        bazaar = bazaar_f.result()
    # The visitor agreed to let VirusTotal scan the file itself (only if it has never been seen)
    if vt_upload and vt_result.get("vt", {}).get("state") == "not_found":
        uploaded = upload_to_virustotal(filename, file_bytes, sha256)
        if uploaded.get("state") == "found":
            vt_result = {**_vt_scoring(uploaded), "vt": uploaded}
        else:
            vt_result["vt"] = uploaded

    links_checked, link_score, link_findings = [], 0, []
    for u, fut in link_futures:
        try:
            lr = fut.result(timeout=80)
        except Exception:
            continue
        links_checked.append({"url": u, "verdict": lr["verdict"], "risk_score": lr["risk_score"],
                              "findings": lr["findings"], "checks": lr.get("checks", []), "details": lr.get("details", {})})
        if lr["verdict"] != "SAFE":
            word = "dangerous" if lr["verdict"] == "DANGEROUS" else "suspicious"
            link_findings.append(f"A link inside this file looks {word}: {u}")
            pts = 50 if lr["verdict"] == "DANGEROUS" else 20
            if pts > link_score:
                link_score = pts
    total_score = min(100, ext_score + content_score + vt_result["score"] + link_score)
    all_findings = ext_findings + content_findings + vt_result["findings"] + link_findings
    if link_score:
        led.add(link_findings[0], link_score)
    if vt_result["score"] and vt_result["findings"]:
        led.add(vt_result["findings"][0], vt_result["score"])
    vt_flagged = (vt_result.get("vt", {}) or {}).get("malicious", 0) or 0
    if bazaar.get("found"):
        all_findings.insert(0, f"This exact file is a known malware sample on MalwareBazaar ({bazaar['signature']}). Delete it")
        led.add(all_findings[0], max(total_score, 95) - total_score)
        total_score = max(total_score, 95)
        known = {"known": False}
    # Strong evidence found inside the file (a disguised program, hidden code, the antivirus test file)
    # is never cancelled by a "known software" list: those lists also contain test files and tools.
    strong_inside = content_score >= 40 or EICAR in file_bytes[:4096]
    if known.get("known") and vt_flagged == 0 and not strong_inside:
        # exactly the same file as a known genuine program: small warning signs don't matter
        all_findings.insert(0, f"This exact file is on a public list of known genuine software ({known['source']})")
        led.add(all_findings[0], min(total_score, 10) - total_score)
        total_score = min(total_score, 10)
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
        "score_parts": led.result(total_score),
        "links_checked": links_checked,
        "apk": {"package": apk["package"], "permissions": apk["permissions"]} if real_type == "Android app" else None,
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings,
    }
    return result
