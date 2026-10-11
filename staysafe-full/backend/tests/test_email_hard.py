"""42 real and scam emails in every format people paste (offline: no DNS, no blocklists, no AI)."""
import sys, os, time, base64, quopri, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scanners.url_scanner as us
us.OFFLINE = True
from scanners.email_analyzer import scan_email

AUTH_PASS = "Authentication-Results: mx.google.com;\n       dkim=pass header.i=@{d};\n       spf=pass smtp.mailfrom={d};\n       dmarc=pass (p=REJECT) header.from={d}\n"
AUTH_FAIL = "Authentication-Results: mx.google.com;\n       dkim=fail header.i=@{d};\n       spf=fail smtp.mailfrom={d};\n       dmarc=fail (p=NONE) header.from={d}\n"

def src(frm, subject, body, auth=None, extra="", ctype="text/plain; charset=UTF-8", cte=None, crlf=False):
    d = frm.split("@")[-1].strip(">").strip()
    h = "Delivered-To: me@gmail.com\nReceived: by 2002:a05:6400:1;\n"
    if auth == "pass": h += AUTH_PASS.format(d=d)
    if auth == "fail": h += AUTH_FAIL.format(d=d)
    h += f"From: {frm}\nTo: me@gmail.com\nSubject: {subject}\nDate: Sun, 11 Oct 2026 10:00:00 +0530\n{extra}MIME-Version: 1.0\nContent-Type: {ctype}\n"
    if cte: h += f"Content-Transfer-Encoding: {cte}\n"
    out = h + "\n" + body
    return out.replace("\n", "\r\n") if crlf else out

def b64(s): return base64.encodebytes(s.encode()).decode()
def qp(s): return quopri.encodestring(s.encode()).decode()

SAFE, CAUTION, DANGER = {"SAFE"}, {"CAUTION"}, {"DANGEROUS"}
OKISH = {"SAFE", "CAUTION"}
RISKY = {"CAUTION", "DANGEROUS"}

