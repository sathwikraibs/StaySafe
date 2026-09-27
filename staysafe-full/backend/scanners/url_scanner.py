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
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "rebrand.ly", "cutt.ly", "t.ly", "rb.gy", "shorturl.at", "tiny.cc", "s.id",
}

SUSPICIOUS_TLDS = {
    "xyz", "top", "club", "work", "click", "gq", "tk", "ml", "cf", "ga", "live",
    "icu", "buzz", "rest", "sbs", "cfd", "cyou", "monster", "quest", "lol", "vip",
    "support", "shop", "online", "site", "fun", "store", "win", "loan", "bid",
}

# Two-part public suffixes, so "sbi.co.in" is treated as the registered domain
MULTI_PART_SUFFIXES = {
    "co.in", "net.in", "org.in", "gov.in", "nic.in", "ac.in", "edu.in", "res.in", "firm.in", "gen.in", "ind.in",
    "co.uk", "org.uk", "gov.uk", "ac.uk", "com.au", "net.au", "org.au", "co.nz", "com.sg", "com.my",
    "co.jp", "com.br", "com.cn", "co.za", "com.pk", "com.bd", "com.np", "co.id",
}

# Brand keyword -> the real registered domains that brand uses
BRANDS = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "onlinesbi.com", "sbicard.com", "sbi"},
    "onlinesbi": {"onlinesbi.sbi", "onlinesbi.com"},
    "hdfc": {"hdfcbank.com", "hdfc.com", "hdfclife.com", "hdfcsec.com"},
    "icici": {"icicibank.com", "icicidirect.com", "iciciprulife.com"},
    "axisbank": {"axisbank.com"},
    "kotak": {"kotak.com"},
    "paytm": {"paytm.com", "paytm.in", "paytmbank.com"},
    "phonepe": {"phonepe.com"},
    "gpay": {"google.com"},
    "google": {"google.com", "google.co.in", "googleusercontent.com", "youtube.com", "goo.gl"},
    "amazon": {"amazon.in", "amazon.com", "amazonaws.com", "amazon.co.uk"},
    "flipkart": {"flipkart.com"},
    "paypal": {"paypal.com", "paypal.me"},
    "apple": {"apple.com", "icloud.com"},
    "icloud": {"icloud.com", "apple.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com", "outlook.com"},
    "netflix": {"netflix.com"},
    "facebook": {"facebook.com", "fb.com"},
    "instagram": {"instagram.com"},
    "whatsapp": {"whatsapp.com", "whatsapp.net", "wa.me"},
    "irctc": {"irctc.co.in"},
    "uidai": {"uidai.gov.in"},
    "aadhaar": {"uidai.gov.in"},
    "incometax": {"incometax.gov.in"},
    "epfo": {"epfindia.gov.in"},
    "npci": {"npci.org.in"},
    "airtel": {"airtel.in", "airtel.com"},
    "jio": {"jio.com"},
    "indiapost": {"indiapost.gov.in"},
    "fedex": {"fedex.com"},
    "dhl": {"dhl.com", "dhl.co.in"},
    "bluedart": {"bluedart.com"},
    "myntra": {"myntra.com"},
    "swiggy": {"swiggy.com"},
    "zomato": {"zomato.com"},
}

# Popular sites we treat as known-good for the "structure" part of the check
TRUSTED_DOMAINS = set().union(*BRANDS.values()) | {
    "wikipedia.org", "github.com", "linkedin.com", "twitter.com", "x.com", "reddit.com",
    "gov.in", "nic.in", "india.gov.in",
}

# Free hosting where ANYONE can publish a page — never "trusted", even if a brand owns the service
FREE_HOSTING = {
    "vercel.app", "netlify.app", "github.io", "web.app", "firebaseapp.com", "herokuapp.com",
    "onrender.com", "blogspot.com", "wixsite.com", "weebly.com", "000webhostapp.com", "pages.dev",
    "workers.dev", "ngrok.io", "ngrok-free.app", "glitch.me", "replit.app", "repl.co",
    "googleusercontent.com", "amazonaws.com", "sites.google.com", "forms.gle",
}
TRUSTED_DOMAINS -= FREE_HOSTING

PHISHING_WORDS = {
    "login", "signin", "sign-in", "verify", "verification", "update", "secure", "security",
    "account", "kyc", "banking", "wallet", "reward", "rewards", "bonus", "gift", "free",
    "claim", "refund", "prize", "support", "helpdesk", "unlock", "confirm", "suspend",
}

LOOKALIKE_MAP = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s"})


def registered_domain(host: str) -> str:
    """'netbanking.hdfcbank.com' -> 'hdfcbank.com', 'www.sbi.co.in' -> 'sbi.co.in'."""
    host = host.lower().strip(".")
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in (MULTI_PART_SUFFIXES | FREE_HOSTING):
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def is_ip(host: str) -> bool:
    return re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host or "") is not None


