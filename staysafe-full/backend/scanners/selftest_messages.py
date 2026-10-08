"""
Sample messages for the owner's message test (/api/selftest/messages). Written in the style of
real scam and real everyday messages people in India receive, in English, Hindi, Kannada, Tulu
and the same languages typed in English letters. Phone numbers, links and names are made up.
"""

SCAM, SAFE = "NOT_SAFE", "SAFE"

MESSAGES = {
    "1": ("English scams (current Indian types)", [
        ("Dear customer, your SBI YONO account will be blocked today. Update your PAN immediately: http://sbi-yono-kyc.in/update", SCAM),
        ("FedEx: A parcel in your name with 5 passports and MDMA drugs was seized at Mumbai customs. Press 1 to speak to the officer or call 9123456780 now.", SCAM),
        ("This is Cyber Crime Branch Mumbai. A case is registered on your Aadhaar for money laundering. Stay on video call, do not tell anyone. You are under digital arrest.", SCAM),
        ("Dear Consumer your electricity power will be disconnected tonight at 9.30 pm because your previous month bill was not updated. Please immediately contact our electricity officer 8250367192", SCAM),
        ("Congrats! You have been selected for part time job. Like YouTube videos and earn Rs 5000 daily. Contact on Telegram @hr_priya_jobs", SCAM),
        ("Your HDFC credit card reward points worth Rs 8,950 will expire today. Redeem now: https://hdfc-rewardz.top/redeem", SCAM),
        ("Hi, I sent Rs 5000 to your GPay by mistake while paying my brother. Please return it, I am in hospital. Sending you the request now, just enter your PIN to approve.", SCAM),
        ("Income Tax Department: You are eligible for a refund of Rs 15,490. Please verify your bank account details at incometax-refund.co.in to receive it.", SCAM),
        ("Your Jio number will be blocked in 2 hours by TRAI due to illegal activity. Press 9 to talk to customer care.", SCAM),
        ("Join our VIP stock market WhatsApp group. Guaranteed 30% monthly return. Invest through our app, minimum Rs 10,000. SEBI registered advisor.", SCAM),
        ("Dear user, your KYC is pending. Download the RTO Challan app to pay your traffic fine: rto_challan.apk", SCAM),
        ("Hello sir, I am army officer posted in Bangalore. I want to rent your house. I will send advance through UPI, please scan this QR to receive money.", SCAM),
    ]),
    "2": ("Hindi and Hinglish scams", [
        ("प्रिय ग्राहक, आपका बैंक खाता आज बंद कर दिया जाएगा। तुरंत अपना KYC अपडेट करें: http://sbi-kyc-update.in", SCAM),
        ("आपके नाम पर 25 लाख की लॉटरी लगी है! KBC से। पैसे पाने के लिए 12,500 रुपये प्रोसेसिंग फीस भेजें।", SCAM),
        ("बिजली विभाग: आपका बिजली कनेक्शन आज रात 9:30 बजे काट दिया जाएगा। तुरंत इस नंबर पर संपर्क करें 9876501234", SCAM),
        ("मैं CBI से बोल रहा हूँ। आपके आधार कार्ड से मनी लॉन्ड्रिंग हुई है। किसी को मत बताना, वीडियो कॉल पर रहिए, आप डिजिटल अरेस्ट में हैं।", SCAM),
        ("Aapka bank account block ho jayega, turant KYC update karein. Link par click karein: bit.ly/kyc-sbi", SCAM),
        ("Ghar baithe kamaye 3000 roz. Sirf YouTube video like karne hain. Telegram par contact karein", SCAM),
        ("Galti se aapke account me 2000 rs bhej diya, please wapas kar do, maine request bheji hai, PIN daal ke approve kar do", SCAM),
        ("Papa main police station mein hoon, accident ho gaya hai. Is number pe turant 50,000 bhejo, kisi ko mat batana", SCAM),
    ]),
    "3": ("Kannada and Kanglish scams", [
        ("ಆತ್ಮೀಯ ಗ್ರಾಹಕರೇ, ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಂದು ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ. ತಕ್ಷಣ KYC ಅಪ್‌ಡೇಟ್ ಮಾಡಿ: http://kyc-update-sbi.in", SCAM),
        ("ನಿಮ್ಮ ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಇಂದು ರಾತ್ರಿ ಕಡಿತಗೊಳ್ಳುತ್ತದೆ. ಹಿಂದಿನ ತಿಂಗಳ ಬಿಲ್ ಅಪ್‌ಡೇಟ್ ಆಗಿಲ್ಲ. ತಕ್ಷಣ 9845012345 ಗೆ ಕರೆ ಮಾಡಿ", SCAM),
        ("ಅಭಿನಂದನೆಗಳು! ನೀವು 25 ಲಕ್ಷ ಲಾಟರಿ ಗೆದ್ದಿದ್ದೀರಿ. ಹಣ ಪಡೆಯಲು 10,000 ರೂ ಶುಲ್ಕ ಕಳುಹಿಸಿ", SCAM),
        ("ನಿಮ್ಮ ಮೊಬೈಲ್‌ಗೆ ಬಂದ OTP ಹೇಳಿ, ನಿಮ್ಮ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ ಬಹುಮಾನ ಅಂಕಗಳನ್ನು ನಗದು ಮಾಡುತ್ತೇವೆ", SCAM),
        ("Nimma account block aagide, KYC update maadi illandre account close aagutte. Ee link click maadi: http://bit.ly/kyc-update1", SCAM),
        ("Ninna number inda illegal activity aagide anta police case register aagide. Video call alli iri, yarigu helbedi", SCAM),
        ("Part time job ide, YouTube video like maadi dina 4000 rupaayi gaLisi. Telegram alli message maadi", SCAM),
    ]),
    "4": ("Tulu and Tulu in English letters scams", [
        ("ಈರೆನ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇನಿ ಬ್ಲಾಕ್ ಆಪುಂಡು. ಬೇಗ KYC ಅಪ್‌ಡೇಟ್ ಮಲ್ಪುಲೆ: http://kyc-update-bank.in", SCAM),
        ("ಈರೆಗ್ 25 ಲಕ್ಷ ಲಾಟರಿ ಬತ್ತ್‌ಂಡ್! ಪೈಸೆ ಪಡೆಯೆರೆ 10,000 ರೂಪಾಯಿ ಫೀಸ್ ಕಡಪುಡುಲೆ", SCAM),
        ("ಈರೆನ ಕರೆಂಟ್ ಕನೆಕ್ಷನ್ ಇನಿ ರಾತ್ರೆ ಕಟ್ ಆಪುಂಡು. ಬಿಲ್ ಅಪ್‌ಡೇಟ್ ಆಯಿಜಿ. ಬೇಗ 9845012345 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ", SCAM),
        ("ಈರೆನ ಫೋನ್‌ಗ್ ಬತ್ತಿನ OTP ಎಂಕ್ ಪನ್ಲೆ, ಈರೆನ ಖಾತೆ ಸರಿ ಮಲ್ಪುವ", SCAM),
        ("Eerena account block aapundu, KYC update malpule. Ee link click malpule: http://bit.ly/kyc-tulu", SCAM),
        ("Eereg lottery battundu, 5 lakh. Paise padeyere 5000 fees kadapule", SCAM),
        ("Yenk thappu da eerena account g 2000 kadaputhe, pin pathd approve malpule", SCAM),
    ]),
    "5": ("Genuine messages in every language (should be SAFE)", [
        ("123456 is your OTP for login to SBI YONO. Do not share it with anyone. SBI never asks for OTP.", SAFE),
        ("Rs 500.00 debited from A/c XX1234 on 07-10-26 to VPA swiggy@icici. Not you? Call 1800 1234 (toll free).", SAFE),
        ("Your Swiggy order from Meghana Foods is out for delivery. Track it in the app.", SAFE),
        ("PNR 4521367890: Train 12658 confirmed, Coach S5 Berth 32. Happy journey - IRCTC", SAFE),
        ("Dear customer, your Jio recharge of Rs 299 is successful. Validity 28 days.", SAFE),
        ("Hi, are we meeting at 5 pm near the college gate? Bring the notes please.", SAFE),
        ("Your appointment with Dr. Rao is confirmed for Friday 10:30 am. Reply C to cancel.", SAFE),
        ("Amma: maga, office inda barovaga halu tagondu baa", SAFE),
        ("ನಾಳೆ ಬೆಳಿಗ್ಗೆ 10 ಗಂಟೆಗೆ ಕಾಲೇಜಿನಲ್ಲಿ ಸಭೆ ಇದೆ. ಎಲ್ಲರೂ ಬನ್ನಿ.", SAFE),
        ("ಎಂಕ್ ಇನಿ ಬರೆರೆ ಆಪುಜಿ, ಎಲ್ಲೆ ಬರ್ಪೆ. ಅಮ್ಮಗ್ ಪನ್ಲೆ.", SAFE),
        ("कल शाम को घर आ जाना, खाना साथ में खाएँगे।", SAFE),
        ("Bhai kal match dekhne chalein? 7 baje stadium ke bahar milte hain", SAFE),
        ("Your BESCOM bill of Rs 1,240 for September is due on 15-10-2026. Pay on the BESCOM app or bescom.karnataka.gov.in", SAFE),
        ("Your Amazon order #405-1234567 has been delivered. Rate your experience in the app.", SAFE),
    ]),
    "6": ("Screenshots (read with OCR on the server): English, Hindi and Kannada", [
        ("sms_en_kyc.png", SCAM), ("wa_en_job.png", SCAM), ("sms_hi_bijli.png", SCAM), ("wa_kn_kyc.png", SCAM),
        ("sms_en_otp_genuine.png", SAFE), ("wa_kn_genuine.png", SAFE),
    ]),
}
