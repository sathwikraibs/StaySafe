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


def lookup_ip(ip: str) -> dict:
    resp = requests.get(
        f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,"
        "isp,org,as,proxy,hosting,mobile,timezone,query",
        timeout=6,
    )
    return resp.json()


def analyze_ip(ip: str, browser_tz: str = "") -> dict:
    findings = []
    checks = []
    score = 0

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

    if data.get("proxy"):
        findings.append("This connection appears to be using a VPN, proxy, or Tor exit node")
        score += 20
        checks.append({"id": "net_vpn", "status": "warn", "value": None})
    else:
        checks.append({"id": "net_vpn", "status": "pass", "value": None})

    if data.get("hosting"):
        findings.append("This IP belongs to a hosting/datacenter provider, not a typical home or mobile network. Unusual for regular browsing")
        score += 15
        checks.append({"id": "net_hosting", "status": "warn", "value": data.get("org") or isp})
    else:
        checks.append({"id": "net_hosting", "status": "pass", "value": isp})

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
            score += 10
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
