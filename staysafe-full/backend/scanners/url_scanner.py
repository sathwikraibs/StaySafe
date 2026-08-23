"""
StaySafe - URL Scanner Module
------------------------------
Analyzes a URL for phishing/malware risk using:
  1. URL structure heuristics
  2. WHOIS domain age
  3. Google Safe Browsing API
  4. VirusTotal API
Combines everything into a 0-100 risk score with a human-readable verdict.

Plug this in to your main Flask app with:
    from url_scanner import url_scanner_bp
    app.register_blueprint(url_scanner_bp)
"""

import re
import os
import requests
import whois
from datetime import datetime, timezone
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify

url_scanner_bp = Blueprint("url_scanner", __name__)

# ---------------------------------------------------------------------------
# CONFIG — put real keys in environment variables, never hardcode them
# ---------------------------------------------------------------------------
GOOGLE_SAFE_BROWSING_API_KEY = os.environ.get("GSB_API_KEY", "")
VIRUSTOTAL_API_KEY = os.environ.get("VT_API_KEY", "")

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly", "cutt.ly"
}

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".club", ".work", ".click", ".gq", ".tk", ".ml", ".cf"
}


# ---------------------------------------------------------------------------
# 1. URL STRUCTURE HEURISTICS
# ---------------------------------------------------------------------------
def analyze_structure(url: str) -> dict:
    findings = []
    score = 0
    parsed = urlparse(url)
    host = parsed.hostname or ""

    if parsed.scheme != "https":
        findings.append("URL does not use HTTPS")
        score += 10

    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        findings.append("Domain is a raw IP address, not a real domain name")
        score += 20

    if "xn--" in host:
        findings.append("Domain uses punycode (possible lookalike character trick)")
        score += 20

    subdomain_count = host.count(".")
    if subdomain_count >= 3:
        findings.append("URL has an unusually high number of subdomains")
        score += 10

    if any(host.endswith(s) for s in SHORTENER_DOMAINS):
        findings.append("URL uses a link shortener (real destination is hidden)")
        score += 10

    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        findings.append(f"Domain uses a TLD commonly abused for scams ({host.split('.')[-1]})")
        score += 10

    if "@" in url:
        findings.append("URL contains '@' symbol (can hide the real destination)")
        score += 15

    if re.search(r"%[0-9A-Fa-f]{2}", url):
        findings.append("URL contains encoded characters")
        score += 5

    return {"score": score, "findings": findings}


# ---------------------------------------------------------------------------
# 2. WHOIS DOMAIN AGE
# ---------------------------------------------------------------------------
def analyze_domain_age(host: str) -> dict:
    findings = []
    score = 0
    try:
        w = whois.whois(host)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]

        if creation:
            if creation.tzinfo is None:
                creation = creation.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - creation).days
            if age_days < 30:
                findings.append(f"Domain registered only {age_days} days ago")
                score += 25
            elif age_days < 180:
                findings.append(f"Domain is relatively new ({age_days} days old)")
                score += 10
        else:
            findings.append("Domain registration date could not be verified")
            score += 5
    except Exception:
        findings.append("WHOIS lookup failed (domain may be unregistered or hidden)")
        score += 5

    return {"score": score, "findings": findings}


# ---------------------------------------------------------------------------
# 3. GOOGLE SAFE BROWSING
# ---------------------------------------------------------------------------
def check_safe_browsing(url: str) -> dict:
    if not GOOGLE_SAFE_BROWSING_API_KEY:
        return {"score": 0, "findings": [], "skipped": "No GSB API key configured"}

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_API_KEY}"
    payload = {
        "client": {"clientId": "staysafe", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        resp = requests.post(endpoint, json=payload, timeout=6)
        matches = resp.json().get("matches", [])
        if matches:
            threat_types = {m["threatType"] for m in matches}
            return {
                "score": 40,
                "findings": [f"Google Safe Browsing flagged this URL: {', '.join(threat_types)}"],
            }
        return {"score": 0, "findings": []}
    except Exception:
        return {"score": 0, "findings": ["Safe Browsing check failed"], "error": True}


# ---------------------------------------------------------------------------
# 4. VIRUSTOTAL
# ---------------------------------------------------------------------------
def check_virustotal(url: str) -> dict:
    if not VIRUSTOTAL_API_KEY:
        return {"score": 0, "findings": [], "skipped": "No VirusTotal API key configured"}

    import base64
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    try:
        resp = requests.get(endpoint, headers=headers, timeout=6)
        if resp.status_code == 404:
            # URL not yet analyzed by VT — submit it (result won't be ready instantly)
            requests.post(
                "https://www.virustotal.com/api/v3/urls",
                headers=headers,
                data={"url": url},
                timeout=6,
            )
            return {"score": 0, "findings": ["URL not previously seen by VirusTotal (submitted for analysis)"]}

        stats = resp.json()["data"]["attributes"]["last_analysis_stats"]
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)

        if malicious > 0:
            return {"score": 40, "findings": [f"{malicious} security engines flagged this URL as malicious"]}
        if suspicious > 0:
            return {"score": 15, "findings": [f"{suspicious} security engines flagged this URL as suspicious"]}
        return {"score": 0, "findings": []}
    except Exception:
        return {"score": 0, "findings": ["VirusTotal check failed"], "error": True}


# ---------------------------------------------------------------------------
# RISK ENGINE — combine all signals into one verdict
# ---------------------------------------------------------------------------
def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "DANGEROUS"
    if score >= 20:
        return "CAUTION"
    return "SAFE"


def scan_url(url: str) -> dict:
    parsed = urlparse(url)
    host = parsed.hostname or ""

    structure = analyze_structure(url)
    domain_age = analyze_domain_age(host)
    safe_browsing = check_safe_browsing(url)
    virustotal = check_virustotal(url)

    total_score = min(
        100,
        structure["score"] + domain_age["score"] + safe_browsing["score"] + virustotal["score"],
    )

    all_findings = (
        structure["findings"]
        + domain_age["findings"]
        + safe_browsing["findings"]
        + virustotal["findings"]
    )

    return {
        "url": url,
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings,
        "breakdown": {
            "structure": structure["score"],
            "domain_age": domain_age["score"],
            "safe_browsing": safe_browsing["score"],
            "virustotal": virustotal["score"],
        },
    }


# ---------------------------------------------------------------------------
# FLASK ROUTE
# ---------------------------------------------------------------------------
@url_scanner_bp.route("/api/scan-url", methods=["POST"])
def scan_url_route():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = scan_url(url)

    from scanners.risk_engine import log_scan
    log_scan("url", result)

    return jsonify(result)
