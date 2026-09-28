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


def crack_time_seconds(password: str):
    """Seconds a real attacker would need (zxcvbn, slow-hash offline attack), or None if unavailable."""
    try:
        from zxcvbn import zxcvbn
    except Exception:
        return None
    try:
        result = zxcvbn(password[:72])
        return float(result["crack_times_seconds"]["offline_slow_hashing_1e4_per_second"])
    except Exception:
        return None


def analyze_strength(password: str) -> dict:
    findings = []
    score = 100  # start high, deduct for weaknesses
    from scanners.ledger import Ledger
    led = Ledger()  # each weakness and how much risk it adds
    length = len(password)
    lower = password.lower()

    if length < 8:
        findings.append("Password is shorter than 8 characters")
        score -= led.note(findings, 40)
    elif length < 12:
        findings.append("Use 12 or more characters for stronger protection")
        score -= led.note(findings, 15)

    # strip leading/trailing digits+symbols, then undo leetspeak: "P@ssw0rd2024!" -> "password"
    core = re.sub(r"^[^a-z@$]+|[^a-z]+$", "", lower)
    base = re.sub(r"[^a-z]", "", core.translate(LEET))
    if lower in COMMON_PASSWORDS:
        findings.append("This is one of the most commonly used passwords in the world")
        score -= led.note(findings, 60)
    elif length >= 6 and (base in COMMON_BASE_WORDS or re.sub(r"[^a-z]", "", lower) in COMMON_BASE_WORDS):
        findings.append("It's a very common word with numbers or symbols added (e.g. Password@123). Attackers try these first")
        score -= led.note(findings, 45)

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
            score -= led.note(findings, class_penalty)

    if re.search(r"(.)\1{2,}", password):
        findings.append("Contains repeated characters (e.g. 'aaa')")
        score -= led.note(findings, 10)

    if has_sequence(password):
        findings.append("Contains a predictable sequence (like 1234, abcd or qwerty)")
        score -= led.note(findings, 15)

    if re.search(r"(19[5-9]\d|20[0-3]\d)[^0-9]*$", password):
        findings.append("Ends with a year (like a birth year). Easy to guess if someone knows you")
        score -= led.note(findings, 10)

    if re.fullmatch(r"[A-Za-z]+[^A-Za-z0-9]?\d{1,4}[^A-Za-z0-9]?", password) and length < 14:
        findings.append("Follows the very common pattern Word + symbol + numbers")
        score -= led.note(findings, 10)

    # zxcvbn (Dropbox's realistic password-guessing model): how long a real attacker with a
    # leaked password database would need. Catches names, dates, keyboard walks and words we miss.
    crack = crack_time_seconds(password)
    crack_bucket = None
    if crack is not None:
        if crack < 60:
            crack_bucket = "minute"
            findings.append("A computer could guess this password in under a minute")
            led.note(findings, max(0, score - 25))
            score = min(score, 25)
        elif crack < 86400:
            crack_bucket = "day"
            findings.append("A computer could guess this password in less than a day")
            led.note(findings, max(0, score - 45))
            score = min(score, 45)
        elif crack < 30 * 86400:
            crack_bucket = "month"
            findings.append("A computer could guess this password in less than a month")
            led.note(findings, max(0, score - 65))
            score = min(score, 65)
        elif crack < 10 * 365 * 86400:
            crack_bucket = "years"
        else:
            crack_bucket = "centuries"

    score = max(0, min(100, score))

    if score >= 80:
        strength = "Strong"
    elif score >= 50:
        strength = "Moderate"
    else:
        strength = "Weak"

    if not findings:
        findings.append("No obvious weaknesses found")

    missing = sum(1 for pattern, _ in classes if not re.search(pattern, password))
    common = lower in COMMON_PASSWORDS or any(f.startswith("It's a very common word") for f in findings)
    patterns = sum(1 for f in findings if f.startswith(("Contains repeated", "Contains a predictable", "Ends with a year", "Follows the very common")))
    checks = [
        {"id": "pw_length", "status": "pass" if length >= 12 else ("warn" if length >= 8 else "fail"), "value": length},
        {"id": "pw_common", "status": "fail" if common else "pass", "value": None},
        {"id": "pw_variety", "status": "pass" if missing == 0 else ("warn" if missing <= 2 else "fail"), "value": 4 - missing},
        {"id": "pw_patterns", "status": "pass" if patterns == 0 else ("warn" if patterns == 1 else "fail"), "value": patterns},
    ]
    if crack_bucket:
        checks.insert(0, {"id": "pw_crack", "status": {"minute": "fail", "day": "fail", "month": "warn"}.get(crack_bucket, "pass"),
                          "value": crack_bucket})
    return {"strength_score": score, "strength_label": strength, "findings": findings, "checks": checks,
            "parts": led.parts}


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

    from scanners.ledger import Ledger
    led = Ledger(strength.get("parts"))
    if breach.get("breached") is True:
        findings.insert(0, f"This password has appeared in {breach['count']:,} known data breaches. Change it everywhere you use it")
        led.add(findings[0], max(risk_score, 70) - risk_score)
        risk_score = max(risk_score, 70)
    elif breach.get("breached") is False:
        findings.append("Not found in any known breach database")

    verdict = "DANGEROUS" if risk_score >= 50 else ("CAUTION" if risk_score >= 20 else "SAFE")
    leak = breach.get("breached")
    checks = [{"id": "pw_leaks", "status": "fail" if leak else ("pass" if leak is False else "skip"),
               "value": breach.get("count") or None}] + strength["checks"]

    return jsonify({
        "checks": checks,
        "strength_score": strength["strength_score"],
        "length": len(password),
        "risk_score": min(100, risk_score),
        "verdict": verdict,
        "strength_label": strength["strength_label"],
        "breached": breach.get("breached"),
        "breach_count": breach.get("count", 0),
        "findings": findings,
        "score_parts": led.result(min(100, risk_score)),
    })


