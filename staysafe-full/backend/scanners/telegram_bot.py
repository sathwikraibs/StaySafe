"""
StaySafe - Telegram bot (@YourStaySafeBot)
--------------------------------------------
People forward a message, a link, a screenshot, a QR photo, a file, a phone number or a UPI
ID to the bot and get the same check the website gives, in a short reply.

Free: Telegram's Bot API costs nothing. Setup (once):
  1. In Telegram, talk to @BotFather, send /newbot, pick a name. It gives a token.
  2. On Render, add the environment variable TELEGRAM_SCAN_BOT_TOKEN = that token. (This must be a
     NEW bot: TELEGRAM_BOT_TOKEN is the private bot that brings contact-form messages to you.)
  3. Open https://<backend>/api/telegram/setup?key=<STATUS_KEY> once. It tells Telegram
     where to send messages (a webhook, with a secret only Telegram and StaySafe know).

The bot reuses the website's own checks by calling the API routes inside this server, so
both always give the same answer. Each Telegram chat has its own rate limit.
"""

import hashlib
import hmac
import os
import re
import threading
import time

import requests
from flask import Blueprint, jsonify, request

from scanners.security import has_status_key

telegram_bp = Blueprint("telegram", __name__)

API = "https://api.telegram.org"
SITE = "https://staysafe-tool.vercel.app"
MAX_FILE = 20 * 1024 * 1024  # Telegram bots can download files up to 20 MB

_LANG = {}           # chat id -> chosen language (kept in memory)
_SEEN = {}           # update id -> time, so a retried update isn't checked twice
_SEEN_LOCK = threading.Lock()


def _token() -> str:
    return os.environ.get("TELEGRAM_SCAN_BOT_TOKEN", "").strip()


def _secret() -> str:
    """Secret Telegram sends back with every update, made from the token (nothing extra to set)."""
    t = _token()
    return hashlib.sha256(("staysafe-webhook:" + t).encode()).hexdigest()[:48] if t else ""


def telegram_status() -> bool:
    return bool(_token())


