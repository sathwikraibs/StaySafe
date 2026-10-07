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

from scanners.security import guarded_fetch, install_connection_guard
from scanners.quota import quota

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
    "share.google", "g.co", "youtu.be", "amzn.to", "amzn.in", "fkrt.it", "paytm.me", "phon.pe",
}
# Short links made by the company itself (Google's "Share" links, Amazon, Flipkart, LinkedIn...):
# not a warning sign on their own, but the real destination is still opened and checked.
# Website endings that only one company can own (nobody else can register a name ending in them)
BRAND_TLDS = {"google", "youtube", "android", "gmail", "amazon", "apple", "microsoft", "sbi", "hdfcbank"}
OFFICIAL_SHORTENERS = {"share.google", "goo.gl", "g.co", "youtu.be", "amzn.to", "amzn.in", "fkrt.it", "lnkd.in",
                       "paytm.me", "phon.pe"}

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

SECOND_LEVEL = {"com", "co", "net", "org", "gov", "ac", "edu", "ne", "or", "go", "gob", "nic", "mil", "ltd", "plc"}
# Global brands whose own country websites (google.de, amazon.co.jp) are real when they are well-known sites
GLOBAL_BRANDS = {"google", "amazon", "apple", "microsoft", "facebook", "instagram", "netflix", "paypal", "youtube",
                 "linkedin", "yahoo", "ebay", "samsung", "whatsapp", "twitter", "hsbc", "citibank", "binance", "roblox"}
MAJOR_CC = set("""in us uk de fr it es nl be ch at se no dk fi ie pt pl cz gr ru ua tr il ae sa eg za ng ke ma
                  jp kr cn hk tw sg my id th vn ph au nz ca mx br ar cl co pe ve pk bd lk np""".split())

# Brand keyword -> the real registered domains that brand uses
BRANDS = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "onlinesbi.com", "sbicard.com", "sbi", "sbi.bank.in", "sbilife.co.in",
            "sbimf.com", "sbigeneral.in", "sbisecurities.in", "sbicaps.com"},
    "onlinesbi": {"onlinesbi.sbi", "onlinesbi.com"},
    "hdfc": {"hdfcbank.com", "hdfcbank.net", "hdfc.com", "hdfclife.com", "hdfcsec.com", "hdfc.bank.in", "hdfcbank.bank.in", "hdfcbank",
             "hdfcergo.com", "hdfcfund.com", "hdfcsky.com"},
    "icici": {"icicibank.com", "icicidirect.com", "iciciprulife.com", "icici.bank.in", "icicilombard.com", "icicipruamc.com",
              "icicisecurities.com"},
    "axisbank": {"axisbank.com", "axis.bank.in", "axismf.com", "axisdirect.in"},
    "kotak": {"kotak.com", "kotak.bank.in", "kotaksecurities.com", "kotakmf.com", "kotaklife.com"},
    "canarabank": {"canarabank.com", "canarabank.in"},
    "pnb": {"pnbindia.in", "pnb.co.in", "pnb.bank.in"},
    "bankofbaroda": {"bankofbaroda.in", "bankofbaroda.com"},
    "unionbank": {"unionbankofindia.co.in"},
    "yesbank": {"yesbank.in"},
    "paytm": {"paytm.com", "paytm.in", "paytmbank.com", "paytmmoney.com", "paytmmall.com", "paytm.me"},
    "phonepe": {"phonepe.com", "phon.pe"},
    "phonepay": {"phonepe.com", "phon.pe"},      # the usual misspelling scammers use
    "gpay": {"google.com"},
    "googlepay": {"google.com"},
    "google": {"google.com", "google.co.in", "googleusercontent.com", "googleapis.com", "gstatic.com", "withgoogle.com", "youtube.com", "youtu.be", "goo.gl", "g.co",
               "google", "youtube", "android", "gmail"},   # the last four: endings only Google can own
    "amazon": {"amazon.in", "amazon.com", "amazonaws.com", "amazon.co.uk", "amzn.to", "amzn.in", "amazon", "amazonpay.in"},
    "flipkart": {"flipkart.com", "fkrt.it"},
    "meesho": {"meesho.com"},
    "paypal": {"paypal.com", "paypal.me"},
    "apple": {"apple.com", "icloud.com", "apple"},
    "icloud": {"icloud.com", "apple.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com", "outlook.com", "microsoftonline.com", "microsoft"},
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
    "mescom": {"mescom.karnataka.gov.in", "mescom.co.in"},
    "hescom": {"hescom.karnataka.gov.in", "hescom.co.in"},
    "gescom": {"gescom.karnataka.gov.in", "gescom.in"},
    "cescmysore": {"cescmysore.karnataka.gov.in", "cescmysore.org"},
    "kseb": {"kseb.in"},
    "tangedco": {"tangedco.gov.in", "tnebltd.gov.in"},
    "cybercrime": {"cybercrime.gov.in"},
    "trai": {"trai.gov.in"},
    "cbi": {"cbi.gov.in"},
    "dtdc": {"dtdc.in", "dtdc.com"},
    "sanchar": {"sancharsaathi.gov.in", "dot.gov.in"},
    "mahadiscom": {"mahadiscom.in"},
    "fastag": {"npci.org.in", "ihmcl.co.in"},
    "parivahan": {"parivahan.gov.in"},
    "echallan": {"parivahan.gov.in"},
    "pmkisan": {"pmkisan.gov.in"},
    "kbc": {"sonyliv.com", "sonypicturesnetworks.com"},
    "digilocker": {"digilocker.gov.in"},
    "sancharsaathi": {"sancharsaathi.gov.in"},
    "bhim": {"bhimupi.org.in", "npci.org.in"},
    "yono": {"onlinesbi.sbi", "sbi.co.in", "sbi"},
    "mobikwik": {"mobikwik.com"},
    "cred": {"cred.club"},
    "zerodha": {"zerodha.com"},
    "groww": {"groww.in"},
    "upstox": {"upstox.com"},
    "angelone": {"angelone.in"},
    "hsbc": {"hsbc.co.in", "hsbc.com", "hsbc.co.uk", "hsbc.com.hk"},
    "citibank": {"citibank.com", "citi.com", "citibank.co.in"},
    # global services that scam pages copy for everyone, Indians included
    "chase": {"chase.com"},
    "bankofamerica": {"bankofamerica.com", "bofa.com"},
    "wellsfargo": {"wellsfargo.com"},
    "coinbase": {"coinbase.com"},
    "binance": {"binance.com"},
    "metamask": {"metamask.io"},
    "trezor": {"trezor.io"},
    "usps": {"usps.com"},
    "docusign": {"docusign.com", "docusign.net"},
    "dropbox": {"dropbox.com", "dropboxusercontent.com", "db.tt"},
    "onedrive": {"live.com", "microsoft.com", "sharepoint.com"},
    "office365": {"microsoft.com", "office.com", "microsoftonline.com", "live.com"},
    "outlook": {"outlook.com", "live.com", "office.com", "microsoft.com"},
    "yahoo": {"yahoo.com", "yahoo.co.jp", "yahoo.co.in"},
    "roblox": {"roblox.com"},
    "steamcommunity": {"steamcommunity.com"},
    "steampowered": {"steampowered.com"},
}
# Brand names that are also ordinary words ("the indian telegram", "pineapple"): only counted
# when they stand alone in the website name or start it ("telegram-premium", "appleid-verify")
WORD_BRANDS = {"telegram", "apple", "chase", "outlook", "cred", "groww", "steam"}
# Short names that are inside ordinary words ("train", "trailer", "ksebastian"): only counted when they
# stand alone in the website name ("trai-sim-block") or are joined to a scam word ("traiverify")
STANDALONE_BRANDS = {"trai", "kseb", "dtdc", "jio", "pnb", "kbc", "dhl", "cbi", "sbi"}

BRAND_DISPLAY = {
    "sbi": "SBI", "onlinesbi": "SBI", "hdfc": "HDFC Bank", "icici": "ICICI Bank", "axisbank": "Axis Bank",
    "kotak": "Kotak Bank", "canarabank": "Canara Bank", "pnb": "PNB", "bankofbaroda": "Bank of Baroda",
    "unionbank": "Union Bank", "yesbank": "Yes Bank", "paytm": "Paytm", "phonepe": "PhonePe",
    "gpay": "Google Pay", "googlepay": "Google Pay", "phonepay": "PhonePe", "google": "Google", "amazon": "Amazon", "flipkart": "Flipkart", "meesho": "Meesho",
    "paypal": "PayPal", "apple": "Apple", "icloud": "Apple iCloud", "microsoft": "Microsoft",
    "netflix": "Netflix", "facebook": "Facebook", "instagram": "Instagram", "whatsapp": "WhatsApp",
    "telegram": "Telegram", "irctc": "IRCTC", "uidai": "Aadhaar (UIDAI)", "aadhaar": "Aadhaar (UIDAI)",
    "incometax": "Income Tax Dept", "epfo": "EPFO", "npci": "NPCI", "airtel": "Airtel", "jio": "Jio",
    "bsnl": "BSNL", "indiapost": "India Post", "fedex": "FedEx", "dhl": "DHL", "bluedart": "Blue Dart",
    "delhivery": "Delhivery", "myntra": "Myntra", "swiggy": "Swiggy", "zomato": "Zomato",
    "bescom": "BESCOM", "mahadiscom": "MSEDCL", "fastag": "FASTag", "parivahan": "Parivahan (Transport Dept)",
    "echallan": "e-Challan (Transport Dept)", "pmkisan": "PM-Kisan", "kbc": "KBC (Kaun Banega Crorepati)",
    "digilocker": "DigiLocker", "sancharsaathi": "Sanchar Saathi", "bhim": "BHIM UPI", "yono": "SBI YONO",
    "mobikwik": "MobiKwik", "cred": "CRED", "zerodha": "Zerodha", "groww": "Groww", "upstox": "Upstox",
    "angelone": "Angel One", "hsbc": "HSBC", "citibank": "Citibank", "chase": "Chase Bank",
    "bankofamerica": "Bank of America", "wellsfargo": "Wells Fargo", "coinbase": "Coinbase", "binance": "Binance",
    "metamask": "MetaMask", "trezor": "Trezor", "usps": "USPS", "docusign": "DocuSign", "dropbox": "Dropbox",
    "onedrive": "Microsoft OneDrive", "office365": "Microsoft Office", "outlook": "Outlook", "yahoo": "Yahoo",
    "roblox": "Roblox", "steamcommunity": "Steam", "steampowered": "Steam",
    "mescom": "MESCOM", "hescom": "HESCOM", "gescom": "GESCOM", "cescmysore": "CESC Mysore", "kseb": "KSEB",
    "tangedco": "TANGEDCO", "cybercrime": "Cyber Crime Portal", "trai": "TRAI", "cbi": "CBI", "dtdc": "DTDC",
    "sanchar": "Department of Telecom",
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
    "sbionline": "sbi", "pnbindia": "pnb", "mobikwik": "mobikwik", "zerodha": "zerodha", "upstox": "upstox",
    "coinbase": "coinbase", "binance": "binance", "metamask": "metamask", "chaseonline": "chase",
    "wellsfargo": "wellsfargo", "bankofamerica": "bankofamerica", "docusign": "docusign", "roblox": "roblox",
    "uidai": "uidai", "parivahan": "parivahan", "digilocker": "digilocker", "pmkisan": "pmkisan",
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
    "cf-ipfs.com", "w3s.link", "nftstorage.link", "4everland.io", "fleek.co", "ipfs.dweb.link",
    "gitbook.io", "codesandbox.io", "csb.app", "ondigitalocean.app", "cleverapps.io", "easywp.com", "mybluehost.me",
    "ic0.app", "icp0.io", "siasky.net", "web3.storage", "vercel.dev", "deno.dev", "pages.github.io", "gitlab.io",
    "bitbucket.io", "notion.site", "typedream.app", "webnode.page", "site123.me", "yolasite.com",
    "tilda.ws", "readthedocs.io", "hpage.com", "ukit.me", "start.page", "linktr.ee", "beacons.ai",
    "firebasestorage.googleapis.com", "storage.googleapis.com", "blob.core.windows.net", "s3.amazonaws.com",
    "backblazeb2.com", "dropboxusercontent.com", "1drv.ms", "sharepoint.com", "my.canva.site", "canva.site",
    "builder.io", "studio.site", "glide.page", "softr.app", "bubbleapps.io", "webcindario.com", "altervista.org",
    "duckdns.org", "ddns.net", "no-ip.org", "no-ip.com", "hopto.org", "zapto.org", "sytes.net", "serveo.net",
    "freedns.org", "mooo.com", "dynu.net", "myftp.biz", "myddns.me", "servehttp.com", "redirectme.net",
    "loca.lt", "localtunnel.me", "serveousercontent.com", "pinggy.link", "devtunnels.ms", "trycloudflare.com",
}
# "Dynamic address" and tunnel services: a home computer can appear as a website for a few hours.
# Genuine banks, shops and government offices never use them
TUNNEL_HOSTS = {"duckdns.org", "ddns.net", "no-ip.org", "no-ip.com", "hopto.org", "zapto.org", "sytes.net",
                "serveo.net", "freedns.org", "mooo.com", "dynu.net", "myftp.biz", "myddns.me", "servehttp.com",
                "redirectme.net", "loca.lt", "localtunnel.me", "serveousercontent.com", "pinggy.link",
                "devtunnels.ms", "trycloudflare.com", "ngrok.io", "ngrok-free.app"}
TRUSTED_DOMAINS -= FREE_HOSTING

PHISHING_WORDS = {
    "login", "signin", "sign-in", "verify", "verification", "update", "secure", "security",
    "account", "kyc", "banking", "wallet", "reward", "rewards", "bonus", "gift", "free",
    "claim", "refund", "prize", "support", "helpdesk", "unlock", "confirm", "suspend",
    "customer", "care", "offer", "lucky", "winner", "cashback", "recharge", "pan", "aadhar",
    "lottery", "jackpot", "parcel", "customs", "challan", "penalty", "disconnection", "blocked", "expired",
    "redeem", "netbanking", "ebanking", "otp", "unblock", "reactivate", "doubling", "profit", "airdrop",
    "giveaway", "subsidy", "scholarship", "loanapp", "instantloan",
}

# Words that are ordinary on their own but tell a scam story together ("dtdc-courier-redelivery",
# "cbi-arrest-warrant", "task-earn-daily"). Only counted with a second such word or a word above.
THEME_WORDS = {
    "redelivery", "courier", "delivery", "tracking", "track", "arrest", "warrant", "police", "complaint", "court",
    "yojana", "scheme", "sim", "block", "earn", "earning", "task", "parttime", "job", "jobs", "hiring", "loan",
    "instant", "investment", "invest", "bitcoin", "crypto", "forex", "trading", "double", "draw", "scratch",
    "scratchcard", "spin", "electricity", "bill", "power", "ration", "laptop", "fee", "fine", "pay", "payment",
    "number", "deactivate", "deactivation", "kyc", "pending", "alert", "notice", "income", "daily", "tips",
    "like", "review", "approval", "cash", "money", "gramin", "list", "status", "seized", "illegal", "drugs",
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
    # any country's second level, like com.mx, co.kr, org.br, gov.ng
    if len(labels) >= 3 and len(labels[-1]) == 2 and labels[-2] in SECOND_LEVEL:
        return ".".join(labels[-3:])
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
# Answers that change slowly are kept longer, so the free daily allowances go further.
CACHE_TTL = {"vt": 3 * 3600, "urlscan": 6 * 3600, "abuseip": 12 * 3600, "rdap": 24 * 3600,
             "crt": 24 * 3600, "ipinfo": 24 * 3600, "whois": 24 * 3600}
# Answers worth keeping across restarts in the long memory (scanners/store.py): how long, by answer.
def _vt_keep(v):
    if not isinstance(v, dict) or v.get("status") not in ("ok", "not_found"):
        return 0
    if (v.get("malicious") or 0) >= 1 or (v.get("domain_malicious") or 0) >= 1:
        return 7 * 86400          # scam links stay scam links
    return 86400 if v.get("status") == "ok" else 6 * 3600


def _keep(seconds):
    return lambda v: seconds if v is not None and not (isinstance(v, dict) and v.get("error")) else 0


PERSIST = {"vt": _vt_keep, "urlscan": _keep(86400), "abusech2": _keep(86400), "otx": _keep(86400), "cfscan": lambda v: (7 * 86400 if v.get("status") == "fail" else 86400) if isinstance(v, dict) and v.get("status") in ("fail", "pass") else 0, "phishstats": _keep(86400), "abuseip": _keep(86400),
           "whois": _keep(2 * 86400), "rdap": _keep(2 * 86400), "crt": _keep(2 * 86400)}
# A check that was skipped because a free limit was reached is never remembered as an answer.
NOT_CHECKED = "_not_checked"


_INFLIGHT: dict = {}


def _cached(key, fn):
    """Remember slow lookups for an hour; if the same lookup is already running, wait for it."""
    now = time.time()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and now - hit[0] < CACHE_TTL.get(key[0], CACHE_SECONDS):
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
        from scanners import store
        ttl_fn = PERSIST.get(key[0])
        value = store.get("link", key) if ttl_fn else None
        fresh = value is None
        if fresh:
            value = fn()
        if not (isinstance(value, dict) and (value.get(NOT_CHECKED)
                                             or (value.get("error") and key[0] in ("gsb", "vt")))):
            with _CACHE_LOCK:
                _CACHE[key] = (time.time(), value)
                if len(_CACHE) > 2000:
                    for k in list(_CACHE)[:500]:
                        _CACHE.pop(k, None)
            if fresh and ttl_fn:
                store.put("link", key, value, ttl_fn(value))
        return value
    finally:
        with _CACHE_LOCK:
            _INFLIGHT.pop(key, None)
        waiter.set()


_PROBLEMS = {"safe_browsing": None, "virustotal": None, "abusech": None, "urlscan": None, "phishstats": None,
             "cloudflare_scan": None, "otx": None}


def link_check_status() -> dict:
    """Shown on the server's home page so problems with API keys are easy to spot."""
    return {
        "safe_browsing": {"configured": bool(GOOGLE_SAFE_BROWSING_API_KEY), "problem": _PROBLEMS["safe_browsing"]},
        "phishstats": {"configured": True, "problem": _PROBLEMS["phishstats"], "today": quota("phishstats").status()["used_today"]},
        "virustotal": {"configured": bool(VIRUSTOTAL_API_KEY), "problem": _PROBLEMS["virustotal"]},
        "abusech": {"configured": bool(_abusech_key()), "problem": _PROBLEMS["abusech"]},
        "urlscan": {"configured": bool(os.environ.get("URLSCAN_API_KEY")), "problem": _PROBLEMS["urlscan"]},
        "cloudflare_scan": {"configured": bool(_cf_scan_conf()), "problem": _PROBLEMS["cloudflare_scan"]},
        "otx": {"configured": bool(os.environ.get("OTX_API_KEY")), "problem": _PROBLEMS["otx"]},
        "rbi_alert_list": __import__("scanners.rbi_alert", fromlist=["status"]).status(),
        "abuseipdb": {"configured": bool(os.environ.get("ABUSEIPDB_KEY"))},
        "public_lists": {"links": sum(_FEEDS["counts"].values()), "counts": _FEEDS["counts"],
                         "problem": _FEEDS["problem"],
                         "big_lists": _BIG["counts"], "big_problem": _BIG["problem"]},
        "popular_sites": {"count": len(_TRANCO["ranks"]), "problem": _TRANCO["problem"]},
    }


# ---------------------------------------------------------------------------
# 1. The address itself
# ---------------------------------------------------------------------------
def path_for_hosting(url: str) -> str:
    try:
        return urlparse(url).path.lower()
    except Exception:
        return ""


def _random_looking(label: str) -> bool:
    """A website name that looks machine-made (svuyvmmweyrfgeqg, iokycc2ghvd74nmnh4ki), not a word or brand."""
    if len(label) < 12 or "xn--" in label:
        return False
    letters = re.sub(r"[^a-z]", "", label)
    digits = sum(ch.isdigit() for ch in label)
    vowels = sum(ch in "aeiou" for ch in letters)
    longest_consonants = max((len(m) for m in re.findall(r"[bcdfghjklmnpqrstvwxz]+", label)), default=0)
    mixed = digits >= 3 and len(letters) >= 6 and re.search(r"[a-z]\d+[a-z]+\d", label) is not None
    return longest_consonants >= 6 or mixed or (len(letters) >= 12 and vowels / max(1, len(letters)) < 0.2)


# Letters from other alphabets that look exactly like English ones (Cyrillic "а" in "аpple")
_CONFUSABLE = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "ј": "j", "ѕ": "s",
    "ԁ": "d", "ɡ": "g", "һ": "h", "ӏ": "l", "ո": "n", "ս": "u", "ν": "v", "ο": "o", "α": "a", "ρ": "p",
    "τ": "t", "κ": "k", "ι": "i", "ε": "e", "ԛ": "q", "ԝ": "w", "м": "m", "т": "t", "к": "k", "в": "b",
    "н": "h", "ь": "b", "г": "r", "ı": "i", "ɩ": "i", "ʟ": "l", "ᴠ": "v", "ɑ": "a", "ɢ": "g",
})


def _decode_idn(host: str) -> str:
    out = []
    for label in host.split("."):
        if label.startswith("xn--"):
            try:
                label = label.encode("ascii").decode("idna")
            except Exception:
                try:
                    label = label[4:].encode("ascii").decode("punycode")
                except Exception:
                    pass
        out.append(label)
    return ".".join(out)


def _skeleton(text: str) -> str:
    """What a name looks like on screen: 'аpple' (Cyrillic а) and 'àpple' both look like 'apple'."""
    import unicodedata
    text = text.translate(_CONFUSABLE)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _scripts(label: str) -> set:
    import unicodedata
    found = set()
    for ch in label:
        if ch.isalpha():
            try:
                found.add(unicodedata.name(ch).split(" ")[0])
            except ValueError:
                pass
    return found


_EMAIL_IN_URL = re.compile(r"[\w.+-]{2,}(?:@|%40)[\w-]{2,}\.[a-z]{2,}", re.I)
_B64_EMAIL = re.compile(r"[A-Za-z0-9+/_-]{16,}={0,2}")
_KIT_WORDS = ("login", "signin", "sign-in", "logon", "auth", "verify", "verification", "kyc", "update", "account",
              "secure", "wp-", "confirm", "billing", "payment", "netbanking", "unlock", "session", "otp", "webmail",
              "validate", "recover", "suspend", "index.php", "index.html", "redeem", "claim", "reward", "refund")
_REDIRECT_WRAPPERS = {
    "google.com": ("/url", ("q", "url")), "google.co.in": ("/url", ("q", "url")),
    "l.facebook.com": ("/l.php", ("u",)), "lm.facebook.com": ("/l.php", ("u",)), "l.messenger.com": ("/l.php", ("u",)),
    "l.instagram.com": ("/", ("u",)), "youtube.com": ("/redirect", ("q",)), "www.youtube.com": ("/redirect", ("q",)),
    "out.reddit.com": ("/", ("url",)), "away.vk.com": ("/away.php", ("to",)), "t.umblr.com": ("/redirect", ("z",)),
    "href.li": ("/", ()), "www.linkedin.com": ("/redir/redirect", ("url",)), "click.snapchat.com": ("/", ("url",)),
}