_BREACH_CACHE: dict = {}      # sha256(email) -> (expires, result)
_BREACH_RATE: dict = {}       # visitor IP -> [times]  (the free services' limits are shared by everyone)


def _breach_lookup(email: str) -> dict:
    """
    Which data leaks an email address appears in. Free sources, tried in order:
      1. Have I Been Pwned (only if HIBP_API_KEY is set; paid)
      2. XposedOrNot (free, no key, about 100 lookups a day)
      3. LeakCheck public API (free, no key; asks for a "Powered by LeakCheck" credit)
    Only the names of the leaks and the kinds of data leaked are returned, never the data itself.
    """
    import os
    key = os.environ.get("HIBP_API_KEY", "")
    if key:
        try:
            resp = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{requests.utils.quote(email)}",
                                headers={"hibp-api-key": key, "user-agent": "StaySafe"}, timeout=8)
            if resp.status_code == 404:
                return {"breached": False, "breaches": [], "source": "Have I Been Pwned"}
            if resp.status_code == 200:
                return {"breached": True, "breaches": [b["Name"] for b in resp.json()], "source": "Have I Been Pwned"}
        except Exception:
            pass
    try:
        resp = requests.get(f"https://api.xposedornot.com/v1/check-email/{requests.utils.quote(email)}",
                            timeout=8, headers={"User-Agent": "StaySafe/2.0"})
        if resp.status_code == 404:
            return {"breached": False, "breaches": [], "source": "XposedOrNot"}
        if resp.status_code == 200:
            data = resp.json()
            names = []

            def walk(x):
                if isinstance(x, str):
                    names.append(x)
                elif isinstance(x, (list, tuple)):
                    for y in x:
                        walk(y)
            walk(data.get("breaches", []))
            if names:
                return {"breached": True, "breaches": sorted(set(names))[:40], "source": "XposedOrNot"}
            if str(data.get("Error", "")).lower() == "not found" or data.get("status") == "success":
                return {"breached": False, "breaches": [], "source": "XposedOrNot"}
    except Exception:
        pass
    try:
        resp = requests.get("https://leakcheck.io/api/public", params={"check": email}, timeout=8,
                            headers={"User-Agent": "StaySafe/2.0"})
        data = resp.json()
        if data.get("success") and data.get("found"):
            names = [str(src.get("name", "")).strip() for src in data.get("sources", []) if isinstance(src, dict)]
            return {"breached": True, "breaches": sorted({n for n in names if n})[:40],
                    "fields": [str(f) for f in data.get("fields", [])][:12], "source": "LeakCheck"}
        if data.get("success") is False and "not found" in str(data.get("error", "")).lower():
            return {"breached": False, "breaches": [], "source": "LeakCheck"}
    except Exception:
        pass
    return {"error": True}


@password_checker_bp.route("/api/check-email-breach", methods=["POST"])
def check_email_breach_route():
    import time
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email):
        return jsonify({"error": "Please enter a full email address, like name@example.com"}), 400

    ip = (request.headers.get("X-Forwarded-For", request.remote_addr or "") or "").split(",")[0].strip()
    now = time.time()
    recent = [t for t in _BREACH_RATE.get(ip, []) if now - t < 3600]
    if len(recent) >= 10:
        return jsonify({"error": "You've checked a lot of addresses. Please try again in an hour."}), 429
    _BREACH_RATE[ip] = recent + [now]

    cache_key = hashlib.sha256(email.encode()).hexdigest()
    hit = _BREACH_CACHE.get(cache_key)
    if hit and hit[0] > now:
        return jsonify(hit[1])
    result = _breach_lookup(email)
    if result.get("error"):
        return jsonify({"error": "The data-leak check isn't available right now. Please try again later."}), 503
    result["breach_count"] = len(result["breaches"])
    _BREACH_CACHE[cache_key] = (now + 24 * 3600, result)
    if len(_BREACH_CACHE) > 5000:
        _BREACH_CACHE.clear()
    return jsonify(result)
