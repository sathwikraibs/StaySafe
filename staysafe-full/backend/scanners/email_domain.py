"""
StaySafe - Checks on the sender's email domain (free, no key)
---------------------------------------------------------------
- Throwaway addresses: the community "disposable-email-domains" list (CC0, ~5,000 services
  like mailinator or 10minutemail), downloaded once a day, plus a small built-in list.
- Does the domain exist and can it receive email? Asked through Cloudflare's public DNS over
  HTTPS (1.1.1.1), so no extra library is needed.
- Anti-spoofing records (SPF and DMARC). A company domain with a strict DMARC policy can't
  easily be faked in the "From" line; one without it can.
- How old the domain is (registration record, via the link checker's WHOIS / RDAP lookups).
"""

import re
import threading
import time

import requests

DOH_URL = "https://cloudflare-dns.com/dns-query"
DISPOSABLE_URL = ("https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/"
                  "main/disposable_email_blocklist.conf")
BUILT_IN_DISPOSABLE = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.net", "sharklasers.com", "10minutemail.com",
    "temp-mail.org", "tempmail.com", "tempmail.net", "yopmail.com", "trashmail.com", "getnada.com",
    "dispostable.com", "maildrop.cc", "mintemail.com", "throwawaymail.com", "fakeinbox.com", "mohmal.com",
    "emailondeck.com", "tempinbox.com", "moakt.com", "tmail.ws", "mailnesia.com", "burnermail.io",
}
_DISPOSABLE = {"set": set(), "loaded_at": 0.0, "loading": False, "problem": None}
_LOCK = threading.Lock()
_DNS_CACHE: dict = {}


def _refresh_disposable():
    try:
        resp = requests.get(DISPOSABLE_URL, timeout=20, headers={"User-Agent": "StaySafe/2.0"})
        if resp.status_code == 200:
            domains = {l.strip().lower() for l in resp.text.splitlines() if l.strip() and not l.startswith("#")}
            if len(domains) > 500:
                _DISPOSABLE["set"] = domains
                _DISPOSABLE["problem"] = None
        else:
            _DISPOSABLE["problem"] = f"HTTP {resp.status_code}"
    except Exception as e:
        _DISPOSABLE["problem"] = type(e).__name__
    _DISPOSABLE.update(loaded_at=time.time(), loading=False)


def ensure_disposable_list(offline: bool = False) -> None:
    if offline:
        return
    with _LOCK:
        if _DISPOSABLE["loading"] or time.time() - _DISPOSABLE["loaded_at"] < 24 * 3600:
            return
        _DISPOSABLE["loading"] = True
    threading.Thread(target=_refresh_disposable, daemon=True).start()


def is_disposable(domain: str) -> bool:
    domain = (domain or "").lower()
    parts = domain.split(".")
    candidates = {".".join(parts[i:]) for i in range(len(parts) - 1)}
    return bool(candidates & (BUILT_IN_DISPOSABLE | _DISPOSABLE["set"]))


def dns_query(name: str, rtype: str):
    """
    Records of one type through DNS over HTTPS. Returns a list of strings, [] when there are
    none, 'nxdomain' when the name doesn't exist, or None when the lookup failed.
    """
    key = (name.lower(), rtype)
    hit = _DNS_CACHE.get(key)
    if hit and hit[0] > time.time():
        return hit[1]
    try:
        resp = requests.get(DOH_URL, params={"name": name, "type": rtype}, timeout=5,
                            headers={"Accept": "application/dns-json"})
        data = resp.json()
    except Exception:
        return None
    status = data.get("Status")
    if status == 3:
        out = "nxdomain"
    elif status != 0:
        return None
    else:
        out = [str(a.get("data", "")).strip('"') for a in data.get("Answer", []) or []
               if a.get("type") == {"MX": 15, "TXT": 16, "A": 1}.get(rtype)]
    _DNS_CACHE[key] = (time.time() + 3600, out)
    if len(_DNS_CACHE) > 2000:
        _DNS_CACHE.clear()
    return out


def mail_setup(domain: str) -> dict:
    """{'exists': bool|None, 'mx': bool|None, 'spf': bool|None, 'dmarc': 'reject'|'quarantine'|'none'|None|False}"""
    mx = dns_query(domain, "MX")
    if mx == "nxdomain":
        return {"exists": False, "mx": False, "spf": None, "dmarc": None}
    if mx is None:
        return {"exists": None, "mx": None, "spf": None, "dmarc": None}
    has_mx = bool([m for m in mx if m and not m.endswith(" .")])
    if not has_mx:
        a = dns_query(domain, "A")
        has_mx = bool(a) and a != "nxdomain"  # mail can also go to the plain address
    txt = dns_query(domain, "TXT") or []
    spf = any(t.lower().startswith("v=spf1") for t in txt) if isinstance(txt, list) else None
    dm = dns_query(f"_dmarc.{domain}", "TXT")
    dmarc = None
    if isinstance(dm, list):
        rec = next((t for t in dm if t.lower().startswith("v=dmarc1")), "")
        m = re.search(r"\bp=(reject|quarantine|none)\b", rec.lower())
        dmarc = m.group(1) if m else False
    elif dm == "nxdomain":
        dmarc = False
    return {"exists": True, "mx": has_mx, "spf": spf, "dmarc": dmarc}


def domain_signals(domain: str, official: bool, free_mail: bool, offline: bool = False) -> dict:
    """Findings and score about the sender's domain. official = the real domain of the brand it names."""
    out = {"findings": [], "score": 0, "safe": [], "setup": {}, "age_days": None}
    domain = (domain or "").lower()
    if not domain:
        return out
    ensure_disposable_list(offline)
    if is_disposable(domain):
        out["findings"].append("The sender uses a throwaway (temporary) email address that anyone can create in seconds")
        out["score"] += 35
    if offline or free_mail:
        return out
    setup = mail_setup(domain)
    out["setup"] = setup
    if setup["exists"] is False:
        out["findings"].append("The sender's email domain doesn't exist. Nobody can reply to this address")
        out["score"] += 35
        return out
    if setup["mx"] is False:
        out["findings"].append("The sender's email domain can't receive email. Real companies can always receive replies")
        out["score"] += 20
    if not official:
        try:
            from scanners.url_scanner import whois_details, registered_domain
            age = whois_details(registered_domain(domain)).get("age_days")
        except Exception:
            age = None
        out["age_days"] = age
        if age is not None and age < 30:
            out["findings"].append(f"The sender's email domain was registered only {age} days ago. Scammers use brand-new domains")
            out["score"] += 30
        elif age is not None and age < 180:
            out["findings"].append(f"The sender's email domain is fairly new ({age} days old)")
            out["score"] += 10
    if official and setup.get("dmarc") in ("reject", "quarantine"):
        out["safe"].append("This company's email domain is protected against fake senders")
    return out