def unwrap_redirect(url: str) -> str:
    """Links that only pass through Google, Facebook, Outlook... ('google.com/url?q=https://evil.xyz') open
    the inner address. Returns that inner address, or '' when the link isn't one of these."""
    from urllib.parse import parse_qs, unquote
    try:
        p = urlparse(url)
    except Exception:
        return ""
    host = (p.hostname or "").lower()
    qs = parse_qs(p.query)
    keys = ()
    if host.endswith("safelinks.protection.outlook.com"):
        keys = ("url",)
    elif host in ("www.google.com", "google.com", "www.google.co.in", "google.co.in"):
        keys = ("q", "url") if p.path == "/url" else ()
    elif host in _REDIRECT_WRAPPERS:
        path, keys = _REDIRECT_WRAPPERS[host]
        if p.path != path:
            keys = ()
        if host == "href.li" and p.query.lower().startswith("http"):
            return unquote(p.query)
    for k in keys:
        v = (qs.get(k) or [""])[0].strip()
        if v.lower().startswith(("http://", "https://")):
            return v
    return ""


_APK_IN_PATH = re.compile(r"\.apk($|[?&/#=])")


def analyze_structure(url: str) -> dict:
    findings, checks = [], []
    score = 0
    from scanners.ledger import Ledger
    led = Ledger()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path + "?" + parsed.query).lower()
    raw_path = parsed.path + "?" + parsed.query
    tricks = 0

    def brand_in_path(min_len: int):
        for brand in BRANDS:
            if len(brand) >= min_len and re.search(rf"[/\-_.=?&]{brand}[/\-_.?=&0-9]", path + "/"):
                return brand
        return None

    if is_ip(host):
        findings.append("Link uses a raw IP address instead of a real website name")
        score += led.note(findings, 25)
        b = brand_in_path(3)
        if b:
            findings.append(f"The page address mentions '{brand_name(b)}', but genuine {brand_name(b)} pages never open from a bare number address")
            score += led.note(findings, 30)
        elif any(w in path for w in _KIT_WORDS):
            findings.append("Link leads to a login or verification page. Never enter details on a page you reached from a message")
            score += led.note(findings, 15)
        if _APK_IN_PATH.search(path):
            findings.append("Link downloads an Android app (.apk) from outside the Play Store. This is a common way to steal OTPs")
            score += led.note(findings, 40)
        _check(checks, "known", "warn", host)
        _check(checks, "imitation", "fail" if b else "pass", brand_name(b) if b else None)
        _check(checks, "name_tricks", "warn", 1)
        return {"score": score, "findings": findings, "checks": checks, "parts": led.parts, "trusted": False,
                "hosting": None, "shortener": False, "brand": b, "apk": bool(_APK_IN_PATH.search(path))}

    reg = registered_domain(host)
    trusted = reg in TRUSTED_DOMAINS or host.endswith((".gov.in", ".nic.in", ".bank.in")) or \
        (host.endswith(tuple("." + t for t in BRAND_TLDS)) and reg not in OFFICIAL_SHORTENERS)
    hosting = next((h for h in FREE_HOSTING if host == h or host.endswith("." + h)), None)
    if not hosting and re.search(r"\.blogspot\.[a-z.]+$", host):
        hosting = "blogspot"
    if not hosting and re.search(r"/ip[fn]s/", path_for_hosting(url)):
        hosting = "IPFS"
    if not hosting and host in ("docs.google.com", "forms.office.com", "forms.microsoft.com") and \
            (parsed.path.startswith("/forms/") or host != "docs.google.com"):
        hosting = "Google Forms" if host == "docs.google.com" else "Microsoft Forms"
    tunnel = hosting in TUNNEL_HOSTS
    shortener = reg in SHORTENER_DOMAINS
    if hosting and hosting.endswith("Forms"):
        trusted = False
        findings.append(f"This is a {hosting.split()[0]} form. Anyone can make one, so never type passwords, OTPs, card or bank details into it")
        score += led.note(findings, 10)
        _check(checks, "known", "warn", hosting)
    elif tunnel:
        trusted = False
        findings.append(f"Website runs on a temporary address service ({hosting}) that turns any computer into a website for a few hours. Banks, shops and government offices never use these")
        score += led.note(findings, 25)
        _check(checks, "known", "warn", hosting)
    elif hosting:
        trusted = False
        findings.append(f"Page is hosted on a free hosting service ({hosting}) where anyone can publish. Check who made it")
        score += led.note(findings, 20 if hosting in ("IPFS", "ipfs.io", "dweb.link", "cf-ipfs.com", "w3s.link",
                                                       "nftstorage.link", "4everland.io", "siasky.net") else 10)
        _check(checks, "known", "warn", hosting)
    elif shortener and reg in OFFICIAL_SHORTENERS:
        _check(checks, "known", "pass", reg)   # the company's own short link: we judge where it leads
    elif shortener and parsed.path.strip("/") == "" and not parsed.query:
        _check(checks, "known", "info", reg)   # just the short-link service's own home page
    elif shortener:
        findings.append("Link uses a link shortener, so the real destination is hidden")
        score += led.note(findings, 15)
        _check(checks, "known", "warn", reg)
        slug = parsed.path.lower()
        slug_brand = next((b for b in BRANDS if len(b) >= 3 and b in slug), None)
        slug_words = [w for w in ("kyc", "reward", "refund", "claim", "bonus", "prize", "lottery", "offer", "update",
                                  "verify", "electricity", "bill", "challan", "parcel", "customs", "apk", "loan", "job")
                      if w in slug]
        if slug_brand or slug_words:
            findings.append("The short link's name was chosen to mention a bank, a brand or a reward. Scammers do this to look genuine")
            score += led.note(findings, 25 if (slug_brand and slug_words) or len(slug_words) >= 2 else 15)
    elif trusted:
        _check(checks, "known", "pass", reg)
    else:
        _check(checks, "known", "info", reg)

    subdomain_part = host[: -len(reg)].rstrip(".") if host.endswith(reg) else ""
    name_part = reg.split(".")[0]
    rank = None if hosting else popularity_rank(reg)

    # Look-alike letters from other alphabets (punycode). A name fully in Hindi, Kannada, Thai or Chinese
    # is normal; English mixed with Cyrillic or Greek letters, or a name that LOOKS like a brand, is not
    idn_brand = None
    if "xn--" in host:
        shown = _decode_idn(host)
        skeleton = _skeleton(shown)
        mixed = any(len(_scripts(lab) - {"DIGIT"}) >= 2 and "LATIN" in _scripts(lab) for lab in shown.split("."))
        if skeleton.isascii() and skeleton != shown:
            sk_reg = registered_domain(skeleton)
            sk_compact = skeleton.replace("-", "")
            if sk_reg in TRUSTED_DOMAINS or (popularity_rank(sk_reg) or 10**9) <= 100_000:
                idn_brand = sk_reg
            else:
                idn_brand = next((brand_name(b) for b in BRANDS if len(b) >= 4 and b in sk_compact), None)
        if idn_brand:
            findings.append(f"Website name '{shown}' uses look-alike letters to pass as '{idn_brand}'. It is a different website")
            score += led.note(findings, 55)
            tricks += 1
        elif mixed:
            findings.append(f"Website name '{shown}' mixes letters from different alphabets, a trick to imitate another site")
            score += led.note(findings, 30)
            tricks += 1

    # Brand impersonation: a brand name appears, but this isn't that brand's real site
    brand_hit = None
    if idn_brand:
        brand_hit = idn_brand
    if not trusted and not brand_hit:
        host_compact = host.replace("-", "")
        host_lookalike = host_compact.translate(LOOKALIKE_MAP).replace("rn", "m").replace("vv", "w")
        host_lookalike2 = host_lookalike.replace("l", "i")       # lcicibank -> icicibank
        reg_parts = reg.split(".")
        top_site = not hosting and host in (reg, "www." + reg) and (rank or 10**9) <= 10_000
        country_site = len(reg_parts) in (2, 3) and len(reg_parts[-1]) == 2 and \
            (len(reg_parts) == 2 or reg_parts[1] in SECOND_LEVEL) and \
            (reg_parts[-1] in MAJOR_CC or top_site or (rank or 10**9) <= 100_000)
        tokens = [t for t in re.split(r"[.\-]", host) if t]
        for brand, official in BRANDS.items():
            if _is_official(host, official):
                continue  # e.g. s3.amazonaws.com really is run by Amazon
            if brand in GLOBAL_BRANDS and reg_parts[0] == brand and country_site:
                continue  # google.de, amazon.co.jp: the brand's own website for that country
            if top_site:
                break  # one of the world's 10,000 most visited websites (kotaku.com, telegram.me), not a fake
            hit_lookalike = False
            if len(brand) <= 3 or brand in WORD_BRANDS or brand in STANDALONE_BRANDS:
                # stands alone ("sbi-kyc", "telegram-premium") or starts a word joined to a scam word
                # ("sbirewards", "appleid") - but not "theindiantelegram" or "pineapple"
                hit_plain = re.search(rf"(^|[.\-]){brand}([.\-]|$)", host) is not None or any(
                    t.startswith(brand) and len(t) > len(brand) and (
                        brand in WORD_BRANDS and len(brand) > 3 or
                        any(w in t[len(brand):] for w in PHISHING_WORDS if len(w) >= 3))
                    for t in tokens)
            else:
                hit_plain = brand in host_compact
                hit_lookalike = not hit_plain and (brand in host_lookalike or brand in host_lookalike2)
            if hit_plain or hit_lookalike:
                how = "uses look-alike characters to imitate" if hit_lookalike else "mentions"
                findings.append(f"Link {how} '{brand_name(brand)}' but is NOT {brand_name(brand)}'s official website ({reg})")
                score += led.note(findings, 50 if hit_lookalike else 40)
                brand_hit = brand
                # spelled almost exactly like the real website (hdfcbannk.com vs hdfcbank.com)
                labels = {d.split(".")[0] for d in official if "." in d}
                cand = name_part.replace("-", "")
                if any(0 < _edit_distance(cand, lab) <= (1 if len(lab) <= 6 else 2) for lab in labels if len(lab) >= 4):
                    findings.append(f"The website name '{reg}' is spelled almost like {brand_name(brand)}'s real website, so it is easy to mistake")
                    score += led.note(findings, 20)
                # a second, different brand or government service in the same name (echallan + parivahan)
                elif any(b2 != brand and BRANDS[b2] != official and len(b2) >= 5 and b2 in host_compact.replace(brand, " ")
                         for b2 in BRANDS):
                    findings.append("Website name strings together the names of two official services, which genuine websites don't do")
                    score += led.note(findings, 15)
                break

        # Misspelled brand name: amazom.in, flipkarrt.com, paytrn.com, g00gle.com
        exact_name = False
        if not brand_hit and not top_site:
            candidates = {name_part, name_part.replace("-", ""),
                          name_part.translate(LOOKALIKE_MAP).replace("rn", "m").replace("vv", "w")}
            for target, brand in TYPO_TARGETS.items():
                if _is_official(host, BRANDS.get(brand, set())):
                    continue
                if len(target) < 6:
                    continue
                for cand in candidates:
                    if cand == target and not (country_site and brand in GLOBAL_BRANDS) and (rank or 10**9) > 100_000:
                        brand_hit, exact_name = brand, True     # sbionline.in, onlinesbi.co: the name itself, elsewhere
                        break
                    # real typo-squats keep the first letter (amazom, flipkarrt); "tomato" is not "zomato"
                    if len(cand) < 5 or cand == target or cand[0] != target[0]:
                        continue
                    limit = 2 if len(target) >= 9 else 1
                    if _edit_distance(cand, target) <= limit:
                        brand_hit = brand
                        break
                if brand_hit and exact_name:
                    findings.append(f"Link uses the name '{brand_name(brand_hit)}' but is NOT {brand_name(brand_hit)}'s official website ({reg})")
                    score += led.note(findings, 45)
                    break
                if brand_hit:
                    findings.append(f"The website name '{reg}' is a misspelling of '{brand_name(brand_hit)}'. Scammers use names like this to trick you")
                    score += led.note(findings, 50)
                    break

        # Brand name hidden in the page address: some-site.com/sbi/login, free-host.app/paytm.html
        if not brand_hit:
            b = brand_in_path(3 if hosting else 4)
            if b and not _is_official(host, BRANDS[b]):
                if any(w in path for w in _KIT_WORDS) or re.search(r"\.(php|html?|aspx?)\b", path):
                    findings.append(f"The page address mentions '{brand_name(b)}' and a login or verification page, but the website is not {brand_name(b)}'s")
                    score += led.note(findings, 40 if hosting else 30)
                    brand_hit = b
                elif hosting:
                    findings.append(f"The page mentions '{brand_name(b)}' but sits on a free hosting service, not on {brand_name(b)}'s own website")
                    score += led.note(findings, 25)
                    brand_hit = b

    _check(checks, "imitation", "fail" if brand_hit else "pass", brand_name(brand_hit) if brand_hit in BRANDS else brand_hit)

    if not trusted:
        tokens = re.split(r"[.\-]", host)
        words_in_host = sorted(w for w in PHISHING_WORDS
                               if any(tok == w or (len(w) >= 5 and w in tok) for tok in tokens))
        theme_in_host = sorted(w for w in THEME_WORDS - set(words_in_host)
                               if any(tok == w or (len(w) >= 7 and w in tok) for tok in tokens[:-1]))
        n_words = len(words_in_host) + len(theme_in_host)
        if words_in_host or n_words >= 2:
            shown_words = (words_in_host + theme_in_host)[:3]
            findings.append(f"Website name contains words scammers love: {', '.join(shown_words)}")
            score += led.note(findings, 35 if n_words >= 3 else 25 if n_words == 2 else 15)
            tricks += 1
        elif any(w in path for w in ("login", "verify", "kyc", "update-account", "signin", "wp-admin")):
            findings.append("Link leads to a login or verification page. Never enter details on a page you reached from a message")
            score += led.note(findings, 5)

        # pretends to be a government website: "pmkisan-gov.in.net", "incometax-refund-gov.in"
        real_gov = re.search(r"(\.gov\.in|\.nic\.in|\.gov|\.mil|\.(gov|gob|go|govt|gouv|gv|mil)\.[a-z]{2})$", host)
        if not real_gov and re.search(r"(^|[.\-])(gov|govt|gouv|sarkar|sarkari)([.\-]|$)", host):
            findings.append("Website name pretends to be a government website, but it is not one (Indian government websites end in .gov.in or .nic.in)")
            score += led.note(findings, 40)
            tricks += 1

        if subdomain_part.count(".") >= 2:
            findings.append("Link has an unusually long chain of sub-domains (a trick to hide the real site)")
            score += led.note(findings, 10)
            tricks += 1

        if "xn--" not in name_part and name_part.count("-") >= 2:
            findings.append("Website name has several hyphens, common in fake sites")
            score += led.note(findings, 5)
            tricks += 1

        if len(host) > 40:
            findings.append("Website name is unusually long")
            score += led.note(findings, 5)
            tricks += 1

        first_label = host.split(".")[0]
        if _random_looking(name_part.replace("-", "")) or (hosting and _random_looking(first_label.replace("-", ""))):
            findings.append("Website name looks randomly generated, typical of throwaway scam sites")
            score += led.note(findings, 15)
            tricks += 1

        if re.search(r"/wp-(content|includes|admin)/[^?#]*(login|signin|webmail|verify|secure|bank|account|auth|update|office|outlook|paypal|apple|netflix|wallet)", path) \
                or re.search(r"/(signin|sign-in|login|logon|auth|verify|verification|validate|webmail|secure-?file|otp\w*|bizmail|mailbox|owa|onedrive|sharepoint|office365|docusign|excel\w*)\.(php|html?|aspx?)\b", path):
            findings.append("The link's address looks like a fake login page hidden inside another website")
            score += led.note(findings, 25)
            tricks += 1

        # another website's address inside the path: evil.com/www.itau.com.br/login, x.com/www.sbi.co.in/
        inner_site = re.search(r"/(www\.[a-z0-9-]+(?:\.[a-z]{2,6}){1,2})(?:/|$)", parsed.path.lower())
        if inner_site and registered_domain(inner_site.group(1)) != reg:
            findings.append(f"The page address contains another website's name ({inner_site.group(1)}) to look like it, but the page is on {reg}")
            score += led.note(findings, 30)
            tricks += 1

        # the victim's email already filled in (?email=you@x.com, or hidden in base64): fake login pages
        # do this so the page looks personal
        email_inside = _EMAIL_IN_URL.search(raw_path) is not None
        if not email_inside:
            for blob in _B64_EMAIL.findall(raw_path)[:6]:
                try:
                    dec = base64.b64decode(blob.replace("-", "+").replace("_", "/") + "=" * (-len(blob) % 4)).decode("utf-8", "ignore")
                except Exception:
                    continue
                if _EMAIL_IN_URL.search(dec):
                    email_inside = True
                    break
        if email_inside:
            findings.append("The link already contains an email address, as fake login pages do to look personal")
            score += led.note(findings, 15)
            tricks += 1

        if re.search(r"\d{4,}", name_part):
            findings.append("Website name contains a long string of numbers, common in throwaway scam sites")
            score += led.note(findings, 10)
            tricks += 1

    tld = reg.rsplit(".", 1)[-1]
    if tld in SUSPICIOUS_TLDS and not trusted:
        findings.append(f"Website ending '.{tld}' is cheap and often used for scams")
        score += led.note(findings, 15)
        tricks += 1

    if "@" in (parsed.netloc or ""):
        shown_part = parsed.netloc.rsplit("@", 1)[0]
        if re.search(r"[a-z0-9-]+\.[a-z]{2,}", shown_part, re.I):
            findings.append(f"Link is made to look like it opens '{shown_part[:60]}', but it really opens {host}")
            score += led.note(findings, 45)
        else:
            findings.append("Link contains an '@' symbol, which can hide the real destination")
            score += led.note(findings, 20)
        tricks += 1

    apk = bool(_APK_IN_PATH.search(path))
    if apk:
        findings.append("Link downloads an Android app (.apk) from outside the Play Store. This is a common way to steal OTPs")
        # on a big file-sharing website (Google Drive, MediaFire) the website is fine but the file is not
        score += led.note(findings, 35 if (trusted or (rank or 10**9) <= 10_000) else 50)
        tricks += 1
        named = next((b for b in BRANDS if len(b) >= 3 and re.search(rf"(^|[^a-z]){b}", path)), None) or \
            next((w for w in ("kisan", "yojana", "challan", "rto", "bill", "kyc", "reward", "aadhaar", "aadhar", "pmkisan",
                              "invoice", "wedding", "invitation", "income", "tax", "customs") if w in path), None)
        if named and not _is_official(host, BRANDS.get(named, set())):
            findings.append("The app file is named after a bank, a government scheme or an invitation. "
                            "Fake apps with names like this are the most common way phones get taken over in India")
            score += led.note(findings, 25)
    elif re.search(r"\.(exe|scr|bat|msi|vbs|js)($|\?)", path):
        findings.append("Link downloads a program file. Only install programs from the maker's official website or app store")
        score += led.note(findings, 30)
        tricks += 1

    if re.search(r"%[0-9a-f]{2}", host):
        findings.append("Website name contains hidden encoded characters")
        score += led.note(findings, 10)
        tricks += 1

    _check(checks, "name_tricks", "pass" if tricks == 0 else ("fail" if tricks >= 3 else "warn"), tricks)

    return {"score": score, "findings": findings, "checks": checks, "parts": led.parts, "trusted": trusted,
            "hosting": hosting, "shortener": shortener, "brand": brand_hit, "apk": apk}


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
        return ipaddress.ip_address(ip.split("%")[0]).is_global
    except ValueError:
        return False


