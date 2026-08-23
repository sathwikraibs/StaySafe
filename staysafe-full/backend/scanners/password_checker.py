"""
StaySafe - Password Health & Breach Checker
----------------------------------------------
Two checks, both privacy-safe:

1. Password strength -- checked with local rules only, password
   NEVER leaves the server in this function.

2. Breach check -- uses Have I Been Pwned's k-anonymity API.
   We only send the FIRST 5 CHARACTERS of the password's SHA-1 hash,
   never the password or full hash itself. This is the same technique
   HIBP recommends and 1Password/Firefox Monitor use.

Register with:
    from password_checker import password_checker_bp
    app.register_blueprint(password_checker_bp)
"""

import re
import hashlib
import requests
from flask import Blueprint, request, jsonify

password_checker_bp = Blueprint("password_checker", __name__)

COMMON_PASSWORDS = {
    "123456", "password", "123456789", "12345678", "12345", "qwerty",
    "abc123", "password1", "admin", "letmein", "welcome", "monkey",
    "iloveyou", "111111", "123123", "sunshine", "princess", "football",
}


def analyze_strength(password: str) -> dict:
    findings = []
    score = 100  # start high, deduct for weaknesses

    if len(password) < 8:
        findings.append("Password is shorter than 8 characters")
        score -= 30
    elif len(password) < 12:
        findings.append("Consider using 12+ characters for stronger protection")
        score -= 10

    if password.lower() in COMMON_PASSWORDS:
        findings.append("This is one of the most commonly used passwords in the world")
        score -= 50

    if not re.search(r"[A-Z]", password):
        findings.append("No uppercase letters")
        score -= 10
    if not re.search(r"[a-z]", password):
        findings.append("No lowercase letters")
        score -= 10
    if not re.search(r"[0-9]", password):
        findings.append("No numbers")
        score -= 10
    if not re.search(r"[^A-Za-z0-9]", password):
        findings.append("No special characters")
        score -= 10

    if re.search(r"(.)\1{2,}", password):
        findings.append("Contains repeated characters (e.g. 'aaa')")
        score -= 10

    if re.search(r"(0123|1234|2345|3456|4567|5678|6789|abcd|qwerty)", password.lower()):
        findings.append("Contains a predictable sequence")
        score -= 15

    score = max(0, score)

    if score >= 80:
        strength = "Strong"
    elif score >= 50:
        strength = "Moderate"
    else:
        strength = "Weak"

    if not findings:
        findings.append("No obvious weaknesses found")

    return {"strength_score": score, "strength_label": strength, "findings": findings}


def check_breach(password: str) -> dict:
    """
    k-anonymity breach check: hash the password with SHA-1, send only the
    first 5 hex characters to HIBP, and check locally if the rest matches
    any returned suffix. The full password/hash never leaves this server.
    """
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        resp = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"Add-Padding": "true"},
            timeout=6,
        )
        if resp.status_code != 200:
            return {"breached": None, "count": 0, "error": "Breach check service unavailable"}

        for line in resp.text.splitlines():
            hash_suffix, count = line.split(":")
            if hash_suffix == suffix:
                return {"breached": True, "count": int(count)}

        return {"breached": False, "count": 0}
    except Exception:
        return {"breached": None, "count": 0, "error": "Breach check failed"}


@password_checker_bp.route("/api/check-password", methods=["POST"])
def check_password_route():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if not password:
        return jsonify({"error": "Missing 'password' in request body"}), 400

    strength = analyze_strength(password)
    breach = check_breach(password)

    findings = list(strength["findings"])
    risk_score = 100 - strength["strength_score"]

    if breach.get("breached") is True:
        findings.insert(0, f"This password has appeared in {breach['count']:,} known data breaches — change it everywhere you use it")
        risk_score = max(risk_score, 70)
    elif breach.get("breached") is False:
        findings.append("Not found in any known breach database")

    verdict = "DANGEROUS" if risk_score >= 50 else ("CAUTION" if risk_score >= 20 else "SAFE")

    return jsonify({
        "risk_score": min(100, risk_score),
        "verdict": verdict,
        "strength_label": strength["strength_label"],
        "breached": breach.get("breached"),
        "breach_count": breach.get("count", 0),
        "findings": findings,
    })


@password_checker_bp.route("/api/check-email-breach", methods=["POST"])
def check_email_breach_route():
    """
    Note: HIBP's email breach API requires a paid API key as of their
    current pricing. This endpoint is scaffolded and ready --
    just add your key to HIBP_API_KEY below once you have one.
    Leave it out of your MVP demo if you don't want to pay for it;
    the password breach check above is completely free.
    """
    import os
    HIBP_API_KEY = os.environ.get("HIBP_API_KEY", "")

    if not HIBP_API_KEY:
        return jsonify({
            "error": "Email breach check requires a paid HIBP API key. "
                     "The password breach check (/api/check-password) is free and doesn't need one."
        }), 501

    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    if not email:
        return jsonify({"error": "Missing 'email' in request body"}), 400

    try:
        resp = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={"hibp-api-key": HIBP_API_KEY},
            timeout=8,
        )
        if resp.status_code == 404:
            return jsonify({"breached": False, "breaches": []})
        breaches = resp.json()
        return jsonify({
            "breached": True,
            "breach_count": len(breaches),
            "breaches": [b["Name"] for b in breaches],
        })
    except Exception:
        return jsonify({"error": "Breach check failed"}), 500