cases = [
 # ---------- real emails ----------
 ("HDFC debit alert (real, DMARC pass)", {"raw_email": src("HDFC Bank InstaAlerts <alerts@hdfcbank.net>", "You have done a UPI txn",
   "Dear Customer,\nRs.500.00 has been debited from account **1234 to VPA swiggy@icici on 11-10-26. Your UPI transaction reference number is 528412345678.\nIf you did not authorize this transaction, please report it immediately by calling 18002586161.\nWarm Regards,\nHDFC Bank", "pass")}, SAFE),
 ("Google security alert (real)", {"raw_email": src("Google <no-reply@accounts.google.com>", "Security alert",
   "A new sign-in on Android\nme@gmail.com\nWe noticed a new sign-in to your Google Account on a Android device. If this was you, you don't need to do anything. If not, we'll help you secure your account.\nCheck activity\nhttps://accounts.google.com/AccountChooser?Email=me@gmail.com&continue=https://myaccount.google.com/alert/nt/1", "pass")}, SAFE),
 ("Amazon shipped (real)", {"raw_email": src("Amazon.in <shipment-tracking@amazon.in>", "Your Amazon.in order #408-1234567-1234567 has shipped",
   "Hello Rahul,\nYour package has been shipped! Arriving Tuesday.\nTrack your package: https://www.amazon.in/gp/your-account/order-details?orderID=408-1234567-1234567", "pass")}, SAFE),
 ("Friend from Gmail (form)", {"sender_email": "Priya <priya.k1998@gmail.com>", "subject": "Saturday plan",
   "body": "Hey! Are we still meeting at 5 near the metro station? Let me know."}, SAFE),
 ("Swiggy newsletter (real)", {"raw_email": src("Swiggy <noreply@swiggy.in>", "Flat 50% off this weekend",
   "Craving something? Get flat 50% off on your next 3 orders. Order now: https://www.swiggy.com/offers\nUnsubscribe: https://www.swiggy.com/unsubscribe", "pass")}, OKISH),
 ("Zomato OTP (real)", {"raw_email": src("Zomato <noreply@zomato.com>", "Your Zomato login OTP",
   "Your OTP for logging in to Zomato is 482913. It is valid for 10 minutes. Do not share this OTP with anyone.", "pass")}, SAFE),
 ("Forwarded real email (no auth headers)", {"raw_email": "From: Ravi <ravi@presidencyuniversity.in>\nTo: me@gmail.com\nSubject: Fwd: Lab schedule\n\nLab sessions move to Thursday 2 pm this week. Please bring your record books."}, SAFE),
 ("Bank form genuine domain", {"sender_email": "SBI <donotreply.sbiatm@alerts.sbi.co.in>", "subject": "Transaction alert",
   "body": "Your A/c XX1234 is debited for Rs.2000.00 on 11Oct26 by ATM withdrawal. If not done by you, call 18001234."}, SAFE),
 ("CRLF Gmail source (real)", {"raw_email": src("Google <no-reply@accounts.google.com>", "Security alert",
   "You allowed TrustLight access to some of your Google Account data.\nhttps://myaccount.google.com/permissions", "pass", crlf=True)}, SAFE),
 ("Real Google, base64 body", {"raw_email": src("Google <no-reply@accounts.google.com>", "Security alert",
   b64("A new sign-in on Windows. If this was you, you don't need to do anything."), "pass", cte="base64")}, SAFE),

 # ---------- scams ----------
 ("SBI KYC from Gmail (form)", {"sender_email": "SBI Customer Care <sbi.kyc.update2026@gmail.com>", "subject": "URGENT: KYC expired",
   "body": "Dear customer your SBI YONO account will be blocked today. Update your PAN and KYC immediately at http://sbi-yono-kyc.in/update or your account will be suspended."}, DANGER),
 ("HDFC spoof domain, auth fail", {"raw_email": src("HDFC Bank <alerts@hdfc-secure-netbank.com>", "Account suspended",
   "Your netbanking is suspended due to unusual activity. Verify within 24 hours: http://hdfc-secure-netbank.com/login", "fail")}, DANGER),
 ("Job offer fee (Infosys on Outlook)", {"sender_email": "Infosys HR <careers.infosys.hr@outlook.com>", "subject": "Offer letter - Infosys",
   "body": "Congratulations! You are selected for Software Engineer at Infosys with 8 LPA. To confirm your offer letter pay the refundable registration fee of Rs 2500 to UPI infosys.hr@okaxis within 24 hours."}, DANGER),
 ("KBC lottery (Yahoo)", {"sender_email": "KBC Lottery Department <kbc.lottery2026@yahoo.com>", "subject": "You won 25 lakh",
   "body": "Congratulations your mobile number has won Rs 25,00,000 in KBC lucky draw. To claim the prize pay processing fee of Rs 12,500 and send your Aadhaar and bank details."}, DANGER),
 ("Income tax refund phishing", {"raw_email": src("Income Tax Department <refund@incometax-gov-refund.in.net>", "Refund approved",
   "You are eligible for an income tax refund of Rs 15,490. Submit your bank details to receive it: http://incometax-gov-refund.in.net/claim", "fail")}, DANGER),
 ("Digital arrest (cyber cell Gmail)", {"sender_email": "Cyber Crime Branch Mumbai <cybercell.mumbai.police@gmail.com>", "subject": "Notice: arrest warrant",
   "body": "A parcel in your name contains illegal drugs. A case is registered and an arrest warrant is issued. Join the video call immediately and do not tell anyone, or you will be arrested."}, DANGER),
 ("Netflix HTML-only, hidden link", {"raw_email": src("Netflix <billing@netflix-payments-help.com>", "Payment failed",
   "<html><body><p>Your payment was declined. Your membership will be cancelled today.</p><a href='http://bit.ly/nflx-upd8'>Update payment</a></body></html>", "fail", ctype="text/html; charset=UTF-8")}, DANGER),
 ("Scam in base64 body", {"raw_email": src("SBI Alerts <sbi.alerts.kyc@gmail.com>", "KYC",
   b64("Your SBI account will be blocked today. Click http://sbi-kyc-verify.xyz/update and enter your OTP to continue."), None, cte="base64")}, DANGER),
 ("Scam in quoted-printable body", {"raw_email": src("Paytm KYC <paytm.kyc.team@gmail.com>", "KYC pending",
   qp("Dear user, your Paytm wallet KYC is pending. Your wallet will be blocked within 24 hours. Complete KYC now: http://paytm-kyc-update.top/verify  Share the OTP you receive with our executive."), None, cte="quoted-printable")}, DANGER),
 ("Multipart scam (text+html)", {"raw_email": src("Amazon Rewards <rewards@amazon-gift-winner.shop>", "You won an iPhone",
   "--b1\nContent-Type: text/plain; charset=UTF-8\n\nCongratulations! You won an iPhone 15. Pay delivery charge of Rs 99 to claim.\n--b1\nContent-Type: text/html; charset=UTF-8\n\n<p>Congratulations! <a href='http://amazon-gift-winner.shop/claim'>Claim now</a></p>\n--b1--\n",
   "fail", ctype='multipart/alternative; boundary="b1"')}, DANGER),
 ("Hindi scam body", {"sender_email": "SBI Bank <sbi.helpdesk.kyc@gmail.com>", "subject": "खाता बंद",
   "body": "प्रिय ग्राहक, आपका बैंक खाता आज बंद हो जाएगा। तुरंत KYC अपडेट करें: http://sbi-kyc-hindi.in/update और OTP शेयर करें।"}, DANGER),
 ("Kannada scam body", {"sender_email": "Bescom Electricity <bescom.bill.update@gmail.com>", "subject": "ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಡಿತ",
   "body": "ಆತ್ಮೀಯ ಗ್ರಾಹಕರೇ, ನಿಮ್ಮ ಬಿಲ್ ಬಾಕಿ ಇರುವುದರಿಂದ ಇಂದು ರಾತ್ರಿ 9:30ಕ್ಕೆ ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಡಿತಗೊಳ್ಳುತ್ತದೆ. ತಕ್ಷಣ ಈ ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ 9876543210"}, DANGER),
 ("Name shows other address", {"raw_email": src('"support@sbi.co.in" <random.user8812@mail.ru>', "Account locked",
   "Your account is locked. Reply with your card number and CVV to unlock.", None)}, DANGER),
 ("Encoded From name (SBI on Gmail)", {"raw_email": src("=?UTF-8?B?" + base64.b64encode("SBI Customer Care".encode()).decode() + "?= <sbi.care.verify@gmail.com>",
   "=?UTF-8?B?" + base64.b64encode("KYC अपडेट".encode()).decode() + "?=",
   "Update your KYC now or your account will be blocked: http://sbi-care-kyc.in/kyc", None)}, DANGER),
 ("Reply-To elsewhere", {"raw_email": src("Accounts Team <accounts@tatasteel-vendors.co>", "Invoice payment details changed",
   "Please note our bank account has changed. Pay the pending invoice of Rs 4,80,000 to the new account below urgently today.", None,
   extra="Reply-To: tatasteel.accounts.dept@gmail.com\n")}, DANGER),
 ("Throwaway sender", {"sender_email": "Prize Team <winner@mailinator.com>", "subject": "Claim",
   "body": "You have won a gift card. Send your address and phone number to claim it today."}, RISKY),
 ("Hidden-dot sender typed", {"sender_email": "PhonePe Support < phonepe.refund [at] gmail [dot] com >", "subject": "Refund",
   "body": "Your refund of Rs 4,999 is pending. Scan the QR code and enter your UPI PIN to receive the refund."}, DANGER),
 ("Very long email (performance)", {"raw_email": src("News <news@example-news.in>", "Digest",
   ("Today's headlines and updates from around the city. " * 4000), None)}, OKISH),
 ("Spaces-only attack body (performance)", {"sender_email": "x@example.org", "subject": "a", "body": "a" + " " * 49000 + "b"}, OKISH),
 ("Gmail personal but says bank in body only", {"sender_email": "Ramesh Kumar <ramesh.k.blr@gmail.com>", "subject": "Money",
   "body": "Hi, I sent the money to your SBI account yesterday, please check and confirm. Thanks."}, OKISH),
]