install_connection_guard(_public_ip)


# ---------------------------------------------------------------------------
# 3. Website age
# ---------------------------------------------------------------------------
def _first(value):
    if isinstance(value, (list, tuple)):
        value = [v for v in value if v]
        return value[0] if value else None
    return value


def _as_date(value):
    if isinstance(value, str):  # RDAP / crt.sh give ISO text like 2021-03-04T10:00:00Z
        try:
            value = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
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
    if OFFLINE or not domain:
        return {}
    if whois is None:
        return rdap_details(domain)

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
    if info.get("error") or not info.get("created"):
        rd = rdap_details(domain)
        if rd:
            merged = dict(rd) if info.get("error") else {**rd, **{k: v for k, v in info.items() if v}}
            return merged
    return {} if info.get("error") else info


def rdap_details(domain: str) -> dict:
    """
    RDAP: the modern, structured version of WHOIS run by the domain registries themselves.
    Much more reliable for the creation date (.in, .com, new endings). Free, no key.
    """
    if OFFLINE or not domain:
        return {}

    def call():
        if not quota("rdap").take(wait=5):
            return {"error": True, NOT_CHECKED: True}
        try:
            resp = requests.get(f"https://rdap.org/domain/{domain}", timeout=8,
                                headers={"Accept": "application/rdap+json", "User-Agent": "StaySafe/2.0"})
            if resp.status_code != 200:
                return {"error": True}
            data = resp.json()
        except Exception:
            return {"error": True}
        events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", []) if isinstance(e, dict)}
        created = _as_date(events.get("registration"))
        updated = _as_date(events.get("last changed"))
        expires = _as_date(events.get("expiration"))
        registrar = ""
        for ent in data.get("entities", []) or []:
            if "registrar" in (ent.get("roles") or []):
                for item in ((ent.get("vcardArray") or [None, []])[1] or []):
                    if item and item[0] == "fn":
                        registrar = str(item[3])[:80]
        now = datetime.now(timezone.utc)
        ns = sorted({str(n.get("ldhName", "")).lower().rstrip(".") for n in data.get("nameservers", []) or []
                     if isinstance(n, dict) and n.get("ldhName")})[:3]
        out = {
            "registrar": registrar, "org": "", "country": "",
            "created": created.date().isoformat() if created else "",
            "updated": updated.date().isoformat() if updated else "",
            "expires": expires.date().isoformat() if expires else "",
            "age_days": max(0, (now - created).days) if created else None,
            "expires_in_days": (expires - now).days if expires else None,
            "name_servers": ns,
        }
        return out if out["created"] or out["registrar"] else {"error": True}

    info = _cached(("rdap", domain), call)
    return {} if info.get("error") else info


