"""
Samples for the owner's QR and phone-number test (/api/selftest/qr, /api/selftest/numbers).
QR pictures live in data/selftest/qr_*.png (made from the texts below). Numbers and IDs are made up.
"""
SAFE, NOT_SAFE, DANGEROUS = "SAFE", "NOT_SAFE", "DANGEROUS"

QR_CODES = [
    # (picture name, what the QR contains, expected)
    ("qr_upi_shop.png", "upi://pay?pa=meghanafoods@okaxis&pn=Meghana%20Foods&mc=5812", SAFE),
    ("qr_upi_refund.png", "upi://pay?pa=refund.helpdesk@ybl&pn=Amazon%20Refund%20Desk&am=4999&tn=Refund%20received", DANGEROUS),
    ("qr_upi_lottery.png", "upi://pay?pa=9876543210@ybl&pn=KBC%20Lottery&am=12500&tn=Lottery%20prize%20claim%20fee", DANGEROUS),
    ("qr_upi_army.png", "upi://pay?pa=armycanteen.sales@paytm&pn=Army%20Officer&am=25000&tn=Receive%20advance%20payment", DANGEROUS),
    ("qr_url_irctc.png", "https://www.irctc.co.in/nget/train-search", SAFE),
    ("qr_url_scam.png", "http://sbi-kyc-update-2026.xyz/login", DANGEROUS),
    ("qr_text_scam.png", "Congratulations! You won Rs 25 lakh in KBC. Call 9876543210 and pay processing fee 5000 to claim.", NOT_SAFE),
    ("qr_wifi.png", "WIFI:T:WPA;S:CafeGuest;P:coffee123;;", SAFE),
]

NUMBERS = [
    # (number or UPI ID, who they said they were, what they asked for, expected)
    ("1930", "", "", SAFE),
    ("+92 300 1234567", "unknown", "nothing", NOT_SAFE),
    ("9876543210", "bank", "otp", DANGEROUS),
    ("1600 123 456", "bank", "nothing", SAFE),
    ("1800 1234 567", "", "", SAFE),
    ("+225 07 12 34 56", "unknown", "nothing", NOT_SAFE),
    ("9845012345", "official", "video", DANGEROUS),
    ("9845012345", "delivery", "pay_to_get", DANGEROUS),
    ("refund.helpdesk@ybl", "", "", NOT_SAFE),
    ("sbi.kyc.update@paytm", "bank", "", DANGEROUS),
    ("meghanafoods@okaxis", "", "", SAFE),
    ("ravi.kumar@oksbi", "family", "nothing", SAFE),
    ("9876543210@ybl", "family", "pay_to_get", DANGEROUS),
    ("shop123@xyzpaybank", "", "", NOT_SAFE),
]
