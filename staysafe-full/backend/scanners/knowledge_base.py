"""
TrustLight - Scam Knowledge Base
------------------------------------
A searchable reference of common scam categories, useful when the user
doesn't have a specific link/message to check but wants to know
"what does a bank scam usually look like?"

Pure static data + simple search -- no external APIs needed.

Register with:
    from knowledge_base import knowledge_base_bp
    app.register_blueprint(knowledge_base_bp)
"""

from flask import Blueprint, request, jsonify

knowledge_base_bp = Blueprint("knowledge_base", __name__)

SCAM_LIBRARY = [
    {
        "id": "kyc_scam",
        "category": "Bank",
        "title": "KYC / Account Suspension Scam",
        "how_it_works": "You get an SMS or call claiming your bank account will be blocked unless you 'update KYC' immediately, usually with a link or a request to install a remote-access app.",
        "red_flags": [
            "Urgency, like 'within 24 hours' or 'today'",
            "Link doesn't go to your bank's real domain",
            "Asks you to install AnyDesk/TeamViewer",
            "Asks for OTP, PIN, or card details",
        ],
        "what_to_do": "Ignore the message. Open your bank's app directly or call the number on your card to verify.",
    },
    {
        "id": "fake_refund",
        "category": "Shopping",
        "title": "Fake Refund / Delivery Scam",
        "how_it_works": "A message claims a refund, delivery fee, or customs charge is pending and asks you to 'accept' it by scanning a QR code or entering your UPI PIN.",
        "red_flags": [
            "Asks you to enter UPI PIN to 'receive' money. You never need a PIN to receive",
            "Unexpected refund you didn't request",
            "Pressure to act immediately or lose the refund",
        ],
        "what_to_do": "Never enter your PIN to receive money. Check the order status directly in the shopping app.",
    },
    {
        "id": "job_scam",
        "category": "Jobs",
        "title": "Fake Job Offer Scam",
        "how_it_works": "You're offered a high-paying work-from-home job, then asked to pay a 'registration' or 'training' fee before starting.",
        "red_flags": [
            "Any legitimate employer asking you to pay to get hired",
            "Contact only through WhatsApp/Telegram, no official email",
            "Salary sounds too good for the effort described",
        ],
        "what_to_do": "Never pay to get a job. Verify the company independently before sharing any documents.",
    },
    {
        "id": "investment_scam",
        "category": "Investment",
        "title": "Guaranteed-Returns Investment Scam",
        "how_it_works": "A 'trading group' or app promises guaranteed daily/weekly returns on crypto or stock trading, often via a WhatsApp/Telegram group with fake screenshots of profits.",
        "red_flags": [
            "Guaranteed or fixed high returns",
            "Pressure to deposit more once you're 'in profit' (to withdraw)",
            "Unregistered trading app, not on Play Store/App Store",
        ],
        "what_to_do": "No legitimate investment guarantees returns. Verify SEBI/RBI registration before investing anything.",
    },
    {
        "id": "digital_arrest",
        "category": "Government Impersonation",
        "title": "'Digital Arrest' / Fake Police Scam",
        "how_it_works": "A caller claims to be police/customs/CBI, says you're implicated in a crime, and demands you stay on a video call and transfer money to 'clear your name'.",
        "red_flags": [
            "Real police never conduct 'arrests' over video call",
            "Demands for money transfer to avoid arrest",
            "Threatens and isolates you from contacting family",
        ],
        "what_to_do": "Hang up. This is always a scam. Report at cybercrime.gov.in or call 1930.",
    },
    {
        "id": "tech_support_scam",
        "category": "Tech Support",
        "title": "Fake Tech Support Popup",
        "how_it_works": "A browser popup claims your device has a virus and shows a phone number to 'call Microsoft/Google support' immediately.",
        "red_flags": [
            "Popups with countdown timers or loud alarm sounds",
            "Asks you to call a number shown in the browser",
            "Real security software never asks you to call a number in a popup",
        ],
        "what_to_do": "Close the browser tab (or force-close the browser). Don't call the number. Run a scan with your actual antivirus if worried.",
    },
    {
        "id": "romance_scam",
        "category": "Social",
        "title": "Romance / Relationship Scam",
        "how_it_works": "Someone builds an online relationship over weeks, then invents an emergency (medical bill, travel, customs fee) and asks for money.",
        "red_flags": [
            "Never willing to video call or meet in person",
            "Relationship escalates to requests for money quickly",
            "Excuses for why they can't verify identity",
        ],
        "what_to_do": "Never send money to someone you haven't met in person. Reverse image search their photos.",
    },
    {
        "id": "sim_swap",
        "category": "Account Security",
        "title": "SIM Swap Fraud",
        "how_it_works": "A scammer tricks your telecom provider into issuing a duplicate SIM for your number, giving them your OTPs and effectively taking over your accounts.",
        "red_flags": [
            "Your phone suddenly loses network signal for no reason",
            "You get an SMS about a SIM swap/port request you didn't initiate",
        ],
        "what_to_do": "Contact your telecom provider immediately if signal drops unexpectedly. Enable app-based MFA (not just SMS) where possible.",
    },
]


@knowledge_base_bp.route("/api/scam-library", methods=["GET"])
def scam_library_route():
    """Optional ?q=search_term and ?category=Bank query params."""
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip().lower()

    results = SCAM_LIBRARY
    if category:
        results = [s for s in results if s["category"].lower() == category]
    if query:
        results = [
            s for s in results
            if query in s["title"].lower()
            or query in s["how_it_works"].lower()
            or query in s["category"].lower()
        ]

    return jsonify({"count": len(results), "scams": results})


@knowledge_base_bp.route("/api/scam-library/categories", methods=["GET"])
def scam_categories_route():
    categories = sorted(set(s["category"] for s in SCAM_LIBRARY))
    return jsonify({"categories": categories})