def first_certificate_days(host: str):
    """
    Days since the first HTTPS certificate was ever issued for this website name (from the
    public Certificate Transparency logs on crt.sh). A good stand-in for "how long has this
    site been online" when the registration date is hidden. None when unknown.
    """
    if OFFLINE or not host or is_ip(host):
        return None

    def call():
        if not quota("crtsh").take(wait=5):
            return {"days": None, NOT_CHECKED: True}
        try:
            resp = requests.get("https://crt.sh/", params={"q": host, "output": "json", "exclude": "expired"},
                                timeout=8, headers={"User-Agent": "StaySafe/2.0"})
            if resp.status_code != 200:
                return {"days": None}
            dates = [_as_date(c.get("not_before")) for c in resp.json()[:500] if isinstance(c, dict)]
        except Exception:
            return {"days": None}
        dates = [d for d in dates if d]
        if not dates:
            return {"days": None}
        return {"days": max(0, (datetime.now(timezone.utc) - min(dates)).days)}

    return _cached(("crt", host), call).get("days")


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
        if not quota("ip_api").take(wait=5):
            return {"error": True, NOT_CHECKED: True}
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
        if not quota("safe_browsing").take(wait=10, priority="high"):
            return {"listed": None, "threats": [], "error": True}
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
            if resp.status_code == 429:
                quota("safe_browsing").cool_down(60)
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
            hdrs = {"User-Agent": "StaySafe/2.0"}
            if "abuse.ch" in src and _abusech_key():
                hdrs["Auth-Key"] = _abusech_key()
            resp = requests.get(src, timeout=25, headers=hdrs)
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
    ensure_big_feeds()
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
# 4c. Big community phishing lists + the "most visited websites" list
#     Phishing.Database (~400k domains, ~800k links, MIT licence) and Phishing Army
#     (CC BY-NC 4.0) are far too big to keep as text on a small server, so each entry is
#     stored as an 8-byte fingerprint in a sorted numpy array (about 10 MB for everything).
#     Tranco (top sites, refreshed daily) lowers false alarms on popular real websites.
# ---------------------------------------------------------------------------
BIG_FEEDS = {
    # name: (url, kind)  kind = "links" (exact addresses) or "domains" (whole website names)
    "Phishing.Database": [
        ("https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE.txt", "links"),
        ("https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-domains-ACTIVE.txt", "domains"),
    ],
    "Phishing Army": [
        ("https://phishing.army/download/phishing_army_blocklist_extended.txt", "domains"),
    ],
}
BIG_FEED_REFRESH_SECONDS = 6 * 3600
TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"
TRANCO_KEEP = 100_000          # the top 100k registered domains
TRANCO_REFRESH_SECONDS = 24 * 3600
_BIG = {"links": {}, "domains": {}, "counts": {}, "loaded_at": 0.0, "loading": False, "problem": None}
_TRANCO = {"ranks": {}, "loaded_at": 0.0, "loading": False, "problem": None}


def _fingerprint(text: str) -> int:
    import hashlib
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8", "ignore"), digest_size=8).digest(), "big")


def _sorted_fingerprints(values):
    import numpy as np
    arr = np.fromiter(values, dtype=np.uint64)
    arr.sort()
    return np.unique(arr)


def _in_fingerprints(arr, text: str) -> bool:
    import numpy as np
    if arr is None or not len(arr):
        return False
    fp = np.uint64(_fingerprint(text))
    i = int(np.searchsorted(arr, fp))
    return i < len(arr) and arr[i] == fp


def refresh_big_feeds() -> None:
    links, domains, counts, problems = {}, {}, {}, []
    for name, sources in BIG_FEEDS.items():
        for src, kind in sources:
            try:
                resp = requests.get(src, timeout=60, stream=True, headers={"User-Agent": "StaySafe/2.0"})
                if resp.status_code != 200:
                    problems.append(f"{name} {kind}: HTTP {resp.status_code}")
                    continue

                def keys():
                    for raw in resp.iter_lines(decode_unicode=True):
                        line = (raw or "").strip()
                        if not line or line.startswith(("#", "!")) or "." not in line:
                            continue
                        if kind == "domains":
                            line = line.split()[-1]  # also accepts "0.0.0.0 domain" style lines
                            yield _fingerprint(re.sub(r"^www\.", "", line.lower().strip(".")))
                        else:
                            yield _fingerprint(_feed_key(line))

                arr = _sorted_fingerprints(keys())
                (links if kind == "links" else domains)[name] = arr
                counts[f"{name} {kind}"] = int(len(arr))
            except Exception as e:
                problems.append(f"{name} {kind}: {type(e).__name__}")
    with _FEED_LOCK:
        if links or domains:
            _BIG.update(links=links or _BIG["links"], domains=domains or _BIG["domains"], counts=counts)
        _BIG.update(loaded_at=time.time(), loading=False, problem="; ".join(problems) or None)


def refresh_tranco() -> None:
    import io
    import zipfile
    try:
        resp = requests.get(TRANCO_URL, timeout=60, headers={"User-Agent": "StaySafe/2.0"})
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        ranks = {}
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            with z.open(z.namelist()[0]) as f:
                for raw in f:
                    rank, _, domain = raw.decode("utf-8", "ignore").strip().partition(",")
                    if domain:
                        ranks.setdefault(domain.lower(), int(rank))
                    if len(ranks) >= TRANCO_KEEP:
                        break
        with _FEED_LOCK:
            _TRANCO.update(ranks=ranks, problem=None)
    except Exception as e:
        _TRANCO["problem"] = f"{type(e).__name__}: {str(e)[:80]}"
    _TRANCO.update(loaded_at=time.time(), loading=False)


def ensure_big_feeds() -> None:
    if OFFLINE:
        return
    for store, refresh, every in ((_BIG, refresh_big_feeds, BIG_FEED_REFRESH_SECONDS),
                                  (_TRANCO, refresh_tranco, TRANCO_REFRESH_SECONDS)):
        with _FEED_LOCK:
            if store["loading"] or time.time() - store["loaded_at"] < every:
                continue
            store["loading"] = True
        threading.Thread(target=refresh, daemon=True).start()


def popularity_rank(domain: str):
    """Position in the list of the world's most visited websites (1 = most visited), or None."""
    ensure_big_feeds()
    return _TRANCO["ranks"].get((domain or "").lower())


def community_listed(kind: str, value: str) -> bool:
    """Reported as a scam by enough different StaySafe users (scanners/reports.py)."""
    if OFFLINE:
        return False
    try:
        from scanners.reports import report_count, REPORT_THRESHOLD
        return report_count(kind, value) >= REPORT_THRESHOLD
    except Exception:
        return False


def big_feed_lookup(urls, host: str, reg: str) -> dict:
    """
    {'status': 'fail'|'warn'|'pass'|'skip', 'source': ...}
    fail: this exact address, or a website that exists only for phishing, is listed.
    warn: a page on a big shared website (like sites.google.com) is listed; the website
          itself is fine, so we only mention it.
    """
    ensure_big_feeds()
    if not _BIG["links"] and not _BIG["domains"]:
        return {"status": "skip"}
    for name, arr in _BIG["links"].items():
        if any(u and _in_fingerprints(arr, _feed_key(u)) for u in urls):
            return {"status": "fail", "source": name}
    h = re.sub(r"^www\.", "", (host or "").lower())
    # Lists sometimes contain pages on big shared websites (docs.google.com, a popular site).
    # The website itself isn't a scam then, so we only mention it instead of condemning it.
    shared = (reg in TRUSTED_DOMAINS or reg in FREE_HOSTING or h in FREE_HOSTING or reg in OFFICIAL_SHORTENERS
              or (popularity_rank(reg) or 10**9) <= 20_000)
    for name, arr in _BIG["domains"].items():
        if any(c and _in_fingerprints(arr, c) for c in {h, reg}):
            return {"status": "warn" if shared else "fail", "source": name}
    return {"status": "pass"}


# ---------------------------------------------------------------------------
# 4d. Lookups that need a free key (each is skipped until its key is added)
#     ABUSECH_AUTH_KEY : URLhaus (malware links, with Spamhaus DBL / SURBL results) and
#                        ThreatFox (malware and botnet servers)       free at auth.abuse.ch
#     URLSCAN_API_KEY  : urlscan.io, past scans of this website marked malicious
#     ABUSEIPDB_KEY    : is the website's server reported for attacks
# ---------------------------------------------------------------------------
BAD_DBL = ("phishing", "malware", "botnet", "spam")


def check_phishstats(url: str, host: str) -> dict:
    """
    PhishStats (phishstats.info): a free, no-key database of phishing pages reported worldwide.
    One request per website. fail = this exact link is listed; warn = other phishing pages on
    this website were listed. About 50 free lookups a day, so it's kept for unknown websites.
    """
    if OFFLINE or not host or is_ip(host):
        return {"status": "skip"}

    def call():
        if not quota("phishstats").take(wait=3, priority="low"):
            return {"status": "skip", NOT_CHECKED: True}
        try:
            r = requests.get("https://api.phishstats.info/api/phishing",
                             params={"_where": f"(host,eq,{host})", "_sort": "-id", "_size": 20},
                             headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=6)
            if r.status_code == 429:
                quota("phishstats").close_day()
                return {"status": "skip", NOT_CHECKED: True}
            if r.status_code != 200:
                _PROBLEMS["phishstats"] = f"HTTP {r.status_code}"
                return {"status": "skip", NOT_CHECKED: True}
            rows = r.json()
        except Exception as e:
            _PROBLEMS["phishstats"] = type(e).__name__
            return {"status": "skip", NOT_CHECKED: True}
        _PROBLEMS["phishstats"] = None
        if not isinstance(rows, list):
            return {"status": "skip"}
        want = _feed_key(url)
        found = [row for row in rows if isinstance(row, dict) and str(row.get("host") or "").lower() == host]
        if any(_feed_key(str(row.get("url") or "")) == want for row in found):
            return {"status": "fail", "source": "PhishStats"}
        def score(row):
            try:
                return float(row.get("score") or 0)
            except (TypeError, ValueError):
                return 0.0
        if any(score(row) >= 5 for row in found):
            return {"status": "warn", "source": "PhishStats"}
        return {"status": "pass"}

    return _cached(("phishstats", host, url), call)


def _abusech_key() -> str:
    return os.environ.get("ABUSECH_AUTH_KEY", "")


def check_abusech(url: str, host: str) -> dict:
    """
    {'status': 'fail'|'warn'|'pass'|'skip', 'source': str, 'detail': str}
    fail: this exact link is a known malware link, the website is a known malware/botnet
          server (ThreatFox), or Spamhaus lists the domain as phishing/malware/spam.
    warn: other links on this website spread malware recently.
    """
    key = _abusech_key()
    if OFFLINE or not key or not host:
        return {"status": "skip"}

    def call():
        if not quota("abusech").take(wait=5, cost=3):
            return {"status": "skip", NOT_CHECKED: True}
        headers = {"Auth-Key": key, "User-Agent": "StaySafe/2.0"}
        out = {"status": "pass"}
        try:
            r = requests.post("https://urlhaus-api.abuse.ch/v1/url/", data={"url": url}, headers=headers, timeout=6).json()
            if r.get("query_status") == "ok":
                return {"status": "fail", "source": "URLhaus", "detail": r.get("threat") or ""}
            h = requests.post("https://urlhaus-api.abuse.ch/v1/host/", data={"host": host}, headers=headers, timeout=6).json()
            if h.get("query_status") == "ok":
                dbl = str((h.get("blacklists") or {}).get("spamhaus_dbl", "")).lower()
                surbl = str((h.get("blacklists") or {}).get("surbl", "")).lower()
                if dbl and not dbl.startswith(("not", "abused_legit")) and any(w in dbl for w in BAD_DBL):
                    return {"status": "fail", "source": "Spamhaus", "detail": dbl}
                if surbl == "listed":
                    out = {"status": "warn", "source": "SURBL", "detail": ""}
                if int(h.get("urls_online") or 0) > 0 or int(h.get("url_count") or 0) >= 3:
                    out = {"status": "warn", "source": "URLhaus", "detail": ""}
            t = requests.post("https://threatfox-api.abuse.ch/api/v1/", json={"query": "search_ioc", "search_term": host},
                              headers=headers, timeout=6).json()
            if t.get("query_status") == "ok" and t.get("data"):
                # ThreatFox also lists big shared websites (github.com, drive.google.com) because some malware
                # was once downloaded from them. There only a match on this exact link counts.
                want = _feed_key(url)
                rows = [d or {} for d in t["data"] if isinstance(d, dict)]
                exact = next((d for d in rows if _feed_key(str(d.get("ioc") or "")) == want), None)
                if exact:
                    return {"status": "fail", "source": "ThreatFox", "detail": exact.get("malware_printable") or ""}
                h0 = re.sub(r"^www\.", "", host.lower())
                reg0 = registered_domain(h0)
                shared = (reg0 in TRUSTED_DOMAINS or reg0 in FREE_HOSTING or h0 in FREE_HOSTING or reg0 in SHORTENER_DOMAINS
                          or (popularity_rank(reg0) or 10**9) <= 20_000)
                whole_site = next((d for d in rows if re.sub(r"^www\.", "", str(d.get("ioc") or "").lower().split(":")[0]) == h0), None)
                if whole_site and not shared:
                    return {"status": "fail", "source": "ThreatFox", "detail": whole_site.get("malware_printable") or ""}
                if rows and out["status"] == "pass":
                    out = {"status": "warn", "source": "ThreatFox", "detail": ""}
        except Exception as e:
            _PROBLEMS["abusech"] = type(e).__name__
            return {"status": "skip"}
        _PROBLEMS["abusech"] = None
        return out

    return _cached(("abusech2", url), call)   # 2: answers kept before the shared-website fix are not reused


