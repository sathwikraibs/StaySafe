"""
"Support TrustLight": an optional way for people to give a voluntary contribution.

Set on the server (Render environment), nothing in the code:
  SUPPORT_LINK  a payment page made in TrustLight's name (https://...), shown as the main button
  SUPPORT_UPI   a UPI ID (name@bank), optional. Note: UPI apps show the account holder's bank name.
Nothing is shown in the app until at least one of them is set.
"""
import os
import re
from urllib.parse import urlparse

from flask import Blueprint, jsonify

support_bp = Blueprint("support", __name__)

UPI_RE = re.compile(r"^[a-zA-Z0-9.\-_]{2,64}@[a-zA-Z][a-zA-Z0-9.\-]{1,32}$")


def support_info() -> dict:
    link = os.environ.get("SUPPORT_LINK", "").strip()
    upi = os.environ.get("SUPPORT_UPI", "").strip()
    try:
        u = urlparse(link)
        link = link if u.scheme == "https" and u.netloc and len(link) <= 300 else ""
    except ValueError:
        link = ""
    upi = upi if UPI_RE.match(upi) else ""
    return {"available": bool(link or upi), "link": link, "upi": upi, "name": "TrustLight"}


@support_bp.route("/api/support", methods=["GET"])
def support_route():
    resp = jsonify(support_info())
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp
