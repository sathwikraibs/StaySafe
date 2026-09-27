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
        findings.append("No authentication results found. Could not verify sender (may be a stripped/forwarded email)")
        return {"score": 5, "findings": findings, "status": "skip"}

    if "spf=fail" in auth_header or "spf=softfail" in auth_header:
        findings.append("SPF check failed. Sender's server is not authorized to send from this domain")
        score += 25
    if "dkim=fail" in auth_header:
        findings.append("DKIM check failed. Email content may have been altered or forged")
        score += 25
    if "dmarc=fail" in auth_header:
        findings.append("DMARC check failed. This email fails the domain's own authentication policy")
        score += 25

    failed = sum(f"{k}=fail" in auth_header for k in ("spf", "dkim", "dmarc")) + ("spf=softfail" in auth_header)
    if score == 0:
        findings.append("Email passed sender authentication checks (SPF/DKIM/DMARC)")

    return {"score": score, "findings": findings, "status": "pass" if score == 0 else "fail", "failed": failed}


def check_sender_mismatch(msg) -> dict:
    findings = []
    score = 0

    from_addr = parseaddr(msg.get("From", ""))[1].lower()
    reply_to = parseaddr(msg.get("Reply-To", ""))[1].lower()

    if reply_to and from_addr and reply_to != from_addr:
        from_domain = from_addr.split("@")[-1] if "@" in from_addr else ""
        reply_domain = reply_to.split("@")[-1] if "@" in reply_to else ""
        if from_domain != reply_domain:
            findings.append(f"Reply-To address ({reply_to}) doesn't match the From address ({from_addr}). Replies go somewhere different than they appear to")
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
    """The formatted (HTML) part. Where links hidden behind 'Click here' buttons live."""
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


