"""
StaySafe - Message / Screenshot Scam Detector
-----------------------------------------------
Analyzes pasted text OR an uploaded screenshot for common scam patterns,
with a focus on scams seen in India (English + Hinglish):
  - Bank / KYC / PAN impersonation
  - OTP / PIN / CVV theft (only when someone ASKS for it)
  - Electricity disconnection scams
  - Courier / "digital arrest" / fake police scams
  - Task-based and fake job scams
  - Prize / lottery / advance-fee scams
  - Investment / trading scams
  - Remote access app requests (AnyDesk etc.)
  - "Hi mum, new number" family impersonation
  - Fake refunds and UPI "collect" tricks

It also recognises SAFE signals. E.g. a real bank OTP message that says
"do not share this OTP with anyone". So genuine messages are not flagged.

Screenshot support uses OCR (Tesseract via pytesseract) to extract the text,
then runs it through the same rule engine as pasted text.
"""

import io
import threading
import os
import time
import re
import shutil
from flask import Blueprint, request, jsonify

message_scanner_bp = Blueprint("message_scanner", __name__)

try:
    import pytesseract
    from PIL import Image, ImageOps
    PYTESSERACT_INSTALLED = True
except ImportError:  # pragma: no cover
    PYTESSERACT_INSTALLED = False


def ocr_status() -> bool:
    """True only if both the Python package AND the Tesseract program exist."""
    if not PYTESSERACT_INSTALLED:
        return False
    cmd = pytesseract.pytesseract.tesseract_cmd
    return bool(shutil.which(cmd))


# ---------------------------------------------------------------------------
# SCAM PATTERN RULES
# Each rule: (label shown to user, list of regexes, weight)
# A rule counts once even if several of its patterns match.
# Text is lower-cased before matching.
# ---------------------------------------------------------------------------
LINK = r"(https?://|www\.|\b[a-z0-9-]+\.(?:xyz|top|club|click|live|icu|buzz|site|online|info|in|com|net|me|ly)/)"

