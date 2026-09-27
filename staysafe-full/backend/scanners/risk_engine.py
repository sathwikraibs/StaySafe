"""
StaySafe - Risk Engine + Dashboard
------------------------------------
Records every scan so the dashboard can show a safety score.

History is kept PER VISITOR: the frontend sends a random anonymous ID in the
`X-Client-Id` header, so people never see each other's checks.

Each scan result also carries a `history_entry` that the frontend saves in
the visitor's own browser. That copy survives Render's free tier putting the
server to sleep (which wipes this in-memory store).

Register with:
    from risk_engine import risk_engine_bp, log_scan
    app.register_blueprint(risk_engine_bp)
"""

import re
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, has_request_context

risk_engine_bp = Blueprint("risk_engine", __name__)

MAX_ENTRIES_PER_CLIENT = 200
MAX_CLIENTS = 1000

# client_id -> list of scan entries (oldest first)
_HISTORY: "OrderedDict[str, list]" = OrderedDict()
_LOCK = threading.Lock()

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
    for key in ("url", "filename", "raw_data", "from", "text_analyzed"):
        value = result.get(key)
        if value:
            return str(value).replace("\n", " ")[:80]
    return scan_type


def log_scan(scan_type: str, result: dict) -> None:
    """
    Call right before returning a scan result. Stores the scan for this
    visitor and adds `history_entry` to the result for the browser copy.
    """
    entry = {
        "type": scan_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_score": result.get("risk_score", 0),
        "verdict": result.get("verdict", "UNKNOWN"),
        "summary": _summary_for(scan_type, result),
    }
    result["history_entry"] = entry

    cid = current_client_id()
    with _LOCK:
        history = _HISTORY.setdefault(cid, [])
        _HISTORY.move_to_end(cid)
        history.append(entry)
        if len(history) > MAX_ENTRIES_PER_CLIENT:
            del history[0]
        while len(_HISTORY) > MAX_CLIENTS:
            _HISTORY.popitem(last=False)


def get_history(cid: str) -> list:
    with _LOCK:
        return list(_HISTORY.get(cid, []))


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
