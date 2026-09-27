"""
StaySafe - Link (URL) checker
-------------------------------
Checks a web address step by step and explains every step:

  1. The address itself: fake brand names, look-alike spellings, risky endings,
     free hosting, link shorteners, raw IP addresses.
  2. Does the website exist at all? (DNS lookup)
  3. How old is the website? (WHOIS, with VirusTotal as a backup source)
  4. Google Safe Browsing blocklist.
  5. VirusTotal (70+ security companies).
  6. We open the page safely on the server (never on the visitor's phone):
     where does the link really lead, is the security certificate valid,
     does the page ask for a password, does it pretend to be a bank or brand?

Every check is returned in `checks` as {id, status, value} so the website can
show a colourful checklist in any language. A hit on a blocklist always makes
the result "risky", whatever the other checks say.
"""

import base64
import ipaddress
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from flask import Blueprint, jsonify, request

try:
    import whois  # python-whois
except Exception:  # pragma: no cover
    whois = None

url_scanner_bp = Blueprint("url_scanner", __name__)

# Keys live in environment variables (Render > Environment), never in code
GOOGLE_SAFE_BROWSING_API_KEY = os.environ.get("GSB_API_KEY", "")
VIRUSTOTAL_API_KEY = os.environ.get("VT_API_KEY", "")

# Tests set this to True so nothing goes to the internet
OFFLINE = False

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Mobile Safari/537.36"
)

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly",
    "cutt.ly", "t.ly", "rb.gy", "shorturl.at", "tiny.cc", "s.id", "v.gd", "shorte.st",
    "adf.ly", "bl.ink", "lnkd.in", "surl.li", "u.to", "clck.ru", "qr.ae", "tiny.one",
}

SUSPICIOUS_TLDS = {
    "xyz", "top", "club", "work", "click", "gq", "tk", "ml", "cf", "ga", "live", "icu",
    "buzz", "rest", "sbs", "cfd", "cyou", "monster", "quest", "lol", "vip", "support",
    "shop", "online", "site", "fun", "store", "win", "loan", "bid", "pw", "cc", "su",
    "kim", "men", "date", "racing", "review", "stream", "download", "gdn", "mom", "zip",
    "mov", "country", "cam", "bond", "ru", "website", "beauty", "hair", "skin", "boats",
}

MULTI_PART_SUFFIXES = {
    "co.in", "net.in", "org.in", "gov.in", "nic.in", "ac.in", "edu.in", "res.in", "firm.in",
    "gen.in", "ind.in", "co.uk", "org.uk", "gov.uk", "ac.uk", "com.au", "net.au", "org.au",
    "co.nz", "com.sg", "com.my", "co.jp", "com.br", "com.cn", "co.za", "com.pk", "com.bd",
    "com.np", "co.id", "bank.in",
}

# Brand keyword -> the real registered domains that brand uses
BRANDS = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "onlinesbi.com", "sbicard.com", "sbi", "sbi.bank.in"},
    "onlinesbi": {"onlinesbi.sbi", "onlinesbi.com"},
    "hdfc": {"hdfcbank.com", "hdfc.com", "hdfclife.com", "hdfcsec.com", "hdfc.bank.in", "hdfcbank.bank.in"},
    "icici": {"icicibank.com", "icicidirect.com", "iciciprulife.com", "icici.bank.in"},
    "axisbank": {"axisbank.com", "axis.bank.in"},
    "kotak": {"kotak.com", "kotak.bank.in"},
    "canarabank": {"canarabank.com", "canarabank.in"},
    "pnb": {"pnbindia.in", "pnb.co.in", "pnb.bank.in"},
    "bankofbaroda": {"bankofbaroda.in", "bankofbaroda.com"},
    "unionbank": {"unionbankofindia.co.in"},
    "yesbank": {"yesbank.in"},
    "paytm": {"paytm.com", "paytm.in", "paytmbank.com"},
    "phonepe": {"phonepe.com"},
    "gpay": {"google.com"},
    "google": {"google.com", "google.co.in", "googleusercontent.com", "youtube.com", "goo.gl", "g.co"},
    "amazon": {"amazon.in", "amazon.com", "amazonaws.com", "amazon.co.uk", "amzn.to", "amzn.in"},
    "flipkart": {"flipkart.com", "fkrt.it"},
    "meesho": {"meesho.com"},
    "paypal": {"paypal.com", "paypal.me"},
    "apple": {"apple.com", "icloud.com"},
    "icloud": {"icloud.com", "apple.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com", "outlook.com", "microsoftonline.com"},
    "netflix": {"netflix.com"},
    "facebook": {"facebook.com", "fb.com", "fb.me"},
    "instagram": {"instagram.com"},
    "whatsapp": {"whatsapp.com", "whatsapp.net", "wa.me"},
    "telegram": {"telegram.org", "t.me"},
    "irctc": {"irctc.co.in"},
    "uidai": {"uidai.gov.in"},
    "aadhaar": {"uidai.gov.in"},
    "incometax": {"incometax.gov.in"},
    "epfo": {"epfindia.gov.in"},
    "npci": {"npci.org.in"},
    "airtel": {"airtel.in", "airtel.com"},
    "jio": {"jio.com"},
    "bsnl": {"bsnl.co.in", "bsnl.in"},
    "indiapost": {"indiapost.gov.in"},
    "fedex": {"fedex.com"},
    "dhl": {"dhl.com", "dhl.co.in"},
    "bluedart": {"bluedart.com"},
    "delhivery": {"delhivery.com"},
    "myntra": {"myntra.com"},
    "swiggy": {"swiggy.com"},
    "zomato": {"zomato.com"},
    "bescom": {"bescom.co.in", "bescom.karnataka.gov.in"},
    "mahadiscom": {"mahadiscom.in"},
    "fastag": {"npci.org.in", "ihmcl.co.in"},
    "parivahan": {"parivahan.gov.in"},
    "echallan": {"parivahan.gov.in"},
}

