"""
StaySafe - Email Analyzer
------------------------------
User pastes the RAW email source (headers + body) -- most email clients
have a "View Original" / "Show Source" / "Download .eml" option that
gives this. We parse it for:

  1. SPF / DKIM / DMARC authentication results (from the
     Authentication-Results header, which most mail servers add)
  2. From / Reply-To mismatch (classic spoofing tell)
  3. Body text scanned with the same scam-pattern rules as
     the message scanner
  4. Any links in the body scanned with the same risk engine
     as the URL scanner

Register with:
    from email_analyzer import email_analyzer_bp
    app.register_blueprint(email_analyzer_bp)
"""

import re
from email import message_from_string
from email.utils import parseaddr
from flask import Blueprint, request, jsonify

from scanners.message_scanner import analyze_text
from scanners.url_scanner import scan_url
from scanners.risk_engine import log_scan

email_analyzer_bp = Blueprint("email_analyzer", __name__)

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")


def check_auth_results(raw_email: str) -> dict:
    findings = []
    score = 0

    auth_header = ""
    match = re.search(r"Authentication-Results:.*?(?=\n\S|\n\n)", raw_email, re.IGNORECASE | re.DOTALL)
    if match:
        auth_header = match.group(0).lower()

    if not auth_header:
        findings.append("No authentication results found — could not verify sender (may be a stripped/forwarded email)")
        return {"score": 5, "findings": findings}

    if "spf=fail" in auth_header or "spf=softfail" in auth_header:
        findings.append("SPF check failed — sender's server is not authorized to send from this domain")
        score += 25
    if "dkim=fail" in auth_header:
        findings.append("DKIM check failed — email content may have been altered or forged")
        score += 25
    if "dmarc=fail" in auth_header:
        findings.append("DMARC check failed — this email fails the domain's own authentication policy")
        score += 25

    if score == 0:
        findings.append("Email passed sender authentication checks (SPF/DKIM/DMARC)")

    return {"score": score, "findings": findings}


def check_sender_mismatch(msg) -> dict:
    findings = []
    score = 0

    from_addr = parseaddr(msg.get("From", ""))[1].lower()
    reply_to = parseaddr(msg.get("Reply-To", ""))[1].lower()

    if reply_to and from_addr and reply_to != from_addr:
        from_domain = from_addr.split("@")[-1] if "@" in from_addr else ""
        reply_domain = reply_to.split("@")[-1] if "@" in reply_to else ""
        if from_domain != reply_domain:
            findings.append(f"Reply-To address ({reply_to}) doesn't match the From address ({from_addr}) — replies go somewhere different than they appear to")
            score += 25

    return {"score": score, "findings": findings, "from": from_addr, "reply_to": reply_to}


def extract_body(msg) -> str:
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    parts.append(part.get_payload(decode=True).decode(errors="ignore"))
                except Exception:
                    pass
        return "\n".join(parts)
    try:
        return msg.get_payload(decode=True).decode(errors="ignore")
    except Exception:
        return str(msg.get_payload())


def extract_html(msg) -> str:
    """The formatted (HTML) part — where links hidden behind 'Click here' buttons live."""
    parts = []
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            try:
                parts.append(part.get_payload(decode=True).decode(errors="ignore"))
            except Exception:
                pass
    return "\n".join(parts)


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "DANGEROUS"
    if score >= 20:
        return "CAUTION"
    return "SAFE"


@email_analyzer_bp.route("/api/scan-email", methods=["POST"])
def scan_email_route():
    data = request.get_json(silent=True) or {}
    raw_email = data.get("raw_email", "").strip()

    if not raw_email:
        return jsonify({
            "error": "Missing 'raw_email'. Paste the full email source "
                     "(most mail apps: menu > 'Show original' / 'View source')."
        }), 400

    msg = message_from_string(raw_email)
    body = extract_body(msg)
    html = extract_html(msg)
    if not body.strip() and html:
        body = html_to_text(html)  # HTML-only email: read its visible text

    auth_result = check_auth_results(raw_email)
    sender_result = check_sender_mismatch(msg)
    body_result = analyze_text(body)

    # Links from the text AND from the HTML (including ones hidden behind "Click here" buttons)
    urls = []
    for u in URL_PATTERN.findall(body + "\n" + html):
        u = u.rstrip(".,;:!?)]}'\"")
        if u not in urls:
            urls.append(u)
    urls = urls[:5]  # cap at 5 to keep it fast
    url_findings = []
    url_score = 0
    for url in urls:
        result = scan_url(url)
        if result["verdict"] != "SAFE":
            url_findings.append(f"Link found is risky ({result['verdict']}): {url}")
            url_score = max(url_score, result["risk_score"] // 2)  # don't double-count fully

    total_score = min(
        100,
        auth_result["score"] + sender_result["score"] + (body_result["risk_score"] // 2) + url_score,
    )

    all_findings = (
        auth_result["findings"]
        + sender_result["findings"]
        + [f"Message body pattern: {p}" for p in body_result["patterns_detected"]]
        + url_findings
    )

    result = {
        "from": sender_result["from"],
        "reply_to": sender_result["reply_to"],
        "links_found": urls,
        "links_found_count": len(urls),
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings or ["No strong risk indicators found"],
    }

    log_scan("email", result)
    return jsonify(result)
