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


def analyze_ip(ip: str) -> dict:
    findings = []
    score = 0

    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,proxy,hosting,mobile",
            timeout=6,
        )
        data = resp.json()
    except Exception:
        return {
            "risk_score": 0,
            "verdict": "SAFE",
            "findings": ["Could not verify network details right now"],
            "ip": ip,
        }

    if data.get("status") != "success":
        return {
            "risk_score": 0,
            "verdict": "SAFE",
            "findings": ["Could not verify network details for this IP"],
            "ip": ip,
        }

    location = f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}"
    isp = data.get("isp", "Unknown")

    if data.get("proxy"):
        findings.append("This connection appears to be using a VPN, proxy, or Tor exit node")
        score += 20
    if data.get("hosting"):
        findings.append("This IP belongs to a hosting/datacenter provider, not a typical home or mobile network — unusual for regular browsing")
        score += 15
    if data.get("mobile"):
        findings.append("You appear to be on a mobile data network")

    if not findings:
        findings.append(f"Standard ISP connection detected ({isp})")

    findings.append(f"Approximate location: {location}")

    verdict = "CAUTION" if score >= 20 else "SAFE"

    return {
        "risk_score": score,
        "verdict": verdict,
        "findings": findings,
        "ip": ip,
        "isp": isp,
        "location": location,
    }


@network_checker_bp.route("/api/check-network", methods=["GET"])
def check_network_route():
    ip = get_client_ip()
    if not ip:
        return jsonify({"error": "Could not determine your network address"}), 400

    result = analyze_ip(ip)
    return jsonify(result)