BRAND_DISPLAY = {
    "sbi": "SBI", "onlinesbi": "SBI", "hdfc": "HDFC Bank", "icici": "ICICI Bank", "axisbank": "Axis Bank",
    "kotak": "Kotak Bank", "canarabank": "Canara Bank", "pnb": "PNB", "bankofbaroda": "Bank of Baroda",
    "unionbank": "Union Bank", "yesbank": "Yes Bank", "paytm": "Paytm", "phonepe": "PhonePe",
    "gpay": "Google Pay", "google": "Google", "amazon": "Amazon", "flipkart": "Flipkart", "meesho": "Meesho",
    "paypal": "PayPal", "apple": "Apple", "icloud": "Apple iCloud", "microsoft": "Microsoft",
    "netflix": "Netflix", "facebook": "Facebook", "instagram": "Instagram", "whatsapp": "WhatsApp",
    "telegram": "Telegram", "irctc": "IRCTC", "uidai": "Aadhaar (UIDAI)", "aadhaar": "Aadhaar (UIDAI)",
    "incometax": "Income Tax Dept", "epfo": "EPFO", "npci": "NPCI", "airtel": "Airtel", "jio": "Jio",
    "bsnl": "BSNL", "indiapost": "India Post", "fedex": "FedEx", "dhl": "DHL", "bluedart": "Blue Dart",
    "delhivery": "Delhivery", "myntra": "Myntra", "swiggy": "Swiggy", "zomato": "Zomato",
    "bescom": "BESCOM", "mahadiscom": "MSEDCL", "fastag": "FASTag", "parivahan": "Parivahan (Transport Dept)",
    "echallan": "e-Challan (Transport Dept)",
}


def brand_name(brand: str) -> str:
    return BRAND_DISPLAY.get(brand, brand.capitalize()) if brand else brand


# Simple names used to spot misspellings like "amazom.in" or "flipkarrt.com"
TYPO_TARGETS = {
    "amazon": "amazon", "flipkart": "flipkart", "paytm": "paytm", "phonepe": "phonepe",
    "google": "google", "facebook": "facebook", "instagram": "instagram", "whatsapp": "whatsapp",
    "netflix": "netflix", "paypal": "paypal", "microsoft": "microsoft", "apple": "apple",
    "hdfcbank": "hdfc", "icicibank": "icici", "axisbank": "axisbank", "onlinesbi": "onlinesbi",
    "irctc": "irctc", "myntra": "myntra", "swiggy": "swiggy", "zomato": "zomato",
    "airtel": "airtel", "indiapost": "indiapost", "incometax": "incometax", "bluedart": "bluedart",
    "delhivery": "delhivery", "meesho": "meesho", "kotak": "kotak", "canarabank": "canarabank",
    "telegram": "telegram", "youtube": "google", "bankofbaroda": "bankofbaroda", "yesbank": "yesbank",
}

TRUSTED_DOMAINS = set().union(*BRANDS.values()) | {
    "wikipedia.org", "github.com", "linkedin.com", "twitter.com", "x.com", "reddit.com",
    "gov.in", "nic.in", "india.gov.in", "rbi.org.in", "cybercrime.gov.in", "stackoverflow.com",
    "yahoo.com", "bing.com", "duckduckgo.com", "zoom.us", "dropbox.com", "spotify.com",
    "hotstar.com", "jiocinema.com", "makemytrip.com", "bookmyshow.com", "zerodha.com",
    "groww.in", "ndtv.com", "thehindu.com", "indiatimes.com", "hindustantimes.com",
    "indianexpress.com", "bbc.com", "bbc.co.uk", "cnn.com", "nytimes.com", "mozilla.org",
    "adobe.com", "canva.com", "notion.so", "openai.com", "anthropic.com", "claude.ai",
    "quora.com", "medium.com", "vercel.com", "cloudflare.com", "wordpress.org",
}

# Free hosting where ANYONE can publish a page. Never "trusted"
FREE_HOSTING = {
    "vercel.app", "netlify.app", "github.io", "web.app", "firebaseapp.com", "herokuapp.com",
    "onrender.com", "blogspot.com", "wixsite.com", "weebly.com", "000webhostapp.com",
    "pages.dev", "workers.dev", "ngrok.io", "ngrok-free.app", "glitch.me", "replit.app",
    "repl.co", "googleusercontent.com", "amazonaws.com", "sites.google.com", "forms.gle",
    "appspot.com", "azurewebsites.net", "wordpress.com", "godaddysites.com", "square.site",
    "webflow.io", "framer.website", "carrd.co", "mystrikingly.com", "jimdosite.com",
    "surge.sh", "fly.dev", "railway.app", "r2.dev", "ipfs.io", "dweb.link", "trycloudflare.com",
}
TRUSTED_DOMAINS -= FREE_HOSTING

PHISHING_WORDS = {
    "login", "signin", "sign-in", "verify", "verification", "update", "secure", "security",
    "account", "kyc", "banking", "wallet", "reward", "rewards", "bonus", "gift", "free",
    "claim", "refund", "prize", "support", "helpdesk", "unlock", "confirm", "suspend",
    "customer", "care", "offer", "lucky", "winner", "cashback", "recharge", "pan", "aadhar",
}

LOOKALIKE_MAP = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t",
                               "8": "b", "@": "a", "$": "s", "!": "i"})


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def registered_domain(host: str) -> str:
    """'netbanking.hdfcbank.com' -> 'hdfcbank.com', 'x.vercel.app' -> 'x.vercel.app'."""
    host = host.lower().strip(".")
    labels = host.split(".")
    for size in (3, 2):  # e.g. "sites.google.com" style hosting, then "co.in"
        suffix = ".".join(labels[-size:])
        if len(labels) > size and (suffix in FREE_HOSTING or suffix in MULTI_PART_SUFFIXES):
            return ".".join(labels[-(size + 1):])
    return ".".join(labels[-2:])


