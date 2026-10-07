"""Message rules: well-known Indian scam types must be flagged, everyday genuine messages must not.
Run: python tests/test_message_rules.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scanners.url_scanner as us  # noqa: E402
us.OFFLINE = True
from scanners.message_scanner import analyze_text, add_entity_checks  # noqa: E402

SCAMS = [
    "Rs 2,450.00 sent to your UPI by mistake. Kindly return it immediately using this link upi://pay?pa=return30@ybl",
    "Your water connection will be disconnected tonight due to unpaid bill. Call officer 9727318510 now",
    "Your gas connection will be disconnected tonight due to unpaid bill. Call officer 7085432781 now",
    "Dear customer your PAYTMKYC has been expired, It will be bl0cked within 24 hour, please contact customer care 7679046492",
    "Please call our customer service on 7908807538 as you have W0N a guaranteed cash prize of Rs.6,00,000. FL1PKART TEAM",
    "Hi, I am calling from Airtel. Your 5G SIM upgrade is pending. Send SIM 20-digit number to 9123123123 by SMS.",
    "Dear student your VTU exam hall ticket is blocked due to pending fee. Pay Rs 1500 at vtu-feepay.in to download",
    "India Post: Your package could not be delivered due to incomplete address. Update within 12 hours: https://indiapost-redeliver.top/in",
    "As a valued customer, you are awarded with a Rs.2,00,000 Bonus Prize, call 6290123456",
    "Dear Customer, your SBI YONO account will be blocked today. Update your PAN immediately: http://sbi-kyc-update.in/verify",
    "Congratulations!!! You are Due for a COVID-19 Grant, To Redeem, Contact us Via Email: covid19grant@cokegrant.com",
    "You've won tkts to the CUP FINAL or Rs 80,000 CASH, to collect CALL 9058099802",
    "ನಿಮ್ಮ ಖಾತೆಗೆ ತಪ್ಪಾಗಿ ರೂ 5000 ಕಳುಹಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ತಕ್ಷಣ ಹಿಂದಿರುಗಿಸಿ upi://pay?pa=refund@ybl",
    "आपके खाते में गलती से 3000 रुपये आ गए हैं, कृपया तुरंत वापस भेजें",
    "आपका सिम 5G में अपग्रेड होगा, सिम का 20 अंक नंबर SMS करें 9123456789",
]
GENUINE = [l.strip() for l in """You have been selected for the interview on Monday at 10 am
Congratulations on your promotion! You have won our hearts
Your KYC is complete. Thank you for banking with us
Dear customer, complete your KYC at your nearest branch to continue services
If this was not done by you, call 1800 425 3800 immediately. -SBI
Rs 499 debited from your account for Netflix. Not you? Call 18002586161 -HDFC Bank
Your OTP for login is 482913. Do not share it with anyone. -ICICI Bank
Your electricity bill of Rs 1,240 is due on 15 Oct. Pay via BESCOM app or bescom.co.in
Your LPG cylinder booking is confirmed. Delivery expected in 2 days. -Indane
Hi, I won the match today! Coming home late
Your parcel has been delivered. Rate your experience in the Amazon app.
Payment of Rs 2,000 received from Ramesh via UPI. Ref 334455667788
Rs 5000 credited to your account. Avl bal Rs 12,450. -Canara Bank
Dear student, your hall ticket for the semester exam is available on the VTU portal.
Your Airtel bill of Rs 499 is generated. Pay before 20 Oct to avoid late fee. airtel.in/pay
Your water bill is due. Pay at the BWSSB office or online at bwssb.karnataka.gov.in
Your Jio SIM will be upgraded to 5G automatically, no action needed.
Mom, I lost my phone, using a friend's phone. Will call you tonight.
The meeting is on hold, we will pay the vendor tomorrow
Your Flipkart order of Samsung phone will be delivered today by 8 PM
Your Swiggy order is on the way!
Reminder: your car insurance expires on 30 Oct. Renew at policybazaar.com""".splitlines() if l.strip()] + [
    "Hi, I won the match today! Coming home late",
    "Its like that hotel dusk game i think. You solve puzzles in a area thing",
    "Lol you won't feel bad when I use her money to take you out to a steak dinner",
    "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ರೂ 5000 ಜಮಾ ಆಗಿದೆ. ಉಳಿಕೆ ರೂ 12000",
    "आपका पार्सल आज डिलीवर हो जाएगा",
]


def check(text):
    return add_entity_checks(analyze_text(text), text)["verdict"]


def test_known_scam_types_are_flagged():
    missed = [t for t in SCAMS if check(t) not in ("SCAM_LIKELY", "SUSPICIOUS")]
    assert not missed, missed


def test_everyday_genuine_messages_are_not_flagged():
    wrong = [t for t in GENUINE if check(t) != "LIKELY_SAFE"]
    assert not wrong, wrong


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_")):
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}")
    print(f"\n{2 - failed}/2 tests passed")
    sys.exit(1 if failed else 0)
