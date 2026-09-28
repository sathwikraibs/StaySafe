"""
StaySafe - "I Already Clicked It" Incident Response Wizard
--------------------------------------------------------------
User selects what happened (clicked a link, entered password, shared OTP,
installed an app, sent money, etc.) and gets an immediate, ordered
action plan. No AI needed here. This is a lookup table, which makes
it fast, reliable, and easy to defend in a project viva.

Register with:
    from incident_wizard import incident_wizard_bp
    app.register_blueprint(incident_wizard_bp)
"""

from flask import Blueprint, request, jsonify

incident_wizard_bp = Blueprint("incident_wizard", __name__)

# ---------------------------------------------------------------------------
# INCIDENT TYPES -> ORDERED ACTION PLAN
# ---------------------------------------------------------------------------
INCIDENT_PLANS = {
    "clicked_link": {
        "label": "I clicked a suspicious link",
        "steps": [
            "Don't enter any information if a page asks for login/payment details.",
            "Close the browser tab immediately.",
            "Run a virus scan on your device. No antivirus app? Download a free, trusted one from the links below.",
            "Check your recent account activity for anything unusual.",
            "Avoid using that device for banking until you've scanned it.",
        ],
    },
    "entered_password": {
        "label": "I entered my password on a suspicious site",
        "steps": [
            "Change that password immediately using the app or the site's real address (type it yourself, don't click a link).",
            "If you reuse that password anywhere else (especially email), change it there too.",
            "Enable multi-factor authentication (MFA) on the affected account.",
            "Check the account's recent login activity/sessions and log out unfamiliar devices.",
            "Monitor the account for a few days for anything unusual.",
        ],
    },
    "entered_card_details": {
        "label": "I entered my card/bank details",
        "steps": [
            "Call your bank's official number (from the back of your card, not from the message) immediately.",
            "Ask them to block/freeze the card if you suspect misuse.",
            "Check recent transactions and dispute anything unauthorized.",
            "Do not share any OTP that arrives after this, even if someone calls claiming to be your bank.",
            "Set up transaction alerts if not already enabled.",
        ],
    },
    "shared_otp": {
        "label": "I shared an OTP or PIN",
        "steps": [
            "If this was for a payment, check immediately whether money was deducted.",
            "Call your bank's official helpline right now to flag possible fraud.",
            "Change your net-banking/UPI app password.",
            "If money was lost, report it via India's Cyber Crime helpline: dial 1930 or visit cybercrime.gov.in immediately. Faster reporting increases the chance of recovery.",
            "Do not respond to further calls/messages asking for more codes. This is a common follow-up scam tactic.",
        ],
    },
    "installed_app": {
        "label": "I installed a suspicious app/APK",
        "steps": [
            "Turn off Wi-Fi/mobile data on the device to stop it communicating.",
            "Do not log into banking or email apps on this device until it's cleaned.",
            "Uninstall the app immediately if the device still lets you.",
            "Check Settings > Apps for unfamiliar 'Device Admin' or 'Accessibility' permissions and revoke them.",
            "Run a mobile security scan (Google Play Protect or a trusted antivirus app).",
            "Change your important passwords from a different, clean device.",
        ],
    },
    "gave_remote_access": {
        "label": "I gave someone remote access to my device (AnyDesk/TeamViewer etc.)",
        "steps": [
            "Uninstall the remote access app immediately.",
            "Turn off Wi-Fi/mobile data to end the session right now.",
            "Restart your device.",
            "Change all important passwords from a different device. Assume anything typed during the session was seen.",
            "Contact your bank if any banking app was open during the session.",
            "Report to Cyber Crime helpline 1930 / cybercrime.gov.in if this involved a 'bank support' or 'refund' call.",
        ],
    },
    "money_transferred": {
        "label": "Money was already transferred/lost",
        "steps": [
            "Call your bank's fraud helpline immediately to request a transaction reversal/hold.",
            "Report immediately at cybercrime.gov.in or call 1930 (India's national cyber fraud helpline). The first few hours matter most for recovery.",
            "Save all evidence: screenshots of messages, transaction ID, the scammer's number/UPI ID.",
            "File a complaint at your local police station if the portal advises it.",
            "Change all financial app passwords and enable MFA.",
        ],
    },
    "account_accessed": {
        "label": "Someone accessed my account without permission",
        "steps": [
            "Change the password immediately from a trusted device.",
            "Log out of all sessions/devices from the account's security settings.",
            "Enable MFA if not already on.",
            "Check account recovery info (backup email/phone) hasn't been changed by the attacker.",
            "Check for unauthorized activity (sent emails, posts, purchases) and report/undo where possible.",
        ],
    },
}


@incident_wizard_bp.route("/api/incident-options", methods=["GET"])
def incident_options_route():
    """Returns the list of incident types for the frontend to render as buttons."""
    return jsonify({
        "options": [
            {"id": key, "label": plan["label"]}
            for key, plan in INCIDENT_PLANS.items()
        ]
    })


@incident_wizard_bp.route("/api/incident-plan", methods=["POST"])
def incident_plan_route():
    data = request.get_json(silent=True) or {}
    incident_type = str(data.get("incident_type", ""))[:80]

    plan = INCIDENT_PLANS.get(incident_type)
    if not plan:
        return jsonify({
            "error": "Unknown incident_type",
            "valid_options": list(INCIDENT_PLANS.keys()),
        }), 400

    return jsonify({
        "incident_type": incident_type,
        "label": plan["label"],
        "action_plan": plan["steps"],
    })
