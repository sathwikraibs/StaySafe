"""
StaySafe - Network / Wi-Fi Safety Checker
----------------------------------------------
IMPORTANT SCOPE NOTE: No website can read a browser's actual Wi-Fi
SSID, WPA2/WPA3 status, or router settings -- browsers deliberately
block that for privacy. What we CAN meaningfully check:
  - The public IP address the request is coming from
  - Whether that IP belongs to a known VPN/proxy/hosting provider
    (a hint you might be on a public/shared network)
  - Geolocation sanity check (does the IP's location match expectations)
  - Whether the page itself was loaded over HTTPS (checked client-side)

Uses ip-api.com's free tier (no key required, 45 req/min limit).

Register with:
    from network_checker import network_checker_bp
    app.register_blueprint(network_checker_bp)
"""

import time
import requests
from flask import Blueprint, request, jsonify

network_checker_bp = Blueprint("network_checker", __name__)


def get_client_ip() -> str:
    """
    Behind Render/Vercel, the real client IP is usually in X-Forwarded-For.
    Falls back to remote_addr for local testing.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""


def _ip_api(ip: str) -> dict:
    """ip-api.com free tier: last fallback (plain HTTP, non-commercial use only)."""
    from scanners.quota import quota
    if not quota("ip_api").take(wait=10):
        return {}
    resp = requests.get(
        f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,"
        "isp,org,as,proxy,hosting,mobile,timezone,query",
        timeout=6,
    )
    return resp.json()


def _proxycheck(ip: str) -> dict:
    """
    proxycheck.io: VPN / proxy / hosting detection plus location, over HTTPS.
    100 lookups a day without a key, 1,000 a day with a free key (PROXYCHECK_KEY).
    """
    import os
    params = {"vpn": 1, "asn": 1}
    if os.environ.get("PROXYCHECK_KEY"):
        params["key"] = os.environ["PROXYCHECK_KEY"]
    from scanners.quota import quota
    if not quota("proxycheck").take(wait=10, priority="high"):
        return {}
    resp = requests.get(f"https://proxycheck.io/v2/{ip}", params=params, timeout=6)
    data = resp.json()
    if str(data.get("status", "")).lower() == "denied":
        quota("proxycheck").close_day()   # today's free allowance is used; ip-api answers instead
        return {}
    info = data.get(ip) if isinstance(data, dict) else None
    if data.get("status") not in ("ok", "warning") or not isinstance(info, dict):
        return {}
    kind = str(info.get("type", "")).lower()
    return {
        "status": "success",
        "country": info.get("country", ""), "countryCode": info.get("isocode", ""),
        "regionName": info.get("region", ""), "city": info.get("city", ""),
        "isp": info.get("provider", ""), "org": info.get("organisation", "") or info.get("provider", ""),
        "as": info.get("asn", ""), "timezone": info.get("timezone", ""),
        "proxy": str(info.get("proxy", "")).lower() == "yes" or kind in ("vpn", "tor"),
        "hosting": kind in ("hosting", "business hosting", "datacenter"),
        "mobile": kind == "wireless",
        "source": "proxycheck.io",
    }


def _ipinfo(ip: str) -> dict:
    """ipinfo Lite (free, unlimited, HTTPS; IPINFO_TOKEN): country and network owner (ASN)."""
    import os
    token = os.environ.get("IPINFO_TOKEN", "")
    if not token:
        return {}
    resp = requests.get(f"https://api.ipinfo.io/lite/{ip}", params={"token": token}, timeout=6)
    if resp.status_code != 200:
        return {}
    d = resp.json()
    return {"country": d.get("country", ""), "countryCode": d.get("country_code", ""),
            "isp": d.get("as_name", ""), "org": d.get("as_name", ""), "as": d.get("asn", "")}


_IP_CACHE: dict = {}   # ip -> (time, answer): the same visitor checking again costs nothing
_IP_TTL = 6 * 3600


def _ip_cached(kind: str, ip: str, fn):
    now = time.time()
    hit = _IP_CACHE.get((kind, ip))
    if hit and now - hit[0] < _IP_TTL:
        return hit[1]
    value = fn(ip)
    if value:
        _IP_CACHE[(kind, ip)] = (now, value)
        if len(_IP_CACHE) > 3000:
            for k in list(_IP_CACHE)[:1000]:
                _IP_CACHE.pop(k, None)
    return value


def lookup_ip(ip: str) -> dict:
    return _ip_cached("lookup", ip, _lookup_ip)


def _lookup_ip(ip: str) -> dict:
    """Combine the free sources: proxycheck.io (+ ipinfo for the network owner), else ip-api."""
    data = {}
    try:
        data = _proxycheck(ip)
    except Exception:
        data = {}
    try:
        extra = _ipinfo(ip)
        if extra:
            data = {**{"status": "success"}, **data, **{k: v for k, v in extra.items() if v}}
    except Exception:
        pass
    if not data.get("city") or not data.get("timezone"):
        try:
            fallback = _ip_api(ip)
            if fallback.get("status") == "success":
                merged = dict(fallback)
                merged.update({k: v for k, v in data.items() if v not in ("", None)})
                if data:  # proxycheck's VPN verdict wins over ip-api's
                    merged["proxy"] = data.get("proxy", False) or fallback.get("proxy", False)
                data = merged
        except Exception:
            pass
    return data


# Services that should never be open to the whole internet on a home connection
RISKY_PORTS = {23: "Telnet", 2323: "Telnet", 21: "FTP", 3389: "Remote Desktop", 5900: "VNC remote control",
               445: "Windows file sharing", 139: "Windows file sharing", 7547: "router remote management (TR-069)",
               8291: "router remote management", 1900: "UPnP", 5555: "Android remote debugging",
               8080: "router admin page", 8443: "router admin page"}


def _internetdb(ip: str) -> dict:
    """Shodan InternetDB (free, no key): what this internet address shows openly to the whole internet."""
    from scanners.quota import quota
    from scanners import url_scanner
    if url_scanner.OFFLINE or not quota("internetdb").take(wait=3):
        return {}
    try:
        r = requests.get(f"https://internetdb.shodan.io/{ip}", timeout=5)
    except Exception:
        return {}
    if r.status_code == 404:
        return {"ports": [], "vulns": [], "known": False}     # nothing seen open on this address
    if r.status_code != 200:
        return {}
    try:
        d = r.json()
    except Exception:
        return {}
    return {"ports": [int(p) for p in d.get("ports") or [] if str(p).isdigit()],
            "vulns": [str(v) for v in d.get("vulns") or []][:50], "known": True}


def exposed_services(ip: str) -> dict:
    return _ip_cached("internetdb", ip, _internetdb)


def abuse_report(ip: str) -> dict:
    return _ip_cached("abuse", ip, _abuse_report) if ip else {}


def _abuse_report(ip: str) -> dict:
    """AbuseIPDB (free key ABUSEIPDB_KEY, 1,000 checks a day): has this address been reported for attacks?"""
    import os
    from scanners.quota import quota
    key = os.environ.get("ABUSEIPDB_KEY", "")
    if not key or not ip or not quota("abuseipdb").take(wait=5):
        return {}
    try:
        resp = requests.get("https://api.abuseipdb.com/api/v2/check", params={"ipAddress": ip, "maxAgeInDays": 90},
                            headers={"Key": key, "Accept": "application/json"}, timeout=6)
        if resp.status_code != 200:
            return {}
        d = resp.json().get("data", {})
        return {"score": int(d.get("abuseConfidenceScore") or 0), "reports": int(d.get("totalReports") or 0),
                "usage": d.get("usageType") or ""}
    except Exception:
        return {}


_TOR = {"ips": set(), "loaded_at": 0.0, "loading": False}


def _refresh_tor():
    """The Tor Project's own list of Tor exit addresses (free, refreshed hourly)."""
    import requests as _rq
    try:
        resp = _rq.get("https://check.torproject.org/torbulkexitlist", timeout=15,
                       headers={"User-Agent": "StaySafe/2.0"})
        if resp.status_code == 200:
            ips = {l.strip() for l in resp.text.splitlines() if l.strip() and not l.startswith("#")}
            if len(ips) > 100:
                _TOR["ips"] = ips
    except Exception:
        pass
    _TOR.update(loaded_at=time.time(), loading=False)