FREE_MAIL = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "ymail.com", "outlook.com", "hotmail.com",
    "live.com", "rediffmail.com", "proton.me", "protonmail.com", "aol.com", "icloud.com", "zohomail.in",
    "mail.com", "gmx.com", "yandex.com", "tutanota.com",
}
COMPANY_WORDS = re.compile(
    r"\b(bank|support|customer care|helpdesk|service|kyc|income tax|police|cyber ?cell|courier|delivery|refund|"
    r"security|team|official|government|govt|department|rbi|npci|uidai|trai|electricity|admin)\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
FIND_EMAIL = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


def split_sender(raw: str):
    """
    'ManageEngine <itom-promotions@itominfo.manageengine.com'  ->  ('ManageEngine', 'itom-promotions@...')
    Works with missing brackets, quotes, 'From:' and 'mailto:' in front, extra spaces.
    """
    raw = (raw or "").strip()
    m = FIND_EMAIL.search(raw)
    if not m:
        return "", ""
    email = m.group(0).strip(".'").lower()
    name = (raw[:m.start()] + " " + raw[m.end():])
    name = re.sub(r"(?i)\b(from|sender|mailto)\s*:", " ", name)
    name = re.sub(r"[<>\"'()\[\]]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" ,;:.-")
    return name[:120], email


def check_sender_identity(from_name: str, from_addr: str) -> dict:
    """Does the sender's name match the address it really comes from?"""
    from scanners.url_scanner import analyze_structure, BRANDS, brand_name, registered_domain
    findings, score, status, value = [], 0, "pass", None
    domain = from_addr.split("@")[-1].lower() if "@" in from_addr else ""
    if not domain:
        return {"score": 0, "findings": [], "status": "skip", "value": None}
    name_l = (from_name or "").lower()
    brand = next((b for b in BRANDS if len(b) >= 3 and re.search(rf"\b{re.escape(b)}\b", name_l.replace(" ", "")) or
                  (len(b) >= 4 and b in name_l.replace(" ", ""))), None)
    reg = registered_domain(domain)
    official = brand and any(reg == d or domain.endswith("." + d) for d in BRANDS[brand])

    if domain in FREE_MAIL and (brand or COMPANY_WORDS.search(name_l)):
        who = brand_name(brand) if brand else from_name.strip()
        findings.append(f"The sender calls themselves '{who}' but writes from a free {domain} address. Real companies use their own email address")
        score += 35
        status, value = "fail", domain
    elif brand and not official:
        findings.append(f"The sender's name says {brand_name(brand)}, but the email does not come from {brand_name(brand)}'s real address ({domain})")
        score += 35
        status, value = "fail", domain
    if re.search(r"[^@\s]+@[^@\s]+", from_name or ""):
        other = re.search(r"[^@\s<>\"']+@[^@\s<>\"']+", from_name).group(0).lower()
        if other != from_addr.lower():
            findings.append(f"The sender's name shows a different email address ({other}) from the real one ({from_addr})")
            score += 25
            status, value = "fail", from_addr

    structure = analyze_structure("https://" + domain)
    risky = [f for f in structure["findings"] if not f.startswith("Page is hosted")]
    if structure["score"] >= 20 and domain not in FREE_MAIL:
        findings.extend(f"Sender address: {f}" for f in risky[:2])
        score += min(40, structure["score"])
        status, value = "fail", domain
    if status == "pass":
        value = domain
    return {"score": score, "findings": findings, "status": status, "value": value}


@email_analyzer_bp.route("/api/scan-email", methods=["POST"])
def scan_email_route():
    data = request.get_json(silent=True) or {}
    raw_email = (data.get("raw_email") or "").strip()
    form_mode = False

    if not raw_email:
        # The simple form: sender, subject and message typed or pasted into separate boxes
        name_in, sender = split_sender(data.get("sender_email") or "")
        body_in = (data.get("body") or "").strip()
        if not body_in and not sender:
            return jsonify({"error": "Please fill in the sender's email address and paste the message."}), 400
        if (data.get("sender_email") or "").strip() and not sender:
            return jsonify({"error": "That sender email address doesn't look right. It should look like name@example.com"}), 400
        name = ((data.get("sender_name") or "").strip() or name_in).replace("\n", " ")[:120]
        reply = split_sender(data.get("reply_to") or "")[1]
        subject = (data.get("subject") or "").strip().replace("\n", " ")[:300]
        raw_email = (f"From: {name} <{sender}>\n" if name else f"From: {sender}\n")
        if reply:
            raw_email += f"Reply-To: {reply}\n"
        raw_email += f"Subject: {subject}\nContent-Type: text/plain; charset=utf-8\n\n{subject}\n{body_in}"
        form_mode = True

    msg = message_from_string(raw_email)
    body = extract_body(msg)
    html = extract_html(msg)
    if not body.strip() and html:
        body = html_to_text(html)  # HTML-only email: read its visible text

    auth_result = check_auth_results(raw_email)
    if form_mode:
        # the form has no technical headers, so this check simply isn't possible (not a warning sign)
        auth_result = {"score": 0, "findings": [], "status": "info"}
    sender_result = check_sender_mismatch(msg)
    from email.utils import parseaddr as _parse
    from_name, from_addr = _parse(msg.get("From", ""))
    identity = check_sender_identity(from_name, from_addr.lower())
    body_result = analyze_text(body)

    # Links from the text AND from the HTML (including ones hidden behind "Click here" buttons)
    urls = []
    for u in URL_PATTERN.findall(body + "\n" + html):
        u = u.rstrip(".,;:!?)]}'\"")
        if u not in urls:
            urls.append(u)
    urls = urls[:5]  # cap at 5 to keep it fast
    from scanners.url_scanner import LINK_POOL
    futures = [(u, LINK_POOL.submit(scan_url, u)) for u in urls]
    url_findings = []
    url_score = 0
    risky_links = 0
    link_results = []
    for url, future in futures:
        try:
            result = future.result(timeout=25)
        except Exception:
            continue
        link_results.append({"url": url, "verdict": result["verdict"], "risk_score": result["risk_score"],
                             "findings": result["findings"], "checks": result.get("checks", []),
                             "details": result.get("details", {})})
        if result["verdict"] != "SAFE":
            risky_links += 1
            word = "dangerous" if result["verdict"] == "DANGEROUS" else "suspicious"
            url_findings.append(f"This link in the email looks {word}: {url}")
            # a link on a blocklist makes the whole email risky
            url_score = max(url_score, result["risk_score"] if result["risk_score"] >= 90 else result["risk_score"] // 2)

    total_score = min(
        100,
        auth_result["score"] + sender_result["score"] + identity["score"] + (body_result["risk_score"] // 2) + url_score,
    )

    all_findings = (
        identity["findings"]
        + auth_result["findings"]
        + sender_result["findings"]
        + [f"In the email text: {p}" for p in body_result["patterns_detected"]]
        + url_findings
    )

    patterns = len(body_result["patterns_detected"])
    checks = [
        {"id": "email_sender", "status": identity["status"], "value": identity["value"]},
        {"id": "email_auth", "status": auth_result["status"], "value": auth_result.get("failed")},
        {"id": "email_reply", "status": "warn" if sender_result["score"] else "pass",
         "value": sender_result["reply_to"] or None},
        {"id": "email_words", "status": "fail" if patterns >= 2 else ("warn" if patterns else "pass"), "value": patterns},
        {"id": "email_links", "status": ("fail" if risky_links else "pass") if urls else "info",
         "value": risky_links if risky_links else len(urls)},
    ]

    result = {
        "from": sender_result["from"],
        "from_name": from_name,
        "mode": "form" if form_mode else "source",
        "reply_to": sender_result["reply_to"],
        "subject": (msg.get("Subject") or "")[:200],
        "links_found": urls,
        "links_found_count": len(urls),
        "links_checked": link_results,
        "risk_score": total_score,
        "verdict": verdict_from_score(total_score),
        "findings": all_findings or ["No strong risk indicators found"],
        "checks": checks,
    }

    log_scan("email", result)
    return jsonify(result)
