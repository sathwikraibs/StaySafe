"""
TrustLight - Risk Engine + Dashboard
------------------------------------
Each scan result carries a `history_entry` that the frontend saves in the
visitor's own browser, where the dashboard is built.

Privacy: the server keeps NO copy of anyone's checks. After a result is sent,
nothing about the message, link or file stays on the server (only anonymous
answers about links/files in the long memory, see store.py).

Register with:
    from risk_engine import risk_engine_bp, log_scan
    app.register_blueprint(risk_engine_bp)
"""

import re
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, has_request_context

risk_engine_bp = Blueprint("risk_engine", __name__)


DANGER = ("DANGEROUS", "SCAM_LIKELY")
CAUTION = ("CAUTION", "SUSPICIOUS", "UNCERTAIN")


def current_client_id() -> str:
    if not has_request_context():
        return "anonymous"
    cid = request.headers.get("X-Client-Id", "")
    # accept only simple ids so the header can't be abused
    if re.fullmatch(r"[A-Za-z0-9_-]{8,64}", cid or ""):
        return cid
    return "anonymous"


def _summary_for(scan_type: str, result: dict) -> str:
    for key in ("url", "filename", "raw_data", "from", "text_analyzed", "value"):
        value = result.get(key)
        if value:
            return str(value).replace("\n", " ")[:80]
    return scan_type


def log_scan(scan_type: str, result: dict) -> None:
    """
    Call right before returning a scan result. Adds `history_entry` (kept only in the
    visitor's own browser) to the result.
    """
    entry = {
        "type": scan_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_score": result.get("risk_score", 0),
        "verdict": result.get("verdict", "UNKNOWN"),
        "summary": _summary_for(scan_type, result),
    }
    result["history_entry"] = entry



def get_history(cid: str) -> list:
    """The server keeps no history any more; the visitor's browser has it."""
    return []


def compute_safety_score(history: list) -> dict:
    """
    Turns scan history into a 0-100 'Digital Safety Score'.
    Start at 100 and deduct for risky things found in the last 50 checks.
    """
    recent = history[-50:]
    dangerous_count = sum(1 for s in recent if s["verdict"] in DANGER)
    caution_count = sum(1 for s in recent if s["verdict"] in CAUTION)
    safe_count = len(recent) - dangerous_count - caution_count

    penalty = (dangerous_count * 8) + (caution_count * 3)
    score = max(0, 100 - penalty)

    return {
        "safety_score": score,
        "total_scans": len(history),
        "dangerous_count": dangerous_count,
        "caution_count": caution_count,
        "safe_count": safe_count,
    }


def safety_label(score: int) -> str:
    if score >= 80:
        return "Good"
    if score >= 50:
        return "Needs Attention"
    return "At Risk"


@risk_engine_bp.route("/api/dashboard", methods=["GET"])
def dashboard_route():
    history = get_history(current_client_id())
    stats = compute_safety_score(history)
    return jsonify({
        "safety_score": stats["safety_score"],
        "safety_label": safety_label(stats["safety_score"]),
        "total_scans": stats["total_scans"],
        "breakdown": {
            "dangerous": stats["dangerous_count"],
            "caution": stats["caution_count"],
            "safe": stats["safe_count"],
        },
        "recent_scans": list(reversed(history[-10:])),  # newest first
    })


@risk_engine_bp.route("/api/history", methods=["GET"])
def history_route():
    return jsonify({"history": list(reversed(get_history(current_client_id())))})