def _cf_scan_conf():
    acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_SCAN_TOKEN", "").strip()
    return (acct, token) if acct and token else None


_PRIVATE_QUERY = re.compile(r"@|%40|(^|[&?])(e?mail|user|login|token|session|key|otp|pass|pwd|phone|mobile|acc|account|id)=|\d{8,}",
                            re.IGNORECASE)
_CF_PENDING = {}     # link -> (time, scan id): a scan started earlier whose answer can be picked up later


def _cf_safe_url(url: str) -> str:
    """Cloudflare's free scans are public, so personal details in the address are left out."""
    p = urlparse(url)
    keep_query = p.query and not _PRIVATE_QUERY.search(p.query)
    return f"{p.scheme}://{p.netloc}{p.path or '/'}" + (f"?{p.query}" if keep_query else "")


def check_cloudflare_scan(url: str, wait: float = 55.0) -> dict:
    """
    Cloudflare's URL Scanner opens the page in a real browser and judges it (phishing kits,
    malware). This catches brand-new scam pages that no list has yet.
    {'status': 'fail'|'pass'|'skip', 'categories': [...]}
    """
    conf = _cf_scan_conf()
    if OFFLINE or not conf:
        return {"status": "skip"}
    acct, token = conf
    target = _cf_safe_url(url)
    base = f"https://api.cloudflare.com/client/v4/accounts/{acct}/urlscanner/v2"
    headers = {"Authorization": f"Bearer {token}"}

    def verdict(data):
        overall = ((data or {}).get("verdicts") or {}).get("overall") or {}
        cats = [c.get("name") if isinstance(c, dict) else str(c) for c in (overall.get("categories") or [])]
        cats += [str(c) for c in (overall.get("phishing") or [])]
        cats = [c for c in cats if c][:3]
        return {"status": "fail" if overall.get("malicious") else "pass", "categories": cats}

    def call():
        deadline = time.time() + wait
        try:
            pending = _CF_PENDING.get(target)
            scan_id = pending[1] if pending and time.time() - pending[0] < 3600 else None
            if not scan_id:
                if not quota("cloudflare_scan").take(wait=min(20.0, wait / 3)):
                    return {"status": "skip", NOT_CHECKED: True}
                r = requests.post(f"{base}/scan", headers=headers, timeout=10,
                                  json={"url": target, "visibility": "Public", "screenshotsResolutions": ["mobile"]})
                if r.status_code == 429:
                    quota("cloudflare_scan").cool_down(60)
                    return {"status": "skip", NOT_CHECKED: True}
                if r.status_code >= 400:
                    _PROBLEMS["cloudflare_scan"] = f"HTTP {r.status_code}"
                    return {"status": "skip", "error": True}
                scan_id = (r.json() or {}).get("uuid")
                if not scan_id:
                    return {"status": "skip", "error": True}
                _CF_PENDING[target] = (time.time(), scan_id)
                time.sleep(12)
            while time.time() < deadline:
                g = requests.get(f"{base}/result/{scan_id}", headers=headers, timeout=10)
                if g.status_code == 200:
                    _CF_PENDING.pop(target, None)
                    _PROBLEMS["cloudflare_scan"] = None
                    return verdict(g.json())
                if g.status_code != 404:
                    _PROBLEMS["cloudflare_scan"] = f"HTTP {g.status_code}"
                    return {"status": "skip", "error": True}
                time.sleep(6)
            return {"status": "skip", NOT_CHECKED: True}   # not ready yet: picked up on the next check
        except Exception as e:
            _PROBLEMS["cloudflare_scan"] = type(e).__name__
            return {"status": "skip", "error": True}

    return _cached(("cfscan", target), call)


OTX_BAD_TAGS = re.compile(r"phish|scam|fraud|malware|trojan|stealer|banker|rat\b|c2|botnet|ransom|spyware|smish",
                          re.IGNORECASE)


def check_otx(domain: str) -> dict:
    """
    AlienVault OTX: security researchers' shared reports ("pulses") that mention this website.
    {'status': 'warn'|'pass'|'skip', 'pulses': n, 'what': 'phishing'}
    """
    key = os.environ.get("OTX_API_KEY", "")
    if OFFLINE or not key or not domain:
        return {"status": "skip"}

    def call():
        if not quota("otx").take(wait=5):
            return {"status": "skip", NOT_CHECKED: True}
        try:
            r = requests.get(f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general",
                             headers={"X-OTX-API-KEY": key, "User-Agent": "StaySafe/2.0"}, timeout=8)
            if r.status_code in (400, 404):
                return {"status": "pass", "pulses": 0}
            if r.status_code != 200:
                _PROBLEMS["otx"] = f"HTTP {r.status_code}"
                return {"status": "skip", "error": True}
            data = r.json()
        except Exception as e:
            _PROBLEMS["otx"] = type(e).__name__
            return {"status": "skip", "error": True}
        _PROBLEMS["otx"] = None
        pulses = (data.get("pulse_info") or {}).get("pulses") or []
        # only reports that call it phishing, scam or malware; known-good lists don't count
        bad = []
        for p in pulses:
            words = " ".join([p.get("name") or ""] + [str(t) for t in (p.get("tags") or [])] +
                             [str((m or {}).get("display_name", "")) for m in (p.get("malware_families") or [])])
            if OTX_BAD_TAGS.search(words):
                bad.append(OTX_BAD_TAGS.search(words).group(0).lower())
        if data.get("validation"):          # OTX itself marks it as a known-good domain
            return {"status": "pass", "pulses": 0}
        if bad:
            return {"status": "warn", "pulses": len(bad), "what": "phishing" if any(
                w.startswith(("phish", "scam", "fraud", "smish")) for w in bad) else "malware"}
        return {"status": "pass", "pulses": 0}

    return _cached(("otx", domain), call)


def check_urlscan(host: str) -> dict:
    """urlscan.io: has this exact website been scanned and marked malicious in the last 90 days?"""
    key = os.environ.get("URLSCAN_API_KEY", "")
    if OFFLINE or not key or not host:
        return {"status": "skip"}

    def call():
        if not quota("urlscan").take(wait=10):
            return {"status": "skip", NOT_CHECKED: True}
        try:
            headers = {"API-Key": key, "User-Agent": "StaySafe/2.0"}
            resp = requests.get("https://urlscan.io/api/v1/search/", timeout=8,
                                params={"q": f'page.domain:"{host}" AND verdicts.malicious:true AND date:>now-90d', "size": 5},
                                headers=headers)
            simple_query = False
            if resp.status_code == 403:
                # Some searches are refused for free accounts: ask more simply and read the verdicts ourselves
                resp = requests.get("https://urlscan.io/api/v1/search/", timeout=8,
                                    params={"q": f'page.domain:"{host}" AND date:>now-90d', "size": 20}, headers=headers)
                simple_query = True
            if resp.status_code != 200:
                _PROBLEMS["urlscan"] = f"HTTP {resp.status_code}"
                if resp.status_code == 429:
                    quota("urlscan").cool_down(60)
                return {"status": "skip", NOT_CHECKED: True}
            data = resp.json()
        except Exception as e:
            _PROBLEMS["urlscan"] = type(e).__name__
            return {"status": "skip"}
        _PROBLEMS["urlscan"] = None
        hits = [r for r in data.get("results", []) if (r.get("page") or {}).get("domain", "").lower() == host
                and (not simple_query or ((r.get("verdicts") or {}).get("malicious") is True)
                     or ((r.get("verdicts") or {}).get("overall") or {}).get("malicious") is True)]
        return {"status": "fail", "count": len(hits)} if hits else {"status": "pass"}

    return _cached(("urlscan", host), call)


def check_server_abuse(ip: str) -> dict:
    """AbuseIPDB: has the server this website runs on been reported for attacks?"""
    key = os.environ.get("ABUSEIPDB_KEY", "")
    if OFFLINE or not key or not ip:
        return {}

    def call():
        if not quota("abuseipdb").take(wait=5):
            return {"none": True, NOT_CHECKED: True}
        try:
            resp = requests.get("https://api.abuseipdb.com/api/v2/check", params={"ipAddress": ip, "maxAgeInDays": 90},
                                headers={"Key": key, "Accept": "application/json"}, timeout=6)
            if resp.status_code == 429:
                quota("abuseipdb").close_day()
            d = resp.json().get("data", {}) if resp.status_code == 200 else {}
        except Exception:
            d = {}
        if not d:
            return {"none": True}
        return {"score": int(d.get("abuseConfidenceScore") or 0), "whitelisted": bool(d.get("isWhitelisted"))}

    out = _cached(("abuseip", ip), call)
    return {} if out.get("none") else out

# ---------------------------------------------------------------------------
# 5. VirusTotal
# ---------------------------------------------------------------------------
VT_WAIT = 35.0   # VirusTotal's free plan allows 4 lookups a minute: wait for a free slot this long


def _vt_get(path: str, wait: float = VT_WAIT, priority: str = "normal"):
    """One VirusTotal lookup, waiting for a free slot of the 4-a-minute allowance if needed."""
    deadline = time.time() + wait
    for _attempt in range(2):
        if not quota("virustotal").take(wait=max(0.0, deadline - time.time()), priority=priority):
            return None, "busy"
        try:
            resp = requests.get(f"https://www.virustotal.com/api/v3/{path}",
                                headers={"x-apikey": VIRUSTOTAL_API_KEY}, timeout=8)
        except Exception as e:
            _PROBLEMS["virustotal"] = f"Could not connect: {type(e).__name__}"
            return None, "error"
        if resp.status_code != 429:
            break
        # VirusTotal says "too many": wait for the next minute and try once more
        quota("virustotal").cool_down(60)
    if resp.status_code == 429:
        return None, "busy"
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


def _vt_report(attrs: dict, scope: str) -> dict:
    """The full VirusTotal result, shown on our own page: what every security company said."""
    from scanners.file_scanner import _engine_list, _vt_date
    stats = attrs.get("last_analysis_stats", {}) or {}
    cats = sorted({str(c) for c in (attrs.get("categories") or {}).values() if c})[:6]
    return {
        "state": "found",
        "scope": scope,                                   # "link" = this exact address, "website" = the whole site
        "malicious": stats.get("malicious", 0),
        "suspicious": stats.get("suspicious", 0),
        "harmless": stats.get("harmless", 0),
        "undetected": stats.get("undetected", 0),
        "total": sum(v for k, v in stats.items() if k in ("malicious", "suspicious", "undetected", "harmless")),
        "engines": _engine_list(attrs.get("last_analysis_results") or {}),
        "categories": cats,
        "reputation": attrs.get("reputation"),
        "first_seen": _vt_date(attrs.get("first_submission_date") or attrs.get("creation_date")),
        "last_analysis": _vt_date(attrs.get("last_analysis_date")),
        "times_submitted": attrs.get("times_submitted"),
        "title": str(attrs.get("title") or "")[:120],
        "tags": (attrs.get("tags") or [])[:6],
    }