# ---------------------------------------------------------------------------
# 1. URL STRUCTURE HEURISTICS
# ---------------------------------------------------------------------------
def analyze_structure(url: str) -> dict:
    findings = []
    score = 0
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path + "?" + parsed.query).lower()

    if parsed.scheme != "https":
        findings.append("Link does not use HTTPS (the connection is not encrypted)")
        score += 10

    if is_ip(host):
        findings.append("Link uses a raw IP address instead of a real website name")
        score += 25
        return {"score": score, "findings": findings, "trusted": False, "hosting": False}

    reg = registered_domain(host)
    trusted = reg in TRUSTED_DOMAINS or host.endswith(".gov.in") or host.endswith(".nic.in")
    hosting = next((h for h in FREE_HOSTING if host == h or host.endswith("." + h)), None)
    if hosting:
        trusted = False
        findings.append(f"Page is hosted on a free hosting service ({hosting}) where anyone can publish — check who made it")
        score += 10
    subdomain_part = host[: -len(reg)].rstrip(".") if host.endswith(reg) else ""
    name_part = reg.split(".")[0]

    if "xn--" in host:
        findings.append("Website name uses special look-alike characters (punycode) to imitate another site")
        score += 30

    # Brand impersonation: a brand name appears, but this isn't that brand's real site
    if not trusted:
        host_compact = host.replace("-", "")
        host_lookalike = host_compact.translate(LOOKALIKE_MAP)
        for brand, official in BRANDS.items():
            if any(host == d or host.endswith("." + d) for d in official):
                continue  # e.g. s3.amazonaws.com really is run by Amazon
            if len(brand) <= 3:
                # short names like "sbi"/"jio" only count as a separate word: sbi-kyc.in, jio.offer.xyz
                hit_plain = re.search(rf"(^|[.\-]){brand}([.\-]|$)", host) is not None
                hit_lookalike = False
            else:
                hit_plain = brand in host_compact
                hit_lookalike = not hit_plain and brand in host_lookalike
            if hit_plain or hit_lookalike:
                how = "uses look-alike characters to imitate" if hit_lookalike else "mentions"
                findings.append(f"Link {how} '{brand}' but is NOT {brand}'s official website ({reg})")
                score += 50 if hit_lookalike else 40
                break

    if not trusted:
        words_in_host = [w for w in PHISHING_WORDS if w in host]
        if words_in_host:
            findings.append(f"Website name contains words scammers love: {', '.join(sorted(words_in_host)[:3])}")
            score += 15
        elif any(w in path for w in ("login", "verify", "kyc", "update-account", "signin")):
            findings.append("Link leads to a login or verification page — never enter details from a link you were sent")
            score += 5

        if subdomain_part.count(".") >= 2:
            findings.append("Link has an unusually long chain of sub-domains (a trick to hide the real site)")
            score += 10

        if "xn--" not in name_part and name_part.count("-") >= 2:
            findings.append("Website name has several hyphens, common in fake sites")
            score += 5

        if len(host) > 40:
            findings.append("Website name is unusually long")
            score += 5

    tld = reg.rsplit(".", 1)[-1]
    if tld in SUSPICIOUS_TLDS:
        findings.append(f"Website ending '.{tld}' is cheap and often used for scams")
        score += 15

    if reg in SHORTENER_DOMAINS:
        findings.append("Link uses a link shortener, so the real destination is hidden")
        score += 15

    if "@" in (parsed.netloc or ""):
        findings.append("Link contains an '@' symbol, which can hide the real destination")
        score += 20

    if path.endswith(".apk") or ".apk?" in path:
        findings.append("Link downloads an Android app (.apk) from outside the Play Store — a common way to steal OTPs")
        score += 40

    if re.search(r"%[0-9a-f]{2}", host):
        findings.append("Website name contains hidden encoded characters")
        score += 10

    return {"score": score, "findings": findings, "trusted": trusted, "hosting": bool(hosting)}


# ---------------------------------------------------------------------------
# 2. WHOIS DOMAIN AGE
# ---------------------------------------------------------------------------
def analyze_domain_age(host: str) -> dict:
    findings = []
    score = 0
    if not host or is_ip(host):
        return {"score": 0, "findings": []}
    domain = registered_domain(host)
    try:
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = min(c for c in creation if c)

        if creation:
            if creation.tzinfo is None:
                creation = creation.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - creation).days
            if age_days < 30:
                findings.append(f"Website was created only {age_days} days ago — very new sites are a big warning sign")
                score += 30
            elif age_days < 180:
                findings.append(f"Website is fairly new ({age_days} days old)")
                score += 10
        else:
            findings.append("Could not confirm when this website was created")
            score += 5
    except Exception:
        findings.append("Could not look up this website's registration details")
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
    # WHOIS is meaningless for well-known sites and for pages on shared hosting (e.g. x.vercel.app)
    skip_whois = structure["trusted"] or structure["hosting"]
    domain_age = {"score": 0, "findings": []} if skip_whois else analyze_domain_age(host)
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
        return jsonify({"error": "Please paste the link you want to check."}), 400
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    host = urlparse(url).hostname or ""
    if "." not in host:
        return jsonify({"error": "That doesn't look like a website link. Try something like example.com"}), 400

    result = scan_url(url)

    from scanners.risk_engine import log_scan
    log_scan("url", result)

    return jsonify(result)