RULES = [
    (
        "Asks you to share an OTP, PIN, CVV or password",
        [
            r"\b(share|send|tell|forward|give|provide|read out|confirm|batao|bata do|bhejo|bhej do)\b[^.\n]{0,40}\b(otp|one[- ]time (password|code)|verification code|cvv|upi pin|atm pin|card pin|mpin)\b",
            r"\b(share|send|tell|give)\b (me |us )?(your|the) (password|pin|login details|card details|card number)\b(?! (manager|tips|policy|rules))",
            r"\b(otp|verification code|cvv|mpin)\b[^.\n]{0,30}\b(share|send|tell|batao|bhejo|bhej do|forward)\b(?! (it )?with anyone)",
            r"\b(code|otp)\b[^.\n]{0,25}\b(you (just )?received|we (have )?sent|aaya hai|aya hai)\b",
            # WhatsApp takeover: "I sent my code to you by mistake, please send it back"
            r"(?=[^\n]*\b(send|share|forward|give|bhej|bhejo|bata)\b)[^\n]*\b(accidentally|by mistake|mistakenly|wrongly|galti se)\b[^\n]{0,50}\b(code|otp|6[- ]digit)\b",
            r"(?=[^\n]*\b(send|share|forward|give|bhej|bhejo|bata)\b)[^\n]*\b(code|otp)\b[^\n]{0,50}\b(by mistake|accidentally|wrongly|galti se)\b",
        ],
        50,
    ),
    (
        "Asks for your UPI PIN to 'receive' money (you never need a PIN to receive)",
        [
            r"\b(enter|type|put|dalo|daalo)\b[^.\n]{0,20}\bupi pin\b",
            r"\bupi pin\b[^.\n]{0,40}\b(receive|get|credit|refund|cashback)\b",
            r"\b(scan|accept)\b[^.\n]{0,30}\b(qr|request)\b[^.\n]{0,40}\b(receive|get|refund|cashback|prize)\b",
        ],
        50,
    ),
    (
        "Bank / KYC / PAN impersonation",
        [
            r"\bre-?kyc\b",
            r"kyc\b[^.\n]{0,40}\b(pending|expired?|expiring|incomplete|not (been )?(updated|completed|verified|done)|block\w*|suspend\w*|deactivat\w*|update (now|immediately|today|within))",
            r"kyc\b[^\n]{0,60}\b(update|verify|complete)\b[^\n]{0,60}(https?://|www\.|\b(link|click|call|contact)\b|\d{10})",
            r"\b(account|a/c|khata|card|yono|net ?banking|wallet|upi id|paytm|phonepe|gpay)\b[^.\n]{0,40}\b(will be |has been |is |ho jayega |hoga )?(blocked|suspended|frozen|deactivated|closed|band)\b",
            r"\b(update|link|verify)\b[^.\n]{0,20}\b(pan|aadhaar|aadhar)\b",
            r"\bverify your (account|bank|kyc|identity)\b",
            r"\b(complete|update|verify|do)\b[^.\n]{0,20}\b(your |the )?kyc\b[^\n]{0,80}(https?://|www\.|\b(call|contact|click|link|immediately|today|within|now)\b|\d{10})",
            r"\b(re-?activate|reactivation|confirm your (details|account|update|registration)|review your details|if (it|this) (is|was) not (done by )?you)\b[^\n]{0,80}(https?:/|www\.|bit\.|[a-z0-9-]+\.(in|com|xyz|top|online|site|info|net|co|org|live|shop)\b)",
            r"\b(unusual|suspicious|unknown|new) (login|log-in|sign-?in|activity|device)\b[^\n]{0,80}\b(secure|verify|confirm|click|update)\b",
            r"\bsecure your (account|bank|card)\b",
            r"\b(debit|credit|atm) card\b[^.\n]{0,40}\b(blocked|suspended|deactivated)\b[^\n]{0,60}\b(call|click|reactivate|verify|update)\b",
        ],
        30,
    ),
    (
        "Electricity disconnection threat",
        [
            r"\b(electricity|bijli|power|light|eb)\b[^.\n]{0,60}\b(disconnect|disconnected|cut|kaat|kat|band)\b(?![^.\n]{0,30}\b(avoid|to avoid)\b)",
            r"\bmeter\b[^.\n]{0,40}\b(will be |is being )?(removed|disconnected|cut|seized)\b",
            r"\b(electricity|power|bijli)\b[^\n]{0,40}\b(officer|lineman)\b[^\n]{0,40}\d{10}",
            r"\belectricity (officer|department)\b",
            r"\b(bill|bijli bill)\b[^.\n]{0,50}\b(not (been )?updated|update nahi)\b",
        ],
        35,
    ),
    (
        "Courier / customs / 'digital arrest' scam",
        [
            r"\bdigital arrest\b",
            r"\b(fedex|dhl|courier|parcel|package|shipment)\b[^\n]{0,100}\b(drugs|narcotics|illegal|seized|police|passports?|mdma)\b",
            r"\b(police|cbi|ncb|narcotics|crime branch|cyber ?crime|ed officer|enforcement directorate)\b[^\n]{0,80}\b(arrest|warrant|case|fir|video call|skype)\b",
            r"\barrest warrant\b",
        ],
        45,
    ),
    (
        "Impersonating government, police or tax department",
        [
            r"\b(income tax|it department|itr)\b[^\n]{0,60}\brefund\b[^\n]{0,60}\b(claim|click|verify|update|pending|approved|link|apply|submit)\b",
            r"\b(income tax|it department)\b[^.\n]{0,40}\b(notice|penalty)\b",
            r"\btax refund\b[^\n]{0,100}\b(form|click|link|claim|process|https?://|www\.)",
            r"\b(police|court) (verification|notice|summons)\b",
            r"\btrai\b[^.\n]{0,60}\b(disconnect|block|suspend)\b",
            r"\bpress \d\b[^.\n]{0,40}\b(officer|executive|agent|speak)\b",
            r"\b(sim|mobile number|number)\b[^.\n]{0,40}\b(will be |is )?(blocked|disconnected|deactivated|band)\b",
            # fake traffic fines / FASTag
            r"\b(e-?challan|traffic challan|challan|fastag)\b[^\n]{0,60}\b(pending|unpaid|due|overdue|pay|blocked|expired?)\b",
        ],
        30,
    ),
    (
        "Promises easy fixed daily/hourly earnings",
        [
            r"\b(earn|kamao|kamaye|income|salary)\b[^.\n]{0,40}(rs\.?|₹|inr)\s?\d[\d,]*\s*(/|per|a|daily|every)\s*(day|daily|hour|hr|task)",
            r"\b(earn|kamao|kamaye)\b\s+(up ?to\s+)?(rs\.?|₹|inr)?\s?\d[\d,]{2,}(\s?(k|rs|rupees))?\s*(/|per|a|every)?\s*(day|daily|hour|hr|week|weekly)\b",

        ],
        15,
    ),
    (
        "Task-based or fake job offer",
        [
            r"(?=[^\n]*\b(earn|task|commission|paid|payment|salary|income|rs\.?|₹|inr|per (like|video|review|task))\b)[^\n]*\b(lik(e|ing)|rat(e|ing)|review(ing)?|subscrib(e|ing))\b[^.\n]{0,40}\b(videos?|youtube|hotels?|products?|google maps)\b",
            r"\b(hiring|job offer|vacancy)\b[^\n]{0,120}\b(telegram|whatsapp)\b",
            r"\b(part[- ]time|work from home|ghar baithe)\b[^\n]{0,80}\b(earn|daily|salary|income|kamao)\b",
            r"\b(registration|joining|security|training) (fee|deposit|charges?)\b",
            r"\bget rich (quick|fast)\b",
            r"\bearn\b[^.\n]{0,40}\b(daily|per day|a day|every day)\b[^.\n]{0,20}\b(from home|sitting at home|online)\b",
        ],
        35,
    ),
    (
        "Prize, lottery or 'you have won' offer",
        [
            r"\b(you|u)( have|'ve|['’]ve| ve| hv)? won(?!['’]t)(?! (our|my|your|the|everyone'?s|their|his|her) (hearts?|match|game|trust|love|race|election))\b",
            r"\b(you|u)( have|'ve|['’]ve| ve| hv)? been (selected|chosen|picked)\b[^\n]{0,60}\b(prize|reward|cash|gift|lucky|winner|claim|free|bonus|holiday|iphone|car|lottery|draw|offer)\b",
            r"\blottery\b", r"\blucky draw\b",
            r"\b(gift|reward|prize|cash|voucher|surprise|bonus)\b[^\n]{0,30}\b(is |are )?(waiting|awaiting|await)\b[^\n]{0,80}\b(call|claim|collect|click|log ?onto|visit|txt|text|reply)\b",
            r"\b(entitled|specially selected|randomly (picked|selected|chosen))\b[^\n]{0,60}\b(free|claim|receive|cash|holiday|prize|grant|compensation|reward|upgrade)\b",
            r"\b(is|are) yours\b[^\n]{0,60}\b(call|claim|collect|txt|text|reply)\b",
            r"\b(awarded|selected to receive|chosen to receive|picked to receive)\b[^\n]{0,60}\b(prize|cash|reward|bonus|award|holiday|voucher|gift)\b",
            r"\b(cash prize|bonus (caller )?prize|guaranteed (prize|cash|award|reward)|prize (money|draw|code))\b",
            r"\b(await(s|ing)? collection|identifier code|claim code)\b",
            r"\bkbc\b", r"\bjackpot\b", r"\bclaim (your )?(prize|reward|gift|cashback)\b",
            r"\bwinner\b[^\n]{0,80}\b(claim|collect|cashback|prize|reward)\b",
            r"\byou (have |'ve )?(got|received|won)\b[^.\n]{0,40}\b(cashback|reward|prize|iphone|gift|bonus)\b[^\n]{0,60}\b(claim|click|collect)\b",
            r"\b(selected|chosen|eligible)\b for\b[^.\n]{0,25}\b(grant|scheme|subsidy|prize|reward|bonus)\b",
            r"\bcongratulations\b[^.\n]{0,60}\b(won(?!['’]t)(?! (our|my|your|the|everyone'?s|their|his|her) (hearts?|match|game|trust|love|race|election))|winner|reward|prize)\b",
            r"\b(inaam|lottery lagi)\b",
        ],
        30,
    ),
    (
        "Asks you to pay a fee to receive money",
        [
            r"\b(processing|delivery|release|clearance|tax|gst|handling) (fee|charges?)\b",
            r"\bpay\b[^.\n]{0,40}\b(to (receive|claim|release|unlock|withdraw))\b",
        ],
        30,
    ),
    (
        "Investment or trading scheme with unrealistic returns",
        [
            r"\bguaranteed (returns?|profit|income)\b", r"\bdouble your money\b",
            r"\b\d{2,3}\s?% (daily|weekly|monthly|returns?|profit)\b",
            r"\b(crypto|bitcoin|forex|stock|ipo)\b[^.\n]{0,40}\b(invest|profit|returns?|tips|signals?)\b",
            r"\bvip (group|trading)\b", r"\btrading (platform|signals?|app)\b",
        ],
        40,
    ),
    (
        "Asks you to install a remote access / screen sharing app",
        [
            r"\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid|screen ?share|remote access)\b",
            r"\b(download|install)\b[^.\n]{0,40}\b(apk|app from this link)\b",
            r"\.apk\b",
            r"\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid)\b[^\n]{0,80}\b(code|id|number)\b",
        ],
        45,
    ),
    (
        "Family member 'new number' / emergency money request",
        [
            r"\b(hi|hello)\s+(mum|mom|dad|mummy|papa|beta)\b[^\n]{0,120}\b(new number|lost my phone|phone (is )?broken)\b",
            r"\b(new number|lost my phone|phone (is )?broken)\b[^\n]{0,120}\b(send|transfer|pay|money|paise)\b",
            r"\b(urgent|emergency)\b[^.\n]{0,40}\b(send|transfer)\b[^.\n]{0,20}\b(money|paise|rs|₹)",
        ],
        30,
    ),
    (
        "Refund or cashback that needs you to click or fill a form",
        [
            r"\b(refund|cashback)\b[^.\n]{0,60}\b(click|link|form|claim|fill|apply)\b",
        ],
        25,
    ),
    (
        "Pressure / urgency language",
        [
            r"\bimmediately\b", r"\burgent(ly)?\b", r"\b(within|in) \d+ (hours?|hrs?|minutes?|mins?)\b",
            r"\bact now\b", r"\b(expire[sd]?|expiring) (today|soon|tonight)\b", r"\btoday itself\b",
            r"\btonight\b", r"\blast (chance|warning|reminder)\b", r"\bturant\b", r"\bjaldi\b", r"\baaj raat\b",
            r"\bfinal notice\b",
        ],
        10,
    ),
    (
        "Contains a shortened or unusual link",
        [
            r"\b(bit\.ly|tinyurl\.com|t\.ly|cutt\.ly|is\.gd|rb\.gy|shorturl\.at|tiny\.cc|ow\.ly|goo\.gl)/\S+",
            r"https?://\S+\.(xyz|top|club|click|live|icu|buzz|site|online|shop|rest|sbs|cfd|cyou|vip|support)\b",
            r"https?://\d{1,3}(\.\d{1,3}){3}",
        ],
        15,
    ),
    (
        "Asks you to call or message an unknown number",
        [
            r"\b(call|contact|whatsapp|message|sms)\b[^.\n]{0,30}(\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b",
            r"\b(contact|message|join)\b[^.\n]{0,20}\b(on |us on |me on )?telegram\b",
            r"\b(call|ring|dial|text|txt)\b[^\n]{0,40}\b0(9\d{8,9}|87\d{8,9}|70\d{8})\b",
            r"\b(urgent|important) (message|delivery|parcel)\b[^\n]{0,30}\bwaiting for you\b",
        ],
        10,
    ),
    (
        "Asks you to install an app from a link or file (APK)",
        [
            r"\b[\w-]+\.apk\b",
            r"\b(download|install)\b[^.\n]{0,30}\b(this |the |our |below )?(app|application|apk)\b[^.\n]{0,30}\b(link|below|here|file|attached)\b",
            r"\b(install|download)\b[^.\n]{0,20}\b(from|using) (this|the|below) link\b",
        ],
        45,
    ),
    (
        "Instant loan with no documents or checks",
        [
            r"\b(instant|quick|easy|pre-?approved)\s+(personal\s+)?loan\b[^\n]{0,80}\b(no|without)\s+(documents?|paperwork|cibil|credit check|income proof)\b",
            r"\bloan\b[^\n]{0,60}\b(in|within) \d+ (minutes?|mins?)\b",
            r"\bno cibil (check|score)?\b",
            r"\bloans?\b[^\n]{0,60}\b(bad credit|no credit check|low cibil|without cibil|poor credit)\b",
        ],
        30,
    ),
    (
        "Fake government scheme, Aadhaar, PAN or gas update",
        [
            r"\b(pm[- ]?kisan|pm[- ]?yojana|pradhan mantri)\b[^\n]{0,80}\b(update|verify|link|claim|apply|kyc|blocked|stopped)\b",
            r"\b(gas|lpg)\s+(connection|subsidy|kyc)\b[^\n]{0,60}\b(update|block|cancel|stop|verify)",
            r"\b(aadhaa?r|pan)(\s+card)?\b[^\n]{0,40}\b(will be |is |has been )?(blocked|deactivated|suspended|cancelled|inactive)\b",
            r"\b(pension|scholarship|subsidy)\b[^\n]{0,40}\b(stopped|blocked|pending)\b[^\n]{0,60}\b(update|link|click|call)\b",
            r"\b(grant|relief (fund|payment)|government payment|stimulus|covid[- ]?19 (fund|payment|grant))\b[^\n]{0,80}\b(redeem|claim|apply|tap|click|contact)\b",
        ],
        30,
    ),
    (
        "Reward points or cashback that 'expire today'",
        [
            r"\breward points?\b[^\n]{0,80}\b(expir|redeem|claim|lapse)",
            r"\b(redeem|claim)\b[^\n]{0,40}\b(points|rewards)\b[^\n]{0,40}\b(today|now|before|expir)",
        ],
        35,
    ),
    (
        "Threatens to share your photos or videos (blackmail)",
        [
            r"\b(video|photos?|pics?|recording)\b[^\n]{0,60}\b(viral|leak|upload|send|share)\b[^\n]{0,40}\b(friends|family|contacts|relatives|everyone|social media|youtube)\b",
            r"\b(pay|send)\b[^\n]{0,40}\b(or|otherwise|warna)\b[^\n]{0,40}\b(viral|leak|upload)\b",
        ],
        50,
    ),
    (
        "Asks for payment by gift card or crypto",
        [
            r"\b(google play|amazon|apple|itunes|steam)\s+(gift\s+)?(card|voucher)s?\b[^\n]{0,60}\b(buy|send|code|purchase)",
            r"\b(buy|send|purchase)\b[^\n]{0,40}\b(gift\s+card|voucher)s?\b",
            r"\b(usdt|bitcoin|btc|crypto)\b[^\n]{0,40}\b(wallet|address|send|deposit|transfer)\b",
        ],
        35,
    ),
    (
        "Asks for your Aadhaar, PAN or bank account details",
        [
            r"\b(send|share|provide|give|submit|upload)\b[^.\n]{0,40}\b(aadhaa?r|pan card|bank (account|a/c) (number|details)|debit card|atm card|card number|passbook)\b",
        ],
        35,
    ),
    (
        "Asks you to keep it secret",
        [
            r"\b(don'?t|do not|never) (tell|inform|share this with) (anyone|anybody|your family|your parents|bank|police)\b",
            r"\bkeep (this|it) (secret|confidential|between us)\b",
            r"\b(kisi ko mat batana|kisi ko na batayein)\b",
        ],
        25,
    ),
    (
        "Romance or dating message from a stranger",
        [
            r"\b(hi|hello|hey) (beautiful|handsome|dear|sweetheart|gorgeous)\b[^\n]{0,80}\b(profile|chat|meet|friend)\b",
            r"\b(single|lonely|hot) (women|girls|ladies|bhabhi|aunty)\b[^\n]{0,80}\b(waiting|meet|call|chat|near you)\b",
            r"\b(saw|liked|found) your profile\b[^\n]{0,60}\b(chat|talk|meet|reply|whatsapp)\b",
            r"\bsecret admirer\b",
            r"\b(video call|friendship|dating)\b[^\n]{0,40}\b(girls?|women|service|club)\b[^\n]{0,40}\b(call|join|whatsapp|click)\b",
        ],
        30,
    ),
    (
        "Discount or refund on a bill, with a link or number to contact",
        [
            r"\b\d{1,3}\s?% (discount|off|cashback)\b[^\n]{0,40}\b(electricity|power|gas|water|phone|mobile) bill\b",
            r"\b(electricity|power|gas|water) bill\b[^\n]{0,40}\b(refund|discount|cashback)\b[^\n]{0,60}\b(claim|click|approved|call)\b",
        ],
        30,
    ),
    (
        "Says money was sent to you by mistake and asks you to return it",
        [
            r"\b(sent|credited|transferred|paid|deposited)\b[^\n]{0,60}\b(by mistake|mistakenly|wrongly|accidentally|galti se)\b[^\n]{0,120}\b(return|refund|send (it )?back|wapas|reverse)\b",
            r"\b(by mistake|mistakenly|wrongly|galti se)\b[^\n]{0,40}\b(sent|credited|transferred)\b[^\n]{0,120}\b(return|refund|send (it )?back|wapas)\b",
        ],
        45,
    ),
    (
        "Threatens to cut your water, gas, internet or TV connection",
        [
            r"\b(water|gas|png|lpg|broadband|internet|wifi|wi-fi|dth|cable tv|tv)\b[^\n]{0,40}\b(connection|supply|service)\b[^\n]{0,60}\b(disconnect(ed)?|cut|suspend(ed)?|stop(ped)?|band)\b",
            r"\b(water|gas|broadband|dth)\b[^\n]{0,60}\b(officer|department)\b[^\n]{0,40}\b(call|contact)\b",
        ],
        35,
    ),
    (
        "Asks for your SIM card number (used to take over your number)",
        [
            r"\bsim\b[^\n]{0,60}\b(\d{2}[- ]?digits?|serial|iccid)\b",
            r"\b(send|sms|share|reply|message|tell)\b[^\n]{0,40}\bsim\b[^\n]{0,20}\bnumber\b",
            r"\b(4g|5g|esim|e-sim) (sim )?(upgrade|activation|conversion)\b[^\n]{0,80}\b(send|sms|share|call|reply|click|otp)\b",
        ],
        45,
    ),
    (
        "Says a parcel couldn't be delivered and asks you to update details or pay",
        [
            r"\b(delivery|deliver|parcel|package|shipment|courier|india post|speed post)\b[^\n]{0,80}\b(failed|unable|could not|couldn'?t|on hold|held|incomplete address|address (is )?(incomplete|incorrect|wrong))\b[^\n]{0,100}\b(update|confirm|reschedule|click|pay|link|https?://|www\.)",
            r"\b(redeliver|re-deliver|reschedule (your )?delivery)\b[^\n]{0,60}\b(click|link|pay|fee|https?://|www\.)",
        ],
        30,
    ),
    (
        "Threatens to block something unless you pay",
        [
            r"\b(blocked|suspended|withheld|cancelled|on hold|stopped)\b[^\n]{0,80}\b(pay|payment|fee|fine|charges|dues)\b[^\n]{0,80}(\b(link|upi|call|immediately|today|now)\b|https?://|www\.|\b[a-z0-9-]+\.(in|com|xyz|top|online|site|info|net|co|org|live|shop)\b)",
            r"\b(pay|payment)\b[^\n]{0,60}\b(or|otherwise|else)\b[^\n]{0,40}\b(blocked|suspended|cancelled|disconnected|withheld)\b",
        ],
        30,
    ),
    (
        "Uses look-alike characters to slip past spam filters (bl0cked, W0N)",
        [r"__DEOBFUSCATED__"],
        20,
    ),
    (
        "Free recharge, data or gifts with a link",
        [
            r"\bfree\b[^\n]{0,30}\b(recharge|data|5g|mobile|iphone|smartphone|laptop|gift)\b[^\n]{0,80}(https?://|www\.|\b[a-z0-9-]+\.(xyz|top|site|online|in|com)\b)",
        ],
        30,
    ),
]