def check_virustotal(url: str, domain: str, priority: str = "normal") -> dict:
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
        # VirusTotal stores "https://site.com" as "https://site.com/": try that form first (saves a lookup)
        variants = [url + "/", url] if urlparse(url).path == "" else [url]
        attrs, state = None, "not_found"
        for v in variants:
            url_id = base64.urlsafe_b64encode(v.encode()).decode().strip("=")
            attrs, state = _vt_get(f"urls/{url_id}", wait=VT_WAIT if priority != "low" else 5, priority=priority)
            if state != "not_found":
                break
        if state in ("error", "busy"):
            return {"status": "skip", "error": True}
        if attrs:
            stats = attrs.get("last_analysis_stats", {})
            out.update(status="ok", malicious=stats.get("malicious", 0), suspicious=stats.get("suspicious", 0),
                       harmless=stats.get("harmless", 0), engines=sum(stats.values()) if stats else 0)
            out["report"] = _vt_report(attrs, "link")
        if out["status"] == "ok":
            return out
        # Link never seen: look at the whole website's reputation (also gives its age)
        dattrs, dstate = _vt_get(f"domains/{domain}", wait=15 if priority != "low" else 5, priority=priority)
        if dattrs:
            dstats = dattrs.get("last_analysis_stats", {})
            out["domain_malicious"] = dstats.get("malicious", 0)
            if out["status"] != "ok":
                out.update(status="ok", suspicious=dstats.get("suspicious", 0),
                           harmless=dstats.get("harmless", 0), engines=sum(dstats.values()) if dstats else 0)
            out["report"] = _vt_report(dattrs, "website")
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


def _strip_blocks(html: str) -> str:
    """Remove <script>/<style> blocks in one pass (a regex here can be made to run for minutes)."""
    low = html.lower()
    out, i = [], 0
    while True:
        a = min((x for x in (low.find("<script", i), low.find("<style", i)) if x != -1), default=-1)
        if a == -1:
            out.append(html[i:])
            break
        out.append(html[i:a])
        close = "</script" if low.startswith("<script", a) else "</style"
        b = low.find(close, a)
        if b == -1:
            break
        e = low.find(">", b)
        i = len(html) if e == -1 else e + 1
        out.append(" ")
    return "".join(out)


def _page_title(html: str) -> str:
    low = html.lower()
    a = low.find("<title")
    if a == -1:
        return ""
    s = low.find(">", a)
    if s == -1:
        return ""
    e = low.find("</title", s)
    raw = html[s + 1: e if e != -1 else s + 1000][:2000]
    return re.sub(r"\s+", " ", raw).strip()[:120]


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
    session.trust_env = False  # never go through a proxy set on the server
    try:
        with guarded_fetch():  # every connection re-checked at connect time: public address, web port
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
                    out["title"] = _page_title(html)
                    out["has_password"] = re.search(r"<input[^>]{0,400}type\s*=\s*[\"']?password", html, re.I) is not None
                    text = _strip_blocks(html)
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


_POOL = ThreadPoolExecutor(max_workers=48)
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
    # other dot characters (。．｡) and invisible characters people copy along with a link
    text = re.sub(r"[。．｡]", ".", text)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff\u00ad]", "", text)
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


def _scan_official_short_link(url: str, reg: str):
    """
    A company's own short link (Google's share.google, g.co, youtu.be, amzn.to...). Scammers use
    these too, so whole short-link services end up on community phishing lists, but the service
    itself proves nothing either way. What matters is the page it opens, and whether this EXACT
    short link was reported. None if the destination couldn't be found (normal check then).
    """
    page = _run(fetch_page, url, timeout=16, default=None) or {}
    final = page.get("final_url") or ""
    final_host = (urlparse(final).hostname or "").lower()
    if not final or not final_host or final_host == urlparse(url).hostname or \
            registered_domain(final_host) in OFFICIAL_SHORTENERS:
        return None
    result = scan_url(final, _hop=1)
    result["url"] = url
    result.setdefault("details", {})["final_url"] = final
    # this exact short link reported as a scam? (only exact-address lists count)
    exact = feed_lookup([url], "")
    if exact["status"] != "fail":
        exact = big_feed_lookup([url], "", "")
    gsb = _run(check_safe_browsing, [url], timeout=8, default={"listed": None}) or {}
    if exact["status"] == "fail" or gsb.get("listed"):
        source = exact.get("source") or "Google Safe Browsing"
        text = f"This link is on a public list of scam and malware links ({source})"
        before = result["risk_score"]
        result["findings"].insert(0, text)
        result["risk_score"] = max(before, 95)
        result.setdefault("score_parts", []).append({"label": text, "points": result["risk_score"] - before})
        result["verdict"] = verdict_from_score(result["risk_score"])
    return result