def is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def _edit_distance(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _is_official(host: str, domains) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def _check(checks: list, cid: str, status: str, value=None) -> None:
    checks.append({"id": cid, "status": status, "value": value})


# Results of slow outside lookups are kept for a while (saves free API quota)
_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()
CACHE_SECONDS = 3600


_INFLIGHT: dict = {}


def _cached(key, fn):
    """Remember slow lookups for an hour; if the same lookup is already running, wait for it."""
    now = time.time()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
        waiter = _INFLIGHT.get(key)
        if waiter is None:
            waiter = threading.Event()
            _INFLIGHT[key] = waiter
            owner = True
        else:
            owner = False
    if not owner:
        waiter.wait(timeout=15)
        with _CACHE_LOCK:
            hit = _CACHE.get(key)
        if hit:
            return hit[1]
        return fn()
    try:
        value = fn()
        if not (isinstance(value, dict) and value.get("error") and key[0] in ("gsb", "vt")):
            with _CACHE_LOCK:
                _CACHE[key] = (time.time(), value)
                if len(_CACHE) > 2000:
                    for k in list(_CACHE)[:500]:
                        _CACHE.pop(k, None)
        return value
    finally:
        with _CACHE_LOCK:
            _INFLIGHT.pop(key, None)
        waiter.set()


_PROBLEMS = {"safe_browsing": None, "virustotal": None}


def link_check_status() -> dict:
    """Shown on the server's home page so problems with API keys are easy to spot."""
    return {
        "safe_browsing": {"configured": bool(GOOGLE_SAFE_BROWSING_API_KEY), "problem": _PROBLEMS["safe_browsing"]},
        "virustotal": {"configured": bool(VIRUSTOTAL_API_KEY), "problem": _PROBLEMS["virustotal"]},
        "public_lists": {"links": sum(_FEEDS["counts"].values()), "counts": _FEEDS["counts"],
                         "problem": _FEEDS["problem"]},
    }


# ---------------------------------------------------------------------------
# 1. The address itself
# ---------------------------------------------------------------------------
def analyze_structure(url: str) -> dict:
    findings, checks = [], []
    score = 0
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path + "?" + parsed.query).lower()
    tricks = 0

    if is_ip(host):
        findings.append("Link uses a raw IP address instead of a real website name")
        score += 25
        _check(checks, "known", "warn", host)
        _check(checks, "imitation", "pass")
        _check(checks, "name_tricks", "warn", 1)
        return {"score": score, "findings": findings, "checks": checks, "trusted": False,
                "hosting": None, "shortener": False, "brand": None}

    reg = registered_domain(host)
    trusted = reg in TRUSTED_DOMAINS or host.endswith((".gov.in", ".nic.in", ".bank.in"))
    hosting = next((h for h in FREE_HOSTING if host == h or host.endswith("." + h)), None)
    shortener = reg in SHORTENER_DOMAINS
    if hosting:
        trusted = False
        findings.append(f"Page is hosted on a free hosting service ({hosting}) where anyone can publish. Check who made it")
        score += 10
        _check(checks, "known", "warn", hosting)
    elif shortener:
        findings.append("Link uses a link shortener, so the real destination is hidden")
        score += 15
        _check(checks, "known", "warn", reg)
    elif trusted:
        _check(checks, "known", "pass", reg)
    else:
        _check(checks, "known", "info", reg)

    subdomain_part = host[: -len(reg)].rstrip(".") if host.endswith(reg) else ""
    name_part = reg.split(".")[0]

    if "xn--" in host:
        findings.append("Website name uses special look-alike characters (punycode) to imitate another site")
        score += 30
        tricks += 1

    # Brand impersonation: a brand name appears, but this isn't that brand's real site
    brand_hit = None
    if not trusted:
        host_compact = host.replace("-", "")
        host_lookalike = host_compact.translate(LOOKALIKE_MAP).replace("rn", "m").replace("vv", "w")
        for brand, official in BRANDS.items():
            if _is_official(host, official):
                continue  # e.g. s3.amazonaws.com really is run by Amazon
            if len(brand) <= 3:
                hit_plain = re.search(rf"(^|[.\-]){brand}([.\-]|$)", host) is not None
                hit_lookalike = False
            else:
                hit_plain = brand in host_compact
                hit_lookalike = not hit_plain and brand in host_lookalike
            if hit_plain or hit_lookalike:
                how = "uses look-alike characters to imitate" if hit_lookalike else "mentions"
                findings.append(f"Link {how} '{brand_name(brand)}' but is NOT {brand_name(brand)}'s official website ({reg})")
                score += 50 if hit_lookalike else 40
                brand_hit = brand
                break

        # Misspelled brand name: amazom.in, flipkarrt.com, paytrn.com, g00gle.com
        if not brand_hit:
            candidates = {name_part, name_part.replace("-", ""),
                          name_part.translate(LOOKALIKE_MAP).replace("rn", "m").replace("vv", "w")}
            for target, brand in TYPO_TARGETS.items():
                if _is_official(host, BRANDS.get(brand, set())):
                    continue
                if len(target) < 6:
                    continue
                for cand in candidates:
                    # real typo-squats keep the first letter (amazom, flipkarrt); "tomato" is not "zomato"
                    if len(cand) < 5 or cand == target or cand[0] != target[0]:
                        continue
                    limit = 2 if len(target) >= 9 else 1
                    if _edit_distance(cand, target) <= limit:
                        brand_hit = brand
                        break
                if brand_hit:
                    findings.append(f"The website name '{reg}' is a misspelling of '{brand_name(brand_hit)}'. Scammers use names like this to trick you")
                    score += 50
                    break

        # Brand name hidden in the page address: some-site.com/sbi/login
        if not brand_hit:
            for brand, official in BRANDS.items():
                if len(brand) >= 4 and re.search(rf"[/\-_.=]{brand}[/\-_.?=]", path + "/"):
                    if any(w in path for w in ("login", "signin", "verify", "kyc", "update", "account", "secure", "wp-")):
                        findings.append(f"The page address mentions '{brand_name(brand)}' and a login or verification page, but the website is not {brand_name(brand)}'s")
                        score += 30
                        brand_hit = brand
                        break

    _check(checks, "imitation", "fail" if brand_hit else "pass", brand_name(brand_hit) if brand_hit else None)

    if not trusted:
        tokens = re.split(r"[.\-]", host)
        words_in_host = sorted(w for w in PHISHING_WORDS
                               if any(tok == w or (len(w) >= 5 and w in tok) for tok in tokens))
        if words_in_host:
            findings.append(f"Website name contains words scammers love: {', '.join(words_in_host[:3])}")
            score += 15
            tricks += 1
        elif any(w in path for w in ("login", "verify", "kyc", "update-account", "signin", "wp-admin")):
            findings.append("Link leads to a login or verification page. Never enter details on a page you reached from a message")
            score += 5

        if subdomain_part.count(".") >= 2:
            findings.append("Link has an unusually long chain of sub-domains (a trick to hide the real site)")
            score += 10
            tricks += 1

        if "xn--" not in name_part and name_part.count("-") >= 2:
            findings.append("Website name has several hyphens, common in fake sites")
            score += 5
            tricks += 1

        if len(host) > 40:
            findings.append("Website name is unusually long")
            score += 5
            tricks += 1

        if re.search(r"\d{4,}", name_part):
            findings.append("Website name contains a long string of numbers, common in throwaway scam sites")
            score += 10
            tricks += 1

    tld = reg.rsplit(".", 1)[-1]
    if tld in SUSPICIOUS_TLDS and not trusted:
        findings.append(f"Website ending '.{tld}' is cheap and often used for scams")
        score += 15
        tricks += 1

    if "@" in (parsed.netloc or ""):
        findings.append("Link contains an '@' symbol, which can hide the real destination")
        score += 20
        tricks += 1

    if re.search(r"\.apk($|\?)", path):
        findings.append("Link downloads an Android app (.apk) from outside the Play Store. This is a common way to steal OTPs")
        score += 40
        tricks += 1
    elif re.search(r"\.(exe|scr|bat|msi|vbs|js)($|\?)", path):
        findings.append("Link downloads a program file. Only install programs from the maker's official website or app store")
        score += 30
        tricks += 1

    if re.search(r"%[0-9a-f]{2}", host):
        findings.append("Website name contains hidden encoded characters")
        score += 10
        tricks += 1

    _check(checks, "name_tricks", "pass" if tricks == 0 else ("fail" if tricks >= 3 else "warn"), tricks)

    return {"score": score, "findings": findings, "checks": checks, "trusted": trusted,
            "hosting": hosting, "shortener": shortener, "brand": brand_hit}