# ---------------------------------------------------------------------------
# KANNADA (also covers much Tulu, which uses Kannada script) and HINDI rules.
# Same scam types as above, written in the native scripts. No \b here: word
# boundaries don't work reliably inside Indian scripts. Text is normalised first
# (zero-width joiners and Hindi nukta dots removed), so patterns omit them.
# ---------------------------------------------------------------------------
KN_ASK = r"(ಹ(ೇ|ೆ)?ಳಿ|ಹೇಳು|ಕಳುಹಿಸಿ|ಕಳಿಸಿ|ಕಳ್ಸಿ|ಶೇರ್ ಮಾಡಿ|ಕೊಡಿ|ತಿಳಿಸಿ|ಹಂಚಿಕೊಳ್ಳಿ|ಪನ್ಲೆ|ಕೊರ್ಲೆ|ಕಡಪುಡ್ಲೆ)"
HI_ASK = r"(बताएं|बताइए|बताओ|बता दो|बता दें|भेजें|भेजो|भेजिए|भेज दो|शेयर करें|शेयर करो|दें|दीजिए|दे दो)"
MONEY = r"(₹|rs\.?|ರೂ\.?|ರೂಪಾಯಿ|रु\.?|रुपये|रुपए)"
NUM = r"(\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}"

NATIVE_PATTERNS = {
    "Says money was sent to you by mistake and asks you to return it": [
        r"(ತಪ್ಪಾಗಿ|ಗೊತ್ತಿಲ್ಲದೆ|ತಪ್ಪಾದ್)[^\n]{0,60}(ಕಳುಹಿಸ|ಕಳಿಸ|ಜಮಾ|ಕ್ರೆಡಿಟ್|ಬಂದಿದೆ|ಕಡಪುಡ)[^\n]{0,100}(ಹಿಂದಿರುಗಿಸ|ವಾಪಸ್|ರಿಟರ್ನ್|ಮರಳಿ|ಪಿರ)",
        r"(गलती से)[^\n]{0,60}(भेज|आ गए|आ गया|क्रेडिट|जमा)[^\n]{0,100}(वापस|लौटा|रिटर्न)",
    ],
    "Threatens to cut your water, gas, internet or TV connection": [
        r"(ನೀರು|ನೀರ್|ಗ್ಯಾಸ್|ಇಂಟರ್ನೆಟ್|ಬ್ರಾಡ್ಬ್ಯಾಂಡ್|ಡಿಟಿಎಚ್)[^\n]{0,60}(ಸಂಪರ್ಕ|ಕನೆಕ್ಷನ್|ಸರಬರಾಜು)[^\n]{0,40}(ಕಟ್|ಕಡಿತ|ಸ್ಥಗಿತ|ನಿಲ್ಲಿಸ)",
        r"(पानी|गैस|इंटरनेट|ब्रॉडबैंड|डीटीएच)[^\n]{0,60}(कनेक्शन|सप्लाई|आपूर्ति)[^\n]{0,40}(कट|काट|बंद)",
    ],
    "Asks for your SIM card number (used to take over your number)": [
        r"ಸಿಮ್[^\n]{0,60}(\d{2} ?ಅಂಕಿ|ಸೀರಿಯಲ್|ನಂಬರ್)[^\n]{0,40}(ಕಳುಹಿಸಿ|ಕಳಿಸಿ|ಹೇಳಿ|sms|ಎಸ್ಎಂಎಸ್|ಕಡಪುಡ್ಲೆ|ಪನ್ಲೆ)",
        r"सिम[^\n]{0,60}(\d{2} ?अंक|सीरियल|नंबर)[^\n]{0,40}(भेजें|भेजो|भेजिए|बताएं|बताओ|sms|एसएमएस)",
    ],
    "Says a parcel couldn't be delivered and asks you to update details or pay": [
        r"(ಪಾರ್ಸೆಲ್|ಕೊರಿಯರ್|ಡೆಲಿವರಿ|ಅಂಚೆ)[^\n]{0,80}(ವಿಳಾಸ|ತಲುಪಿಸಲು ಆಗಿಲ್ಲ|ವಿಫಲ|ತಡೆ)[^\n]{0,80}(ಅಪ್ಡೇಟ್|ಕ್ಲಿಕ್|ಲಿಂಕ್|ಪಾವತಿ|ಕಟ್ಟಿ)",
        r"(पार्सल|कूरियर|डिलीवरी|पैकेज|इंडिया पोस्ट)[^\n]{0,80}(पता|नहीं हो (सकी|पाई)|असफल|रुकी|रोक)[^\n]{0,80}(अपडेट|क्लिक|लिंक|भुगतान|शुल्क)",
    ],
    "Threatens to block something unless you pay": [
        r"(ಬ್ಲಾಕ್|ರದ್ದು|ಸ್ಥಗಿತ|ತಡೆಹಿಡಿ)[^\n]{0,60}(ಪಾವತಿ|ಶುಲ್ಕ|ದಂಡ|ಹಣ ಕಟ್ಟ|ಫೀಸ್)[^\n]{0,60}(ಲಿಂಕ್|ಕರೆ|ತಕ್ಷಣ|ಇಂದೇ|upi|ಯುಪಿಐ)",
        r"(ब्लॉक|रद्द|बंद|रोक)[^\n]{0,60}(भुगतान|शुल्क|जुर्माना|फीस)[^\n]{0,60}(लिंक|कॉल|तुरंत|आज ही|upi|यूपीआई)",
    ],
    "Asks you to share an OTP, PIN, CVV or password": [
        r"(otp|ಒಟಿಪಿ|ಓಟಿಪಿ|pin|ಪಿನ್|cvv|ಪಾಸ್ವರ್ಡ್|ಕೋಡ್)[^.\n]{0,40}" + KN_ASK,
        r"(ಬಂದ|ಬಂದಿರುವ|ಬತ್ತಿನ)[^.\n]{0,12}(otp|ಒಟಿಪಿ|ಕೋಡ್)",
        r"(otp|ओटीपी|pin|पिन|cvv|पासवर्ड|कोड)[^।.\n]{0,40}" + HI_ASK,
        r"(आया|आए|आई|आया हुआ)[^।\n]{0,12}(otp|ओटीपी|कोड)",
    ],
    "Asks for your UPI PIN to 'receive' money (you never need a PIN to receive)": [
        r"(upi pin|ಯುಪಿಐ ಪಿನ್|यूपीआई पिन|upi पिन)[^.\n]{0,40}(ಪಡೆಯ|ಸ್ವೀಕರಿಸ|ಕ್ಯಾಶ್ಬ್ಯಾಕ್|ರಿಫಂಡ್|ಬರುತ್ತ|प्राप्त|पाने|मिलेगा|मिलेंगे|कैशबैक|रिफंड)",
        r"(ಪಡೆಯಲು|ಸ್ವೀಕರಿಸಲು|पाने के लिए|प्राप्त करने के लिए)[^.\n]{0,30}(ಪಿನ್|pin|पिन)",
    ],
    "Bank / KYC / PAN impersonation": [
        r"(ಖಾತೆ|ಅಕೌಂಟ್|ಕಾರ್ಡ್|ಬ್ಯಾಂಕ್)[^.\n]{0,40}(ಬ್ಲಾಕ್|ಬಂದ್ ಆಗ|ಸ್ಥಗಿತ|ನಿಷ್ಕ್ರಿಯ|ಫ್ರೀಜ್)",
        r"(kyc|ಕೆವೈಸಿ)[^.\n]{0,40}(ಅಪ್ಡೇಟ್|ಬಾಕಿ|ಪರಿಶೀಲ|ಪೂರ್ಣ|ಮಾಡಿ)",
        r"(ಪ್ಯಾನ್|pan|ಆಧಾರ್)[^.\n]{0,20}(ಲಿಂಕ್|ಅಪ್ಡೇಟ್|ಜೋಡಿಸ)",
        r"(खाता|खाते|अकाउंट|कार्ड|बैंक)[^।\n]{0,40}(बंद हो|बंद कर|ब्लॉक|निलंबित|फ्रीज)",
        r"(kyc|केवाईसी)[^।\n]{0,40}(अपडेट|लंबित|पूरा|करें|कराएं)",
        r"(पैन|pan|आधार)[^।\n]{0,20}(लिंक|अपडेट)",
    ],
    "Electricity disconnection threat": [
        r"(ಕರೆಂಟ್|ವಿದ್ಯುತ್|ಲೈಟ್|ಬೆಸ್ಕಾಂ|ಮೆಸ್ಕಾಂ|ಹೆಸ್ಕಾಂ|ಚೆಸ್ಕಾಂ|ಜೆಸ್ಕಾಂ)[^.\n]{0,60}(ಕಟ್|ಸ್ಥಗಿತ|ಕಡಿತ|ನಿಲ್ಲಿಸ)",
        r"(ಕರೆಂಟ್ ಬಿಲ್|ವಿದ್ಯುತ್ ಬಿಲ್)[^.\n]{0,50}(ಅಪ್ಡೇಟ್ ಆಗಿಲ್ಲ|ಬಾಕಿ|ಪಾವತಿಸಿಲ್ಲ)",
        r"(बिजली|लाइट|विद्युत)[^।\n]{0,60}(कट|काट|बंद कर|बंद हो)",
        r"(बिजली बिल|बिल)[^।\n]{0,50}(अपडेट नहीं|बकाया|जमा नहीं)",
    ],
    "Courier / customs / 'digital arrest' scam": [
        r"(ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್|डिजिटल अरेस्ट|डिजिटल गिरफ्तारी)",
        r"(ಪಾರ್ಸೆಲ್|ಕೊರಿಯರ್|पार्सल|कूरियर|कुरियर)[^\n]{0,100}(ಡ್ರಗ್ಸ್|ಮಾದಕ|ಪೊಲೀಸ್|ಅಕ್ರಮ|ವಶಪಡಿಸ|ड्रग्स|नशीले|पुलिस|अवैध|गैरकानूनी|जब्त)",
        r"(ಪೊಲೀಸ್|ಸಿಬಿಐ|cbi|ಕ್ರೈಂ ಬ್ರಾಂಚ್|पुलिस|सीबीआई|क्राइम ब्रांच|साइबर क्राइम)[^\n]{0,80}(ಅರೆಸ್ಟ್|ಬಂಧನ|ಬಂಧಿಸ|ವಾರಂಟ್|ವೀಡಿಯೊ ಕಾಲ್|ವಿಡಿಯೋ ಕಾಲ್|गिरफ्तार|वारंट|वीडियो कॉल|अरेस्ट)",
    ],
    "Impersonating government, police or tax department": [
        r"(ಆದಾಯ ತೆರಿಗೆ|ಇನ್ಕಮ್ ಟ್ಯಾಕ್ಸ್|आयकर|इनकम टैक्स)[^.\n]{0,40}(ರಿಫಂಡ್|ನೋಟಿಸ್|ದಂಡ|रिफंड|नोटिस|जुर्माना)",
        r"(ಸಿಮ್|ಮೊಬೈಲ್ ನಂಬರ್|ನಿಮ್ಮ ನಂಬರ್|सिम|मोबाइल नंबर|आपका नंबर)[^.\n]{0,40}(ಬ್ಲಾಕ್|ಸ್ಥಗಿತ|ಬಂದ್|बंद|ब्लॉक)",
    ],
    "Promises easy fixed daily/hourly earnings": [
        r"(ದಿನಕ್ಕೆ|ಪ್ರತಿದಿನ|ಗಂಟೆಗೆ|रोज|प्रतिदिन|रोजाना|प्रति दिन|हर दिन|घंटे)[^.\n]{0,30}" + MONEY + r"\s?\d",
        MONEY + r"\s?\d[\d,]*[^.\n]{0,25}(ದಿನಕ್ಕೆ|ಪ್ರತಿದಿನ|ಗಂಟೆಗೆ|रोज|प्रतिदिन|रोजाना|प्रति दिन)",
    ],
    "Task-based or fake job offer": [
        r"(ಲೈಕ್|ರಿವ್ಯೂ|ರೇಟಿಂಗ್|ಸಬ್ಸ್ಕ್ರೈಬ್|लाइक|रिव्यू|रेटिंग|सब्सक्राइब)[^.\n]{0,40}(ವೀಡಿಯೊ|ವಿಡಿಯೋ|ಯೂಟ್ಯೂಬ್|youtube|ಹೋಟೆಲ್|वीडियो|यूट्यूब|होटल)",
        r"(ನೋಂದಣಿ|ರಿಜಿಸ್ಟ್ರೇಶನ್|ತರಬೇತಿ|ಟ್ರೇನಿಂಗ್|ಸೆಕ್ಯುರಿಟಿ) ?(ಶುಲ್ಕ|ಫೀ|ಫೀಸ್|ಠೇವಣಿ)",
        r"(रजिस्ट्रेशन|पंजीकरण|ट्रेनिंग|सिक्योरिटी) ?(फीस|शुल्क|डिपॉजिट)",
        r"(ಮನೆಯಿಂದಲೇ|ಮನೆಯಲ್ಲೇ ಕುಳಿತು|ಪಾರ್ಟ್ ಟೈಮ್|घर बैठे|पार्ट टाइम)[^\n]{0,80}(ಗಳಿಸಿ|ಸಂಪಾದ|ಸಂಬಳ|ಆದಾಯ|कमाएं|कमाई|कमाइए|सैलरी|आय)",
    ],
    "Prize, lottery or 'you have won' offer": [
        r"(ಲಾಟರಿ|ಲಕ್ಕಿ ಡ್ರಾ|ನೀವು ಗೆದ್ದಿದ್ದೀರಿ|ಬಹುಮಾನ ಗೆದ್ದ|ಬಹುಮಾನ ಸಿಕ್ಕ|लॉटरी|लकी ड्रॉ|आपने जीत|इनाम जीत|इनाम मिला|केबीसी)",
        # "Congratulations ... ₹25 lakh"। Also survives screenshot misreads of the prize words
        r"(ಅಭಿನಂದನೆ|बधाई)[^\n]{0,80}" + MONEY + r"\s?\d[\d,]*\s?(ಲಕ್ಷ|ಕೋಟಿ|लाख|करोड)",
    ],
    "Asks you to pay a fee to receive money": [
        r"(ಪ್ರೊ?ಸೆ?ಸಿಂಗ್|ಡೆಲಿವರಿ|ಕ್ಲಿಯರೆನ್ಸ್|ಜಿಎಸ್ಟಿ|ತೆರಿಗೆ|ಬಿಡುಗಡೆ) ?(ಶುಲ್ಕ|ಫೀ|ಫೀಸ್|ಚಾರ್ಜ್)",
        r"(प्र(ो)?स(े)?सिंग|डिलीवरी|क्लियरेंस|जीएसटी|टैक्स|रिलीज) ?(फीस|शुल्क|चार्ज)",
        r"(ಶುಲ್ಕ|ಫೀ|फीस|शुल्क|चार्ज)[^।.\n]{0,15}" + MONEY + r"\s?\d[^।.\n]{0,30}(ಕಳುಹಿಸಿ|ಕಳಿಸಿ|भेजें|भेजो|भेज दें|भेजिए)",
    ],
    "Investment or trading scheme with unrealistic returns": [
        r"(ಖಚಿತ|ಗ್ಯಾರಂಟಿ|ಗ್ಯಾರಂಟೀಡ್)[^.\n]{0,15}(ಲಾಭ|ರಿಟರ್ನ್|ಆದಾಯ)",
        r"(गारंटी|पक्का|निश्चित|गारंटीड)[^।\n]{0,15}(मुनाफा|रिटर्न|लाभ|कमाई)",
        r"(ಹಣ ಡಬಲ್|ದುಡ್ಡು ಡಬಲ್|पैसा डबल|पैसे डबल|रकम दोगुनी)",
        r"(ಕ್ರಿಪ್ಟೋ|ಟ್ರೇಡಿಂಗ್|ಷೇರು|क्रिप्टो|ट्रेडिंग|शेयर बाजार)[^.\n]{0,40}(ಲಾಭ|ಹೂಡಿಕೆ|ಟಿಪ್ಸ್|मुनाफ|निवेश|टिप्स)",
    ],
    "Asks you to install a remote access / screen sharing app": [
        r"(ಎನಿಡೆಸ್ಕ್|ಟೀಮ್ವೀವರ್|ಸ್ಕ್ರೀನ್ ಶೇರ್|एनीडेस्क|टीमव्यूअर|स्क्रीन शेयर)",
        r"(ಎಪಿಕೆ|एपीके)",
    ],
    "Family member 'new number' / emergency money request": [
        r"(ಹೊಸ ನಂಬರ್|ಫೋನ್ ಕಳೆದು|ಫೋನ್ ಹಾಳಾ|ಪೊಸ ನಂಬರ್|नया नंबर|फोन खो|फोन खराब|फोन टूट)[^\n]{0,120}(ಹಣ|ದುಡ್ಡು|ಕಳುಹಿಸ|ಪೈಸೆ|पैसे|पैसा|भेज)",
        r"(ಅಮ್ಮ|ಅಪ್ಪ|ಮಮ್ಮಿ|ಪಪ್ಪ|ಅಪ್ಪೆ|ಅಮ್ಮೆ|मम्मी|पापा|माँ|मां)[^\n]{0,60}(ಹೊಸ ನಂಬರ್|ಪೊಸ ನಂಬರ್|नया नंबर)",
    ],
    "Refund or cashback that needs you to click or fill a form": [
        r"(ರಿಫಂಡ್|ಕ್ಯಾಶ್ಬ್ಯಾಕ್|ಹಣ ವಾಪಸ್|रिफंड|कैशबैक|पैसे वापस)[^.\n]{0,60}(ಕ್ಲಿಕ್|ಲಿಂಕ್|ಫಾರ್ಮ್|क्लिक|लिंक|फॉर्म)",
    ],
    "Pressure / urgency language": [
        r"(ತಕ್ಷಣ|ಕೂಡಲೇ|ಇಂದೇ|ಇವತ್ತೇ|ಇಂದು ರಾತ್ರಿ|ಇವತ್ತು ರಾತ್ರಿ|ಕೊನೆಯ ಅವಕಾಶ|ಕೊನೆಯ ಎಚ್ಚರಿಕೆ|ತುರ್ತು|ತುರ್ತಾಗಿ|ಇತ್ತೆನೇ|ಬೇಗನೇ)",
        r"(तुरंत|फौरन|आज ही|आज रात|अंतिम चेतावनी|आखिरी मौका|जल्द से जल्द|घंटे के भीतर|घंटों में)",
    ],
    "Asks you to call or message an unknown number": [
        r"(ಕರೆ ಮಾಡಿ|ಸಂಪರ್ಕಿಸಿ|ವಾಟ್ಸಾಪ್|ಕಾಲ್ ಮಲ್ಪುಲೆ|कॉल करें|फोन करें|संपर्क करें|व्हाट्सएप)[^\n]{0,40}" + NUM,
        NUM + r"[^\n]{0,30}(ಗೆ ಕರೆ|ಕರೆ ಮಾಡಿ|ಸಂಪರ್ಕಿಸಿ|ಕಾಲ್ ಮಲ್ಪುಲೆ|पर कॉल|पर फोन|पर संपर्क)",
    ],
}
for _label, _patterns, _w in RULES:
    _patterns.extend(NATIVE_PATTERNS.get(_label, []))


