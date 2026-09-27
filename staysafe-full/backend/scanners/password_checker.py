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
    "123456", "password", "123456789", "12345678", "12345", "qwerty", "abc123", "password1",
    "admin", "letmein", "welcome", "monkey", "iloveyou", "111111", "123123", "sunshine",
    "princess", "football", "1234567890", "000000", "qwerty123", "1q2w3e4r", "dragon",
    "india123", "india@123", "admin@123", "pass@123", "password@123", "welcome@123",
}

# Common words people build passwords around (checked after removing digits/symbols)
COMMON_BASE_WORDS = {
    "password", "passw0rd", "qwerty", "admin", "welcome", "letmein", "iloveyou", "india",
    "sunshine", "princess", "football", "cricket", "monkey", "dragon", "master", "login",
    "abc", "abcd", "test", "user", "hello", "love", "god", "krishna", "ganesh", "shiva",
    "ram", "sairam", "jaishreeram", "mother", "baby", "qwertyuiop", "asdf", "zxcv",
}

LEET = str.maketrans({"@": "a", "4": "a", "0": "o", "1": "i", "!": "i", "3": "e", "$": "s", "5": "s", "7": "t"})

SEQUENCES = [
    "0123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiop", "asdfghjkl", "zxcvbnm", "1qaz2wsx", "1q2w3e4r",
]


def has_sequence(pw: str, length: int = 4) -> bool:
    low = pw.lower()
    for seq in SEQUENCES:
        for i in range(len(seq) - length + 1):
            chunk = seq[i:i + length]
            if chunk in low or chunk[::-1] in low:
                return True
    return False


def analyze_strength(password: str) -> dict:
    findings = []
    score = 100  # start high, deduct for weaknesses
    length = len(password)
    lower = password.lower()

    if length < 8:
        findings.append("Password is shorter than 8 characters")
        score -= 40
    elif length < 12:
        findings.append("Use 12 or more characters for stronger protection")
        score -= 15

    # strip leading/trailing digits+symbols, then undo leetspeak: "P@ssw0rd2024!" -> "password"
    core = re.sub(r"^[^a-z@$]+|[^a-z]+$", "", lower)
    base = re.sub(r"[^a-z]", "", core.translate(LEET))
    if lower in COMMON_PASSWORDS:
        findings.append("This is one of the most commonly used passwords in the world")
        score -= 60
    elif length >= 6 and (base in COMMON_BASE_WORDS or re.sub(r"[^a-z]", "", lower) in COMMON_BASE_WORDS):
        findings.append("It's a very common word with numbers or symbols added (e.g. Password@123) — attackers try these first")
        score -= 45

    # Missing character types matter less for long passphrases
    class_penalty = 5 if length >= 16 else 10
    classes = [
        (r"[A-Z]", "No uppercase letters"),
        (r"[a-z]", "No lowercase letters"),
        (r"[0-9]", "No numbers"),
        (r"[^A-Za-z0-9]", "No special characters"),
    ]
    for pattern, message in classes:
        if not re.search(pattern, password):
            findings.append(message)
            score -= class_penalty

    if re.search(r"(.)\1{2,}", password):
        findings.append("Contains repeated characters (e.g. 'aaa')")
        score -= 10

    if has_sequence(password):
        findings.append("Contains a predictable sequence (like 1234, abcd or qwerty)")
        score -= 15

    if re.search(r"(19[5-9]\d|20[0-3]\d)[^0-9]*$", password):
        findings.append("Ends with a year (like a birth year) — easy to guess if someone knows you")
        score -= 10

    if re.fullmatch(r"[A-Za-z]+[^A-Za-z0-9]?\d{1,4}[^A-Za-z0-9]?", password) and length < 14:
        findings.append("Follows the very common pattern Word + symbol + numbers")
        score -= 10

    score = max(0, min(100, score))

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
        return jsonify({"error": "Please type a password to check."}), 400

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
