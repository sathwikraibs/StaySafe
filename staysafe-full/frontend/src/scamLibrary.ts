// The scam knowledge base (English). Kept in the website itself so it opens instantly.
// Translations: i18n/content-*.ts (first 8 scams) and i18n/scams-*.ts (examples, checks and newer scams).

export interface Scam {
  id: string;
  category: string;
  title: string;
  how_it_works: string;
  red_flags: string[];
  what_to_do: string;
  /** a short made-up example of what the scam message looks like */
  example?: string;
  /** simple ways to check if it's real */
  check?: string[];
  /** how common / harmful: 3 = very common in India right now */
  level: 1 | 2 | 3;
  /** which tool helps with this scam */
  tool?: "/scan-message" | "/scan-url" | "/scan-qr" | "/scan-file" | "/scan-email";
  icon: "bank" | "bag" | "job" | "chart" | "police" | "monitor" | "heart" | "sim" | "bolt" | "box" | "gift" | "upi" | "video" | "loan" | "phone" | "chat" | "family" | "car" | "tag" | "app";
}

export const SCAMS_EN: Scam[] = [
  {
    id: "kyc_scam", category: "Bank", title: "KYC / Account Suspension Scam", level: 3, icon: "bank", tool: "/scan-message",
    how_it_works: "You get an SMS or call claiming your bank account will be blocked unless you 'update KYC' immediately, usually with a link or a request to install a remote-access app.",
    red_flags: ["Urgency, like 'within 24 hours' or 'today'", "Link doesn't go to your bank's real domain", "Asks you to install AnyDesk/TeamViewer", "Asks for OTP, PIN, or card details"],
    what_to_do: "Ignore the message. Open your bank's app directly or call the number on your card to verify.",
    example: "Dear Customer, your SBI YONO account will be blocked today. Update your PAN now: sbi-kyc-update.xyz",
    check: ["Open your bank's own app and look for any alert there", "Call the number printed on the back of your card", "Paste the message into Check a Message"],
  },
  {
    id: "fake_refund", category: "Shopping", title: "Fake Refund / Delivery Scam", level: 3, icon: "bag", tool: "/scan-qr",
    how_it_works: "A message claims a refund, delivery fee, or customs charge is pending and asks you to 'accept' it by scanning a QR code or entering your UPI PIN.",
    red_flags: ["Asks you to enter UPI PIN to 'receive' money. You never need a PIN to receive", "Unexpected refund you didn't request", "Pressure to act immediately or lose the refund"],
    what_to_do: "Never enter your PIN to receive money. Check the order status directly in the shopping app.",
    example: "Your refund of Rs 1,499 is ready. Scan this QR and enter your UPI PIN to receive it.",
    check: ["Open the shopping app and check the order yourself", "Remember: a UPI PIN only ever sends money out"],
  },
  {
    id: "job_scam", category: "Jobs", title: "Fake Job Offer Scam", level: 3, icon: "job", tool: "/scan-message",
    how_it_works: "You're offered a high-paying work-from-home job, then asked to pay a 'registration' or 'training' fee before starting.",
    red_flags: ["Any legitimate employer asking you to pay to get hired", "Contact only through WhatsApp/Telegram, no official email", "Salary sounds too good for the effort described"],
    what_to_do: "Never pay to get a job. Verify the company independently before sharing any documents.",
    example: "Part-time job! Earn Rs 3,000 to 8,000 daily by liking YouTube videos. Contact HR on Telegram @jobs_hr_desk",
    check: ["Search the company name with the word 'scam'", "Look for the job on the company's own careers page", "Never pay any fee or 'task deposit'"],
  },
  {
    id: "investment_scam", category: "Investment", title: "Guaranteed-Returns Investment Scam", level: 3, icon: "chart",
    how_it_works: "A 'trading group' or app promises guaranteed daily/weekly returns on crypto or stock trading, often via a WhatsApp/Telegram group with fake screenshots of profits.",
    red_flags: ["Guaranteed or fixed high returns", "Pressure to deposit more once you're 'in profit' (to withdraw)", "Unregistered trading app, not on Play Store/App Store"],
    what_to_do: "No legitimate investment guarantees returns. Verify SEBI/RBI registration before investing anything.",
    example: "Join our VIP stock group. 30% guaranteed monthly returns. Our members made Rs 5 lakh last week!",
    check: ["Check the adviser or broker on the SEBI website", "Only use apps from well-known, registered brokers", "If you can't withdraw without paying a 'tax', it's a scam", "Paste the app's website into StaySafe: it warns about platforms on RBI's Alert List"],
  },
  {
    id: "digital_arrest", category: "Government Impersonation", title: "'Digital Arrest' / Fake Police Scam", level: 3, icon: "police",
    how_it_works: "A caller claims to be police/customs/CBI, says you're implicated in a crime, and demands you stay on a video call and transfer money to 'clear your name'.",
    red_flags: ["Real police never conduct 'arrests' over video call", "Demands for money transfer to avoid arrest", "Threatens and isolates you from contacting family"],
    what_to_do: "Hang up. This is always a scam. Report at cybercrime.gov.in or call 1930.",
    example: "This is Mumbai Police Cyber Cell. A parcel in your name has drugs. Stay on this video call or you will be arrested.",
    check: ["Hang up and tell a family member straight away", "There is no such thing as a 'digital arrest' in Indian law", "Call your local police station on its real number"],
  },
  {
    id: "tech_support_scam", category: "Tech Support", title: "Fake Tech Support Popup", level: 2, icon: "monitor",
    how_it_works: "A browser popup claims your device has a virus and shows a phone number to 'call Microsoft/Google support' immediately.",
    red_flags: ["Popups with countdown timers or loud alarm sounds", "Asks you to call a number shown in the browser", "Real security software never asks you to call a number in a popup"],
    what_to_do: "Close the browser tab (or force-close the browser). Don't call the number. Run a scan with your actual antivirus if worried.",
    example: "WARNING! Your computer is infected. Call Microsoft Support now at +1-800-XXX-XXXX. Do not close this window.",
    check: ["Close the tab or restart the browser", "Microsoft and Google never show phone numbers in popups"],
  },
  {
    id: "romance_scam", category: "Social", title: "Romance / Relationship Scam", level: 2, icon: "heart",
    how_it_works: "Someone builds an online relationship over weeks, then invents an emergency (medical bill, travel, customs fee) and asks for money.",
    red_flags: ["Never willing to video call or meet in person", "Relationship escalates to requests for money quickly", "Excuses for why they can't verify identity"],
    what_to_do: "Never send money to someone you haven't met in person. Reverse image search their photos.",
    example: "My love, I sent you a gift from London but customs is holding it. Please pay Rs 45,000 clearance fee, I will return it.",
    check: ["Do a reverse image search of their photos", "Ask for a live video call", "Talk to a friend before sending any money"],
  },
  {
    id: "sim_swap", category: "Account Security", title: "SIM Swap Fraud", level: 2, icon: "sim",
    how_it_works: "A scammer tricks your telecom provider into issuing a duplicate SIM for your number, giving them your OTPs and effectively taking over your accounts.",
    red_flags: ["Your phone suddenly loses network signal for no reason", "You get an SMS about a SIM swap/port request you didn't initiate"],
    what_to_do: "Contact your telecom provider immediately if signal drops unexpectedly. Enable app-based MFA (not just SMS) where possible.",
    example: "Dear customer, your request for a new SIM has been received. If not requested by you, reply NO.",
    check: ["Call your mobile operator from another phone", "Check your bank for any new transactions"],
  },
  {
    id: "electricity_bill", category: "Bills", title: "Electricity Disconnection Scam", level: 3, icon: "bolt", tool: "/scan-message",
    how_it_works: "An SMS says your power will be cut tonight because your last bill wasn't updated, and gives a personal mobile number to call. The 'officer' then asks you to install an app or pay a small amount through a link.",
    red_flags: ["Personal 10-digit mobile number instead of the official helpline", "Power cut 'tonight at 9:30 pm'", "Asks you to install an app or pay through a link"],
    what_to_do: "Don't call the number. Check your bill in the official electricity board app or website, or visit the office.",
    example: "Dear consumer, your electricity will be disconnected tonight at 9:30 pm as your last bill is not updated. Call officer 98XXXXXX10.",
    check: ["Check your bill in the BESCOM / MESCOM / official board app", "Electricity boards don't send SMS from personal numbers"],
  },
  {
    id: "parcel_fee", category: "Delivery", title: "Parcel On Hold / Small Fee Scam", level: 3, icon: "box", tool: "/scan-url",
    how_it_works: "A message says your parcel can't be delivered because the address is incomplete, and asks you to pay a tiny fee (like Rs 25) on a website. The page steals your card details.",
    red_flags: ["You aren't expecting a parcel", "A very small 're-delivery' or 'address update' fee", "The link isn't the courier's real website"],
    what_to_do: "Don't click. Track parcels only in the official app or website of India Post or the courier.",
    example: "India Post: Your package is on hold due to an incomplete address. Update within 12 hours: indiapost-track.top",
    check: ["Copy the link and paste it into Check a Link", "Track with the tracking number on the courier's own website"],
  },
  {
    id: "lottery_prize", category: "Prize", title: "Lottery / KBC Prize Scam", level: 2, icon: "gift", tool: "/scan-message",
    how_it_works: "You're told you've won a lottery, KBC prize, car or phone. To receive it, you must first pay 'tax', 'processing' or 'GST' fees.",
    red_flags: ["You never entered any lottery", "You must pay money to get money", "WhatsApp calls with a KBC logo or 'manager' photo"],
    what_to_do: "Ignore and block. Real prizes never ask you to pay first.",
    example: "Congratulations! Your number won Rs 25,00,000 in KBC Lucky Draw. Pay Rs 8,500 processing fee to claim.",
    check: ["Ask yourself: did I enter anything?", "Never pay a fee to receive a prize"],
  },
  {
    id: "upi_collect", category: "Payments", title: "UPI 'Collect Request' Scam", level: 3, icon: "upi", tool: "/scan-qr",
    how_it_works: "While selling something online, the 'buyer' sends a payment request (or QR) and tells you to approve it to receive money. Approving it with your PIN sends your money to them.",
    red_flags: ["'Enter your PIN to receive the payment'", "A 'buyer' who agrees to any price without seeing the item", "Request says 'Pay' in your UPI app"],
    what_to_do: "Decline the request. To receive money you only share your UPI ID. You never enter a PIN.",
    example: "I have sent you a request of Rs 12,000 for the sofa. Please accept and enter PIN to get the money.",
    check: ["Read the screen: if it says 'Pay', money will leave your account", "Ask the buyer to send money to your UPI ID instead"],
  },
  {
    id: "video_call_blackmail", category: "Social", title: "Video Call Blackmail", level: 2, icon: "video",
    how_it_works: "An unknown number makes a video call that shows objectionable content, records your face, and then demands money, threatening to send the video to your contacts.",
    red_flags: ["Video call from an unknown number, often late at night", "Threats and a deadline to pay", "Fake 'police' or 'YouTube' follow-up calls"],
    what_to_do: "Don't pay; paying brings more demands. Block the number, report at cybercrime.gov.in and tell someone you trust.",
    example: "I have recorded your video call. Pay Rs 20,000 in 1 hour or I will send it to all your friends.",
    check: ["Do not answer video calls from unknown numbers", "Report the account on WhatsApp / Instagram"],
  },
  {
    id: "loan_app", category: "Loans", title: "Instant Loan App Harassment", level: 3, icon: "loan", tool: "/scan-file",
    how_it_works: "An app offers an instant loan with no documents. It takes permission to read your contacts and photos, gives a small amount, then demands huge repayments and harasses your contacts.",
    red_flags: ["Loan in minutes, no documents", "App asks for contacts, photos and SMS permission", "Not linked to any RBI-registered bank or NBFC"],
    what_to_do: "Only borrow through apps of RBI-registered banks or NBFCs. If harassed, report at cybercrime.gov.in and on Sachet (RBI).",
    example: "Get Rs 50,000 instant loan in 5 minutes. No CIBIL check. Download app: quickcash-loan.apk",
    check: ["Check the lender on the RBI list of registered NBFCs", "Never install loan apps from links or APK files"],
  },
  {
    id: "fake_customer_care", category: "Search", title: "Fake Customer Care Number", level: 3, icon: "phone",
    how_it_works: "You search Google for a company's helpline and call a number scammers posted. The 'agent' asks you to install a screen-sharing app or share an OTP to 'solve' your problem.",
    red_flags: ["Number found on a random website, Google Maps or comment", "Asks you to install AnyDesk, TeamViewer or QuickSupport", "Asks for OTP or card details for a refund"],
    what_to_do: "Take helpline numbers only from the official app or website of the company. Never install screen-sharing apps on a call.",
    example: "Hello, I am from Flipkart support. For your refund, please install QuickSupport and tell me the code on screen.",
    check: ["Open the company's app and use its Help section", "Real support never needs your OTP or screen"],
  },
  {
    id: "whatsapp_otp_hijack", category: "Account Security", title: "WhatsApp Account Takeover", level: 3, icon: "chat",
    how_it_works: "A friend's hacked account (or a stranger) says they sent you a code 'by mistake' and asks you to forward it. That code is the one that moves your WhatsApp to their phone.",
    red_flags: ["'I sent you an OTP by mistake, please send it'", "A 6-digit WhatsApp code you didn't ask for", "Message from a friend that sounds unlike them"],
    what_to_do: "Never share any code. Turn on Two-step verification in WhatsApp (Settings, Account).",
    example: "Hi, I accidentally sent my 6 digit code to your number. Can you please send it to me? Urgent.",
    check: ["Call your friend on their normal number", "Set a WhatsApp two-step PIN today"],
  },
  {
    id: "family_emergency", category: "Family", title: "'Hi Mum, New Number' Emergency", level: 2, icon: "family", tool: "/scan-message",
    how_it_works: "A message from an unknown number pretends to be your child, relative or friend who 'lost their phone' and urgently needs money for rent, a bill or a hospital.",
    red_flags: ["New number, same story: phone lost or broken", "Urgent request to send money to someone else's account", "Avoids a voice call"],
    what_to_do: "Call the person on their old number or ask a question only they would know before sending anything.",
    example: "Hi Mum, this is my new number, my phone fell in water. Can you send Rs 15,000 urgently for rent? I'll return tomorrow.",
    check: ["Call their old number", "Ask something only they would know"],
  },
  {
    id: "marketplace_army", category: "Shopping", title: "'Army Officer' Buyer / Seller Scam", level: 2, icon: "tag",
    how_it_works: "On OLX, Facebook or rental sites, someone claiming to be an army officer being 'transferred' offers a great deal or agrees to buy instantly, then asks for advance payments or sends UPI requests.",
    red_flags: ["Army ID card photo to build trust", "Deal that's far below market price", "Advance payment for 'gate pass' or 'transport'"],
    what_to_do: "Only pay after you see the item in person. Never approve UPI requests to 'receive' money.",
    example: "I am Army officer, transferred to Pune. Selling my bike for Rs 18,000. Pay Rs 2,000 for army courier charge.",
    check: ["Meet in a public place and see the item first", "Reverse image search the ID card photo"],
  },
  {
    id: "echallan", category: "Government Impersonation", title: "Fake Traffic Challan / FASTag Link", level: 3, icon: "car", tool: "/scan-url",
    how_it_works: "An SMS or WhatsApp message says you have an unpaid traffic fine or FASTag problem, with a link or an APK to pay. The link steals card details or the app steals your OTPs.",
    red_flags: ["Link isn't echallan.parivahan.gov.in", "An APK file instead of a website", "Threat of court case or licence suspension"],
    what_to_do: "Check challans only on echallan.parivahan.gov.in or the mParivahan app. Never install an APK from a message.",
    example: "Your vehicle KA-19-XX-1234 has a pending challan of Rs 500. Pay now to avoid court: echallan-pay.apk",
    check: ["Type echallan.parivahan.gov.in yourself", "Paste the link into Check a Link"],
  },
  {
    id: "apk_invitation", category: "Apps", title: "Wedding Invitation / APK File Scam", level: 3, icon: "app", tool: "/scan-file",
    how_it_works: "A WhatsApp message with a file named like 'Wedding Invitation.apk', 'PM Kisan.apk' or 'Bank KYC.apk'. Installing it lets scammers read your SMS and OTPs and empty your account.",
    red_flags: ["A file that ends in .apk", "From an unknown number or a hacked friend", "Asks for 'Install unknown apps' or 'Accessibility' permission"],
    what_to_do: "Never open .apk files from messages. If you installed one, turn off the internet and follow the recovery plan.",
    example: "Hello, you are invited to our wedding. Please see the invitation card: Wedding_Invitation.apk",
    check: ["Check the file in Check a File", "Real invitations are photos or PDFs, never apps"],
  },
];