# ---------------------------------------------------------------------------
# TAMIL, TELUGU, MALAYALAM and MARATHI rules. So the most common scams are
# caught even when no translation is available (the ₹0 fallback).
# ---------------------------------------------------------------------------
MORE_NATIVE_PATTERNS = {
    "Asks you to share an OTP, PIN, CVV or password": [
        r"(otp|ஓடிபி|pin|பின்|cvv|கடவுச்சொல்|குறியீடு)[^.\n]{0,40}(சொல்லுங்கள்|சொல்லுங்க|சொல்லவும்|அனுப்புங்கள்|அனுப்பவும்|பகிரவும்|பகிருங்கள்|கொடுங்கள்|தெரிவிக்கவும்)",
        r"(வந்த|பெற்ற)[^.\n]{0,12}(otp|ஓடிபி|குறியீடு)",
        r"(otp|ఓటీపీ|pin|పిన్|cvv|పాస్వర్డ్|కోడ్)[^.\n]{0,40}(చెప్పండి|చెప్పు|పంపండి|పంపు|షేర్ చేయండి|ఇవ్వండి|తెలియజేయండి)",
        r"(వచ్చిన)[^.\n]{0,12}(otp|ఓటీపీ|కోడ్)",
        r"(otp|ഒടിപി|pin|പിൻ|cvv|പാസ്വേഡ്|കോഡ്)[^.\n]{0,40}(പറയൂ|പറയുക|അയക്കൂ|അയയ്ക്കുക|ഷെയർ ചെയ്യൂ|നൽകൂ|നൽകുക)",
        r"(വന്ന|ലഭിച്ച)[^.\n]{0,12}(otp|ഒടിപി|കോഡ്)",
        r"(otp|ओटीपी|pin|पिन|cvv|पासवर्ड|कोड)[^।.\n]{0,40}(सांगा|पाठवा|शेअर करा|द्या)",
        r"(आलेला|आलेले)[^।\n]{0,12}(otp|ओटीपी|कोड)",
    ],
    "Asks for your UPI PIN to 'receive' money (you never need a PIN to receive)": [
        r"(upi pin|யுபிஐ பின்)[^.\n]{0,40}(பெற|கேஷ்பேக்|ரீஃபண்ட்|பணம் வர)",
        r"(upi pin|యూపీఐ పిన్)[^.\n]{0,40}(పొంద|క్యాష్బ్యాక్|రీఫండ్|డబ్బు వస్తుంది)",
        r"(upi pin|യുപിഐ പിൻ)[^.\n]{0,40}(ലഭിക്ക|സ്വീകരി|ക്യാഷ്ബാക്ക്|റീഫണ്ട്)",
    ],
    "Bank / KYC / PAN impersonation": [
        r"(கணக்கு|அக்கவுண்ட்|கார்டு|வங்கி)[^.\n]{0,40}(முடக்க|தடை|பிளாக்|நிறுத்த|மூடப்)",
        r"(kyc|கேஒய்சி)[^.\n]{0,40}(புதுப்பி|அப்டேட்|நிலுவை|சரிபார்)",
        r"(பான்|pan|ஆதார்)[^.\n]{0,20}(இணை|புதுப்பி|அப்டேட்|லிங்க்)",
        r"(ఖాతా|అకౌంట్|కార్డ్|బ్యాంక్)[^.\n]{0,40}(బ్లాక్|నిలిపి|స్తంభింప|మూసివేయ|ఫ్రీజ్)",
        r"(kyc|కేవైసీ)[^.\n]{0,40}(అప్డేట్|పెండింగ్|పూర్తి|ధృవీకరి)",
        r"(పాన్|pan|ఆధార్)[^.\n]{0,20}(లింక్|అప్డేట్)",
        r"(അക്കൗണ്ട്|കാർഡ്|ബാങ്ക്)[^.\n]{0,40}(ബ്ലോക്ക്|മരവിപ്പി|റദ്ദാക്ക|നിർത്ത)",
        r"(kyc|കെവൈസി)[^.\n]{0,40}(അപ്ഡേറ്റ്|പുതുക്ക|പൂർത്തിയാക്ക)",
        r"(പാൻ|pan|ആധാർ)[^.\n]{0,20}(ലിങ്ക്|അപ്ഡേറ്റ്)",
        r"(खाते|अकाउंट|कार्ड|बँक)[^।\n]{0,40}(बंद होईल|बंद केले|ब्लॉक|गोठव)",
    ],
    "Electricity disconnection threat": [
        r"(மின்சார|மின் இணைப்பு|கரண்ட்)[^.\n]{0,60}(துண்டிக்க|நிறுத்த|கட்)",
        r"(కరెంట్|విద్యుత్|పవర్)[^.\n]{0,60}(కట్|నిలిపి|డిస్కనెక్ట్)",
        r"(വൈദ്യുതി|കറന്റ്|കെഎസ്ഇബി)[^.\n]{0,60}(വിച്ഛേദി|കട്ട്|നിർത്ത)",
        r"(वीज|लाईट|महावितरण)[^।\n]{0,60}(कापली|कापण्यात|कट|खंडित|बंद)",
    ],
    "Courier / customs / 'digital arrest' scam": [
        r"(டிஜிட்டல் கைது|டிஜிட்டல் அரெஸ்ட்|డిజిటల్ అరెస్ట్|ഡിജിറ്റൽ അറസ്റ്റ്)",
        r"(பார்சல்|கூரியர்)[^\n]{0,100}(போதை|போலீஸ்|காவல்|சட்டவிரோத)",
        r"(போலீஸ்|காவல்துறை|சிபிஐ|cbi)[^\n]{0,80}(கைது|வாரண்ட்|வீடியோ கால்)",
        r"(పార్సెల్|కొరియర్)[^\n]{0,100}(డ్రగ్స్|మత్తు|పోలీస్|అక్రమ)",
        r"(పోలీస్|సీబీఐ|cbi)[^\n]{0,80}(అరెస్ట్|వారెంట్|వీడియో కాల్)",
        r"(പാർസൽ|കൊറിയർ)[^\n]{0,100}(മയക്കുമരുന്ന്|ഡ്രഗ്സ്|പോലീസ്|നിയമവിരുദ്ധ)",
        r"(പോലീസ്|സിബിഐ|cbi)[^\n]{0,80}(അറസ്റ്റ്|വാറണ്ട്|വീഡിയോ കോൾ)",
    ],
    "Prize, lottery or 'you have won' offer": [
        r"(லாட்டரி|லக்கி டிரா|நீங்கள் வென்று|பரிசு வென்ற|பரிசு பெற்ற)",
        r"(లాటరీ|లక్కీ డ్రా|మీరు గెలుచుకున్నారు|బహుమతి గెలుచ)",
        r"(ലോട്ടറി|ലക്കി ഡ്രോ|നിങ്ങൾ നേടി|സമ്മാനം നേടി)",
        r"(लॉटरी|तुम्ही जिंकला|बक्षीस जिंक)",
    ],
    "Asks you to pay a fee to receive money": [
        r"(செயலாக்க|டெலிவரி|ஜிஎஸ்டி) ?(கட்டணம்|சார்ஜ்)",
        r"(ప్రాసెసింగ్|డెలివరీ|జీఎస్టీ) ?(ఫీజు|రుసుము|చార్జ్)",
        r"(പ്രോസസ്സിംഗ്|ഡെലിവറി|ജിഎസ്ടി) ?(ഫീസ്|ചാർജ്)",
        r"(प्रोसेसिंग|डिलिव्हरी) ?(फी|शुल्क)",
    ],
    "Promises easy fixed daily/hourly earnings": [
        r"(தினமும்|ஒரு நாளைக்கு|தினசரி|రోజుకు|ప్రతిరోజు|రోజూ|ദിവസവും|പ്രതിദിനം|दररोज|रोज)[^.\n]{0,30}" + MONEY + r"\s?\d",
    ],
    "Task-based or fake job offer": [
        r"(வீட்டிலிருந்தே|பகுதி நேர)[^\n]{0,80}(சம்பாதி|வருமானம்|சம்பளம்)",
        r"(லைக்|ரிவ்யூ|ரேட்டிங்)[^.\n]{0,40}(வீடியோ|யூடியூப்|youtube)",
        r"(பதிவு|பயிற்சி) ?கட்டணம்",
        r"(ఇంటి నుండే|పార్ట్ టైమ్)[^\n]{0,80}(సంపాదించ|జీతం|ఆదాయం)",
        r"(లైక్|రివ్యూ|రేటింగ్)[^.\n]{0,40}(వీడియో|యూట్యూబ్|youtube)",
        r"(రిజిస్ట్రేషన్|ట్రైనింగ్) ?(ఫీజు|రుసుము)",
        r"(വീട്ടിലിരുന്ന്|പാർട്ട് ടൈം)[^\n]{0,80}(സമ്പാദി|ശമ്പളം|വരുമാനം)",
        r"(ലൈക്ക്|റിവ്യൂ|റേറ്റിംഗ്)[^.\n]{0,40}(വീഡിയോ|യൂട്യൂബ്|youtube)",
        r"(രജിസ്ട്രേഷൻ|ട്രെയിനിംഗ്) ?ഫീസ്",
        r"(घरबसल्या|पार्ट टाइम)[^\n]{0,80}(कमवा|पगार|उत्पन्न)",
    ],
    "Investment or trading scheme with unrealistic returns": [
        r"(உத்தரவாத|கியாரண்டி)[^.\n]{0,15}(லாபம்|வருமானம்)", r"பணம் இரட்டிப்பு",
        r"(గ్యారంటీ|హామీ)[^.\n]{0,15}(లాభం|రాబడి)", r"డబ్బు రెట్టింపు",
        r"(ഉറപ്പായ|ഗ്യാരണ്ടി)[^.\n]{0,15}(ലാഭം|റിട്ടേൺ)", r"പണം ഇരട്ടി",
        r"(खात्रीशीर|हमखास)[^।\n]{0,15}(नफा|परतावा)",
    ],
    "Asks you to install a remote access / screen sharing app": [
        r"(எனிடெஸ்க்|டீம்வியூவர்|ஸ்கிரீன் ஷேர்|ఎనీడెస్క్|టీమ్వ్యూయర్|స్క్రీన్ షేర్|എനിഡെസ്ക്|ടീംവ്യൂവർ|സ്ക്രീൻ ഷെയർ)",
    ],
    "Family member 'new number' / emergency money request": [
        r"(புதிய எண்|போன் தொலை)[^\n]{0,120}(பணம்|அனுப்ப)",
        r"(కొత్త నంబర్|ఫోన్ పోయింది)[^\n]{0,120}(డబ్బు|పంప)",
        r"(പുതിയ നമ്പർ|ഫോൺ നഷ്ടപ്പെട്ടു)[^\n]{0,120}(പണം|അയക്ക)",
        r"(नवीन नंबर|फोन हरवला)[^\n]{0,120}(पैसे|पाठव)",
    ],
    "Refund or cashback that needs you to click or fill a form": [
        r"(ரீஃபண்ட்|கேஷ்பேக்|பணம் திரும்ப)[^.\n]{0,60}(கிளிக்|லிங்க்|இணைப்பை)",
        r"(రీఫండ్|క్యాష్బ్యాక్)[^.\n]{0,60}(క్లిక్|లింక్)",
        r"(റീഫണ്ട്|ക്യാഷ്ബാക്ക്)[^.\n]{0,60}(ക്ലിക്ക്|ലിങ്ക്)",
    ],
    "Pressure / urgency language": [
        r"(உடனே|உடனடியாக|இன்றே|இன்று இரவு|கடைசி வாய்ப்பு|அவசர)",
        r"(వెంటనే|తక్షణమే|ఈరోజే|ఈ రాత్రి|చివరి అవకాశం|అత్యవసర)",
        r"(ഉടൻ|ഉടനടി|ഇന്ന് തന്നെ|ഇന്ന് രാത്രി|അവസാന അവസരം|അടിയന്തര)",
        r"(ताबडतोब|लगेच|आजच|आज रात्री|शेवटची संधी)",
    ],
    "Asks you to call or message an unknown number": [
        r"(அழைக்கவும்|தொடர்பு கொள்ளவும்|கால் செய்|కాల్ చేయండి|సంప్రదించండి|വിളിക്കുക|ബന്ധപ്പെടുക|कॉल करा|संपर्क करा)[^\n]{0,40}" + NUM,
        NUM + r"[^\n]{0,30}(அழைக்கவும்|தொடர்பு|కి కాల్|కాల్ చేయండి|വിളിക്കുക|ബന്ധപ്പെടുക|वर कॉल करा|वर संपर्क)",
    ],
}

