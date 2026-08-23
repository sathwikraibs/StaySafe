"""
StaySafe - Risk Engine + Dashboard
------------------------------------
Combines results from all scanner modules into a unified history log
and exposes a dashboard endpoint showing the user's overall safety picture.

Uses simple in-memory storage for now (swap for Firestore/SQLite later —
see the note at the bottom).

Register with:
    from risk_engine import risk_engine_bp, log_scan
    app.register_blueprint(risk_engine_bp)
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify

risk_engine_bp = Blueprint("risk_engine", __name__)

# ---------------------------------------------------------------------------
# IN-MEMORY SCAN HISTORY
# Replace this list with a real database call in log_scan() / get_history()
# when you're ready (Firestore example is at the bottom of this file).
# ---------------------------------------------------------------------------
SCAN_HISTORY = []


def log_scan(scan_type: str, result: dict) -> None:
    """
    Call this from url_scanner.py / message_scanner.py right after
    producing a result, so every scan gets recorded for the dashboard.

    Example (inside scan_url_route, right before `return jsonify(result)`):
        from risk_engine import log_scan
        log_scan("url", result)
    """
    SCAN_HISTORY.append({
        "type": scan_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_score": result.get("risk_score", 0),
        "verdict": result.get("verdict", "UNKNOWN"),
        "summary": result.get("url") or result.get("text_analyzed", "")[:80],
    })
    # keep only the most recent 200 entries so this doesn't grow forever
    if len(SCAN_HISTORY) > 200:
        SCAN_HISTORY.pop(0)


def compute_safety_score() -> dict:
    """
    Turns scan history into a 0-100 'Digital Safety Score'.
    Logic: start at 100, deduct for risky scans found recently.
    More dangerous verdicts and more recent scans matter more.
    """
    if not SCAN_HISTORY:
        return {
            "safety_score": 100,
            "total_scans": 0,
            "dangerous_count": 0,
            "caution_count": 0,
            "safe_count": 0,
        }

    recent = SCAN_HISTORY[-50:]  # weight recent activity most
    dangerous_count = sum(1 for s in recent if s["verdict"] in ("DANGEROUS", "SCAM_LIKELY"))
    caution_count = sum(1 for s in recent if s["verdict"] in ("CAUTION", "SUSPICIOUS"))
    safe_count = len(recent) - dangerous_count - caution_count

    penalty = (dangerous_count * 8) + (caution_count * 3)
    score = max(0, 100 - penalty)

    return {
        "safety_score": score,
        "total_scans": len(SCAN_HISTORY),
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


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------
@risk_engine_bp.route("/api/dashboard", methods=["GET"])
def dashboard_route():
    stats = compute_safety_score()
    return jsonify({
        "safety_score": stats["safety_score"],
        "safety_label": safety_label(stats["safety_score"]),
        "total_scans": stats["total_scans"],
        "breakdown": {
            "dangerous": stats["dangerous_count"],
            "caution": stats["caution_count"],
            "safe": stats["safe_count"],
        },
        "recent_scans": list(reversed(SCAN_HISTORY[-10:])),  # newest first
    })


@risk_engine_bp.route("/api/history", methods=["GET"])
def history_route():
    return jsonify({"history": list(reversed(SCAN_HISTORY))})


# ---------------------------------------------------------------------------
# OPTIONAL: swap in Firestore later like this
# ---------------------------------------------------------------------------
# from firebase_admin import firestore
# db = firestore.client()
#
# def log_scan(scan_type, result):
#     db.collection("scan_history").add({
#         "type": scan_type,
#         "timestamp": datetime.now(timezone.utc),
#         "risk_score": result.get("risk_score", 0),
#         "verdict": result.get("verdict", "UNKNOWN"),
#     })
