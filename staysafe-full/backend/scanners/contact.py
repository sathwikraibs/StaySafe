"""
TrustLight - "Talk to a person" form
-----------------------------------
A visitor fills a short form in the TrustLight Helper. The message reaches the TrustLight team
straight away on their phone, for free, even when nobody is logged in to the live chat:

  1. Telegram (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID): an instant notification in the Telegram
     app, with tap-to-reply links for the visitor's email or WhatsApp. Free, no card, no limit
     that a small site could reach.
  2. Email through Resend (RESEND_API_KEY + CONTACT_EMAIL): a copy in the inbox. Free plan:
     100 emails a day, no card; the default sender can send to your own address.

The message is delivered if at least one of them works. Nothing is stored on our server.
Long numbers that look like card, account or Aadhaar numbers, and OTPs, are hidden before
sending, so they never sit in anyone's inbox.
"""

import html
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque

import requests
from flask import Blueprint, jsonify, request

from scanners.security import client_ip

contact_bp = Blueprint("contact", __name__)

LANGS = {"en": "English", "hi": "Hindi", "kn": "Kannada", "tcy": "Tulu"}
LOST = {"yes": "YES", "no": "No", "unsure": "Not sure"}
TOPICS = {"lost_money", "check_msg", "clicked", "report", "digital_arrest", "job_invest", "hacked", "about", ""}

_per_ip: "defaultdict[str, deque]" = defaultdict(deque)
_lock = threading.Lock()
PER_IP_HOUR = 5


def _telegram_ready() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def _email_ready() -> bool:
    return bool(os.environ.get("RESEND_API_KEY") and os.environ.get("CONTACT_EMAIL"))


def contact_status() -> dict:
    return {"telegram": _telegram_ready(), "email": _email_ready()}


def _hide_sensitive(text: str) -> str:
    """Hide OTPs and long card/account/Aadhaar-like numbers. Phone numbers (10 digits) stay."""
    text = re.sub(r"(?i)\b(otp|pin|cvv|password|passcode)\b(\W{0,12})([\w@#$%&*!-]{3,12})", r"\1\2[hidden]", text)
    return re.sub(r"(?<!\d)(?:\d[ -]?){11,19}\d(?!\d)", "[number hidden]", text)


def _allowed(ip: str) -> bool:
    now = time.time()
    with _lock:
        q = _per_ip[ip]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= PER_IP_HOUR:
            return False
        q.append(now)
        return True


def _send_telegram(text_html: str) -> bool:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=10, json={
            "chat_id": chat, "text": text_html[:4000], "parse_mode": "HTML", "disable_web_page_preview": True})
        return r.status_code == 200 and r.json().get("ok") is True
    except Exception:
        return False


def _send_email(subject: str, text_html: str, reply_to: str) -> bool:
    body = {"from": os.environ.get("CONTACT_FROM", "TrustLight <onboarding@resend.dev>"),
            "to": [os.environ.get("CONTACT_EMAIL", "")], "subject": subject[:150],
            "html": text_html.replace("\n", "<br>")}
    if reply_to:
        body["reply_to"] = reply_to
    try:
        r = requests.post("https://api.resend.com/emails", timeout=10, json=body,
                          headers={"Authorization": f"Bearer {os.environ.get('RESEND_API_KEY', '')}"})
        return r.status_code in (200, 201)
    except Exception:
        return False


@contact_bp.route("/api/contact/status", methods=["GET"])
def contact_status_route():
    """Only says whether the form can be used (never which services are set up)."""
    return jsonify({"available": _telegram_ready() or _email_ready()})


@contact_bp.route("/api/contact", methods=["POST"])
def contact_route():
    data = request.get_json(silent=True) or {}
    if str(data.get("website") or "").strip():          # hidden field only bots fill in
        return jsonify({"ok": True, "ref": "SS-" + secrets.token_hex(3).upper()})
    if not (_telegram_ready() or _email_ready()):
        return jsonify({"error": "Messages can't be sent right now. Please use the live chat instead."}), 503

    name = re.sub(r"\s+", " ", str(data.get("name") or "")).strip()[:80]
    email = str(data.get("email") or "").strip()[:120]
    phone = re.sub(r"[^\d+]", "", str(data.get("phone") or ""))[:16]
    message = str(data.get("message") or "").strip()[:1500]
    lost = str(data.get("lost") or "").lower()
    lang = str(data.get("lang") or "en").lower()
    topic = str(data.get("topic") or "")
    page = str(data.get("page") or "")[:60]

    if len(message) < 5:
        return jsonify({"error": "Please tell us a little about what happened."}), 400
    if email and not re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,100}\.[A-Za-z]{2,24}", email):
        return jsonify({"error": "That email address doesn't look right. It should look like name@example.com"}), 400
    if phone and not re.fullmatch(r"\+?\d{10,15}", phone):
        return jsonify({"error": "That phone number doesn't look right. Please enter a 10-digit mobile number."}), 400
    if not email and not phone:
        return jsonify({"error": "Please add your email or WhatsApp number so we can reply to you."}), 400
    if not _allowed(client_ip()):
        return jsonify({"error": "You've sent a few messages already. We'll reply soon. Please wait for our answer."}), 429

    ref = "SS-" + secrets.token_hex(3).upper()
    urgent = lost == "yes"
    wa = phone if phone.startswith("+") else ("+91" + phone[-10:] if len(phone) >= 10 else phone)
    e = html.escape
    lines = [
        f"{'🚨 URGENT: money lost' if urgent else '💬 New message'} · <b>{ref}</b>",
        f"Name: {e(name) or '(not given)'}",
        f"Lost money: {LOST.get(lost, 'not said')}",
        f"Language: {LANGS.get(lang, e(lang))}",
    ]
    if topic in TOPICS and topic:
        lines.append(f"Helper topic: {e(topic)}")
    if page:
        lines.append(f"Page: {e(page)}")
    if email:
        lines.append(f"Email: {e(email)}")
    if phone:
        digits = re.sub(r"\D", "", wa)
        lines.append(f'WhatsApp: <a href="https://wa.me/{digits}">{e(wa)}</a>')
    lines += ["", e(_hide_sensitive(message))]
    text = "\n".join(lines)

    sent_tg = _send_telegram(text) if _telegram_ready() else False
    sent_mail = _send_email(f"[TrustLight {ref}]{' URGENT' if urgent else ''} {name or 'New message'}", text, email) \
        if _email_ready() else False
    if not (sent_tg or sent_mail):
        return jsonify({"error": "We couldn't send your message right now. Please try the live chat, or try again in a minute."}), 502
    return jsonify({"ok": True, "ref": ref})
