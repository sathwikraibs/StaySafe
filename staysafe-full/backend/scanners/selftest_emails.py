"""Sample emails for the owner's email test (/api/selftest/emails). Addresses are made up."""
SAFE, NOT_SAFE, DANGEROUS = "SAFE", "NOT_SAFE", "DANGEROUS"

_SPOOF_RAW = """Authentication-Results: mx.google.com; spf=fail smtp.mailfrom=paypal.com; dkim=fail header.d=paypal.com; dmarc=fail header.from=paypal.com
From: PayPal <service@paypal.com>
Reply-To: paypal.resolution.center@gmail.com
Subject: Your account has been limited
Content-Type: text/plain

Dear customer, we noticed unusual activity. Your account is limited. Verify your identity within 24 hours at http://paypal-resolution-center.top/verify or your account will be closed.
"""
_GOOGLE_RAW = """Authentication-Results: mx.google.com; spf=pass smtp.mailfrom=accounts.google.com; dkim=pass header.d=accounts.google.com; dmarc=pass header.from=accounts.google.com
From: Google <no-reply@accounts.google.com>
Subject: Security alert
Content-Type: text/plain

A new sign-in on Android. If this was you, you don't need to do anything. If not, we'll help you secure your account. Check activity at https://myaccount.google.com/notifications
"""
_HTML_RAW = """From: DHL Express <noreply@dhl-parcel-notice.com>
Subject: Your parcel is on hold
Content-Type: text/html

<html><body><p>Your parcel could not be delivered due to unpaid customs duty of Rs 49.</p>
<a href="http://dhl-redelivery-pay.xyz/pay">Click here to pay and reschedule</a></body></html>
"""

EMAILS = [
    # (description, request body as the website sends it, expected)
    ("Fake SBI alert from a lookalike domain", {"sender_name": "SBI Alerts", "sender_email": "alerts@sbi-secure-mail.com",
     "subject": "Your account will be suspended today", "body": "Dear customer, your YONO account will be suspended. Update your KYC now at http://sbi-kyc-verify.top/login"}, DANGEROUS),
    ("Bank name on a Gmail address", {"sender_name": "HDFC Bank", "sender_email": "hdfcbank.helpdesk@gmail.com",
     "subject": "Verify your account", "body": "Your net banking is blocked. Reply with your customer ID and OTP to unblock."}, NOT_SAFE),
    ("Fake income tax refund", {"sender_name": "Income Tax Department", "sender_email": "refund@incometax-gov.in.net",
     "subject": "Refund of Rs 15,490 approved", "body": "You are eligible for an income tax refund. Submit your bank account details to receive it."}, DANGEROUS),
    ("Fake job offer with a fee", {"sender_name": "HR Infosys", "sender_email": "hr.infosys.careers@outlook.com",
     "subject": "Offer letter", "body": "Congratulations, you are selected. Pay Rs 4,500 registration fee for your laptop and training to receive the offer letter."}, NOT_SAFE),
    ("Real brand name, replies go to Gmail", {"sender_name": "Amazon", "sender_email": "no-reply@amazon.in", "reply_to": "amazon.support.desk@gmail.com",
     "subject": "Refund pending", "body": "Your refund of Rs 2,999 is pending. Reply with your bank account number and IFSC to receive it."}, NOT_SAFE),
    ("Spoofed PayPal email (full source)", {"raw_email": _SPOOF_RAW}, DANGEROUS),
    ("Fake DHL email with a hidden 'Click here' link (full source)", {"raw_email": _HTML_RAW}, NOT_SAFE),
    ("Real Amazon shipping email", {"sender_name": "Amazon.in", "sender_email": "shipment-tracking@amazon.in",
     "subject": "Your order has shipped", "body": "Your package will arrive on Friday. Track it at https://www.amazon.in/gp/your-account/order-history"}, SAFE),
    ("Real IRCTC booking", {"sender_name": "IRCTC", "sender_email": "ticketadmin@irctc.co.in",
     "subject": "Booking confirmation PNR 4521367890", "body": "Your ticket is booked. Train 12658, Coach S5, Berth 32. Happy journey."}, SAFE),
    ("Friend on Gmail", {"sender_name": "Ravi Kumar", "sender_email": "ravi.kumar1998@gmail.com",
     "subject": "Notes", "body": "Hi, sending the notes for tomorrow's exam. See you at college."}, SAFE),
    ("Real Google security alert (full source)", {"raw_email": _GOOGLE_RAW}, SAFE),
]