# Malayalam "chillu" letters can be typed two ways; store both texts and patterns one way
CHILLU = {"ൺ": "ണ്", "ൻ": "ന്", "ർ": "ര്", "ൽ": "ല്", "ൾ": "ള്"}


def _unify_chillu(text: str) -> str:
    for atomic, seq in CHILLU.items():
        text = text.replace(atomic, seq)
    return text


for _label, _patterns, _w in RULES:
    _patterns.extend(_unify_chillu(p).replace("‍", "").replace("‌", "")
                     for p in MORE_NATIVE_PATTERNS.get(_label, []))

# Signals that a message is a genuine notification, not a scam
SAFE_SIGNALS = [
    r"\b(do not|don't|dont|never)\s+share\b",
    r"\bnever (ask|asks) for (your )?(otp|pin|password|cvv)\b",
    r"\bkisi (ke saath|se bhi|ko bhi)\b[^.\n]{0,30}\b(share na|mat)\b",
    r"\bif (this was )?not (done by )?you\b",
    # Kannada / Tulu: "don't tell/share with anyone"
    r"ಯಾರಿಗೂ[^.\n]{0,15}(ಹೇಳಬೇಡಿ|ಹಂಚಿಕೊಳ್ಳಬೇಡಿ|ಕೊಡಬೇಡಿ|ಶೇರ್ ಮಾಡಬೇಡಿ|ತಿಳಿಸಬೇಡಿ)",
    r"(ಹಂಚಿಕೊಳ್ಳಬೇಡಿ|ಶೇರ್ ಮಾಡಬೇಡಿ|ಕೊರೊಡ್ಚಿ|ಪನೊಡ್ಚಿ)",
    r"(ನೀವು ಮಾಡಿಲ್ಲದಿದ್ದರೆ|ನೀವು ಮಾಡದಿದ್ದರೆ)",
    # Hindi: "don't share with anyone"
    r"(किसी को भी|किसी के साथ|किसी से)[^।\n]{0,20}(न|ना|मत) ",
    r"(न|ना|मत) (बताएं|बताइए|बताओ|शेयर करें|शेयर करो|दें)",
    r"(यदि|अगर) (यह )?(आपने नहीं|आपके द्वारा नहीं)",
    # Tamil, Telugu, Malayalam, Marathi: "don't share / tell anyone"
    r"(யாருடனும்|யாரிடமும்)[^.\n]{0,20}(பகிர வேண்டாம்|சொல்ல வேண்டாம்|பகிராதீர்கள்)",
    r"(ఎవరితోనూ|ఎవరికీ)[^.\n]{0,20}(షేర్ చేయవద్దు|చెప్పవద్దు|పంచుకోవద్దు)",
    _unify_chillu(r"(ആരുമായും|ആരോടും)[^.\n]{0,20}(പങ്കിടരുത്|പറയരുത്|ഷെയർ ചെയ്യരുത്)"),
    r"(कोणालाही|कोणासोबतही)[^।\n]{0,20}(सांगू नका|शेअर करू नका|देऊ नका)",
]

HIGH_RISK_LABELS = {r[0] for r in RULES if r[2] >= 30}


# ---------------------------------------------------------------------------
# LANGUAGE COVERAGE. Be honest when a message is in a script we can't check well
# ---------------------------------------------------------------------------
NOTE_OTHER_SCRIPT = (
    "This message is mostly in a language our checks can't read yet (we check English, Hinglish, Kannada, "
    "Hindi, Tamil, Telugu, Malayalam and Marathi). We couldn't fully check it. Be careful, and never share "
    "OTPs, PINs or passwords."
)
NOTE_NEW_SCRIPT = (
    "Our checks for messages written in Indian-language scripts are new and may miss some scams. Stay careful."
)
NOTE_TRANSLATED_CHECK = (
    "We also checked an automatic English translation of this message. Translations can miss details. Stay careful."
)
NOTE_HIDDEN_LINK = (
    "This message asks you to click a link, but the link itself isn't visible here. It may be hidden "
    "behind words like 'click here'. Press and hold the link, choose 'Copy link', and paste it into Check a Link."
)