def is_tor_exit(ip: str) -> bool:
    import threading
    if not _TOR["loading"] and time.time() - _TOR["loaded_at"] > 3600:
        _TOR["loading"] = True
        threading.Thread(target=_refresh_tor, daemon=True).start()
    return ip in _TOR["ips"]


def analyze_ip(ip: str, browser_tz: str = "") -> dict:
    findings = []
    checks = []
    score = 0
    from scanners.ledger import Ledger
    led = Ledger()

    try:
        data = lookup_ip(ip)
    except Exception:
        data = {}

    if data.get("status") != "success":
        return {
            "risk_score": 0,
            "verdict": "SAFE",
            "findings": ["Could not verify network details right now"],
            "checks": [{"id": "net_lookup", "status": "skip", "value": None}],
            "ip": ip,
        }

    parts = [data.get("city", ""), data.get("regionName", ""), data.get("country", "")]
    location = ", ".join(p for p in parts if p)
    isp = data.get("isp", "") or "Unknown"
    ip_tz = data.get("timezone", "")
    ip_version = "IPv6" if ":" in ip else "IPv4"

    if is_tor_exit(ip):
        findings.append("You are using the Tor network. Many banking and payment sites block Tor or ask for extra checks")
        score += led.note(findings, 20)
        checks.append({"id": "net_vpn", "status": "warn", "value": "Tor"})
    elif data.get("proxy"):
        findings.append("This connection appears to be using a VPN, proxy, or Tor exit node")
        score += led.note(findings, 20)
        checks.append({"id": "net_vpn", "status": "warn", "value": None})
    else:
        checks.append({"id": "net_vpn", "status": "pass", "value": None})

    if data.get("hosting"):
        findings.append("This IP belongs to a hosting/datacenter provider, not a typical home or mobile network. Unusual for regular browsing")
        score += led.note(findings, 15)
        checks.append({"id": "net_hosting", "status": "warn", "value": data.get("org") or isp})
    else:
        checks.append({"id": "net_hosting", "status": "pass", "value": isp})

    abuse = abuse_report(ip)
    if abuse:
        if abuse["score"] >= 25:
            findings.append(f"Your internet address has been reported for attacks or spam ({abuse['score']}% confidence). "
                            "This can happen on shared networks like public Wi-Fi or mobile data, or if a device on your network is infected")
            score += led.note(findings, 15 if abuse["score"] >= 50 else 5)
            checks.append({"id": "net_abuse", "status": "warn", "value": abuse["score"]})
        else:
            checks.append({"id": "net_abuse", "status": "pass", "value": None})

    # Is something on this connection (usually the Wi-Fi router) open to the whole internet?
    # Only for home broadband: mobile data, VPNs and datacenters share addresses with many others.
    if not data.get("mobile") and not data.get("proxy") and not data.get("hosting") and ":" not in ip:
        seen = exposed_services(ip)
        if seen:
            risky = sorted({RISKY_PORTS[p] for p in seen.get("ports", []) if p in RISKY_PORTS})
            if risky:
                services = ", ".join(risky)
                findings.append(f"Your internet connection has a service open to the whole internet ({services}). "
                                "If this is your home Wi-Fi, turn off remote access in the router's settings and change its password")
                score += led.note(findings, 15)
                checks.append({"id": "net_exposed", "status": "warn", "value": services})
            else:
                checks.append({"id": "net_exposed", "status": "pass", "value": None})
            if seen.get("vulns"):
                n = len(seen["vulns"])
                findings.append(f"Security scanners found {n} known security holes on your internet address. "
                                "Update your Wi-Fi router's software (firmware), or ask your internet provider to")
                score += led.note(findings, 10)

    if data.get("mobile"):
        findings.append("You appear to be on a mobile data network")
        checks.append({"id": "net_type", "status": "pass", "value": "mobile"})
    else:
        checks.append({"id": "net_type", "status": "info", "value": "broadband"})

    # Your phone's clock zone vs the internet address's zone: a mismatch means traffic
    # is being routed somewhere else (VPN, proxy, or an unusual public Wi-Fi setup).
    if browser_tz and ip_tz:
        if browser_tz == ip_tz or (browser_tz in ("Asia/Calcutta", "Asia/Kolkata") and ip_tz in ("Asia/Calcutta", "Asia/Kolkata")):
            checks.append({"id": "net_timezone", "status": "pass", "value": ip_tz})
        else:
            findings.append(f"Your device's time zone ({browser_tz}) is different from where your internet connection comes out ({ip_tz}). This usually means a VPN or proxy is in use")
            score += led.note(findings, 10)
            checks.append({"id": "net_timezone", "status": "warn", "value": ip_tz})

    if not findings:
        findings.append(f"Standard ISP connection detected ({isp})")

    findings.append(f"Approximate location: {location}")

    verdict = "CAUTION" if score >= 20 else "SAFE"

    return {
        "risk_score": score,
        "verdict": verdict,
        "findings": findings,
        "checks": checks,
        "score_parts": led.result(score),
        "ip": ip,
        "ip_version": ip_version,
        "isp": isp,
        "org": data.get("org", ""),
        "asn": data.get("as", ""),
        "location": location,
        "country_code": data.get("countryCode", ""),
        "timezone": ip_tz,
    }


@network_checker_bp.route("/api/check-network", methods=["GET"])
def check_network_route():
    ip = get_client_ip()
    if not ip:
        return jsonify({"error": "Could not determine your network address"}), 400

    tz = (request.args.get("tz") or "")[:64]
    result = analyze_ip(ip, tz)
    return jsonify(result)