# --- Texts ---------------------------------------------------------------------------------
TEXTS = {
    "en": {
        "hello": ("Hi! I'm StaySafe. Send or forward me anything you're not sure about and I'll check it for scams:\n"
                  "• a message (SMS, WhatsApp, email)\n• a link\n• a screenshot or a photo of a QR code\n"
                  "• a file (APK, PDF...)\n• a phone number or UPI ID\n\n"
                  "Language: /en English, /hi हिन्दी, /kn ಕನ್ನಡ, /tcy ತುಳು\n"
                  "Lost money? Call 1930 right away."),
        "checking": "Checking it carefully. This can take up to a minute...",
        "SAFE": "✅ Looks safe", "CAUTION": "⚠️ Be careful", "DANGEROUS": "🛑 Looks like a scam",
        "UNCERTAIN": "⚠️ Not sure: be careful",
        "do_SAFE": "No strong warning signs. Still, never share an OTP or PIN.",
        "do_CAUTION": "Don't click, pay or share anything until you've checked with the real company yourself.",
        "do_DANGEROUS": "Don't click, reply or pay. Block the sender. If you already paid or shared details, call 1930 now.",
        "score": "Risk: {n}/100",
        "noticed": "What we noticed:",
        "full": "Full check in your language on the website: {url}",
        "busy": "Too many checks right now. Please try again in a minute.",
        "fail": "Sorry, I couldn't check that. Please try again, or use the website: {url}",
        "unknown": "Please send a message, link, screenshot, file, phone number or UPI ID to check.",
        "big": "That file is too big for me (over 20 MB). Use the website instead: {url}",
        "lang": "OK, I'll reply in English.",
    },
    "hi": {
        "hello": ("नमस्ते! मैं StaySafe हूँ। जिस चीज़ पर शक हो, मुझे भेजें या फ़ॉरवर्ड करें, मैं जाँच करूँगा कि कहीं यह ठगी तो नहीं:\n"
                  "• मैसेज (SMS, WhatsApp, ईमेल)\n• लिंक\n• स्क्रीनशॉट या QR कोड की फ़ोटो\n"
                  "• फ़ाइल (APK, PDF...)\n• फ़ोन नंबर या UPI ID\n\n"
                  "भाषा: /en English, /hi हिन्दी, /kn ಕನ್ನಡ, /tcy ತುಳು\n"
                  "पैसे गए हैं? तुरंत 1930 पर कॉल करें।"),
        "checking": "ध्यान से जाँच हो रही है। इसमें एक मिनट तक लग सकता है...",
        "SAFE": "✅ सुरक्षित लगता है", "CAUTION": "⚠️ सावधान रहें", "DANGEROUS": "🛑 ठगी लगती है",
        "UNCERTAIN": "⚠️ पक्का नहीं: सावधान रहें",
        "do_SAFE": "खतरे का कोई बड़ा संकेत नहीं मिला। फिर भी OTP या PIN कभी न बताएँ।",
        "do_CAUTION": "जब तक असली कंपनी से खुद पक्का न कर लें, तब तक कुछ भी क्लिक न करें, पैसे न भेजें और कोई जानकारी न दें।",
        "do_DANGEROUS": "क्लिक न करें, जवाब न दें, पैसे न भेजें। भेजने वाले को ब्लॉक करें। अगर पैसे भेज दिए या जानकारी दे दी है, तो अभी 1930 पर कॉल करें।",
        "score": "खतरा: {n}/100",
        "noticed": "हमने क्या देखा (अंग्रेज़ी में):",
        "full": "वेबसाइट पर हिन्दी में पूरी जाँच: {url}",
        "busy": "अभी बहुत ज़्यादा जाँचें हो रही हैं। कृपया एक मिनट बाद फिर कोशिश करें।",
        "fail": "माफ़ करें, यह जाँच नहीं हो पाई। फिर कोशिश करें, या वेबसाइट इस्तेमाल करें: {url}",
        "unknown": "जाँच के लिए मैसेज, लिंक, स्क्रीनशॉट, फ़ाइल, फ़ोन नंबर या UPI ID भेजें।",
        "big": "यह फ़ाइल मेरे लिए बहुत बड़ी है (20 MB से ज़्यादा)। वेबसाइट इस्तेमाल करें: {url}",
        "lang": "ठीक है, मैं हिन्दी में जवाब दूँगा।",
    },
    "kn": {
        "hello": ("ನಮಸ್ಕಾರ! ನಾನು StaySafe. ಅನುಮಾನವಿರುವ ಯಾವುದನ್ನಾದರೂ ನನಗೆ ಕಳುಹಿಸಿ ಅಥವಾ ಫಾರ್ವರ್ಡ್ ಮಾಡಿ, ಅದರಲ್ಲಿ ವಂಚನೆ ಇದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸುತ್ತೇನೆ:\n"
                  "• ಮೆಸೇಜ್ (SMS, WhatsApp, ಇಮೇಲ್)\n• ಲಿಂಕ್\n• ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಅಥವಾ QR ಕೋಡ್‌ನ ಫೋಟೋ\n"
                  "• ಫೈಲ್ (APK, PDF...)\n• ಫೋನ್ ಸಂಖ್ಯೆ ಅಥವಾ UPI ID\n\n"
                  "ಭಾಷೆ: /en English, /hi हिन्दी, /kn ಕನ್ನಡ, /tcy ತುಳು\n"
                  "ಹಣ ಕಳೆದುಕೊಂಡಿದ್ದೀರಾ? ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ."),
        "checking": "ಎಚ್ಚರಿಕೆಯಿಂದ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇವೆ. ಇದಕ್ಕೆ ಒಂದು ನಿಮಿಷದವರೆಗೆ ಸಮಯ ಬೇಕಾಗಬಹುದು...",
        "SAFE": "✅ ಸುರಕ್ಷಿತವಾಗಿ ಕಾಣುತ್ತದೆ", "CAUTION": "⚠️ ಎಚ್ಚರವಾಗಿರಿ", "DANGEROUS": "🛑 ವಂಚನೆಯಂತೆ ಕಾಣುತ್ತದೆ",
        "UNCERTAIN": "⚠️ ಖಚಿತವಿಲ್ಲ: ಎಚ್ಚರವಾಗಿರಿ",
        "do_SAFE": "ದೊಡ್ಡ ಎಚ್ಚರಿಕೆಯ ಸೂಚನೆಗಳಿಲ್ಲ. ಆದರೂ OTP ಅಥವಾ PIN ಎಂದಿಗೂ ಹೇಳಬೇಡಿ.",
        "do_CAUTION": "ನಿಜವಾದ ಕಂಪನಿಯೊಂದಿಗೆ ನೀವೇ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳುವವರೆಗೆ ಏನನ್ನೂ ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ, ಹಣ ಕಳುಹಿಸಬೇಡಿ, ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.",
        "do_DANGEROUS": "ಕ್ಲಿಕ್ ಮಾಡಬೇಡಿ, ಉತ್ತರಿಸಬೇಡಿ, ಹಣ ಕಳುಹಿಸಬೇಡಿ. ಕಳುಹಿಸಿದವರನ್ನು ಬ್ಲಾಕ್ ಮಾಡಿ. ಈಗಾಗಲೇ ಹಣ ಅಥವಾ ವಿವರ ಕೊಟ್ಟಿದ್ದರೆ ಈಗಲೇ 1930 ಗೆ ಕರೆ ಮಾಡಿ.",
        "score": "ಅಪಾಯ: {n}/100",
        "noticed": "ನಾವು ಗಮನಿಸಿದ್ದು (ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ):",
        "full": "ಕನ್ನಡದಲ್ಲಿ ಪೂರ್ಣ ವರದಿಯನ್ನು ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ ನೋಡಿ: {url}",
        "busy": "ಈಗ ತುಂಬಾ ಪರಿಶೀಲನೆಗಳು ನಡೆಯುತ್ತಿವೆ. ದಯವಿಟ್ಟು ಒಂದು ನಿಮಿಷದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "fail": "ಕ್ಷಮಿಸಿ, ಇದನ್ನು ಪರಿಶೀಲಿಸಲು ಆಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ, ಅಥವಾ ವೆಬ್‌ಸೈಟ್ ಬಳಸಿ: {url}",
        "unknown": "ಪರಿಶೀಲನೆಗೆ ಮೆಸೇಜ್, ಲಿಂಕ್, ಸ್ಕ್ರೀನ್‌ಶಾಟ್, ಫೈಲ್, ಫೋನ್ ಸಂಖ್ಯೆ ಅಥವಾ UPI ID ಕಳುಹಿಸಿ.",
        "big": "ಈ ಫೈಲ್ ನನಗೆ ತುಂಬಾ ದೊಡ್ಡದು (20 MB ಗಿಂತ ಹೆಚ್ಚು). ವೆಬ್‌ಸೈಟ್ ಬಳಸಿ: {url}",
        "lang": "ಸರಿ, ನಾನು ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸುತ್ತೇನೆ.",
    },
    "tcy": {
        "hello": ("ನಮಸ್ಕಾರ! ಯಾನ್ StaySafe. ಸಂಶಯ ಉಪ್ಪುನ ದಾದಾಂಡಲ ಎಂಕ್ ಕಡಪುಡ್ಲೆ ಅತ್ತಂಡ ಫಾರ್ವರ್ಡ್ ಮಲ್ಪುಲೆ, ಯಾನ್ ಮೋಸೊಗು ಪರಿಶೀಲನೆ ಮಲ್ಪುವೆ:\n"
                  "• ಮೆಸೇಜ್ (SMS, WhatsApp, ಇಮೇಲ್)\n• ಲಿಂಕ್\n• ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಅತ್ತಂಡ QR ಕೋಡ್‌ದ ಫೋಟೋ\n"
                  "• ಫೈಲ್ (APK, PDF...)\n• ಫೋನ್ ನಂಬರ್ ಅತ್ತಂಡ UPI ID\n\n"
                  "ಭಾಷೆ: /en English, /hi हिन्दी, /kn ಕನ್ನಡ, /tcy ತುಳು\n"
                  "ಪೈಸೆ ಪೋಂಡಾ? ಕೂಡಲೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ."),
        "checking": "ಜಾಗ್ರತೆಡ್ ಪರಿಶೀಲನೆ ಮಲ್ಪೊಂದುಲ್ಲ. ಒಂಜಿ ನಿಮಿಷ ಮುಟ್ಟ ಆವೊಲಿ...",
        "SAFE": "✅ ಸುರಕ್ಷಿತ ಲೆಕ್ಕ ತೋಜುಂಡು", "CAUTION": "⚠️ ಜಾಗ್ರತೆ", "DANGEROUS": "🛑 ಮೋಸದ ಲೆಕ್ಕ ತೋಜುಂಡು",
        "UNCERTAIN": "⚠️ ಖಚಿತ ಇಜ್ಜಿ: ಜಾಗ್ರತೆ",
        "do_SAFE": "ಮಲ್ಲ ಎಚ್ಚರಿಕೆದ ಸೂಚನೆಲು ಇಜ್ಜಿ. ಆಂಡಲಾ OTP ಅತ್ತಂಡ PIN ಏಪಲಾ ಪನೊಡ್ಚಿ.",
        "do_CAUTION": "ನಿಜವಾಯಿನ ಕಂಪನಿಡ್ ಈರೇ ಖಚಿತ ಮಲ್ಪುನ ಮುಟ್ಟ ದಾಲಾ ಕ್ಲಿಕ್ ಮಲ್ಪೊಡ್ಚಿ, ಪೈಸೆ ಕಡಪುಡೊಡ್ಚಿ, ದಾಲಾ ಕೊರೊಡ್ಚಿ.",
        "do_DANGEROUS": "ಕ್ಲಿಕ್ ಮಲ್ಪೊಡ್ಚಿ, ಉತ್ತರ ಕೊರೊಡ್ಚಿ, ಪೈಸೆ ಕಡಪುಡೊಡ್ಚಿ. ಕಡಪುಡಿನಾಕುಲೆನ್ ಬ್ಲಾಕ್ ಮಲ್ಪುಲೆ. ಪೈಸೆ ಅತ್ತಂಡ ವಿವರ ಕೊರ್ದಿತ್ತ್ಂಡ ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ.",
        "score": "ಅಪಾಯ: {n}/100",
        "noticed": "ಎಂಕುಲು ತೂಯಿನವು (ಇಂಗ್ಲಿಷ್‌ಡ್):",
        "full": "ವೆಬ್‌ಸೈಟ್‌ಡ್ ತುಳುಟು ಪೂರ್ತಿ ಪರಿಶೀಲನೆ: {url}",
        "busy": "ಇತ್ತೆ ಮಸ್ತ್ ಪರಿಶೀಲನೆಲು ನಡತೊಂದುಂಡು. ದಯಮಲ್ತ್ ಒಂಜಿ ನಿಮಿಷ ಬುಕ್ಕ ಕುಡೊರ ಪ್ರಯತ್ನ ಮಲ್ಪುಲೆ.",
        "fail": "ಕ್ಷಮಿಸಾಲೆ, ಉಂದೆನ್ ಪರಿಶೀಲನೆ ಮಲ್ಪೆರೆ ಆಯಿಜಿ. ಕುಡೊರ ಪ್ರಯತ್ನ ಮಲ್ಪುಲೆ, ಅತ್ತಂಡ ವೆಬ್‌ಸೈಟ್ ಉಪಯೋಗ ಮಲ್ಪುಲೆ: {url}",
        "unknown": "ಪರಿಶೀಲನೆಗ್ ಮೆಸೇಜ್, ಲಿಂಕ್, ಸ್ಕ್ರೀನ್‌ಶಾಟ್, ಫೈಲ್, ಫೋನ್ ನಂಬರ್ ಅತ್ತಂಡ UPI ID ಕಡಪುಡ್ಲೆ.",
        "big": "ಈ ಫೈಲ್ ಎಂಕ್ ಮಸ್ತ್ ಮಲ್ಲ (20 MB ಡ್ದ್ ಜಾಸ್ತಿ). ವೆಬ್‌ಸೈಟ್ ಉಪಯೋಗ ಮಲ್ಪುಲೆ: {url}",
        "lang": "ಆವು, ಯಾನ್ ತುಳುಟು ಉತ್ತರ ಕೊರ್ಪೆ.",
    },
}
TOOL_PAGE = {"message": "/#/scan-message", "screenshot": "/#/scan-message", "url": "/#/scan-url",
             "qr": "/#/scan-qr", "file": "/#/scan-file", "number": "/#/check-number"}