HIDDEN_LINK_PHRASES = re.compile(
    r"(click here|tap here|click (on )?(the )?(below |above )?link|tap (on )?(the )?link|click (the |this )?button|"
    r"click below|link below|ಇಲ್ಲಿ ಕ್ಲಿಕ್|ಇಲ್ಲಿ ಒತ್ತಿ|ಕೆಳಗಿನ ಲಿಂಕ್|ಲಿಂಕ್ ಕ್ಲಿಕ್|ಲಿಂಕ್ ಒತ್ತಿ|ಮುಲ್ಪ ಕ್ಲಿಕ್|"
    r"यहाँ क्लिक|यहां क्लिक|यहाँ टैप|यहां टैप|नीचे दिए (गए )?लिंक|लिंक पर क्लिक|इस लिंक)",
)


def script_mix(text: str) -> dict:
    """Share of letters in: latin, supported Indian scripts (Kannada, Devanagari), other scripts."""
    counts = {"latin": 0, "supported": 0, "other": 0}
    for ch in text:
        if not ch.isalpha():
            continue
        code = ord(ch)
        if ch.isascii():
            counts["latin"] += 1
        elif (0x0900 <= code <= 0x097F or 0x0C80 <= code <= 0x0CFF or 0x0B80 <= code <= 0x0BFF
              or 0x0C00 <= code <= 0x0C7F or 0x0D00 <= code <= 0x0D7F):
            counts["supported"] += 1
        else:
            counts["other"] += 1
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}


def verdict_from_score(score: int) -> str:
    if score >= 50:
        return "SCAM_LIKELY"
    if score >= 25:
        return "SUSPICIOUS"
    return "LIKELY_SAFE"


def _normalise(text: str) -> str:
    text = text.lower()
    # zero-width joiners (common in Kannada words like ಅಪ್‌ಡೇಟ್) and Hindi nukta dots
    text = text.replace("\u200c", "").replace("\u200d", "").replace("\u093c", "")
    text = _unify_chillu(text)
    text = text.replace("’", "'").replace("₹", "₹")
    text = re.sub(r"[ \t]+", " ", text)
    return text


# Scammers write "bl0cked", "W0N", "FL1PKART" so spam filters miss them
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
_DISGUISED = re.compile(r"\b(?=[a-z0-9@$]*[a-z][0-9@$]+[a-z])[a-z0-9@$]{3,}\b")
_SCAM_WORDS = {"blocked", "block", "won", "win", "winner", "kyc", "paytm", "flipkart", "amazon", "account", "verify",
               "prize", "claim", "bank", "update", "cash", "free", "offer", "urgent", "suspended", "lottery", "reward",
               "refund", "click", "bonus", "gift", "expired", "expire", "sbi", "hdfc", "icici", "password", "otp", "loan"}


def _deobfuscate(text_norm: str):
    """(readable text, True if a disguised scam word was found)."""
    found = False

    def fix(m):
        nonlocal found
        word = m.group(0)
        plain = word.translate(_LEET)
        if plain in _SCAM_WORDS or any(plain.startswith(w) for w in ("flipkart", "paytm", "block", "verif", "suspend")):
            found = True
        return plain
    return _DISGUISED.sub(fix, text_norm), found


def analyze_text(text: str) -> dict:
    text_norm = _normalise(text)
    readable, disguised = _deobfuscate(text_norm)
    if readable != text_norm:
        text_norm = text_norm + "\n" + readable      # rules see both the original and the de-disguised words
    findings = []
    score = 0

    parts = []
    for label, patterns, weight in RULES:
        hits = sum(1 for p in patterns if (disguised if p == "__DEOBFUSCATED__" else re.search(p, text_norm)))
        if hits:
            findings.append(label)
            score += weight
            pts = weight
            if hits >= 2 and weight >= 30:
                score += 10  # several independent signs of the same scam type
                pts += 10
            parts.append({"label": label, "points": pts})

    # A plain link on its own is normal, but links in a threatening message are a red flag
    has_link = re.search(LINK, text_norm) is not None
    high_risk_hits = [f for f in findings if f in HIGH_RISK_LABELS]
    if has_link and high_risk_hits:
        findings.append("Contains a link inside a threatening or too-good-to-be-true message")
        score += 15
        parts.append({"label": findings[-1], "points": 15})

    # Pressure + a high-risk ask together is a classic scam combo
    if "Pressure / urgency language" in findings and high_risk_hits:
        score += 10
        parts.append({"label": "Pressure together with a risky request", "points": 10})

    safe_hits = [p for p in SAFE_SIGNALS if re.search(p, text_norm)]
    notes = []
    if safe_hits:
        otp_label = RULES[0][0]
        # A genuine OTP SMS says "do not share this OTP". That alone shouldn't count as asking for it
        asks_to_share_with_sender = re.search(
            r"\b(share|send|tell|forward|give)\b[^.\n]{0,40}\b(otp|code|pin)\b[^.\n]{0,20}\b(with (me|us)|to (me|us)|here)\b",
            text_norm,
        )
        if otp_label in findings and not asks_to_share_with_sender:
            findings.remove(otp_label)
            score -= RULES[0][2]
            parts = [p for p in parts if p["label"] != otp_label]
        score -= 15
        parts.append({"label": "Contains a genuine-looking safety warning (e.g. 'do not share your OTP')", "points": -15})
        notes.append("Contains a genuine-looking safety warning (e.g. 'do not share your OTP')")

    score = max(0, min(100, score))
    verdict = verdict_from_score(score)

    info = []
    mix = script_mix(text)
    if not findings:
        if mix["other"] > 0.4:
            verdict = "UNCERTAIN"  # don't tell people it's safe when we couldn't read it
            info.append(NOTE_OTHER_SCRIPT)
        elif mix["supported"] > 0.4:
            info.append(NOTE_NEW_SCRIPT)

    return {
        "text_analyzed": text,
        "risk_score": score,
        "verdict": verdict,
        "patterns_detected": findings,
        "safe_signals": notes,
        "notes": info,
        "score_parts": parts,
    }



# ---------------------------------------------------------------------------
# LINK CHECK. Every link in the message gets the full link scanner
# (structure rules + domain age + Google Safe Browsing + VirusTotal)
# ---------------------------------------------------------------------------
MAX_LINKS_CHECKED = 5

URL_IN_TEXT = re.compile(
    r"(?<![@\w.])("
    r"https?://[^\s<>\"'()]+"
    r"|www\.[^\s<>\"'()]+"
    r"|(?:[a-z0-9-]+\.)+(?:com|in|net|org|info|xyz|top|club|click|live|icu|buzz|site|online|shop|store|"
    r"rest|sbs|cfd|cyou|vip|support|me|ly|co|io|app|link|tk|ml|ga|cf|gq|ru|cn|sbi)(?:/[^\s<>\"'()]*)?"
    r")",
    re.IGNORECASE,
)


def extract_links(text: str) -> list:
    """Find links in the text (with or without http://), de-duplicated, in order."""
    links = []
    for match in URL_IN_TEXT.finditer(text):
        link = match.group(1).rstrip(".,;:!?)]}'\"")
        if not link.lower().startswith(("http://", "https://")):
            link = "https://" + link
        if link.lower() not in (l.lower() for l in links):
            links.append(link)
    return links


# Screenshot reading often turns the dot in ".gov.in" into an "l" or "i" (TRAI.GOV.IN -> TRAILGOV.IN)
OCR_LINK_FIXES = [(re.compile(r"(?i)^(https?://)?([a-z0-9-]+?)[li1|,]((?:gov|nic|org|co|ac|edu)\.in)(/|$)"), r"\1\2.\3\4"),
                  (re.compile(r"(?i),(com|in|org|net)\b"), r".\1")]


def fix_ocr_link(link: str) -> str:
    """A misread official address is put right when the corrected one is a known official site."""
    from scanners.url_scanner import registered_domain, TRUSTED_DOMAINS, BRANDS, resolve_host, OFFLINE
    from urllib.parse import urlparse
    official = TRUSTED_DOMAINS | set().union(*BRANDS.values())
    for rx, repl in OCR_LINK_FIXES:
        fixed = rx.sub(repl, link)
        if fixed != link:
            # never "correct" an address that really exists: a scam site could use that exact name
            orig_host = (urlparse(link if "://" in link else "https://" + link).hostname or "").lower()
            if not OFFLINE and resolve_host(orig_host).get("exists") is not False:
                continue
            host = (urlparse(fixed if "://" in fixed else "https://" + fixed).hostname or "").lower()
            if host.endswith((".gov.in", ".nic.in")) or registered_domain(host) in official:
                return fixed
    return link


def start_link_checks(text: str, from_screenshot: bool = False):
    """
    Start checking the message's links right away (at the same time as the other work), so
    waiting for a free slot on one service doesn't make the whole check slower.
    Returns (links, [(link, future), ...]).
    """
    from scanners.url_scanner import LINK_POOL, scan_url
    links = extract_links(text)
    if from_screenshot:
        links = list(dict.fromkeys(fix_ocr_link(l) for l in links))
    return links, [(link, LINK_POOL.submit(scan_url, link)) for link in links[:MAX_LINKS_CHECKED]]


def check_links_in_result(result: dict, from_screenshot: bool = False, started=None) -> dict:
    """Run the full link scanner on up to 5 links and fold the results into the verdict."""
    links, futures = started or start_link_checks(result.get("text_analyzed", ""), from_screenshot)
    checked = []
    extra_score = 0
    extra_label = ""
    # The links are checked at the same time, so three links take about as long as one
    for link, future in futures:
        try:
            link_result = future.result(timeout=80)
        except Exception:
            continue
        checked.append({
            "url": link,
            "verdict": link_result["verdict"],
            "risk_score": link_result["risk_score"],
            "findings": link_result["findings"],
            "checks": link_result.get("checks", []),
            "details": link_result.get("details", {}),
        })
        if from_screenshot:
            # A link read from a picture may be misread. A made-up looking address that simply
            # doesn't exist is then more likely our misreading than a scam, unless other checks agree.
            hard = [c for c in link_result.get("checks", []) if c["status"] == "fail" and c["id"] != "exists"]
            if not hard and any(c["id"] == "exists" and c["status"] == "fail" for c in link_result.get("checks", [])):
                checked.pop()
                continue
        reason = next((f for f in link_result["findings"] if "Could not" not in f), "")
        if link_result["verdict"] == "DANGEROUS":
            result["patterns_detected"].append(
                f"The link {link} looks dangerous" + (f": {reason}" if reason else "")
            )
            if extra_score < 50:
                extra_label = result["patterns_detected"][-1]
            extra_score = max(extra_score, 50)
        elif link_result["verdict"] == "CAUTION":
            result["patterns_detected"].append(
                f"The link {link} looks suspicious" + (f": {reason}" if reason else "")
            )
            if extra_score < 20:
                extra_label = result["patterns_detected"][-1]
            extra_score = max(extra_score, 20)

    if len(links) > MAX_LINKS_CHECKED:
        result["patterns_detected"].append(
            f"This message has {len(links)} links; we checked the first {MAX_LINKS_CHECKED}"
        )

    if not links and HIDDEN_LINK_PHRASES.search(_normalise(result.get("text_analyzed", ""))):
        result.setdefault("notes", []).append(NOTE_HIDDEN_LINK)

    result["links_checked"] = checked
    if extra_score:
        result.setdefault("score_parts", []).append({"label": extra_label, "points": extra_score})
    result["risk_score"] = min(100, result["risk_score"] + extra_score)
    if extra_score or result.get("verdict") != "UNCERTAIN":
        result["verdict"] = verdict_from_score(result["risk_score"])
    return result