def scan_url(url: str, _hop: int = 0) -> dict:
    url = normalize_url(url)
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    reg = host if is_ip(host) else registered_domain(host)
    inner = unwrap_redirect(url) if _hop < 3 else ""
    if inner:
        # google.com/url?q=..., Facebook/Instagram/Outlook "safe" links: what matters is where it goes
        result = scan_url(inner, _hop=_hop + 1)
        inner_host = (urlparse(normalize_url(inner)).hostname or "").lower()
        result["url"] = url
        result.setdefault("details", {})["final_url"] = inner
        result["findings"].insert(0, f"This link only passes through {host} and actually opens {inner_host}. The result below is for {inner_host}")
        return result
    if reg in OFFICIAL_SHORTENERS and not _hop and not OFFLINE:
        judged = _scan_official_short_link(url, reg)
        if judged:
            return judged

    structure = analyze_structure(url)
    checks = list(structure["checks"])
    findings = list(structure["findings"])
    score = structure["score"]
    from scanners.ledger import Ledger, ADJ_TRUSTED, ADJ_POPULAR
    led = Ledger(structure.get("parts"))
    trusted = structure["trusted"]

    # Slow lookups run at the same time so the whole check takes a few seconds
    dns_f = _POOL.submit(resolve_host, host)
    official_short = structure["shortener"] and reg in OFFICIAL_SHORTENERS
    whois_f = None if (trusted or official_short or structure["hosting"] or is_ip(host)) else _POOL.submit(whois_age_days, reg)
    # extra details for the "Website details" card (also for well-known sites)
    who_f = None if (structure["hosting"] or is_ip(host)) else _POOL.submit(whois_details, reg)
    cert_f = _POOL.submit(cert_details, host) if parsed.scheme == "https" else None
    # Well-known sites (official brands, the world's 10,000 most visited) use VirusTotal only when
    # plenty of today's allowance is left, so it is saved for the unknown links that need it
    well_known = trusted or (not structure["hosting"] and (popularity_rank(reg) or 10**9) <= 10_000)
    # Already on a downloaded scam list (or StaySafe's own reports)? The answer is clear without
    # VirusTotal, so it only uses VirusTotal when plenty is left (for the engine details).
    listed = not trusted and (feed_lookup([url], host)["status"] == "fail"
                              or big_feed_lookup([url], host, reg)["status"] == "fail"
                              or community_listed("link", url))
    vt_f = _POOL.submit(check_virustotal, url, reg, "low" if (well_known or listed) else "normal")
    gsb_f = _POOL.submit(check_safe_browsing, [url, f"{parsed.scheme}://{host}/"])
    page_f = None if trusted else _POOL.submit(fetch_page, url)
    crt_f = None if (trusted or official_short or structure["hosting"] or is_ip(host)) else _POOL.submit(first_certificate_days, host)
    abusech_f = _POOL.submit(check_abusech, url, host)
    urlscan_f = None if (trusted or official_short or is_ip(host)) else _POOL.submit(check_urlscan, host)
    # Cloudflare opens unknown pages in a real browser (not needed for well-known or already-listed links)
    cfscan_f = None if (well_known or listed or official_short) else _POOL.submit(check_cloudflare_scan, url)
    otx_f = None if (well_known or official_short or structure["hosting"] or is_ip(host)) else _POOL.submit(check_otx, reg)
    phishstats_f = None if (trusted or official_short or structure["hosting"] or is_ip(host)) else \
        _POOL.submit(check_phishstats, url, host)

    def result_of(f, default, timeout=10):
        if f is None:
            return default
        try:
            return f.result(timeout=timeout)
        except Exception:
            return default

    dns = result_of(dns_f, {"exists": None, "ips": []}, 5)
    # Protective DNS (Cloudflare 1.1.1.2, Quad9): do these security services refuse this website?
    from scanners import protective_dns
    pdns_f = None if (OFFLINE or trusted or official_short or is_ip(host) or dns["exists"] is False) else \
        _POOL.submit(protective_dns.check, host, dns["exists"])
    page = result_of(page_f, {"ok": False, "error": "skipped", "final_url": url, "hops": [],
                              "ssl_error": False, "title": "", "has_password": False, "text": "",
                              "download": None, "blocked": False}, 16)
    final_url = page.get("final_url") or url
    final_host = (urlparse(final_url).hostname or "").lower()
    gsb = result_of(gsb_f, {"listed": None, "threats": []}, 12)
    if not gsb.get("listed") and final_url != url:
        gsb2 = _run(check_safe_browsing, [final_url], timeout=6, default={"listed": None, "threats": []})
        if gsb2.get("listed"):
            gsb = gsb2
    vt = result_of(vt_f, {"status": "skip"}, 60)
    if official_short and vt.get("domain_malicious"):
        vt = dict(vt, domain_malicious=0)   # reports about the whole short-link service say nothing about this link
    age_days = result_of(whois_f, None, 12)
    if age_days is None and vt.get("created_days") is not None and not trusted:
        age_days = vt["created_days"]
    first_cert_days = result_of(crt_f, None, 8) if age_days is None else None

    # --- does it exist?
    if dns["exists"] is False:
        findings.append("This website doesn't exist or has been shut down. No server answers for this name. Scam links are often taken down after a few days")
        score = led.moved(findings, score, max(score + 40, 55))
        _check(checks, "exists", "fail")
    elif dns["exists"]:
        _check(checks, "exists", "pass")
    else:
        _check(checks, "exists", "skip")

    # --- HTTPS and certificate
    if page.get("ssl_error"):
        findings.append("The website's security certificate is not valid. Your browser would show a warning, and anything you type could be seen by others")
        score += led.note(findings, 30)
        _check(checks, "https", "fail")
    elif parsed.scheme != "https" and not final_url.lower().startswith("https://"):
        findings.append("Link does not use HTTPS (the connection is not encrypted)")
        score += led.note(findings, 10)
        _check(checks, "https", "warn")
    else:
        _check(checks, "https", "pass")

    # --- website age
    if trusted:
        _check(checks, "age", "pass", None)
    elif structure["hosting"] or is_ip(host) or official_short:
        _check(checks, "age", "skip", None)
    elif age_days is None and first_cert_days is not None:
        # registration date hidden: use the date of its first security certificate instead
        if first_cert_days < 30:
            findings.append(f"This website first appeared online only {first_cert_days} days ago. Very new sites are a big warning sign")
            score += led.note(findings, 30)
            _check(checks, "age", "fail", first_cert_days)
        elif first_cert_days < 180:
            findings.append(f"This website first appeared online {first_cert_days} days ago (fairly new)")
            score += led.note(findings, 10)
            _check(checks, "age", "warn", first_cert_days)
        else:
            _check(checks, "age", "pass", first_cert_days)
    elif age_days is None:
        if dns["exists"] is not False:
            findings.append("Could not confirm when this website was created")
            score += led.note(findings, 5)
        _check(checks, "age", "skip", None)
    elif age_days < 30:
        findings.append(f"Website was created only {age_days} days ago. Very new sites are a big warning sign")
        score += led.note(findings, 35)
        _check(checks, "age", "fail", age_days)
    elif age_days < 180:
        findings.append(f"Website is fairly new ({age_days} days old)")
        score += led.note(findings, 15)
        _check(checks, "age", "warn", age_days)
    else:
        _check(checks, "age", "pass", age_days)

    # --- where does it really lead?
    if page.get("ok") or page.get("hops"):
        final_reg = registered_domain(final_host) if final_host and not is_ip(final_host) else final_host
        dest_official = any(_is_official(final_host, d) for d in BRANDS.values()) or final_reg in TRUSTED_DOMAINS
        same_owner = final_host and final_reg != reg and final_reg.split(".")[0] == reg.split(".")[0] and (
            final_host.endswith((".bank.in", ".gov.in", ".nic.in")) or final_reg in TRUSTED_DOMAINS
            or (popularity_rank(final_reg) or 10**9) <= 100_000)
        if final_host and final_reg != reg and official_short and dest_official:
            _check(checks, "redirect", "pass", final_host)   # e.g. Google's share link opening google.com
        elif same_owner:
            _check(checks, "redirect", "pass", final_host)   # same name, new address (banks moving to .bank.in)
        elif final_host and final_reg != reg:
            findings.append(f"This link secretly sends you to a different website: {final_host}")
            _check(checks, "redirect", "warn", final_host)
            dest = analyze_structure(final_url)
            if structure["shortener"] or dest["score"] >= 20:
                score += dest["score"]
                findings.extend(f"Final website: {f}" for f in dest["findings"])
                for dp in dest.get("parts", []):
                    led.add(f"Final website: {dp['label']}", dp["points"])
            else:
                score += led.note(findings, 10)
        else:
            _check(checks, "redirect", "pass", final_host or host)
    elif page.get("error") == "private":
        findings.append("This link points to a private or local network address, not a public website")
        score += led.note(findings, 20)
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
        score += led.note(findings, 40)
        _check(checks, "page", "fail", "apk")
    elif page.get("download") == "program":
        findings.append("Opening this link downloads a program straight away")
        score += led.note(findings, 30)
        _check(checks, "page", "fail", "program")
    elif page.get("ok") and not final_official:
        haystack = (page.get("title", "") + " " + page.get("text", "")[:3000]).lower()
        pretends = next((b for w, b in LOGIN_BRAND_WORDS.items() if re.search(rf"\b{re.escape(w)}\b", haystack)), None)
        otp_words = re.search(r"\b(otp|upi pin|atm pin|cvv|card number|net ?banking|aadhaa?r number)\b", haystack)
        pretends = brand_name(pretends) if pretends else pretends
        if page.get("has_password") and pretends:
            findings.append(f"This page asks for a password and looks like a {pretends} page, but it is not on {pretends}'s website. This is a fake login page")
            score += led.note(findings, 45)
            _check(checks, "page", "fail", pretends)
        elif otp_words and pretends:
            findings.append(f"This page asks for bank or card details and uses the name {pretends}, but it is not {pretends}'s website")
            score += led.note(findings, 40)
            _check(checks, "page", "fail", pretends)
        elif page.get("has_password"):
            findings.append("This page asks you to type a password. Only do that on a website you opened yourself")
            score += led.note(findings, 10)
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
        score = led.moved(findings, score, max(score + 50, 95))
        _check(checks, "google", "fail", names)
    elif gsb.get("listed") is False:
        _check(checks, "google", "pass")
    else:
        _check(checks, "google", "skip")

    # --- Public scam-link lists (OpenPhish, URLhaus)
    feed = feed_lookup([url, final_url], host) if not trusted else {"status": "pass"}
    big = big_feed_lookup([url, final_url], host, reg)
    if trusted and big["status"] == "warn":
        big = {"status": "pass"}
    rank_order = {"fail": 0, "warn": 1, "pass": 2, "skip": 3}
    if rank_order[big["status"]] < rank_order[feed["status"]] or (feed["status"] == "skip" and big["status"] != "skip"):
        feed = big
    ach = result_of(abusech_f, {"status": "skip"}, 14)
    if trusted and ach["status"] == "warn":
        ach = {"status": "pass"}
    if rank_order[ach["status"]] < rank_order[feed["status"]] or (feed["status"] == "skip" and ach["status"] != "skip"):
        feed = ach
    ps = result_of(phishstats_f, {"status": "skip"}, 8)
    if ps["status"] == "warn" and (popularity_rank(reg) or 10**9) <= 20_000:
        ps = {"status": "pass"}      # one reported page on a very popular website doesn't make the site a scam
    for extra in (ps, result_of(pdns_f, {"status": "skip"}, 10)):
        if rank_order[extra["status"]] < rank_order[feed["status"]] or (feed["status"] == "skip" and extra["status"] != "skip"):
            feed = extra
    if feed["status"] == "fail":
        findings.insert(0, f"This link is on a public list of scam and malware links ({feed['source']})")
        score = led.moved(findings, score, max(score + 50, 95))
        _check(checks, "feeds", "fail", feed["source"])
    elif feed["status"] == "warn" and not structure["hosting"] and not structure["shortener"]:
        findings.append(f"Scam pages on this website were reported recently ({feed['source']})")
        score += led.note(findings, 25)
        _check(checks, "feeds", "warn", feed["source"])
    elif feed["status"] == "skip":
        _check(checks, "feeds", "skip")
    else:
        _check(checks, "feeds", "pass")

    # --- StaySafe's own list: reported as a scam by its users
    if not trusted and not OFFLINE:
        try:
            from scanners.reports import community_signal
            sig = community_signal("link", url) or (community_signal("link", final_url) if final_url != url else None)
        except Exception:
            sig = None
        if sig:
            findings.insert(0, sig[0])
            score += led.note(findings, sig[1])
            _check(checks, "community", "fail" if sig[1] >= 35 else "warn", int(re.search(r"\d+", sig[0]).group()))

    # --- urlscan.io: scans by security researchers that found a scam page on this website
    shared_site = structure["hosting"] and host == structure["hosting"]
    # --- RBI Alert List: forex trading platforms not allowed in India
    from scanners import rbi_alert
    rbi_name = rbi_alert.domain_hit(final_host or host, reg, OFFLINE) or rbi_alert.domain_hit(host, reg, OFFLINE)
    if rbi_name:
        findings.insert(0, f"{rbi_name} is on RBI's Alert List of unauthorised forex trading platforms. "
                           "Trading through it is not allowed in India and your money is not protected")
        score = led.moved(findings, score, max(score + 60, 85))
        _check(checks, "rbi", "fail", rbi_name)

    cf = result_of(cfscan_f, {"status": "skip"}, 60)
    if cf.get("status") == "fail":
        kinds = ", ".join(cf.get("categories") or []) or "scam or malware"
        findings.insert(0, f"Cloudflare's scanner opened this page and found it harmful ({kinds})")
        score = led.moved(findings, score, max(score + 50, 90))
        _check(checks, "cfscan", "fail", kinds)
    elif cf.get("status") == "pass":
        _check(checks, "cfscan", "pass")

    otx = result_of(otx_f, {"status": "skip"}, 10)
    if otx.get("status") == "warn" and (popularity_rank(reg) or 10**9) > 20_000:
        findings.append("Security researchers have reported this website for phishing or scams (AlienVault OTX)"
                        if otx.get("what") == "phishing" else
                        "Security researchers have reported this website for spreading malware (AlienVault OTX)")
        score += led.note(findings, 30 if otx.get("pulses", 0) >= 2 else 20)
        _check(checks, "otx", "warn", otx.get("pulses"))
    elif otx.get("status") == "pass":
        _check(checks, "otx", "pass")

    us_res = result_of(urlscan_f, {"status": "skip"}, 12)
    if us_res["status"] == "fail" and not shared_site and (popularity_rank(reg) or 10**9) > 20_000:
        findings.append("Security scans on urlscan.io found a scam or malware page on this website in the last 3 months")
        score += led.note(findings, 30)
        _check(checks, "urlscan", "fail", us_res.get("count"))
    elif us_res["status"] == "pass":
        _check(checks, "urlscan", "pass")

    # --- AbuseIPDB: the server itself
    server_ip = (dns.get("ips") or [None])[0]
    if server_ip and not trusted and not structure["hosting"]:
        ab = _run(check_server_abuse, server_ip, timeout=6, default={}) or {}
        if ab.get("score", 0) >= 50 and not ab.get("whitelisted"):
            findings.append(f"The server this website runs on has been reported for attacks ({ab['score']}% confidence)")
            score += led.note(findings, 10)
            _check(checks, "server", "warn", ab["score"])
        elif ab:
            _check(checks, "server", "pass")

    # --- VirusTotal
    if vt.get("status") == "ok":
        mal, sus = vt.get("malicious", 0), vt.get("suspicious", 0)
        if mal >= 3 or vt.get("domain_malicious", 0) >= 3:
            n = max(mal, vt.get("domain_malicious", 0))
            findings.insert(0, f"{n} security companies on VirusTotal flagged this link as malicious")
            score = led.moved(findings, score, max(score + 40, 90))
            _check(checks, "virustotal", "fail", n)
        elif mal >= 1 or vt.get("domain_malicious", 0) >= 1:
            n = max(mal, vt.get("domain_malicious", 0))
            findings.insert(0, f"{n} security companies on VirusTotal flagged this link as malicious")
            score += led.note(findings, 35)
            _check(checks, "virustotal", "fail", n)
        elif sus:
            findings.append(f"{sus} security companies on VirusTotal flagged this link as suspicious")
            score += led.note(findings, 15)
            _check(checks, "virustotal", "warn", sus)
        else:
            _check(checks, "virustotal", "pass", vt.get("engines") or None)
    elif vt.get("status") == "not_found":
        _check(checks, "virustotal", "info")
    else:
        _check(checks, "virustotal", "skip")

    total = max(0, min(100, score))
    # Known-good sites keep a low score unless a blocklist says otherwise
    if trusted and not gsb.get("listed") and vt.get("malicious", 0) < 3 and feed["status"] != "fail" and not structure.get("apk"):
        if total > 15:
            led.add(ADJ_TRUSTED, 15 - total)
        total = min(total, 15)

    # One of the world's most visited websites: small warning signs (a new-looking name, a
    # risky word) matter less. Real danger signals (lists, security companies, fake login
    # page, lookalike name) are never softened. Lookalike sites are never in this list.
    # (a link shortener being popular says nothing about where this short link goes)
    rank = None if (trusted or structure["hosting"] or is_ip(host) or (structure["shortener"] and not official_short)) \
        else popularity_rank(reg)
    hard = gsb.get("listed") or feed["status"] == "fail" or vt.get("malicious", 0) >= 1 \
        or vt.get("domain_malicious", 0) >= 1 or dns["exists"] is False \
        or structure.get("apk") \
        or any(c["id"] in ("imitation", "page", "cfscan", "community", "rbi") and c["status"] == "fail" for c in checks)
    if rank and not hard:
        _check(checks, "known", "pass", reg)
        checks[:] = [c for c in checks if not (c["id"] == "known" and c["status"] == "info")]
        new_total = min(total, 15) if rank <= 10_000 else max(0, total - 10)   # 15: stays below "caution"
        if new_total != total:
            led.add(ADJ_POPULAR, new_total - total)
        total = new_total

    order = ["rbi", "google", "feeds", "community", "cfscan", "otx", "urlscan", "virustotal", "server", "exists", "imitation", "page", "redirect", "age", "https", "known", "name_tricks"]
    checks.sort(key=lambda c: order.index(c["id"]) if c["id"] in order else 99)

    return {
        "url": url,
        "risk_score": total,
        "verdict": verdict_from_score(total),
        "findings": findings,
        "checks": checks,
        "score_parts": led.result(total),
        "details": {
            "domain": host,
            "registered_domain": reg,
            "final_url": final_url if final_url != url else "",
            "page_title": page.get("title", ""),
            "age_days": age_days,
            "ip": (dns.get("ips") or [""])[0],
            "virustotal": vt.get("report"),
            "whois": result_of(who_f, {}, 10),
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
    raw = str(data.get("url") or "").strip()

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