cases += [
 ("IRCTC booking (real)", {"raw_email": src("IRCTC <ticketadmin@irctc.co.in>", "Booking Confirmation on IRCTC, Train: 12608",
   "Dear Customer, your ticket is booked. PNR: 4512345678. Train 12608 Lalbagh Express, Bangalore to Chennai, 14-Oct-2026. Have a happy journey.", "pass")}, SAFE),
 ("LinkedIn job alert (real)", {"raw_email": src("LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>", "New jobs for Software Engineer in Bengaluru",
   "30+ new jobs match your preferences. Software Engineer at Razorpay, Bengaluru. View job: https://www.linkedin.com/comm/jobs/view/3812345678", "pass")}, OKISH),
 ("GitHub password reset (real)", {"raw_email": src("GitHub <noreply@github.com>", "[GitHub] Please reset your password",
   "We heard that you lost your GitHub password. Sorry about that! But don't worry! You can use the following link to reset your password: https://github.com/password_reset/abc123 If you don't use this link within 3 hours, it will expire.", "pass")}, OKISH),
 ("College exam notice (real, form)", {"sender_email": "Exam Cell <examcell@presidencyuniversity.in>", "subject": "Mid-term schedule",
   "body": "Dear students, the mid-term examinations will begin on 20 October. The detailed timetable is attached. All the best."}, SAFE),
 ("Flipkart OTP (real)", {"raw_email": src("Flipkart <noreply@nct.flipkart.com>", "Your Flipkart OTP",
   "123456 is your OTP to log in to Flipkart. Do not share it with anyone. Flipkart will never call you asking for the OTP.", "pass")}, SAFE),
 ("Microsoft lookalike rnicrosoft", {"raw_email": src("Microsoft Account Team <security@rnicrosoft-account.com>", "Unusual sign-in activity",
   "We detected something unusual about a recent sign-in to your Microsoft account. Please verify your account within 24 hours or it will be suspended: http://rnicrosoft-account.com/verify", "fail")}, DANGER),
 ("Amazon on lookalike domain (form)", {"sender_email": "Amazon <order-update@amazon-support-desk.in>", "subject": "Order cancelled",
   "body": "Your order has been cancelled due to payment failure. To get a refund, verify your card details here: http://amazon-support-desk.in/refund"}, DANGER),
 ("Outlook-style pasted email", {"raw_email": "From: HR Department <hr.recruitment.tcs@gmail.com>\nSent: Monday, October 12, 2026 10:15 AM\nTo: me@gmail.com\nSubject: TCS offer letter\n\nYou are selected for TCS. Pay Rs 3,500 security deposit for your laptop and joining kit before tomorrow."}, DANGER),
 ("Romanized Hindi scam (form)", {"sender_email": "Bank Helpline <bank.helpline.kyc@gmail.com>", "subject": "Zaroori",
   "body": "Aapka bank account aaj band ho jayega. Turant KYC update karo is link par http://kyc-update-bank.in aur OTP batao."}, DANGER),
 ("Image-only email with link", {"raw_email": src("Offers <deals@mega-sale-offer.top>", "Big sale",
   "<html><body><a href='http://mega-sale-offer.top/win'><img src='http://mega-sale-offer.top/banner.png'></a></body></html>", None, ctype="text/html")}, RISKY),
 ("HTML entities text", {"raw_email": src("Support <help@account-verify-center.xyz>", "Verify",
   "<p>Your account will be blocked&nbsp;today. Verify&#32;now &amp; enter your OTP: <a href='http://account-verify-center.xyz'>here</a></p>", "fail", ctype="text/html")}, DANGER),
 ("Real bank e-statement (form, no link)", {"sender_email": "ICICI Bank <estatement@icicibank.com>", "subject": "Your account statement for September 2026",
   "body": "Dear Customer, please find attached your account statement for September 2026. The attachment is password protected. ICICI Bank will never ask for your password or OTP."}, SAFE),
]



def _run(cases):
    bad = []
    for name, data, want in cases:
        t = time.time()
        r = scan_email(data)
        assert time.time() - t < 20, f"{name} too slow"
        if r.get("verdict") not in want:
            bad.append(f"{name}: {r.get('verdict') or r.get('error')} (want {sorted(want)})")
    assert not bad, "; ".join(bad)


def test_real_emails_are_not_flagged():
    _run([c for c in cases if c[2] in (SAFE, OKISH)])


def test_scam_emails_are_caught():
    _run([c for c in cases if c[2] in (DANGER, RISKY)])


def test_kannada_and_hindi_text_is_read_not_garbled():
    from email import message_from_string
    from scanners.email_analyzer import extract_body
    m = message_from_string("From: a@b.com\nSubject: x\nContent-Type: text/plain; charset=utf-8\n\nನಿಮ್ಮ ಬಿಲ್ आपका")
    assert extract_body(m).strip() == "ನಿಮ್ಮ ಬಿಲ್ आपका"


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    ok = 0
    for t in tests:
        try:
            t(); ok += 1; print("PASS ", t.__name__)
        except Exception as e:
            print("FAIL ", t.__name__, repr(e)[:600])
    print(f"\n{ok}/{len(tests)} tests passed")