# ---------------------------------------------------------------------------
# TRANSLATION. Understand other languages, and explain in the visitor's language
# ---------------------------------------------------------------------------
def request_language() -> str:
    """The website language the visitor is using (sent by the frontend as X-Lang)."""
    lang = (request.headers.get("X-Lang") or "en").strip().lower()
    return lang if re.fullmatch(r"[a-z]{2,3}", lang) else "en"


def add_translation(result: dict, ui_lang: str) -> dict:
    """
    1. If the message isn't mainly in English letters, check an English translation
       with the same rules and merge what it finds (the rules still decide).
    2. If the message's language differs from the website's, add
       result["translation"] = {"text", "from", "to"} so we can show what it says.
    """
    from scanners.translator import translate

    text = result.get("text_analyzed", "")
    mix = script_mix(text)
    non_latin = mix["supported"] + mix["other"]
    english = None

    if non_latin >= 0.2:
        english = translate(text, "en", priority="high", wait=30)
        if english and english["text"].strip():
            en_result = analyze_text(english["text"])
            for pattern in en_result["patterns_detected"]:
                if pattern not in result["patterns_detected"]:
                    result["patterns_detected"].append(pattern)
            if en_result["risk_score"] > result["risk_score"]:
                have = {p["label"] for p in result.get("score_parts", [])}
                result.setdefault("score_parts", []).extend(p for p in en_result["score_parts"] if p["label"] not in have)
            was_unreadable = result.get("verdict") == "UNCERTAIN" or not result["patterns_detected"]
            result["risk_score"] = max(result["risk_score"], en_result["risk_score"])
            result["verdict"] = verdict_from_score(result["risk_score"])
            notes = [n for n in result.get("notes", []) if n not in (NOTE_OTHER_SCRIPT, NOTE_NEW_SCRIPT)]
            if was_unreadable or mix["other"] > 0.4:
                notes.append(NOTE_TRANSLATED_CHECK)
            result["notes"] = notes

    # "What this message says" in the visitor's language
    target = ui_lang
    meaning = english if (english and target == "en") else None
    if meaning is None and text.strip():
        if non_latin >= 0.2 or target != "en":
            meaning = translate(text, target, priority="normal", wait=20)
    if meaning and meaning.get("from") and meaning["from"].split("-")[0] not in (target, meaning.get("to")) \
            and meaning["text"].strip().lower() != text.strip().lower():
        result["translation"] = meaning

    # Which language the message is in, so the page can offer translations
    from scanners.translator import guess_language
    detected = ((english or meaning or {}).get("from") or "").split("-")[0].lower()
    result["message_language"] = detected if re.fullmatch(r"[a-z]{2,3}", detected) else guess_language(text)
    return result


TRANSLATE_TARGETS = {"en", "kn", "hi", "tcy"}


@message_scanner_bp.route("/api/translate", methods=["POST"])
def translate_route():
    """Translate a message the visitor already checked into another website language."""
    from scanners.translator import translate
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()[:1500]
    target = str(data.get("to") or "").strip().lower()
    if not text:
        return jsonify({"error": "Please paste the message you want to check."}), 400
    if target not in TRANSLATE_TARGETS:
        return jsonify({"error": "That language isn't available."}), 400
    out = translate(text, target, priority="low", wait=20)
    src = (out or {}).get("from", "").split("-")[0]
    if not out or not out.get("text", "").strip() or (src and src == out.get("to")):
        return jsonify({"error": "We couldn't translate this right now. Please try again in a moment."}), 503
    return jsonify({"text": out["text"], "from": (out.get("from") or "").split("-")[0], "to": out.get("to", target)})


# ---------------------------------------------------------------------------
# OCR helpers
# ---------------------------------------------------------------------------
def _prepare_for_ocr(img, target_w: int = 1100):
    """
    Grayscale, fix phone photo rotation, bring the size into the range Tesseract reads
    best AND fast, handle dark mode. Phone screenshots (e.g. 1080x2400) are scaled so the
    width is about 1100px; huge photos are shrunk, tiny crops are enlarged.
    """
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    w, h = img.size
    scale = target_w / w
    # never let the picture get too big in total (that is what makes reading slow)
    max_pixels = 3_000_000
    if (w * scale) * (h * scale) > max_pixels:
        scale = (max_pixels / (w * h)) ** 0.5
    scale = max(0.3, min(scale, 2.5))
    if abs(scale - 1) > 0.08:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    # Dark-mode chat screenshots: light text on dark background -> invert
    histogram = img.histogram()
    total_pixels = img.size[0] * img.size[1]
    if sum(histogram[:100]) > total_pixels * 0.5:
        img = ImageOps.invert(img)
    return ImageOps.autocontrast(img)


_OCR_LANGS = None


def ocr_languages() -> str:
    """English plus Kannada and Hindi when their language packs are installed (see Dockerfile)."""
    global _OCR_LANGS
    if _OCR_LANGS is None:
        try:
            installed = set(pytesseract.get_languages(config=""))
        except Exception:
            installed = {"eng"}
        _OCR_LANGS = "+".join(l for l in ("eng", "kan", "hin") if l in installed) or "eng"
    return _OCR_LANGS


OCR_TIME_BUDGET = 80  # seconds for all reading passes together (gunicorn allows 120)
# One screenshot at a time: two readings in parallel on a small server make both slow
_OCR_LOCK = threading.Semaphore(1)
OCR_PROBLEM = {"last": None}


def _looks_like_real_english(text: str) -> bool:
    """True when the English pass produced mostly real words (not garbage from another script)."""
    words = re.findall(r"[A-Za-z0-9@₹.:/'-]+", text)
    if len(words) < 3:
        return False
    good = [w for w in words if re.fullmatch(r"[A-Za-z]{2,}", w) and re.search(r"[aeiouyAEIOUY]", w)
            or re.fullmatch(r"[0-9₹.,:/-]{2,}", w) or "http" in w.lower() or "@" in w]
    return len(good) / len(words) >= 0.55


def _tesseract(img, lang: str, config: str, timeout: int) -> str:
    """Run Tesseract; returns '' on time-out or error (and remembers the error for /api/ocr-check)."""
    try:
        return pytesseract.image_to_string(img, lang=lang, config=config, timeout=max(5, timeout)).strip()
    except RuntimeError as e:  # time-out, or a Tesseract error (TesseractError is a RuntimeError)
        OCR_PROBLEM["last"] = f"{lang} {config}: {str(e)[:160] or 'timed out'}"
        return ""
    except Exception as e:
        OCR_PROBLEM["last"] = f"{lang}: {type(e).__name__}: {str(e)[:120]}"
        return ""


def _ocr_space(image_bytes_jpeg: bytes) -> str:
    """
    Optional free backup reader (OCR.space, 25,000 free reads a month, no card).
    Used only when Tesseract fails. Needs OCRSPACE_API_KEY in Render's environment.
    """
    key = os.environ.get("OCRSPACE_API_KEY", "")
    from scanners.quota import quota
    if not key or not quota("ocrspace").take(wait=15):
        return ""
    try:
        import requests
        resp = requests.post(
            "https://api.ocr.space/parse/image",
            headers={"apikey": key},
            files={"file": ("screenshot.jpg", image_bytes_jpeg, "image/jpeg")},
            data={"OCREngine": "2", "language": "auto", "scale": "true", "detectOrientation": "true"},
            timeout=25,
        )
        data = resp.json()
        if data.get("IsErroredOnProcessing"):
            OCR_PROBLEM["last"] = f"OCR.space: {str(data.get('ErrorMessage'))[:120]}"
            return ""
        return "\n".join(r.get("ParsedText", "") for r in data.get("ParsedResults") or []).strip()
    except Exception as e:
        OCR_PROBLEM["last"] = f"OCR.space: {type(e).__name__}"
        return ""


def _tesseract_conf(img, lang: str, config: str, timeout: int):
    """Text plus Tesseract's average confidence (0-100) for the words it read."""
    try:
        d = pytesseract.image_to_data(img, lang=lang, config=config, timeout=max(5, timeout),
                                      output_type=pytesseract.Output.DICT)
    except RuntimeError as e:
        OCR_PROBLEM["last"] = f"{lang} {config}: {str(e)[:160] or 'timed out'}"
        return "", 0.0
    except Exception as e:
        OCR_PROBLEM["last"] = f"{lang}: {type(e).__name__}: {str(e)[:120]}"
        return "", 0.0
    lines, confs = {}, []
    for k, word in enumerate(d.get("text", [])):
        if not str(word).strip():
            continue
        key = (d["block_num"][k], d["par_num"][k], d["line_num"][k])
        lines.setdefault(key, []).append(str(word))
        try:
            c = float(d["conf"][k])
            if c >= 0:
                confs.append(c)
        except (TypeError, ValueError):
            pass
    text = "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
    return text.strip(), (sum(confs) / len(confs) if confs else 0.0)


def _latin_items(text: str) -> list:
    """Links, email addresses, UPI IDs and phone numbers in an English reading of a picture."""
    items = []
    for m in re.finditer(r"(?:https?://)?(?:[A-Za-z0-9-]+\.)+(?:com|in|net|org|co|xyz|top|info|app|link|me|ly|io|gov\.in|nic\.in)(?:/[^\s]*)?"
                         r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)*|\+?\d[\d\s-]{8,}\d", text or "", re.IGNORECASE):
        v = m.group(0).strip().rstrip(".,;:")
        if v and v not in items:
            items.append(v)
    return items[:8]


def fix_ocr_links(text: str) -> str:
    """
    Screenshot reading often turns the dot in an underlined link into 'L', 'I' or '1'
    ('TRAI.GOV.IN' -> 'TRAILGOV.IN'). When the name as read doesn't exist on the internet and
    putting a dot back gives a known official website (a bank, a brand, any .gov.in / .nic.in /
    .bank.in site), use that instead. A lookalike that really exists is never "corrected".
    """
    from scanners.url_scanner import TRUSTED_DOMAINS, registered_domain

    def official(host: str) -> bool:
        host = host.lower()
        return registered_domain(host) in TRUSTED_DOMAINS or host.endswith((".gov.in", ".nic.in", ".bank.in"))

    def fix(m):
        host = m.group(0)
        if official(host):
            return host
        # a real website with this exact name (maybe a lookalike a scammer bought) stays as read
        try:
            from scanners.url_scanner import resolve_host
            if resolve_host(host.lower()).get("exists") is not False:
                return host
        except Exception:
            return host
        for i, ch in enumerate(host):
            if ch in "lLiI1|":
                for cand in (host[:i] + "." + host[i + 1:], host[:i] + "." + host[i:]):
                    if ".." not in cand and official(cand):
                        return cand
        return host

    return re.sub(r"(?<![\w@.-])(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?![\w-])", fix, text or "")


def _detect_script(img) -> str:
    """Tesseract's script detector: 'Kannada', 'Devanagari', 'Latin'... or '' when unsure."""
    try:
        osd = pytesseract.image_to_osd(img, config="--psm 0", timeout=10)
    except Exception:
        return ""
    m = re.search(r"Script:\s*(\w+)", osd)
    return m.group(1) if m else ""