PHONE_ONLY = re.compile(r"^\+?[\d\s\-().]{3,25}$")
UPI_ONLY = re.compile(r"^[\w.\-]{2,256}@[A-Za-z][A-Za-z0-9]{1,64}$")
LINK_ONLY = re.compile(r"^(https?://|www\.)\S+$|^[\w-]+(\.[\w-]+)+(/\S*)?$", re.IGNORECASE)


def _lang_for(chat_id, user: dict) -> str:
    if chat_id in _LANG:
        return _LANG[chat_id]
    code = ((user or {}).get("language_code") or "en").lower()[:2]
    return code if code in ("hi", "kn") else "en"


def _send(chat_id, text: str, reply_to=None) -> None:
    try:
        payload = {"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True}
        if reply_to:
            payload["reply_parameters"] = {"message_id": reply_to, "allow_sending_without_reply": True}
        requests.post(f"{API}/bot{_token()}/sendMessage", json=payload, timeout=20)
    except Exception:
        pass


def _typing(chat_id) -> None:
    try:
        requests.post(f"{API}/bot{_token()}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=10)
    except Exception:
        pass


def _download(file_id: str):
    """(bytes, file_path) of a file sent to the bot, or (None, reason)."""
    r = requests.get(f"{API}/bot{_token()}/getFile", params={"file_id": file_id}, timeout=20).json()
    if not r.get("ok"):
        return None, "fail"
    info = r["result"]
    if (info.get("file_size") or 0) > MAX_FILE:
        return None, "big"
    data = requests.get(f"{API}/file/bot{_token()}/{info['file_path']}", timeout=60).content
    return data, info.get("file_path", "")


def _call(app, path: str, chat_id, lang: str, json=None, data=None):
    """Run one of the website's own API routes inside this server."""
    headers = {"X-Client-Id": f"tg{chat_id}", "X-Lang": "en" if lang == "tcy" else lang}
    with app.test_client() as c:
        if json is not None:
            resp = c.post(path, json=json, headers=headers, environ_base={"REMOTE_ADDR": f"tg-{chat_id}"})
        else:
            resp = c.post(path, data=data, headers=headers, content_type="multipart/form-data",
                          environ_base={"REMOTE_ADDR": f"tg-{chat_id}"})
    return resp.status_code, (resp.get_json(silent=True) or {})


def format_result(result: dict, lang: str, tool: str) -> str:
    T = TEXTS.get(lang, TEXTS["en"])
    verdict = result.get("verdict", "CAUTION")
    tone = {"SAFE": "SAFE", "LIKELY_SAFE": "SAFE", "DANGEROUS": "DANGEROUS", "SCAM_LIKELY": "DANGEROUS",
            "SCAM": "DANGEROUS"}.get(verdict, "CAUTION")
    head = T.get(verdict) or T[tone]
    lines = [head, T["score"].format(n=result.get("risk_score", 0)), ""]
    findings = result.get("findings") or result.get("patterns_detected") or []
    findings = [f for f in findings if f and not f.startswith("Remember:")][:4]
    if findings:
        lines.append(T["noticed"])
        lines += [f"• {f}" for f in findings]
        lines.append("")
    lines.append(T[f"do_{tone}"])
    lines += ["", T["full"].format(url=SITE + TOOL_PAGE.get(tool, ""))]
    return "\n".join(lines)


def handle_update(app, update: dict) -> None:
    msg = update.get("message") or update.get("edited_message") or update.get("channel_post")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    if msg["chat"].get("type") not in (None, "private"):
        return  # only private chats, so nobody's group messages are read
    lang = _lang_for(chat_id, msg.get("from"))
    T = TEXTS[lang]
    text = (msg.get("text") or msg.get("caption") or "").strip()

    cmd = text.split()[0].lower().split("@")[0] if text.startswith("/") else ""
    if cmd in ("/en", "/hi", "/kn", "/tcy"):
        _LANG[chat_id] = cmd[1:]
        _send(chat_id, TEXTS[cmd[1:]]["lang"] + "\n\n" + TEXTS[cmd[1:]]["hello"])
        return
    if cmd in ("/start", "/help") or (cmd and not text[len(cmd):].strip()):
        _send(chat_id, T["hello"])
        return
    if cmd:
        text = text[len(cmd):].strip()

    _typing(chat_id)
    try:
        photo = msg.get("photo")
        doc = msg.get("document")
        if photo or (doc and (doc.get("mime_type") or "").startswith("image/")):
            file_id = photo[-1]["file_id"] if photo else doc["file_id"]
            data, info = _download(file_id)
            if data is None:
                _send(chat_id, T[info].format(url=SITE), msg.get("message_id"))
                return
            from scanners.qr_scanner import decode_qr_image
            try:
                qr = decode_qr_image(data)
            except Exception:
                qr = None
            if qr:
                status, result = _call(app, "/api/scan-qr-text", chat_id, lang, json={"data": qr})
                tool = "qr"
            else:
                import io
                status, result = _call(app, "/api/scan-screenshot", chat_id, lang,
                                       data={"image": (io.BytesIO(data), "shot.jpg"), "sender": ""})
                tool = "screenshot"
        elif doc:
            if (doc.get("file_size") or 0) > MAX_FILE:
                _send(chat_id, T["big"].format(url=SITE), msg.get("message_id"))
                return
            data, info = _download(doc["file_id"])
            if data is None:
                _send(chat_id, T[info].format(url=SITE), msg.get("message_id"))
                return
            import io
            status, result = _call(app, "/api/scan-file", chat_id, lang,
                                   data={"file": (io.BytesIO(data), doc.get("file_name") or "file")})
            tool = "file"
        elif text:
            compact = text.replace(" ", "")
            if UPI_ONLY.match(compact) or (PHONE_ONLY.match(text) and len(re.sub(r"\D", "", text)) >= 3):
                status, result = _call(app, "/api/check-number", chat_id, lang, json={"value": text})
                tool = "number"
            elif LINK_ONLY.match(text) and "\n" not in text:
                status, result = _call(app, "/api/scan-url", chat_id, lang, json={"url": text})
                tool = "url"
            else:
                status, result = _call(app, "/api/scan-message", chat_id, lang, json={"text": text})
                tool = "message"
        else:
            _send(chat_id, T["unknown"])
            return
    except Exception:
        _send(chat_id, T["fail"].format(url=SITE), msg.get("message_id"))
        return

    if status == 429:
        _send(chat_id, T["busy"], msg.get("message_id"))
    elif status != 200 or "verdict" not in result:
        err = result.get("error")
        _send(chat_id, err if err and lang == "en" else T["fail"].format(url=SITE), msg.get("message_id"))
    else:
        _send(chat_id, format_result(result, lang, tool), msg.get("message_id"))


@telegram_bp.route("/api/telegram/webhook", methods=["POST"])
def telegram_webhook():
    secret = _secret()
    given = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret or not hmac.compare_digest(secret.encode(), given.encode()):
        return jsonify({"ok": False}), 403
    update = request.get_json(silent=True) or {}
    uid = update.get("update_id")
    with _SEEN_LOCK:
        now = time.time()
        for k in [k for k, t in _SEEN.items() if now - t > 3600]:
            _SEEN.pop(k, None)
        if uid in _SEEN:
            return jsonify({"ok": True})
        _SEEN[uid] = now
    from flask import current_app
    app = current_app._get_current_object()
    # Answer Telegram at once; the check runs in the background and replies when done
    threading.Thread(target=handle_update, args=(app, update), daemon=True).start()
    return jsonify({"ok": True})


@telegram_bp.route("/api/telegram/setup", methods=["GET"])
def telegram_setup():
    if not has_status_key():
        return jsonify({"error": "not found"}), 404
    if not _token():
        return jsonify({"ok": False, "problem": "TELEGRAM_SCAN_BOT_TOKEN is not set on the server"})
    base = os.environ.get("PUBLIC_API_URL", "").rstrip("/") or request.host_url.rstrip("/").replace("http://", "https://")
    url = f"{base}/api/telegram/webhook"
    try:
        r = requests.post(f"{API}/bot{_token()}/setWebhook", json={
            "url": url, "secret_token": _secret(), "allowed_updates": ["message"], "drop_pending_updates": True,
        }, timeout=20).json()
        me = requests.get(f"{API}/bot{_token()}/getMe", timeout=20).json()
        requests.post(f"{API}/bot{_token()}/setMyCommands", json={"commands": [
            {"command": "start", "description": "How to use StaySafe"},
            {"command": "en", "description": "Reply in English"},
            {"command": "hi", "description": "हिन्दी में जवाब"},
            {"command": "kn", "description": "ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ"},
            {"command": "tcy", "description": "ತುಳುಟು ಉತ್ತರ"},
        ]}, timeout=20)
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "problem": type(e).__name__})
    username = (me.get("result") or {}).get("username")
    return jsonify({"ok": bool(r.get("ok")), "webhook": url, "telegram": r.get("description"),
                    "bot": f"https://t.me/{username}" if username else None})