# ---------------------------------------------------------------------------
# 2. Does the website exist?
# ---------------------------------------------------------------------------
def resolve_host(host: str) -> dict:
    """{'exists': True/False/None, 'ips': [...]}. None means we couldn't tell."""
    if OFFLINE:
        return {"exists": None, "ips": []}
    if is_ip(host):
        return {"exists": True, "ips": [host.strip("[]")]}
    try:
        infos = socket.getaddrinfo(host, None)
        ips = sorted({i[4][0] for i in infos})
        return {"exists": bool(ips), "ips": ips}
    except socket.gaierror as e:
        # EAI_NONAME / EAI_NODATA = the name really doesn't exist
        if e.errno in (socket.EAI_NONAME, getattr(socket, "EAI_NODATA", -5)):
            return {"exists": False, "ips": []}
        return {"exists": None, "ips": []}
    except Exception:
        return {"exists": None, "ips": []}


def _public_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# 3. Website age
# ---------------------------------------------------------------------------
def _first(value):
    if isinstance(value, (list, tuple)):
        value = [v for v in value if v]
        return value[0] if value else None
    return value


def _as_date(value):
    value = value if not isinstance(value, (list, tuple)) else min((v for v in value if isinstance(v, datetime)), default=None)
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


PRIVACY_WORDS = ("privacy", "redacted", "withheld", "proxy", "protected", "not disclosed", "data protected", "gdpr")


def whois_details(domain: str) -> dict:
    """
    Public registration record of a website (WHOIS): who registered it through which company,
    when, when it was last changed and when it expires. {} when not available.
    """
    if OFFLINE or whois is None or not domain:
        return {}

    def call():
        try:
            w = whois.whois(domain)
        except Exception:
            return {"error": True}
        created, updated, expires = _as_date(w.creation_date), _as_date(w.updated_date), _as_date(w.expiration_date)
        now = datetime.now(timezone.utc)
        org = _first(w.get("org")) or _first(w.get("registrant_organization")) or _first(w.get("name"))
        if org and any(x in str(org).lower() for x in PRIVACY_WORDS):
            org = "hidden"
        ns = w.name_servers or []
        if isinstance(ns, str):
            ns = [ns]
        ns = sorted({str(n).lower().rstrip(".") for n in ns if n})[:3]
        out = {
            "registrar": (_first(w.registrar) or "")[:80],
            "org": (str(org)[:80] if org else ""),
            "country": (str(_first(w.get("country")) or "")[:40]),
            "created": created.date().isoformat() if created else "",
            "updated": updated.date().isoformat() if updated else "",
            "expires": expires.date().isoformat() if expires else "",
            "age_days": max(0, (now - created).days) if created else None,
            "expires_in_days": (expires - now).days if expires else None,
            "name_servers": ns,
        }
        return out if any(v for k, v in out.items() if k != "name_servers") else {"error": True}

    info = _cached(("whois", domain), call)
    return {} if info.get("error") else info


def whois_age_days(domain: str):
    """Days since the domain was registered, or None."""
    return whois_details(domain).get("age_days")