SCRIPT_LANG = {"Kannada": "kan", "Devanagari": "hin"}


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    1. Ask Tesseract which script the screenshot is in. Kannada or Hindi screenshots are read
       with that language (plus English for numbers, links and names).
    2. Otherwise read it as English, and check Tesseract's own confidence. Text in another
       script read as English comes back as confident-looking nonsense with LOW confidence, so
       then we read it again with Kannada and Hindi and keep the better reading.
    3. If nothing worked, try a smaller picture, then the optional OCR.space backup.
    Raises RuntimeError only when every way failed.
    """
    started = time.time()
    img = Image.open(io.BytesIO(image_bytes))
    img.load()
    prepared = _prepare_for_ocr(img)
    langs = ocr_languages()
    installed = set(langs.split("+"))

    def left() -> int:
        return int(OCR_TIME_BUDGET - (time.time() - started))

    def native_share(text: str) -> float:
        mix = script_mix(text)
        return mix["supported"] + mix["other"]

    with _OCR_LOCK:
        script = _detect_script(prepared) if len(installed) > 1 else ""
        native = SCRIPT_LANG.get(script)
        if native and native in installed:
            # Indian scripts have small joined letters: a bigger picture reads them much better
            big = _prepare_for_ocr(img, 1600)
            text, conf = _tesseract_conf(big, f"{native}+eng", "--oem 1 --psm 6", min(45, left()))
            if text and (conf >= 45 or native_share(text) >= 0.2):
                # ...but the bigger picture can garble underlined links. Take links, numbers and
                # email addresses from a normal-size English reading too, so they get checked.
                if left() > 8:
                    english = _tesseract(prepared, "eng", "--oem 1 --psm 6", min(25, left()))
                    extras = [x for x in _latin_items(english) if x.lower() not in text.lower()]
                    if extras:
                        text = text.rstrip() + "\n" + " ".join(extras)
                return text

        english, eng_conf = _tesseract_conf(prepared, "eng", "--oem 1 --psm 6", min(40, left()))
        if english and (langs == "eng" or (eng_conf >= 72 and _looks_like_real_english(english))):
            return english

        best, best_conf = english, eng_conf
        if langs != "eng" and left() > 10:
            mixed, mixed_conf = _tesseract_conf(prepared, langs, "--oem 1 --psm 6", left())
            # prefer the Indian-language reading when it is at least as sure, or clearly found that script
            if mixed and (mixed_conf >= best_conf - 5 or native_share(mixed) >= 0.25):
                best, best_conf = mixed, mixed_conf
        if best:
            return best

        # Nothing yet: a smaller picture reads faster
        if left() > 10:
            small = prepared.copy()
            small.thumbnail((800, 1800))
            best = _tesseract(small, "eng" if langs == "eng" else langs, "--oem 1 --psm 3", left())
            if best:
                return best

    # Last try: the free OCR.space backup (if a key is set)
    buf = io.BytesIO()
    backup = prepared.copy()
    backup.thumbnail((1400, 2400))
    backup.convert("L").save(buf, "JPEG", quality=80)
    text = _ocr_space(buf.getvalue())
    if text:
        return text
    raise RuntimeError("could not read the image")


def ocr_self_check() -> dict:
    """Reads a small built-in test picture and reports how long it took (for /api/ocr-check)."""
    from PIL import ImageDraw
    img = Image.new("L", (900, 260), 255)
    d = ImageDraw.Draw(img)
    d.text((30, 60), "Your SBI account will be blocked today", fill=0)
    d.text((30, 120), "Update KYC now 9876543210", fill=0)
    img = img.resize((1800, 520))
    t = time.time()
    text = _tesseract(img, "eng", "--oem 1 --psm 6", 60)
    return {
        "ok": bool(text),
        "seconds": round(time.time() - t, 1),
        "read": text[:80],
        "languages": ocr_languages(),
        "omp_thread_limit": os.environ.get("OMP_THREAD_LIMIT", ""),
        "ocr_space_backup": bool(os.environ.get("OCRSPACE_API_KEY")),
        "last_problem": OCR_PROBLEM["last"],
    }


# ---------------------------------------------------------------------------
# ROUTE 1. Paste text directly (SMS / WhatsApp / email body)
# ---------------------------------------------------------------------------
# Warning signs that mean "this message pretends to be an organisation"
ORG_LABELS = {
    "Bank / KYC / PAN impersonation", "Electricity disconnection threat",
    "Courier / customs / 'digital arrest' scam", "Fake government scheme, Aadhaar, PAN or gas update",
    "Reward points or cashback that 'expire today'",
}


EMAIL_IN_TEXT = re.compile(r"(?<![\w.+-])([A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
UPI_IN_TEXT = re.compile(r"(?<![\w.@-])([\w.\-]{2,64}@(?:ok[a-z]+|ybl|ibl|axl|paytm|upi|apl|yapl|ptyes|ptsbi|pthdfc|ptaxis|"
                         r"freecharge|jupiteraxis|axisbank|sbi|hdfcbank|icici|kotak|pnb|boi|barodampay|ikwik|fbl|idfcbank|"
                         r"indus|rbl|yesbank|airtel|jio|slc|timecosmos|waaxis|waicici|wahdfcbank|wasbi))\b", re.IGNORECASE)
PAY_WORDS = re.compile(r"\b(pay|send|transfer|deposit|fee|charges?|refund|return|wapas|bhejo|bhej|jama|ಪಾವತಿ|ಕಳುಹಿಸಿ|भेज|भुगतान|जमा)", re.IGNORECASE)


def add_entity_checks(result: dict, text: str = None) -> dict:
    """
    Everything else inside the text gets checked too:
    - email addresses: throwaway services, domains that don't exist, brand-new domains, and the
      domain goes through the same blocklists as links (Google, VirusTotal, scam lists)
    - UPI IDs: asking you to pay a UPI ID written in a message is how most fee scams collect money
    """
    text = text if text is not None else result.get("text_analyzed", "")
    from scanners.url_scanner import LINK_POOL, scan_url
    from scanners.email_domain import domain_signals
    from scanners.email_analyzer import FREE_MAIL
    import scanners.url_scanner as _us
    added = []

    upis = [u for u in UPI_IN_TEXT.findall(text)]
    emails = [e for e in EMAIL_IN_TEXT.findall(text) if e not in upis][:2]
    futures = []
    for e in emails:
        dom = e.split("@")[-1].lower()
        if dom not in FREE_MAIL:
            futures.append((e, dom, LINK_POOL.submit(scan_url, "https://" + dom)))
    for e in emails:
        dom = e.split("@")[-1].lower()
        sig = domain_signals(dom, False, dom in FREE_MAIL, offline=_us.OFFLINE)
        for f in sig["findings"][:1]:
            added.append((f"The email address {e} in this message: {f}", sig.get("points", {}).get(f, 20)))
    for e, dom, fut in futures:
        try:
            r = fut.result(timeout=80)
        except Exception:
            continue
        listed = [c for c in r.get("checks", []) if c["id"] in ("google", "feeds", "virustotal", "urlscan") and c["status"] == "fail"]
        if listed and r.get("findings"):
            added.append((f"The email address {e} in this message: {r['findings'][0]}", 40))

    if upis and PAY_WORDS.search(text):
        upi = upis[0]
        # with other scam signs this is how the money is collected; alone it can be a normal request
        added.append((f"Asks you to send money to a UPI ID written in the message ({upi}). Check who it really belongs to",
                      25 if result.get("patterns_detected") else 10))

    for finding, pts in added:
        if finding not in result["patterns_detected"]:
            result["patterns_detected"].append(finding)
            result.setdefault("score_parts", []).append({"label": finding, "points": pts})
            result["risk_score"] = min(100, result["risk_score"] + pts)
    if added:
        result["verdict"] = verdict_from_score(result["risk_score"])
    return result


def finalize_parts(result: dict) -> dict:
    """Turn the recorded points into the final bill that adds up to the score."""
    from scanners.ledger import Ledger
    result["score_parts"] = Ledger(result.get("score_parts")).result(result["risk_score"])
    return result


def add_sender_checks(result: dict, sender: str = "") -> dict:
    """Who sent it (TRAI sender rules) and foreign phone numbers inside the message."""
    from scanners.sender_check import sender_signals, find_sender_in_text, foreign_numbers_in_text
    text = result.get("text_analyzed", "")
    tr = result.get("translation") or {}
    english = tr.get("text", "") if tr.get("to") == "en" else ""
    sender = (sender or "").strip()[:60] or find_sender_in_text(text)
    claims_org = any(p in ORG_LABELS for p in result.get("patterns_detected", []))
    sig = sender_signals(sender, text + "\n" + english, claims_org) if sender else {"findings": [], "score": 0, "safe": []}
    added = list(sig["findings"])
    score = sig["score"]
    if not any(f.startswith("Sent from a foreign phone number") for f in added):
        countries = foreign_numbers_in_text(text)
        if countries:
            added.append(f"Asks you to contact a foreign phone number ({', '.join(countries[:2])})")
            score += 20
    for f in added:
        if f not in result["patterns_detected"]:
            result["patterns_detected"].append(f)
    if added and score:
        result.setdefault("score_parts", []).append({"label": added[0], "points": sig["score"] or score})
        if len(added) > 1 and sig["score"]:
            result["score_parts"].append({"label": added[-1], "points": score - sig["score"]})
    if score:
        result["risk_score"] = max(0, min(100, result["risk_score"] + score))
        result["verdict"] = verdict_from_score(result["risk_score"])
    if not result["patterns_detected"]:  # scammers can register senders too, so only as reassurance
        result.setdefault("safe_signals", []).extend(sig["safe"])
    if sender:
        result["sender"] = sender
    return result


def start_background_work(text: str, ui_lang: str, from_screenshot: bool = False):
    """Ask Gemini once for everything it's needed for, and start the link checks, in parallel."""
    from scanners.gemini_combo import prefetch
    from scanners.url_scanner import _POOL
    return _POOL.submit(prefetch, text, ui_lang), start_link_checks(text, from_screenshot)


def _wait_for(future, timeout: float = 60):
    try:
        future.result(timeout=timeout)
    except Exception:
        pass


@message_scanner_bp.route("/api/scan-message", methods=["POST"])
def scan_message_route():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()[:10000]

    if not text:
        return jsonify({"error": "Please paste the message you want to check."}), 400

    ui = request_language()
    gemini_f, links = start_background_work(text, ui)
    result = analyze_text(text)
    _wait_for(gemini_f)
    result = add_translation(result, ui)
    result = add_sender_checks(result, str(data.get("sender") or "")[:300])
    result = add_entity_checks(result)
    from scanners.ai_review import apply_review
    result = apply_review(result, text)
    result = check_links_in_result(result, started=links)
    result = finalize_parts(result)

    from scanners.risk_engine import log_scan
    log_scan("message", result)

    return jsonify(result)


# ---------------------------------------------------------------------------
# ROUTE 2. Upload a screenshot (OCR extracts text, then same analysis)
# ---------------------------------------------------------------------------
@message_scanner_bp.route("/api/ocr-check", methods=["GET"])
def ocr_check_route():
    """Open this (with ?key=<STATUS_KEY>) to see if screenshot reading works on the server and how fast."""
    from scanners.security import has_status_key
    if not has_status_key():
        return jsonify({"error": "Not found"}), 404
    if not ocr_status():
        return jsonify({"ok": False, "error": "Tesseract is not installed"})
    return jsonify(ocr_self_check())


@message_scanner_bp.route("/api/scan-screenshot", methods=["POST"])
def scan_screenshot_route():
    if not ocr_status():
        return jsonify({
            "error": "Screenshot reading isn't available right now. You can paste the message text instead."
        }), 503

    if "image" not in request.files:
        return jsonify({"error": "Please choose a screenshot to upload."}), 400

    image_bytes = request.files["image"].read()
    if not image_bytes:
        return jsonify({"error": "The uploaded image was empty."}), 400

    try:
        extracted_text = extract_text_from_image(image_bytes)
    except RuntimeError:
        return jsonify({"error": "We couldn't read this picture right now. Please try again in a moment, or paste the message text instead."}), 400
    except Exception:
        return jsonify({"error": "We couldn't open this image. Please upload a PNG or JPG screenshot."}), 400

    if len(extracted_text) < 5:
        return jsonify({
            "error": "We couldn't find readable text in this image. Try a clearer, uncropped screenshot, "
                     "or paste the message text instead."
        }), 400

    extracted_text = fix_ocr_links(extracted_text)
    ui = request_language()
    gemini_f, links = start_background_work(extracted_text, ui, from_screenshot=True)
    result = analyze_text(extracted_text)
    _wait_for(gemini_f)
    result = add_translation(result, ui)
    result = add_sender_checks(result, request.form.get("sender", "")[:300])
    result = add_entity_checks(result)
    from scanners.ai_review import apply_review
    result = apply_review(result, extracted_text)
    result = check_links_in_result(result, from_screenshot=True, started=links)
    result = finalize_parts(result)

    from scanners.risk_engine import log_scan
    log_scan("screenshot", result)

    return jsonify(result)
