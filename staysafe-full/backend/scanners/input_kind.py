"""
TrustLight - What did the person put in?

People sometimes paste a link into the email checker, a phone number into the link checker,
or upload a QR code as a message screenshot. Each check uses this to notice that and point
them to the right tool (with "wrong_tool" in the answer, so the website can offer a button),
instead of giving a confusing result.
"""
import re

_URL = re.compile(r"^(?:https?://|www\.)\S+$|^(?:[a-z0-9-]+\.)+[a-z]{2,}(?:[/?#:]\S*)?$", re.I)
_EMAIL_ADDR = re.compile(r"^[A-Za-z0-9._%+'-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")
_UPI = re.compile(r"^[A-Za-z0-9._-]{2,}@[A-Za-z]{2,}[A-Za-z0-9]*$")
_PHONE = re.compile(r"^\+?[\d\s().-]{7,20}$")
_HEADER = re.compile(r"^(from|to|subject|received|return-path|dkim-signature|message-id|date|reply-to|"
                     r"authentication-results|mime-version|content-type|x-[\w-]+)\s*:", re.I | re.M)

MESSAGES = {
    "link": "This looks like a website link. Please check it in Check a Link.",
    "email": "This looks like an email address. To check an email, use Check an Email.",
    "number": "This looks like a phone number or UPI ID. Please check it in Check a Number or UPI ID.",
    "message": "This looks like a message. Please check it in Check a Message.",
    "qr": "This picture is a QR code. Please check it in Check a QR Code.",
}


def kind_of(text: str) -> str:
    """'empty', 'link', 'email_address', 'upi', 'phone', 'email_source' or 'message'."""
    v = (text or "").strip()
    if not v:
        return "empty"
    if len(_HEADER.findall(v)) >= 2:
        return "email_source"
    one = v.strip("<>\"' ")
    if not re.search(r"\s", one):
        if _EMAIL_ADDR.match(one):
            return "email_address"
        if _UPI.match(one):
            return "upi"
        if _URL.match(one) and "@" not in one:
            return "link"
    if _PHONE.match(v) and 10 <= len(re.sub(r"\D", "", v)) <= 13:
        return "phone"
    return "message"


def wrong_tool(text: str, here: str):
    """The tool this input belongs to, if it isn't `here`; else None.
    here: 'link' | 'email' | 'number' | 'message'."""
    k = kind_of(text)
    target = {"link": "link", "email_address": "email", "upi": "number", "phone": "number",
              "email_source": "email", "message": "message"}.get(k)
    if not target or target == here:
        return None
    # a word or two typed into the number box isn't a message; let the number checker explain
    if here == "number" and target == "message" and len((text or "").split()) < 4:
        return None
    # a message with a link inside is fine for the link checker (it finds the link)
    if here == "link" and target == "message":
        return None
    # the email form's sender box legitimately holds an email address; whole emails go to the email checker
    if here == "email" and target in ("email",):
        return None
    return target


def wrong_tool_answer(text: str, here: str):
    """{'error', 'wrong_tool'} to send back with a 400, or None when the input fits this tool."""
    t = wrong_tool(text, here)
    return {"error": MESSAGES[t], "wrong_tool": t} if t else None