def cert_details(host: str) -> dict:
    """The website's security certificate (its HTTPS 'licence'): who issued it and how long it is valid."""
    if OFFLINE or not host or is_ip(host):
        return {}

    def call():
        import ssl
        ips = resolve_host(host).get("ips") or []
        if not ips or not all(_public_ip(ip) for ip in ips):
            return {"error": True}
        ctx = ssl.create_default_context()
        try:
            with socket.create_connection((host, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    cert = tls.getpeercert()
        except ssl.SSLCertVerificationError as e:
            return {"valid": False, "problem": str(getattr(e, "verify_message", "") or "not trusted")[:80]}
        except Exception:
            return {"error": True}

        def name(parts, key):
            for rdn in parts or ():
                for k, v in rdn:
                    if k == key:
                        return v
            return ""
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return {
            "valid": True,
            "issuer": name(cert.get("issuer"), "organizationName") or name(cert.get("issuer"), "commonName"),
            "issued_to": name(cert.get("subject"), "organizationName") or name(cert.get("subject"), "commonName"),
            "valid_from": not_before.date().isoformat(),
            "valid_to": not_after.date().isoformat(),
            "days_left": (not_after - now).days,
            "cert_age_days": (now - not_before).days,
        }

    info = _cached(("cert", host), call)
    return {} if info.get("error") else info


def server_details(ip: str) -> dict:
    """Where the website's computer is and which company hosts it (ip-api.com)."""
    if OFFLINE or not ip or not _public_ip(ip):
        return {}

    def call():
        try:
            data = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,hosting",
                                timeout=5).json()
        except Exception:
            return {"error": True}
        if data.get("status") != "success":
            return {"error": True}
        return {"country": data.get("country", ""), "city": data.get("city", ""),
                "company": data.get("org") or data.get("isp") or ""}

    info = _cached(("ipinfo", ip), call)
    return {} if info.get("error") else info


# ---------------------------------------------------------------------------
# 4. Google Safe Browsing
# ---------------------------------------------------------------------------
def check_safe_browsing(urls) -> dict:
    """{'listed': bool|None, 'threats': [...]}. None means not checked."""
    if OFFLINE or not GOOGLE_SAFE_BROWSING_API_KEY:
        return {"listed": None, "threats": []}
    urls = list(dict.fromkeys(u for u in urls if u))

    def call():
        endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_API_KEY}"
        payload = {
            "client": {"clientId": "staysafe", "clientVersion": "2.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE",
                                "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": u} for u in urls],
            },
        }
        try:
            resp = requests.post(endpoint, json=payload, timeout=6)
        except Exception as e:
            _PROBLEMS["safe_browsing"] = f"Could not connect: {type(e).__name__}"
            return {"listed": None, "threats": [], "error": True}
        if resp.status_code != 200:
            try:
                msg = resp.json().get("error", {}).get("message", "")
            except Exception:
                msg = ""
            _PROBLEMS["safe_browsing"] = f"HTTP {resp.status_code}: {msg[:160]}"
            return {"listed": None, "threats": [], "error": True}
        _PROBLEMS["safe_browsing"] = None
        matches = resp.json().get("matches", [])
        threats = sorted({m.get("threatType", "") for m in matches})
        return {"listed": bool(matches), "threats": threats}

    return _cached(("gsb", tuple(urls)), call)


THREAT_NAMES = {
    "MALWARE": "harmful software",
    "SOCIAL_ENGINEERING": "phishing (fake page that steals details)",
    "UNWANTED_SOFTWARE": "unwanted software",
    "POTENTIALLY_HARMFUL_APPLICATION": "harmful app",
}


# ---------------------------------------------------------------------------
# 4b. Free public lists of scam / malware links (no key needed)
#     OpenPhish community feed (phishing) and URLhaus (malware links), refreshed every 3 hours.
# ---------------------------------------------------------------------------
FEED_SOURCES = {
    "OpenPhish": "https://raw.githubusercontent.com/openphish/public_feed/main/feed.txt",
    "URLhaus": "https://urlhaus.abuse.ch/downloads/text_online/",
}
FEED_REFRESH_SECONDS = 3 * 3600
_FEEDS = {"urls": {}, "hosts": {}, "loaded_at": 0.0, "loading": False, "counts": {}, "problem": None}
_FEED_LOCK = threading.Lock()


def _feed_key(u: str) -> str:
    u = u.strip().lower()
    u = re.sub(r"^[a-z]+://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def refresh_feeds() -> None:
    urls, hosts, counts, problems = {}, {}, {}, []
    for name, src in FEED_SOURCES.items():
        try:
            resp = requests.get(src, timeout=25, headers={"User-Agent": "StaySafe/2.0"})
            if resp.status_code != 200:
                problems.append(f"{name}: HTTP {resp.status_code}")
                continue
            n = 0
            for line in resp.text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "." not in line:
                    continue
                key = _feed_key(line)
                urls.setdefault(key, name)
                host = key.split("/")[0].split(":")[0]
                hosts.setdefault(host, name)
                n += 1
            counts[name] = n
        except Exception as e:
            problems.append(f"{name}: {type(e).__name__}")
    with _FEED_LOCK:
        if urls:
            _FEEDS.update(urls=urls, hosts=hosts, counts=counts)
        _FEEDS.update(loaded_at=time.time(), loading=False, problem="; ".join(problems) or None)


def ensure_feeds() -> None:
    """Start a background refresh when the lists are missing or older than 3 hours."""
    if OFFLINE:
        return
    with _FEED_LOCK:
        stale = time.time() - _FEEDS["loaded_at"] > FEED_REFRESH_SECONDS
        if not stale or _FEEDS["loading"]:
            return
        _FEEDS["loading"] = True
    threading.Thread(target=refresh_feeds, daemon=True).start()


def feed_lookup(urls, host: str) -> dict:
    """{'status': 'fail'|'warn'|'pass'|'skip', 'source': ...}"""
    ensure_feeds()
    if not _FEEDS["urls"]:
        return {"status": "skip"}
    for u in urls:
        if not u:
            continue
        hit = _FEEDS["urls"].get(_feed_key(u))
        if hit:
            return {"status": "fail", "source": hit}
    h = re.sub(r"^www\.", "", (host or "").lower())
    if h and h in _FEEDS["hosts"]:
        return {"status": "warn", "source": _FEEDS["hosts"][h]}
    return {"status": "pass"}


# ---------------------------------------------------------------------------
# 5. VirusTotal
# ---------------------------------------------------------------------------
def _vt_get(path: str):
    try:
        resp = requests.get(f"https://www.virustotal.com/api/v3/{path}",
                            headers={"x-apikey": VIRUSTOTAL_API_KEY}, timeout=6)
    except Exception as e:
        _PROBLEMS["virustotal"] = f"Could not connect: {type(e).__name__}"
        return None, "error"
    if resp.status_code == 404:
        return None, "not_found"
    if resp.status_code != 200:
        _PROBLEMS["virustotal"] = f"HTTP {resp.status_code}"
        return None, "error"
    _PROBLEMS["virustotal"] = None
    try:
        return resp.json()["data"]["attributes"], "ok"
    except Exception:
        return None, "error"


def check_virustotal(url: str, domain: str) -> dict:
    """
    {'status': 'ok'|'not_found'|'skip', 'malicious', 'suspicious', 'harmless', 'engines',
     'domain_malicious', 'created_days'}
    Looks up the exact link first, then the website as a whole (costs 1-2 of the free 4 lookups/minute).
    """
    if OFFLINE or not VIRUSTOTAL_API_KEY:
        return {"status": "skip"}

    def call():
        out = {"status": "not_found", "malicious": 0, "suspicious": 0, "harmless": 0,
               "engines": 0, "domain_malicious": 0, "created_days": None}
        variants = [url] + ([url + "/"] if urlparse(url).path == "" else [])
        attrs, state = None, "not_found"
        for v in variants:
            url_id = base64.urlsafe_b64encode(v.encode()).decode().strip("=")
            attrs, state = _vt_get(f"urls/{url_id}")
            if state != "not_found":
                break
        if state == "error":
            return {"status": "skip", "error": True}
        if attrs:
            stats = attrs.get("last_analysis_stats", {})
            out.update(status="ok", malicious=stats.get("malicious", 0), suspicious=stats.get("suspicious", 0),
                       harmless=stats.get("harmless", 0), engines=sum(stats.values()) if stats else 0)
        if out["status"] == "ok":
            return out
        # Link never seen: look at the whole website's reputation (also gives its age)
        dattrs, dstate = _vt_get(f"domains/{domain}")
        if dattrs:
            dstats = dattrs.get("last_analysis_stats", {})
            out["domain_malicious"] = dstats.get("malicious", 0)
            if out["status"] != "ok":
                out.update(status="ok", suspicious=dstats.get("suspicious", 0),
                           harmless=dstats.get("harmless", 0), engines=sum(dstats.values()) if dstats else 0)
            created = dattrs.get("creation_date")
            if isinstance(created, (int, float)) and created > 0:
                out["created_days"] = max(0, int((time.time() - created) // 86400))
        return out

    return _cached(("vt", url), call)


# ---------------------------------------------------------------------------
# 6. Open the page safely (on the server) and look at it
# ---------------------------------------------------------------------------
MAX_PAGE_BYTES = 300_000
LOGIN_BRAND_WORDS = {
    "sbi": "sbi", "state bank": "sbi", "hdfc": "hdfc", "icici": "icici", "axis bank": "axisbank",
    "kotak": "kotak", "paytm": "paytm", "phonepe": "phonepe", "google pay": "gpay", "amazon": "amazon",
    "flipkart": "flipkart", "paypal": "paypal", "microsoft": "microsoft", "outlook": "microsoft",
    "office 365": "microsoft", "apple id": "apple", "icloud": "icloud", "netflix": "netflix",
    "facebook": "facebook", "instagram": "instagram", "whatsapp": "whatsapp", "gmail": "google",
    "irctc": "irctc", "aadhaar": "aadhaar", "income tax": "incometax", "india post": "indiapost",
    "canara": "canarabank", "punjab national": "pnb", "bank of baroda": "bankofbaroda",
}


def fetch_page(url: str) -> dict:
    """
    Follows the link (max 5 redirects) without running anything on the page.
    Refuses private/internal addresses so nobody can use StaySafe to poke at our own server.
    Returns {'ok', 'final_url', 'hops', 'status', 'ssl_error', 'title', 'has_password',
             'text', 'download', 'blocked', 'error'}.
    """
    out = {"ok": False, "final_url": url, "hops": [], "status": None, "ssl_error": False,
           "title": "", "has_password": False, "text": "", "download": None, "blocked": False, "error": None}
    if OFFLINE:
        out["error"] = "offline"
        return out
    current = url
    session = requests.Session()
    try:
        for _ in range(6):
            host = urlparse(current).hostname or ""
            ips = resolve_host(host).get("ips") or []
            if not ips or not all(_public_ip(ip) for ip in ips):
                out["blocked"] = bool(ips)
                out["error"] = "private" if ips else "no_dns"
                return out
            try:
                resp = session.get(current, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-IN,en"},
                                   timeout=(4, 5), allow_redirects=False, stream=True)
            except requests.exceptions.SSLError:
                out["ssl_error"] = True
                out["error"] = "ssl"
                return out
            if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
                nxt = resp.headers.get("Location")
                resp.close()
                if not nxt:
                    break
                current = urljoin(current, nxt)
                out["hops"].append(current)
                if not current.lower().startswith(("http://", "https://")):
                    out["error"] = "odd_redirect"
                    out["final_url"] = current
                    return out
                continue
            out["status"] = resp.status_code
            out["final_url"] = current
            ctype = (resp.headers.get("Content-Type") or "").lower()
            dispo = (resp.headers.get("Content-Disposition") or "").lower()
            if "android.package-archive" in ctype or ".apk" in dispo:
                out["download"] = "apk"
            elif "msdownload" in ctype or "x-msdos-program" in ctype or re.search(r"\.(exe|msi|scr|bat)\b", dispo):
                out["download"] = "program"
            if "html" in ctype or not ctype:
                body = b""
                for chunk in resp.iter_content(16384):
                    body += chunk
                    if len(body) >= MAX_PAGE_BYTES:
                        break
                html = body.decode(resp.encoding or "utf-8", errors="ignore")
                m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                out["title"] = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else ""
                out["has_password"] = re.search(r"<input[^>]+type\s*=\s*[\"']?password", html, re.I) is not None
                text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
                out["text"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))[:5000].lower()
            resp.close()
            out["ok"] = True
            return out
        out["error"] = "too_many_redirects"
        return out
    except Exception as e:
        out["error"] = type(e).__name__
        return out


# ---------------------------------------------------------------------------
# Put everything together
# ---------------------------------------------------------------------------
def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "DANGEROUS"
    if score >= 20:
        return "CAUTION"
    return "SAFE"


_POOL = ThreadPoolExecutor(max_workers=32)
# separate pool for checking several links at once (avoids waiting on our own workers)
LINK_POOL = ThreadPoolExecutor(max_workers=8)


def _run(fn, *args, timeout=9, default=None):
    try:
        return _POOL.submit(fn, *args).result(timeout=timeout)
    except Exception:
        return default


_URL_WITH_SCHEME = re.compile(r"(?:https?|hxxps?)://[^\s<>\"'`]+", re.IGNORECASE)
_BARE_DOMAIN = re.compile(
    r"(?<![@\w.-])((?:www\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}(?::\d{2,5})?(?:/[^\s<>\"'`]*)?)",
    re.IGNORECASE)


def extract_url(raw: str) -> str:
    """
    Pull the web address out of whatever was pasted: a whole message, 'Link: <https://x>',
    a markdown link, defanged 'hxxp://evil[.]com', text with quotes or brackets around it.
    Returns '' when there is no web address at all.
    """
    text = (raw or "").strip()
    if not text:
        return ""
    # defanged addresses used in security reports
    text = re.sub(r"\[\.\]|\(\.\)|\{\.\}|\s\[dot\]\s|\[dot\]", ".", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhxxp", "http", text, flags=re.IGNORECASE)
    md = re.search(r"\]\((\S+?)\)", text)  # [text](url)
    if md and ("." in md.group(1) or "://" in md.group(1)):
        text = md.group(1)
    m = _URL_WITH_SCHEME.search(text)
    if m:
        found = m.group(0)
    else:
        candidates = [c for c in _BARE_DOMAIN.findall(text) if not re.fullmatch(r"[\d.]+", c.split("/")[0])]
        # prefer something that looks like a website over a stray "e.g." or file name
        candidates = [c for c in candidates if not re.search(r"\.(jpg|jpeg|png|pdf|txt|doc|docx)$", c, re.I) or "/" in c]
        if not candidates:
            ip = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?(?:/\S*)?", text)
            found = ip.group(0) if ip else ""
        else:
            found = candidates[0]
    found = re.split(r"\]\(|\)\[", found)[0]  # stop at leftover markdown brackets
    found = found.strip().rstrip(".,;:!?)]}>'\"”’").lstrip("(<[{'\"“‘")
    # keep brackets that belong to the address itself, like ?id=[1] or /page(2)
    for open_b, close_b in ("[]", "()"):
        if found.count(open_b) > found.count(close_b):
            found += close_b
    return found


def normalize_url(raw: str) -> str:
    url = extract_url(raw) or (raw or "").strip()
    url = url.replace(" ", "")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    return url


def scan_url(url: str) -> dict:
    url = normalize_url(url)
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    reg = host if is_ip(host) else registered_domain(host)

    structure = analyze_structure(url)
    checks = list(structure["checks"])
    findings = list(structure["findings"])
    score = structure["score"]
    trusted = structure["trusted"]

    # Slow lookups run at the same time so the whole check takes a few seconds
    dns_f = _POOL.submit(resolve_host, host)
    whois_f = None if (trusted or structure["hosting"] or is_ip(host)) else _POOL.submit(whois_age_days, reg)
    # extra details for the "Website details" card (also for well-known sites)
    who_f = None if (structure["hosting"] or is_ip(host)) else _POOL.submit(whois_details, reg)
    cert_f = _POOL.submit(cert_details, host) if parsed.scheme == "https" else None
    vt_f = _POOL.submit(check_virustotal, url, reg)
    gsb_f = _POOL.submit(check_safe_browsing, [url, f"{parsed.scheme}://{host}/"])
    page_f = None if trusted else _POOL.submit(fetch_page, url)

    def result_of(f, default, timeout=10):
        if f is None:
            return default
        try:
            return f.result(timeout=timeout)
        except Exception:
            return default

    dns = result_of(dns_f, {"exists": None, "ips": []}, 5)
    page = result_of(page_f, {"ok": False, "error": "skipped", "final_url": url, "hops": [],
                              "ssl_error": False, "title": "", "has_password": False, "text": "",
                              "download": None, "blocked": False}, 12)
    final_url = page.get("final_url") or url
    final_host = (urlparse(final_url).hostname or "").lower()
    gsb = result_of(gsb_f, {"listed": None, "threats": []}, 8)
    if not gsb.get("listed") and final_url != url:
        gsb2 = _run(check_safe_browsing, [final_url], timeout=6, default={"listed": None, "threats": []})
        if gsb2.get("listed"):
            gsb = gsb2
    vt = result_of(vt_f, {"status": "skip"}, 12)
    age_days = result_of(whois_f, None, 9)
    if age_days is None and vt.get("created_days") is not None and not trusted:
        age_days = vt["created_days"]

    # --- does it exist?
    if dns["exists"] is False:
        findings.append("This website doesn't exist or has been shut down. No server answers for this name. Scam links are often taken down after a few days")
        score = max(score + 40, 55)
        _check(checks, "exists", "fail")
    elif dns["exists"]:
        _check(checks, "exists", "pass")
    else:
        _check(checks, "exists", "skip")

    # --- HTTPS and certificate
    if page.get("ssl_error"):
        findings.append("The website's security certificate is not valid. Your browser would show a warning, and anything you type could be seen by others")
        score += 30
        _check(checks, "https", "fail")
    elif parsed.scheme != "https" and not final_url.lower().startswith("https://"):
        findings.append("Link does not use HTTPS (the connection is not encrypted)")
        score += 10
        _check(checks, "https", "warn")
    else:
        _check(checks, "https", "pass")

    # --- website age
    if trusted:
        _check(checks, "age", "pass", None)
    elif structure["hosting"] or is_ip(host):
        _check(checks, "age", "skip", None)
    elif age_days is None:
        if dns["exists"] is not False:
            findings.append("Could not confirm when this website was created")
            score += 5
        _check(checks, "age", "skip", None)
    elif age_days < 30:
        findings.append(f"Website was created only {age_days} days ago. Very new sites are a big warning sign")
        score += 35
        _check(checks, "age", "fail", age_days)
    elif age_days < 180:
        findings.append(f"Website is fairly new ({age_days} days old)")
        score += 15
        _check(checks, "age", "warn", age_days)
    else:
        _check(checks, "age", "pass", age_days)

    # --- where does it really lead?
    if page.get("ok") or page.get("hops"):
        final_reg = registered_domain(final_host) if final_host and not is_ip(final_host) else final_host
        if final_host and final_reg != reg:
            findings.append(f"This link secretly sends you to a different website: {final_host}")
            _check(checks, "redirect", "warn", final_host)
            dest = analyze_structure(final_url)
            if structure["shortener"] or dest["score"] >= 20:
                score += dest["score"]
                findings.extend(f"Final website: {f}" for f in dest["findings"])
            else:
                score += 10
        else:
            _check(checks, "redirect", "pass", final_host or host)
    elif page.get("error") == "private":
        findings.append("This link points to a private or local network address, not a public website")
        score += 20
        _check(checks, "redirect", "warn", host)
    elif trusted:
        _check(checks, "redirect", "pass", host)
    else:
        _check(checks, "redirect", "skip")

    # --- the page itself
    final_official = any(_is_official(final_host, d) for d in BRANDS.values()) or \
        registered_domain(final_host or host) in TRUSTED_DOMAINS
    if page.get("download") == "apk":
        findings.append("Opening this link downloads an Android app (APK) straight away. Never install apps from links")
        score += 40
        _check(checks, "page", "fail", "apk")
    elif page.get("download") == "program":
        findings.append("Opening this link downloads a program straight away")
        score += 30
        _check(checks, "page", "fail", "program")
    elif page.get("ok") and not final_official:
        haystack = (page.get("title", "") + " " + page.get("text", "")[:3000]).lower()
        pretends = next((b for w, b in LOGIN_BRAND_WORDS.items() if re.search(rf"\b{re.escape(w)}\b", haystack)), None)
        otp_words = re.search(r"\b(otp|upi pin|atm pin|cvv|card number|net ?banking|aadhaa?r number)\b", haystack)
        pretends = brand_name(pretends) if pretends else pretends
        if page.get("has_password") and pretends:
            findings.append(f"This page asks for a password and looks like a {pretends} page, but it is not on {pretends}'s website. This is a fake login page")
            score += 45
            _check(checks, "page", "fail", pretends)
        elif otp_words and pretends:
            findings.append(f"This page asks for bank or card details and uses the name {pretends}, but it is not {pretends}'s website")
            score += 40
            _check(checks, "page", "fail", pretends)
        elif page.get("has_password"):
            findings.append("This page asks you to type a password. Only do that on a website you opened yourself")
            score += 10
            _check(checks, "page", "warn", "password")
        else:
            _check(checks, "page", "pass", page.get("title") or None)
    elif trusted or final_official:
        _check(checks, "page", "pass", None)
    else:
        _check(checks, "page", "skip")

    # --- Google Safe Browsing
    if gsb.get("listed"):
        names = ", ".join(THREAT_NAMES.get(t, t.lower()) for t in gsb["threats"])
        findings.insert(0, f"Google Safe Browsing lists this link as dangerous: {names}")
        score = max(score + 50, 95)
        _check(checks, "google", "fail", names)
    elif gsb.get("listed") is False:
        _check(checks, "google", "pass")
    else:
        _check(checks, "google", "skip")

    # --- Public scam-link lists (OpenPhish, URLhaus)
    feed = feed_lookup([url, final_url], host) if not trusted else {"status": "pass"}
    if feed["status"] == "fail":
        findings.insert(0, f"This link is on a public list of scam and malware links ({feed['source']})")
        score = max(score + 50, 95)
        _check(checks, "feeds", "fail", feed["source"])
    elif feed["status"] == "warn" and not structure["hosting"]:
        findings.append(f"Scam pages on this website were reported recently ({feed['source']})")
        score += 25
        _check(checks, "feeds", "warn", feed["source"])
    elif feed["status"] == "skip":
        _check(checks, "feeds", "skip")
    else:
        _check(checks, "feeds", "pass")

    # --- VirusTotal
    if vt.get("status") == "ok":
        mal, sus = vt.get("malicious", 0), vt.get("suspicious", 0)
        if mal >= 3 or vt.get("domain_malicious", 0) >= 3:
            n = max(mal, vt.get("domain_malicious", 0))
            findings.insert(0, f"{n} security companies on VirusTotal flagged this link as malicious")
            score = max(score + 40, 90)
            _check(checks, "virustotal", "fail", n)
        elif mal >= 1 or vt.get("domain_malicious", 0) >= 1:
            n = max(mal, vt.get("domain_malicious", 0))
            findings.insert(0, f"{n} security companies on VirusTotal flagged this link as malicious")
            score += 35
            _check(checks, "virustotal", "fail", n)
        elif sus:
            findings.append(f"{sus} security companies on VirusTotal flagged this link as suspicious")
            score += 15
            _check(checks, "virustotal", "warn", sus)
        else:
            _check(checks, "virustotal", "pass", vt.get("engines") or None)
    elif vt.get("status") == "not_found":
        _check(checks, "virustotal", "info")
    else:
        _check(checks, "virustotal", "skip")

    total = max(0, min(100, score))
    # Known-good sites keep a low score unless a blocklist says otherwise
    if trusted and not gsb.get("listed") and vt.get("malicious", 0) < 3 and feed["status"] != "fail":
        total = min(total, 15)

    order = ["google", "feeds", "virustotal", "exists", "imitation", "page", "redirect", "age", "https", "known", "name_tricks"]
    checks.sort(key=lambda c: order.index(c["id"]) if c["id"] in order else 99)

    return {
        "url": url,
        "risk_score": total,
        "verdict": verdict_from_score(total),
        "findings": findings,
        "checks": checks,
        "details": {
            "domain": host,
            "registered_domain": reg,
            "final_url": final_url if final_url != url else "",
            "page_title": page.get("title", ""),
            "age_days": age_days,
            "ip": (dns.get("ips") or [""])[0],
            "whois": result_of(who_f, {}, 6),
            "certificate": result_of(cert_f, {}, 6),
            "server": _run(server_details, (dns.get("ips") or [""])[0], timeout=6, default={}),
        },
    }


# ---------------------------------------------------------------------------
# FLASK ROUTE
# ---------------------------------------------------------------------------
@url_scanner_bp.route("/api/scan-url", methods=["POST"])
def scan_url_route():
    data = request.get_json(silent=True) or {}
    raw = (data.get("url") or "").strip()

    if not raw:
        return jsonify({"error": "Please paste the link you want to check."}), 400
    raw = raw[:5000]
    if not extract_url(raw):
        return jsonify({"error": "We couldn't find a web address in what you pasted. Try something like example.com"}), 400
    url = normalize_url(raw)
    host = urlparse(url).hostname or ""
    if "." not in host and not is_ip(host):
        return jsonify({"error": "That doesn't look like a website link. Try something like example.com"}), 400

    result = scan_url(url)

    from scanners.risk_engine import log_scan
    log_scan("url", result)

    return jsonify(result)
