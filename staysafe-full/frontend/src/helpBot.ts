// StaySafe Helper: ready answers to the questions people ask most, in every site language.
// Works any time of day, with no server and no cost. "Talk to a person" opens the live chat.
import { useEffect } from "react";
import type { Lang } from "@/i18n";

export type HelpAction = { kind: "go"; path: string; label: string } | { kind: "person"; label: string };

export interface HelpTopic {
  id: string;
  /** The button text */
  q: string;
  /** The answer, one line per bubble line */
  a: string[];
  actions?: HelpAction[];
  /** Words people type when they mean this topic (any language, any spelling) */
  words: string[];
}

export interface HelpTexts {
  title: string;
  subtitle: string;
  hello: string;
  pick: string;
  placeholder: string;
  send: string;
  noMatch: string;
  linkSeen: string;
  messageSeen: string;
  checkThisLink: string;
  checkThisMessage: string;
  person: string;
  personOnline: string;
  personOffline: string;
  personNotReady: string;
  more: string;
  close: string;
  never: string;
  urgent: string;
  formIntro: string;
  chatNow: string;
  writeToUs: string;
  formTitle: string;
  formName: string;
  formEmail: string;
  formPhone: string;
  formEither: string;
  formLost: string;
  lostYes: string;
  lostNo: string;
  lostUnsure: string;
  formMessage: string;
  formMessagePh: string;
  formSend: string;
  formSending: string;
  formBack: string;
  sent: string;
  sentUrgent: string;
  aiLabel: string;
  aiName: string;
  stillNeed: string;
  writeTeam: string;
  langAsk: string;
  commonTitle: string;
  typing: string;
  actIncident: string;
  actCheckMessage: string;
  actCheckLink: string;
  actPassword: string;
  actLibrary: string;
}

/** Words that mean the same in every language (numbers, English words people mix in). */
const COMMON: Record<string, string[]> = {
  lost_money: ["otp", "upi", "debit", "debited", "deducted", "transfer", "lost money", "money gone", "fraud", "1930",
    "paisa", "paise", "kat gaya", "chala gaya", "hana hoytu", "duddu", "refund"],
  check_msg: ["is this", "scam", "fake", "real", "genuine", "sms", "message", "call", "whatsapp", "kyc", "blocked", "suspend",
    "lottery", "prize", "electricity", "bill", "courier", "parcel"],
  clicked: ["clicked", "opened link", "installed", "apk", "app install", "downloaded", "screen share", "anydesk", "teamviewer",
    "quicksupport", "remote"],
  report: ["report", "complaint", "complain", "police", "cyber cell", "cybercrime", "chakshu", "sanchar saathi", "1909"],
  digital_arrest: ["digital arrest", "arrest", "cbi", "ed ", "customs", "narcotics", "drugs", "fedex", "court", "warrant",
    "video call police", "trai"],
  job_invest: ["job", "task", "part time", "work from home", "like youtube", "review", "rating", "investment", "invest",
    "trading", "stock", "crypto", "double", "returns", "telegram"],
  hacked: ["hacked", "hack", "account taken", "password changed", "cant login", "can't login", "instagram", "facebook",
    "gmail", "email hacked", "whatsapp hacked", "someone using my"],
  about: ["free", "cost", "price", "privacy", "private", "data", "safe to use", "who are you", "about", "staysafe"],
};

const TOPICS: Record<Lang, HelpTopic[]> = {
  en: [
    {
      id: "lost_money", q: "I lost money or shared my OTP",
      a: ["Act fast, the first hour matters most.",
        "1. Call 1930 (National Cyber Crime Helpline) right away, or report at cybercrime.gov.in.",
        "2. Call your bank on the number printed on your card or in its app, and ask them to block your card, UPI and net banking.",
        "3. Change the passwords and PINs you shared. Never share an OTP again, not even with 'bank staff'.",
        "4. Keep screenshots of the messages, numbers and payment details. They help the police."],
      actions: [{ kind: "go", path: "/incident", label: "Step-by-step recovery plan" }],
      words: ["money", "lost", "otp", "shared otp", "account empty"],
    },
    {
      id: "check_msg", q: "Is this message, call or link a scam?",
      a: ["You can check it here in a few seconds.",
        "Paste the message or upload a screenshot in Check a Message. For a web address, use Check a Link.",
        "Quick signs of a scam: hurry ('today', 'within 2 hours'), threats (account blocked, arrest), asking for OTP, PIN or payment, and links that aren't the official website."],
      actions: [{ kind: "go", path: "/scan-message", label: "Check a message" }, { kind: "go", path: "/scan-url", label: "Check a link" }],
      words: ["check", "suspicious", "doubt"],
    },
    {
      id: "clicked", q: "I clicked a link or installed an app",
      a: ["Don't panic. Do these now:",
        "1. If you typed a password, PIN or card details on that page, change them and call your bank.",
        "2. Uninstall any app you were asked to install (screen sharing apps like AnyDesk too).",
        "3. Turn off mobile data or Wi-Fi for a moment if the phone is acting strange.",
        "4. If money was taken, call 1930 at once."],
      actions: [{ kind: "go", path: "/incident", label: "What to do now" }, { kind: "go", path: "/scan-url", label: "Check that link" }],
      words: ["click", "link", "app"],
    },
    {
      id: "report", q: "How do I report a scam?",
      a: ["Money lost: call 1930 or file a complaint at cybercrime.gov.in.",
        "Fraud call or SMS (no money lost): report it on Sanchar Saathi, 'Chakshu' (sancharsaathi.gov.in).",
        "Spam SMS: forward it to 1909.",
        "Also tell your bank if the message pretended to be them."],
      words: ["how to report", "where to report"],
    },
    {
      id: "digital_arrest", q: "Police, CBI or courier call says I'm in trouble",
      a: ["This is a well-known scam. There is no such thing as a 'digital arrest'.",
        "Real police, CBI, customs or courier companies never ask you to stay on a video call or to pay to 'clear your name'.",
        "Hang up. Don't pay, don't share Aadhaar or bank details, and don't install any app they send.",
        "Tell a family member, and report the number on Sanchar Saathi or call 1930 if you paid."],
      words: ["police call", "cbi call", "arrest"],
    },
    {
      id: "job_invest", q: "Job, task or investment offer: is it real?",
      a: ["Be very careful. Real jobs never ask you to pay first.",
        "'Like videos and earn', 'rate hotels', Telegram tasks and 'guaranteed double returns' are common scams. They pay small amounts first, then ask for bigger deposits.",
        "Never pay a 'registration', 'unlock' or 'tax' fee to get your money out."],
      actions: [{ kind: "go", path: "/scam-library", label: "Read about these scams" }],
      words: ["earn", "income", "offer"],
    },
    {
      id: "hacked", q: "My WhatsApp, Instagram or email was hacked",
      a: ["1. Use 'Forgot password' on the app or website to take the account back, then set a new strong password.",
        "2. Turn on two-step verification (WhatsApp: Settings, Account, Two-step verification).",
        "3. Tell your friends not to send money or codes to 'you'.",
        "4. Check if your email appeared in a data leak on Check a Password."],
      actions: [{ kind: "go", path: "/check-password", label: "Check my password and email" }],
      words: ["account", "login"],
    },
    {
      id: "about", q: "Is StaySafe free? Is my data safe?",
      a: ["Yes, StaySafe is completely free, with no sign-up.",
        "Your check history stays on your own device. We never ask for your OTP, PIN, password or bank details."],
      actions: [{ kind: "go", path: "/about", label: "How StaySafe works" }],
      words: [],
    },
  ],
  hi: [
    {
      id: "lost_money", q: "मेरे पैसे कट गए या मैंने OTP बता दिया",
      a: ["जल्दी करें, पहला घंटा सबसे ज़रूरी है।",
        "1. तुरंत 1930 (राष्ट्रीय साइबर क्राइम हेल्पलाइन) पर कॉल करें, या cybercrime.gov.in पर शिकायत करें।",
        "2. कार्ड या बैंक ऐप पर लिखे नंबर पर बैंक को कॉल करें और कार्ड, UPI और नेट बैंकिंग बंद करवाएँ।",
        "3. जो पासवर्ड और PIN बताए हैं, उन्हें बदलें। OTP किसी को न बताएँ, 'बैंक कर्मचारी' को भी नहीं।",
        "4. मैसेज, नंबर और पेमेंट की जानकारी के स्क्रीनशॉट रखें। ये पुलिस के काम आते हैं।"],
      actions: [{ kind: "go", path: "/incident", label: "कदम-दर-कदम मदद" }],
      words: ["पैसे", "पैसा", "कट गए", "ओटीपी", "धोखा", "ठगी"],
    },
    {
      id: "check_msg", q: "क्या यह मैसेज, कॉल या लिंक धोखा है?",
      a: ["आप इसे यहीं कुछ सेकंड में जाँच सकते हैं।",
        "'मैसेज जाँचें' में मैसेज पेस्ट करें या स्क्रीनशॉट डालें। वेब पते के लिए 'लिंक जाँचें' का इस्तेमाल करें।",
        "धोखे के आम संकेत: जल्दबाज़ी ('आज ही', '2 घंटे में'), धमकी (खाता बंद, गिरफ़्तारी), OTP, PIN या पैसे माँगना, और ऐसे लिंक जो आधिकारिक वेबसाइट नहीं हैं।"],
      actions: [{ kind: "go", path: "/scan-message", label: "मैसेज जाँचें" }, { kind: "go", path: "/scan-url", label: "लिंक जाँचें" }],
      words: ["मैसेज", "कॉल", "लिंक", "असली", "नकली", "जाँच", "शक"],
    },
    {
      id: "clicked", q: "मैंने लिंक खोला या ऐप इंस्टॉल किया",
      a: ["घबराएँ नहीं। अभी यह करें:",
        "1. अगर उस पेज पर पासवर्ड, PIN या कार्ड की जानकारी डाली थी, तो उसे बदलें और बैंक को कॉल करें।",
        "2. जो ऐप इंस्टॉल करने को कहा गया था, उसे हटा दें (AnyDesk जैसे स्क्रीन शेयर ऐप भी)।",
        "3. फ़ोन अजीब चल रहा हो तो थोड़ी देर के लिए मोबाइल डेटा या Wi-Fi बंद करें।",
        "4. पैसे कटे हों तो तुरंत 1930 पर कॉल करें।"],
      actions: [{ kind: "go", path: "/incident", label: "अब क्या करें" }, { kind: "go", path: "/scan-url", label: "वह लिंक जाँचें" }],
      words: ["क्लिक", "खोला", "इंस्टॉल", "ऐप", "डाउनलोड"],
    },
    {
      id: "report", q: "धोखे की शिकायत कैसे करें?",
      a: ["पैसे कटे हैं: 1930 पर कॉल करें या cybercrime.gov.in पर शिकायत करें।",
        "धोखे वाली कॉल या SMS (पैसे नहीं कटे): संचार साथी के 'चक्षु' पर बताएँ (sancharsaathi.gov.in)।",
        "स्पैम SMS: उसे 1909 पर फ़ॉरवर्ड करें।",
        "अगर मैसेज बैंक के नाम से था, तो बैंक को भी बताएँ।"],
      words: ["शिकायत", "रिपोर्ट", "पुलिस"],
    },
    {
      id: "digital_arrest", q: "पुलिस, CBI या कूरियर कॉल कह रहा है कि मैं मुसीबत में हूँ",
      a: ["यह एक जाना-माना धोखा है। 'डिजिटल अरेस्ट' जैसी कोई चीज़ नहीं होती।",
        "असली पुलिस, CBI, कस्टम या कूरियर कंपनी कभी वीडियो कॉल पर रुकने या 'नाम साफ़ करने' के लिए पैसे नहीं माँगती।",
        "फ़ोन काट दें। पैसे न दें, आधार या बैंक की जानकारी न दें, और उनका भेजा कोई ऐप इंस्टॉल न करें।",
        "परिवार को बताएँ, और नंबर की शिकायत संचार साथी पर करें। पैसे दिए हों तो 1930 पर कॉल करें।"],
      words: ["गिरफ्तार", "गिरफ़्तारी", "अरेस्ट", "पुलिस कॉल", "कूरियर"],
    },
    {
      id: "job_invest", q: "नौकरी, टास्क या निवेश का ऑफ़र: क्या असली है?",
      a: ["बहुत सावधान रहें। असली नौकरी में पहले पैसे नहीं देने पड़ते।",
        "'वीडियो लाइक करके कमाएँ', 'होटल रेटिंग', Telegram टास्क और 'पक्का दोगुना फ़ायदा' आम धोखे हैं। पहले थोड़े पैसे देते हैं, फिर बड़ी रकम जमा करवाते हैं।",
        "पैसे निकालने के लिए कभी 'रजिस्ट्रेशन', 'अनलॉक' या 'टैक्स' फ़ीस न दें।"],
      actions: [{ kind: "go", path: "/scam-library", label: "इन धोखों के बारे में पढ़ें" }],
      words: ["नौकरी", "कमाई", "टास्क", "निवेश", "ट्रेडिंग", "दोगुना"],
    },
    {
      id: "hacked", q: "मेरा WhatsApp, Instagram या ईमेल हैक हो गया",
      a: ["1. ऐप या वेबसाइट पर 'पासवर्ड भूल गए' से खाता वापस लें, फिर नया मज़बूत पासवर्ड रखें।",
        "2. टू-स्टेप वेरिफ़िकेशन चालू करें (WhatsApp: सेटिंग्स, अकाउंट, टू-स्टेप वेरिफ़िकेशन)।",
        "3. दोस्तों को बताएँ कि 'आपके' नाम से पैसे या कोड न भेजें।",
        "4. 'पासवर्ड जाँचें' में देखें कि आपका ईमेल किसी डेटा लीक में है या नहीं।"],
      actions: [{ kind: "go", path: "/check-password", label: "पासवर्ड और ईमेल जाँचें" }],
      words: ["हैक", "खाता", "लॉगिन"],
    },
    {
      id: "about", q: "क्या StaySafe मुफ़्त है? मेरी जानकारी सुरक्षित है?",
      a: ["हाँ, StaySafe पूरी तरह मुफ़्त है, साइन-अप की ज़रूरत नहीं।",
        "आपकी जाँच का इतिहास आपके ही फ़ोन पर रहता है। हम कभी OTP, PIN, पासवर्ड या बैंक की जानकारी नहीं माँगते।"],
      actions: [{ kind: "go", path: "/about", label: "StaySafe कैसे काम करता है" }],
      words: ["मुफ़्त", "मुफ्त", "फ्री", "सुरक्षित", "जानकारी"],
    },
  ],
  kn: [
    {
      id: "lost_money", q: "ನನ್ನ ಹಣ ಹೋಯಿತು ಅಥವಾ OTP ಹೇಳಿಬಿಟ್ಟೆ",
      a: ["ಬೇಗ ಮಾಡಿ, ಮೊದಲ ಒಂದು ಗಂಟೆ ತುಂಬಾ ಮುಖ್ಯ.",
        "1. ತಕ್ಷಣ 1930 (ರಾಷ್ಟ್ರೀಯ ಸೈಬರ್ ಕ್ರೈಂ ಸಹಾಯವಾಣಿ) ಗೆ ಕರೆ ಮಾಡಿ, ಅಥವಾ cybercrime.gov.in ನಲ್ಲಿ ದೂರು ನೀಡಿ.",
        "2. ಕಾರ್ಡ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ಆ್ಯಪ್‌ನಲ್ಲಿರುವ ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಿ, ಕಾರ್ಡ್, UPI ಮತ್ತು ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ ನಿಲ್ಲಿಸಲು ಹೇಳಿ.",
        "3. ಹೇಳಿದ ಪಾಸ್‌ವರ್ಡ್ ಮತ್ತು PIN ಬದಲಿಸಿ. OTP ಯಾರಿಗೂ ಹೇಳಬೇಡಿ, 'ಬ್ಯಾಂಕ್ ಸಿಬ್ಬಂದಿ'ಗೂ ಸಹ.",
        "4. ಮೆಸೇಜ್, ನಂಬರ್ ಮತ್ತು ಪಾವತಿ ವಿವರಗಳ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಇಟ್ಟುಕೊಳ್ಳಿ. ಪೊಲೀಸರಿಗೆ ಸಹಾಯವಾಗುತ್ತದೆ."],
      actions: [{ kind: "go", path: "/incident", label: "ಹಂತ ಹಂತದ ಸಹಾಯ" }],
      words: ["ಹಣ", "ದುಡ್ಡು", "ಹೋಯಿತು", "ಕಳೆದು", "ಮೋಸ", "ವಂಚನೆ", "ಓಟಿಪಿ"],
    },
    {
      id: "check_msg", q: "ಈ ಮೆಸೇಜ್, ಕರೆ ಅಥವಾ ಲಿಂಕ್ ಮೋಸವೇ?",
      a: ["ಇಲ್ಲೇ ಕೆಲವು ಸೆಕೆಂಡುಗಳಲ್ಲಿ ಪರಿಶೀಲಿಸಬಹುದು.",
        "'ಮೆಸೇಜ್ ಪರಿಶೀಲಿಸಿ' ಯಲ್ಲಿ ಮೆಸೇಜ್ ಪೇಸ್ಟ್ ಮಾಡಿ ಅಥವಾ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಹಾಕಿ. ವೆಬ್ ವಿಳಾಸಕ್ಕೆ 'ಲಿಂಕ್ ಪರಿಶೀಲಿಸಿ' ಬಳಸಿ.",
        "ಮೋಸದ ಸಾಮಾನ್ಯ ಲಕ್ಷಣಗಳು: ಅವಸರ ('ಇಂದೇ', '2 ಗಂಟೆಯೊಳಗೆ'), ಬೆದರಿಕೆ (ಖಾತೆ ಬ್ಲಾಕ್, ಬಂಧನ), OTP, PIN ಅಥವಾ ಹಣ ಕೇಳುವುದು, ಅಧಿಕೃತವಲ್ಲದ ವೆಬ್‌ಸೈಟ್ ಲಿಂಕ್‌ಗಳು."],
      actions: [{ kind: "go", path: "/scan-message", label: "ಮೆಸೇಜ್ ಪರಿಶೀಲಿಸಿ" }, { kind: "go", path: "/scan-url", label: "ಲಿಂಕ್ ಪರಿಶೀಲಿಸಿ" }],
      words: ["ಮೆಸೇಜ್", "ಕರೆ", "ಲಿಂಕ್", "ನಿಜವೇ", "ನಕಲಿ", "ಅನುಮಾನ", "ಪರಿಶೀಲಿಸ"],
    },
    {
      id: "clicked", q: "ನಾನು ಲಿಂಕ್ ತೆರೆದೆ ಅಥವಾ ಆ್ಯಪ್ ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿದೆ",
      a: ["ಗಾಬರಿಯಾಗಬೇಡಿ. ಈಗಲೇ ಇದನ್ನು ಮಾಡಿ:",
        "1. ಆ ಪುಟದಲ್ಲಿ ಪಾಸ್‌ವರ್ಡ್, PIN ಅಥವಾ ಕಾರ್ಡ್ ವಿವರ ಹಾಕಿದ್ದರೆ, ಅದನ್ನು ಬದಲಿಸಿ ಮತ್ತು ಬ್ಯಾಂಕ್‌ಗೆ ಕರೆ ಮಾಡಿ.",
        "2. ಅವರು ಹೇಳಿದ ಆ್ಯಪ್ ಅನ್ನು ತೆಗೆದುಹಾಕಿ (AnyDesk ನಂತಹ ಸ್ಕ್ರೀನ್ ಶೇರ್ ಆ್ಯಪ್‌ಗಳೂ ಸಹ).",
        "3. ಫೋನ್ ವಿಚಿತ್ರವಾಗಿ ವರ್ತಿಸುತ್ತಿದ್ದರೆ ಸ್ವಲ್ಪ ಸಮಯ ಮೊಬೈಲ್ ಡೇಟಾ ಅಥವಾ Wi-Fi ಆಫ್ ಮಾಡಿ.",
        "4. ಹಣ ಹೋಗಿದ್ದರೆ ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ."],
      actions: [{ kind: "go", path: "/incident", label: "ಈಗ ಏನು ಮಾಡಬೇಕು" }, { kind: "go", path: "/scan-url", label: "ಆ ಲಿಂಕ್ ಪರಿಶೀಲಿಸಿ" }],
      words: ["ಕ್ಲಿಕ್", "ತೆರೆದೆ", "ಇನ್‌ಸ್ಟಾಲ್", "ಆ್ಯಪ್", "ಡೌನ್‌ಲೋಡ್"],
    },
    {
      id: "report", q: "ಮೋಸದ ಬಗ್ಗೆ ದೂರು ಹೇಗೆ ನೀಡುವುದು?",
      a: ["ಹಣ ಹೋಗಿದ್ದರೆ: 1930 ಗೆ ಕರೆ ಮಾಡಿ ಅಥವಾ cybercrime.gov.in ನಲ್ಲಿ ದೂರು ನೀಡಿ.",
        "ಮೋಸದ ಕರೆ ಅಥವಾ SMS (ಹಣ ಹೋಗಿಲ್ಲ): ಸಂಚಾರ್ ಸಾಥಿಯ 'ಚಕ್ಷು' ದಲ್ಲಿ ತಿಳಿಸಿ (sancharsaathi.gov.in).",
        "ಸ್ಪ್ಯಾಮ್ SMS: ಅದನ್ನು 1909 ಗೆ ಫಾರ್ವರ್ಡ್ ಮಾಡಿ.",
        "ಮೆಸೇಜ್ ಬ್ಯಾಂಕ್ ಹೆಸರಿನಲ್ಲಿ ಇದ್ದರೆ ಬ್ಯಾಂಕ್‌ಗೂ ತಿಳಿಸಿ."],
      words: ["ದೂರು", "ರಿಪೋರ್ಟ್", "ಪೊಲೀಸ್"],
    },
    {
      id: "digital_arrest", q: "ಪೊಲೀಸ್, CBI ಅಥವಾ ಕೊರಿಯರ್ ಕರೆ ನಾನು ತೊಂದರೆಯಲ್ಲಿದ್ದೇನೆ ಎನ್ನುತ್ತಿದೆ",
      a: ["ಇದು ಗೊತ್ತಿರುವ ಮೋಸ. 'ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್' ಎಂಬುದೇ ಇಲ್ಲ.",
        "ನಿಜವಾದ ಪೊಲೀಸ್, CBI, ಕಸ್ಟಮ್ಸ್ ಅಥವಾ ಕೊರಿಯರ್ ಕಂಪನಿ ವೀಡಿಯೊ ಕರೆಯಲ್ಲೇ ಇರಲು ಅಥವಾ 'ಹೆಸರು ಸರಿಪಡಿಸಲು' ಹಣ ಕೇಳುವುದಿಲ್ಲ.",
        "ಕರೆ ಕಡಿತಗೊಳಿಸಿ. ಹಣ ಕೊಡಬೇಡಿ, ಆಧಾರ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ವಿವರ ಹೇಳಬೇಡಿ, ಅವರು ಕಳುಹಿಸಿದ ಆ್ಯಪ್ ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಬೇಡಿ.",
        "ಮನೆಯವರಿಗೆ ತಿಳಿಸಿ, ನಂಬರ್ ಅನ್ನು ಸಂಚಾರ್ ಸಾಥಿಯಲ್ಲಿ ದೂರು ನೀಡಿ. ಹಣ ಕೊಟ್ಟಿದ್ದರೆ 1930 ಗೆ ಕರೆ ಮಾಡಿ."],
      words: ["ಬಂಧನ", "ಅರೆಸ್ಟ್", "ಪೊಲೀಸ್ ಕರೆ", "ಕೊರಿಯರ್"],
    },
    {
      id: "job_invest", q: "ಉದ್ಯೋಗ, ಟಾಸ್ಕ್ ಅಥವಾ ಹೂಡಿಕೆ ಆಫರ್: ನಿಜವೇ?",
      a: ["ತುಂಬಾ ಎಚ್ಚರವಾಗಿರಿ. ನಿಜವಾದ ಉದ್ಯೋಗಕ್ಕೆ ಮೊದಲು ಹಣ ಕೊಡಬೇಕಾಗಿಲ್ಲ.",
        "'ವೀಡಿಯೊ ಲೈಕ್ ಮಾಡಿ ಗಳಿಸಿ', 'ಹೋಟೆಲ್ ರೇಟಿಂಗ್', Telegram ಟಾಸ್ಕ್ ಮತ್ತು 'ಖಚಿತ ಎರಡು ಪಟ್ಟು ಲಾಭ' ಸಾಮಾನ್ಯ ಮೋಸಗಳು. ಮೊದಲು ಸ್ವಲ್ಪ ಹಣ ಕೊಟ್ಟು, ನಂತರ ದೊಡ್ಡ ಮೊತ್ತ ಕಟ್ಟಲು ಹೇಳುತ್ತಾರೆ.",
        "ಹಣ ತೆಗೆಯಲು 'ನೋಂದಣಿ', 'ಅನ್‌ಲಾಕ್' ಅಥವಾ 'ತೆರಿಗೆ' ಶುಲ್ಕ ಎಂದಿಗೂ ಕಟ್ಟಬೇಡಿ."],
      actions: [{ kind: "go", path: "/scam-library", label: "ಈ ಮೋಸಗಳ ಬಗ್ಗೆ ಓದಿ" }],
      words: ["ಉದ್ಯೋಗ", "ಕೆಲಸ", "ಗಳಿಕೆ", "ಟಾಸ್ಕ್", "ಹೂಡಿಕೆ", "ಟ್ರೇಡಿಂಗ್", "ಲಾಭ"],
    },
    {
      id: "hacked", q: "ನನ್ನ WhatsApp, Instagram ಅಥವಾ ಇಮೇಲ್ ಹ್ಯಾಕ್ ಆಗಿದೆ",
      a: ["1. ಆ್ಯಪ್ ಅಥವಾ ವೆಬ್‌ಸೈಟ್‌ನಲ್ಲಿ 'ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿದ್ದೀರಾ' ಬಳಸಿ ಖಾತೆ ಮರಳಿ ಪಡೆಯಿರಿ, ನಂತರ ಹೊಸ ಬಲವಾದ ಪಾಸ್‌ವರ್ಡ್ ಇಡಿ.",
        "2. ಟೂ-ಸ್ಟೆಪ್ ವೆರಿಫಿಕೇಶನ್ ಆನ್ ಮಾಡಿ (WhatsApp: ಸೆಟ್ಟಿಂಗ್ಸ್, ಅಕೌಂಟ್, ಟೂ-ಸ್ಟೆಪ್ ವೆರಿಫಿಕೇಶನ್).",
        "3. 'ನಿಮ್ಮ' ಹೆಸರಿನಲ್ಲಿ ಹಣ ಅಥವಾ ಕೋಡ್ ಕಳುಹಿಸಬೇಡಿ ಎಂದು ಸ್ನೇಹಿತರಿಗೆ ತಿಳಿಸಿ.",
        "4. 'ಪಾಸ್‌ವರ್ಡ್ ಪರಿಶೀಲಿಸಿ' ಯಲ್ಲಿ ನಿಮ್ಮ ಇಮೇಲ್ ಡೇಟಾ ಸೋರಿಕೆಯಲ್ಲಿ ಇದೆಯೇ ನೋಡಿ."],
      actions: [{ kind: "go", path: "/check-password", label: "ಪಾಸ್‌ವರ್ಡ್ ಮತ್ತು ಇಮೇಲ್ ಪರಿಶೀಲಿಸಿ" }],
      words: ["ಹ್ಯಾಕ್", "ಖಾತೆ", "ಲಾಗಿನ್"],
    },
    {
      id: "about", q: "StaySafe ಉಚಿತವೇ? ನನ್ನ ಮಾಹಿತಿ ಸುರಕ್ಷಿತವೇ?",
      a: ["ಹೌದು, StaySafe ಸಂಪೂರ್ಣ ಉಚಿತ, ಸೈನ್-ಅಪ್ ಬೇಕಿಲ್ಲ.",
        "ನಿಮ್ಮ ಪರಿಶೀಲನೆಯ ಇತಿಹಾಸ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲೇ ಇರುತ್ತದೆ. ನಾವು ಎಂದಿಗೂ OTP, PIN, ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ವಿವರ ಕೇಳುವುದಿಲ್ಲ."],
      actions: [{ kind: "go", path: "/about", label: "StaySafe ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ" }],
      words: ["ಉಚಿತ", "ಫ್ರೀ", "ಸುರಕ್ಷಿತ", "ಮಾಹಿತಿ"],
    },
  ],
  tcy: [
    {
      id: "lost_money", q: "ಎನ್ನ ದುಡ್ಡು ಪೋಂಡು ಅತ್ತಂಡ OTP ಪಂಡೆ",
      a: ["ಬೇಗ ಮಲ್ಪುಲೆ, ಸುರುತ ಒಂಜಿ ಗಂಟೆ ಮಸ್ತ್ ಮುಖ್ಯ.",
        "1. ಇತ್ತೆನೇ 1930 (ರಾಷ್ಟ್ರೀಯ ಸೈಬರ್ ಕ್ರೈಂ ಸಹಾಯವಾಣಿ) ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ, ಅತ್ತಂಡ cybercrime.gov.in ಡ್ ದೂರು ಕೊರ್ಲೆ.",
        "2. ಕಾರ್ಡ್ ಅತ್ತಂಡ ಬ್ಯಾಂಕ್ ಆ್ಯಪ್‌ಡ್ ಇತ್ತಿನ ನಂಬರ್‌ಗ್ ಕಾಲ್ ಮಲ್ತ್‌ದ್, ಕಾರ್ಡ್, UPI ಬೊಕ್ಕ ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ ನಿಲ್ಲಾವರೆ ಪನ್ಲೆ.",
        "3. ಪಂಡಿನ ಪಾಸ್‌ವರ್ಡ್ ಬೊಕ್ಕ PIN ಬದಲ್ ಮಲ್ಪುಲೆ. OTP ಏರೆಗ್‌ಲಾ ಪನೊಡ್ಚಿ, 'ಬ್ಯಾಂಕ್ ಸಿಬ್ಬಂದಿ'ಗ್‌ಲಾ.",
        "4. ಮೆಸೇಜ್, ನಂಬರ್ ಬೊಕ್ಕ ಪಾವತಿದ ವಿವರೊಲೆನ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ದೀವೊಲೆ. ಪೊಲೀಸೆರೆಗ್ ಸಹಾಯ ಆಪುಂಡು."],
      actions: [{ kind: "go", path: "/incident", label: "ಒಂಜೊಂಜಿ ಹಂತದ ಸಹಾಯ" }],
      words: ["ದುಡ್ಡು", "ಪೋಂಡು", "ಮೋಸ", "ವಂಚನೆ", "ಓಟಿಪಿ"],
    },
    {
      id: "check_msg", q: "ಈ ಮೆಸೇಜ್, ಕಾಲ್ ಅತ್ತಂಡ ಲಿಂಕ್ ಮೋಸನಾ?",
      a: ["ಮುಲ್ಪನೇ ಕೆಲವು ಸೆಕೆಂಡ್‌ಡ್ ಪರಿಶೀಲನೆ ಮಲ್ಪೊಲಿ.",
        "'ಮೆಸೇಜ್ ಪರಿಶೀಲನೆ' ಡ್ ಮೆಸೇಜ್ ಪೇಸ್ಟ್ ಮಲ್ಪುಲೆ ಅತ್ತಂಡ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಪಾಡ್ಲೆ. ವೆಬ್ ವಿಳಾಸೊಗು 'ಲಿಂಕ್ ಪರಿಶೀಲನೆ' ಬಳಸಲೆ.",
        "ಮೋಸದ ಸಾಮಾನ್ಯ ಲಕ್ಷಣೊಲು: ಅವಸರ ('ಇನಿಯೇ', '2 ಗಂಟೆದುಲಾಯಿ'), ಬೆದರಿಕೆ (ಖಾತೆ ಬ್ಲಾಕ್, ಬಂಧನ), OTP, PIN ಅತ್ತಂಡ ದುಡ್ಡು ಕೇನುನ, ಅಧಿಕೃತ ಅತ್ತಿನ ವೆಬ್‌ಸೈಟ್ ಲಿಂಕ್‌ಲು."],
      actions: [{ kind: "go", path: "/scan-message", label: "ಮೆಸೇಜ್ ಪರಿಶೀಲನೆ" }, { kind: "go", path: "/scan-url", label: "ಲಿಂಕ್ ಪರಿಶೀಲನೆ" }],
      words: ["ಮೆಸೇಜ್", "ಕಾಲ್", "ಲಿಂಕ್", "ನಿಜನಾ", "ನಕಲಿ", "ಸಂಶಯ"],
    },
    {
      id: "clicked", q: "ಯಾನ್ ಲಿಂಕ್ ತೆರೆಯೆ ಅತ್ತಂಡ ಆ್ಯಪ್ ಇನ್‌ಸ್ಟಾಲ್ ಮಲ್ತೆ",
      a: ["ಗಾಬರಿ ಆವೊಡ್ಚಿ. ಇತ್ತೆನೇ ಉಂದೆನ್ ಮಲ್ಪುಲೆ:",
        "1. ಆ ಪುಟೊಡು ಪಾಸ್‌ವರ್ಡ್, PIN ಅತ್ತಂಡ ಕಾರ್ಡ್ ವಿವರ ಪಾಡ್ದಿತ್ತರ್ಂಡ, ಅವೆನ್ ಬದಲ್ ಮಲ್ತ್‌ದ್ ಬ್ಯಾಂಕ್‌ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ.",
        "2. ಅಕುಲು ಪಂಡಿನ ಆ್ಯಪ್‌ನ್ ದೆತ್ತ್ ಪಾಡ್ಲೆ (AnyDesk ಲೆಕ್ಕೊತ್ತ ಸ್ಕ್ರೀನ್ ಶೇರ್ ಆ್ಯಪ್‌ಲಾ).",
        "3. ಫೋನ್ ವಿಚಿತ್ರವಾದ್ ನಡತೊಂದುಂಡ ಕೊಂಚ ಪೊರ್ತು ಮೊಬೈಲ್ ಡೇಟಾ ಅತ್ತಂಡ Wi-Fi ಆಫ್ ಮಲ್ಪುಲೆ.",
        "4. ದುಡ್ಡು ಪೋದಿತ್ತುಂಡ ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ."],
      actions: [{ kind: "go", path: "/incident", label: "ಇತ್ತೆ ದಾದ ಮಲ್ಪೊಡು" }, { kind: "go", path: "/scan-url", label: "ಆ ಲಿಂಕ್ ಪರಿಶೀಲನೆ" }],
      words: ["ಕ್ಲಿಕ್", "ತೆರೆಯೆ", "ಇನ್‌ಸ್ಟಾಲ್", "ಆ್ಯಪ್", "ಡೌನ್‌ಲೋಡ್"],
    },
    {
      id: "report", q: "ಮೋಸದ ಬಗ್ಗೆ ದೂರು ಎಂಚ ಕೊರೊಡು?",
      a: ["ದುಡ್ಡು ಪೋದಿತ್ತುಂಡ: 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ ಅತ್ತಂಡ cybercrime.gov.in ಡ್ ದೂರು ಕೊರ್ಲೆ.",
        "ಮೋಸದ ಕಾಲ್ ಅತ್ತಂಡ SMS (ದುಡ್ಡು ಪೋಯಿಜಿ): ಸಂಚಾರ್ ಸಾಥಿದ 'ಚಕ್ಷು' ಡ್ ತಿಳಿಪಾಲೆ (sancharsaathi.gov.in).",
        "ಸ್ಪ್ಯಾಮ್ SMS: ಅವೆನ್ 1909 ಗ್ ಫಾರ್ವರ್ಡ್ ಮಲ್ಪುಲೆ.",
        "ಮೆಸೇಜ್ ಬ್ಯಾಂಕ್ ಪುದರ್‌ಡ್ ಇತ್ತುಂಡ ಬ್ಯಾಂಕ್‌ಗ್‌ಲಾ ತಿಳಿಪಾಲೆ."],
      words: ["ದೂರು", "ರಿಪೋರ್ಟ್", "ಪೊಲೀಸ್"],
    },
    {
      id: "digital_arrest", q: "ಪೊಲೀಸ್, CBI ಅತ್ತಂಡ ಕೊರಿಯರ್ ಕಾಲ್ ಯಾನ್ ತೊಂದರೆಡ್ ಉಲ್ಲೆ ಪನ್ಪುಂಡು",
      a: ["ಉಂದು ಗೊತ್ತಿತ್ತಿನ ಮೋಸ. 'ಡಿಜಿಟಲ್ ಅರೆಸ್ಟ್' ಪನ್ಪಿನವು ಇಜ್ಜಿ.",
        "ನಿಜವಾಯಿನ ಪೊಲೀಸ್, CBI, ಕಸ್ಟಮ್ಸ್ ಅತ್ತಂಡ ಕೊರಿಯರ್ ಕಂಪೆನಿ ವೀಡಿಯೊ ಕಾಲ್‌ಡೇ ಉಪ್ಪೆರೆ ಅತ್ತಂಡ 'ಪುದರ್ ಸರಿ ಮಲ್ಪೆರೆ' ದುಡ್ಡು ಕೇನುಜಿ.",
        "ಕಾಲ್ ಕಡಿಲೆ. ದುಡ್ಡು ಕೊರೊಡ್ಚಿ, ಆಧಾರ್ ಅತ್ತಂಡ ಬ್ಯಾಂಕ್ ವಿವರ ಪನೊಡ್ಚಿ, ಅಕುಲು ಕಡಪುಡಿನ ಆ್ಯಪ್ ಇನ್‌ಸ್ಟಾಲ್ ಮಲ್ಪೊಡ್ಚಿ.",
        "ಇಲ್ಲಡ್ ತಿಳಿಪಾಲೆ, ನಂಬರ್‌ನ್ ಸಂಚಾರ್ ಸಾಥಿಡ್ ದೂರು ಕೊರ್ಲೆ. ದುಡ್ಡು ಕೊರ್ತಿತ್ತುಂಡ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ."],
      words: ["ಬಂಧನ", "ಅರೆಸ್ಟ್", "ಪೊಲೀಸ್ ಕಾಲ್", "ಕೊರಿಯರ್"],
    },
    {
      id: "job_invest", q: "ಬೇಲೆ, ಟಾಸ್ಕ್ ಅತ್ತಂಡ ಹೂಡಿಕೆದ ಆಫರ್: ನಿಜನಾ?",
      a: ["ಮಸ್ತ್ ಜಾಗ್ರತೆಡ್ ಇಪ್ಪುಲೆ. ನಿಜವಾಯಿನ ಬೇಲೆಗ್ ಸುರುಕು ದುಡ್ಡು ಕೊರೊಡ್ಚಿ.",
        "'ವೀಡಿಯೊ ಲೈಕ್ ಮಲ್ತ್‌ದ್ ಸಂಪಾದನೆ', 'ಹೋಟೆಲ್ ರೇಟಿಂಗ್', Telegram ಟಾಸ್ಕ್ ಬೊಕ್ಕ 'ಖಚಿತ ರಡ್ಡ್ ಪಟ್ಟು ಲಾಭ' ಸಾಮಾನ್ಯ ಮೋಸೊಲು. ಸುರುಕು ಎಲ್ಯ ದುಡ್ಡು ಕೊರ್ದು, ಬುಕ್ಕ ಮಲ್ಲ ಮೊತ್ತ ಕಟ್ಟೆರೆ ಪನ್ಪೆರ್.",
        "ದುಡ್ಡು ದೆಪ್ಪೆರೆ 'ನೋಂದಣಿ', 'ಅನ್‌ಲಾಕ್' ಅತ್ತಂಡ 'ತೆರಿಗೆ' ಶುಲ್ಕ ಏಪಲಾ ಕಟ್ಟೊಡ್ಚಿ."],
      actions: [{ kind: "go", path: "/scam-library", label: "ಈ ಮೋಸೊಲೆನ ಬಗ್ಗೆ ಓದುಲೆ" }],
      words: ["ಬೇಲೆ", "ಸಂಪಾದನೆ", "ಟಾಸ್ಕ್", "ಹೂಡಿಕೆ", "ಟ್ರೇಡಿಂಗ್", "ಲಾಭ"],
    },
    {
      id: "hacked", q: "ಎನ್ನ WhatsApp, Instagram ಅತ್ತಂಡ ಇಮೇಲ್ ಹ್ಯಾಕ್ ಆತ್ಂಡ್",
      a: ["1. ಆ್ಯಪ್ ಅತ್ತಂಡ ವೆಬ್‌ಸೈಟ್‌ಡ್ 'ಪಾಸ್‌ವರ್ಡ್ ಮದತ್ತ್‌ಂಡ' ಬಳಸ್‌ದ್ ಖಾತೆ ಪಿರ ದೆತೊನ್ಲೆ, ಬುಕ್ಕ ಪೊಸ ಗಟ್ಟಿ ಪಾಸ್‌ವರ್ಡ್ ದೀಲೆ.",
        "2. ಟೂ-ಸ್ಟೆಪ್ ವೆರಿಫಿಕೇಶನ್ ಆನ್ ಮಲ್ಪುಲೆ (WhatsApp: ಸೆಟ್ಟಿಂಗ್ಸ್, ಅಕೌಂಟ್, ಟೂ-ಸ್ಟೆಪ್ ವೆರಿಫಿಕೇಶನ್).",
        "3. 'ಈರೆನ' ಪುದರ್‌ಡ್ ದುಡ್ಡು ಅತ್ತಂಡ ಕೋಡ್ ಕಡಪುಡೊಡ್ಚಿ ಪಂದ್ ಸ್ನೇಹಿತೆರೆಗ್ ತಿಳಿಪಾಲೆ.",
        "4. 'ಪಾಸ್‌ವರ್ಡ್ ಪರಿಶೀಲನೆ' ಡ್ ಈರೆನ ಇಮೇಲ್ ಡೇಟಾ ಸೋರಿಕೆಡ್ ಉಂಡಾ ತೂಲೆ."],
      actions: [{ kind: "go", path: "/check-password", label: "ಪಾಸ್‌ವರ್ಡ್ ಬೊಕ್ಕ ಇಮೇಲ್ ಪರಿಶೀಲನೆ" }],
      words: ["ಹ್ಯಾಕ್", "ಖಾತೆ", "ಲಾಗಿನ್"],
    },
    {
      id: "about", q: "StaySafe ಉಚಿತನಾ? ಎನ್ನ ಮಾಹಿತಿ ಸುರಕ್ಷಿತನಾ?",
      a: ["ಅಂದ್, StaySafe ಪೂರ್ತಿ ಉಚಿತ, ಸೈನ್-ಅಪ್ ಬೋಡಾಂದ್.",
        "ಈರೆನ ಪರಿಶೀಲನೆದ ಇತಿಹಾಸ ಈರೆನ ಫೋನ್‌ಡೇ ಉಪ್ಪುಂಡು. ಎಂಕುಲು ಏಪಲಾ OTP, PIN, ಪಾಸ್‌ವರ್ಡ್ ಅತ್ತಂಡ ಬ್ಯಾಂಕ್ ವಿವರ ಕೇನುಜ."],
      actions: [{ kind: "go", path: "/about", label: "StaySafe ಎಂಚ ಬೇಲೆ ಮಲ್ಪುಂಡು" }],
      words: ["ಉಚಿತ", "ಫ್ರೀ", "ಸುರಕ್ಷಿತ", "ಮಾಹಿತಿ"],
    },
  ],
};

export const HELP_TEXTS: Record<Lang, HelpTexts> = {
  en: {
    title: "Ask StaySafe AI", subtitle: "Answers any time, in your language",
    hello: "Hi! Tell me what happened, in any language. I'll help you right away.",
    pick: "Type below, or tap a common question.",
    placeholder: "Type your problem here...",
    send: "Ask",
    noMatch: "I'm not sure I understood. Here are the things I can help with, or you can talk to a person.",
    linkSeen: "I see a web address. Let's check if it's safe.",
    messageSeen: "That looks like a message you received. Let's check it for scam signs.",
    checkThisLink: "Check this link now", checkThisMessage: "Check this message now",
    person: "Talk to a person",
    personOnline: "Someone from our team is online now.",
    personOffline: "Our team isn't online right now. Leave a message with your email and we'll reply as soon as we're back. If you lost money, call 1930 now, don't wait for us.",
    personNotReady: "Messages to our team can't be sent from here right now. Please try again a little later. If you lost money, call 1930 now.",
    more: "Other questions", close: "Close",
    never: "We will never ask for your OTP, PIN, password or bank details.",
    urgent: "Lost money? Call 1930 now",
    formIntro: "I'll pass your message to a real person from the StaySafe team. Please be patient: they reply when they're free, which may take a few hours or longer, and we can't promise a time. If you lost money, don't wait for us, call 1930 now.",
    chatNow: "Chat live now",
    writeToUs: "Write to us",
    formTitle: "Write to the StaySafe team",
    formName: "Your name (optional)",
    formEmail: "Email",
    formPhone: "WhatsApp number",
    formEither: "Give at least one, so we can reply to you.",
    formLost: "Did you lose money?",
    lostYes: "Yes",
    lostNo: "No",
    lostUnsure: "Not sure",
    formMessage: "What happened?",
    formMessagePh: "Tell us in your own words, in any language.",
    formSend: "Send message",
    formSending: "Sending...",
    formBack: "Back",
    sent: "Your message has been passed to a real person. Your reference is {ref}. They'll reply by email or WhatsApp when they're free. We can't promise when, but you won't be forgotten.",
    sentUrgent: "Since money was lost, please also call 1930 right now. The first hours matter most.",
    aiLabel: "This is StaySafe AI Assistant's answer, not a person's. It can make mistakes.",
    aiName: "StaySafe AI Assistant",
    typing: "Thinking...",
    actIncident: "Recovery steps",
    actCheckMessage: "Check a message",
    actCheckLink: "Check a link",
    actPassword: "Check my password and email",
    actLibrary: "Learn about scams",
    stillNeed: "Still need a person?",
    writeTeam: "Write to our team",
    langAsk: "Which language would you like me to answer in?",
    commonTitle: "Common questions",
  },
  hi: {
    title: "StaySafe AI से पूछें", subtitle: "कभी भी, आपकी भाषा में जवाब",
    hello: "नमस्ते! किसी भी भाषा में बताइए क्या हुआ। मैं तुरंत मदद करूँगा।",
    pick: "नीचे लिखें, या कोई आम सवाल चुनें।",
    placeholder: "अपनी समस्या यहाँ लिखें...",
    send: "पूछें",
    noMatch: "मैं ठीक से समझ नहीं पाया। इनमें से किसी में मदद कर सकता हूँ, या आप किसी व्यक्ति से बात कर सकते हैं।",
    linkSeen: "इसमें एक वेब पता है। चलिए देखते हैं कि यह सुरक्षित है या नहीं।",
    messageSeen: "यह आपको मिला हुआ मैसेज लगता है। चलिए इसमें धोखे के संकेत देखते हैं।",
    checkThisLink: "यह लिंक अभी जाँचें", checkThisMessage: "यह मैसेज अभी जाँचें",
    person: "किसी व्यक्ति से बात करें",
    personOnline: "हमारी टीम का कोई सदस्य अभी ऑनलाइन है।",
    personOffline: "हमारी टीम अभी ऑनलाइन नहीं है। अपने ईमेल के साथ मैसेज छोड़ दें, हम लौटते ही जवाब देंगे। पैसे कटे हों तो हमारा इंतज़ार न करें, अभी 1930 पर कॉल करें।",
    personNotReady: "अभी यहाँ से हमारी टीम को मैसेज नहीं भेजा जा सकता। कृपया थोड़ी देर बाद कोशिश करें। पैसे कटे हों तो अभी 1930 पर कॉल करें।",
    more: "दूसरे सवाल", close: "बंद करें",
    never: "हम कभी आपका OTP, PIN, पासवर्ड या बैंक की जानकारी नहीं माँगेंगे।",
    urgent: "पैसे कटे? अभी 1930 पर कॉल करें",
    formIntro: "मैं आपका मैसेज StaySafe टीम के एक असली व्यक्ति तक पहुँचा दूँगा। कृपया धैर्य रखें: वे खाली होने पर जवाब देते हैं, इसमें कुछ घंटे या ज़्यादा लग सकते हैं, और हम समय का वादा नहीं कर सकते। पैसे कटे हों तो हमारा इंतज़ार न करें, अभी 1930 पर कॉल करें।",
    chatNow: "अभी लाइव चैट करें",
    writeToUs: "हमें लिखें",
    formTitle: "StaySafe टीम को लिखें",
    formName: "आपका नाम (ज़रूरी नहीं)",
    formEmail: "ईमेल",
    formPhone: "WhatsApp नंबर",
    formEither: "कम से कम एक दें, ताकि हम आपको जवाब दे सकें।",
    formLost: "क्या आपके पैसे कटे?",
    lostYes: "हाँ",
    lostNo: "नहीं",
    lostUnsure: "पक्का नहीं",
    formMessage: "क्या हुआ?",
    formMessagePh: "अपने शब्दों में, किसी भी भाषा में बताएँ।",
    formSend: "मैसेज भेजें",
    formSending: "भेज रहे हैं...",
    formBack: "वापस",
    sent: "आपका मैसेज एक असली व्यक्ति तक पहुँचा दिया गया है। आपका रेफ़रेंस नंबर {ref} है। वे खाली होने पर ईमेल या WhatsApp पर जवाब देंगे। समय का वादा नहीं कर सकते, पर आपको भुलाया नहीं जाएगा।",
    sentUrgent: "पैसे कटे हैं, इसलिए अभी 1930 पर भी कॉल करें। शुरुआती घंटे सबसे ज़रूरी हैं।",
    aiLabel: "यह StaySafe AI सहायक का जवाब है, किसी व्यक्ति का नहीं। इसमें गलती हो सकती है।",
    aiName: "StaySafe AI सहायक",
    typing: "सोच रहा है...",
    actIncident: "रिकवरी के कदम",
    actCheckMessage: "मैसेज जाँचें",
    actCheckLink: "लिंक जाँचें",
    actPassword: "पासवर्ड और ईमेल जाँचें",
    actLibrary: "धोखों के बारे में जानें",
    stillNeed: "फिर भी किसी व्यक्ति से बात करनी है?",
    writeTeam: "हमारी टीम को लिखें",
    langAsk: "मैं किस भाषा में जवाब दूँ?",
    commonTitle: "आम सवाल",
  },
  kn: {
    title: "StaySafe AI ಕೇಳಿ", subtitle: "ಯಾವಾಗ ಬೇಕಾದರೂ, ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಉತ್ತರ",
    hello: "ನಮಸ್ಕಾರ! ಏನಾಯಿತು ಎಂದು ಯಾವುದೇ ಭಾಷೆಯಲ್ಲಿ ಹೇಳಿ. ನಾನು ತಕ್ಷಣ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
    pick: "ಕೆಳಗೆ ಬರೆಯಿರಿ, ಅಥವಾ ಒಂದು ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆ ಆಯ್ಕೆ ಮಾಡಿ.",
    placeholder: "ನಿಮ್ಮ ಸಮಸ್ಯೆ ಇಲ್ಲಿ ಬರೆಯಿರಿ...",
    send: "ಕೇಳಿ",
    noMatch: "ನನಗೆ ಸರಿಯಾಗಿ ಅರ್ಥವಾಗಲಿಲ್ಲ. ಇವುಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ, ಅಥವಾ ಒಬ್ಬ ವ್ಯಕ್ತಿಯೊಂದಿಗೆ ಮಾತನಾಡಬಹುದು.",
    linkSeen: "ಇದರಲ್ಲಿ ಒಂದು ವೆಬ್ ವಿಳಾಸ ಇದೆ. ಅದು ಸುರಕ್ಷಿತವೇ ನೋಡೋಣ.",
    messageSeen: "ಇದು ನಿಮಗೆ ಬಂದ ಮೆಸೇಜ್‌ನಂತೆ ಕಾಣುತ್ತಿದೆ. ಅದರಲ್ಲಿ ಮೋಸದ ಲಕ್ಷಣಗಳಿವೆಯೇ ನೋಡೋಣ.",
    checkThisLink: "ಈ ಲಿಂಕ್ ಈಗಲೇ ಪರಿಶೀಲಿಸಿ", checkThisMessage: "ಈ ಮೆಸೇಜ್ ಈಗಲೇ ಪರಿಶೀಲಿಸಿ",
    person: "ಒಬ್ಬ ವ್ಯಕ್ತಿಯೊಂದಿಗೆ ಮಾತನಾಡಿ",
    personOnline: "ನಮ್ಮ ತಂಡದವರು ಈಗ ಆನ್‌ಲೈನ್‌ನಲ್ಲಿದ್ದಾರೆ.",
    personOffline: "ನಮ್ಮ ತಂಡ ಈಗ ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಇಲ್ಲ. ನಿಮ್ಮ ಇಮೇಲ್ ಜೊತೆ ಮೆಸೇಜ್ ಬಿಡಿ, ಬಂದ ತಕ್ಷಣ ಉತ್ತರಿಸುತ್ತೇವೆ. ಹಣ ಹೋಗಿದ್ದರೆ ನಮಗಾಗಿ ಕಾಯಬೇಡಿ, ಈಗಲೇ 1930 ಗೆ ಕರೆ ಮಾಡಿ.",
    personNotReady: "ಈಗ ಇಲ್ಲಿಂದ ನಮ್ಮ ತಂಡಕ್ಕೆ ಮೆಸೇಜ್ ಕಳುಹಿಸಲು ಆಗುತ್ತಿಲ್ಲ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ. ಹಣ ಹೋಗಿದ್ದರೆ ಈಗಲೇ 1930 ಗೆ ಕರೆ ಮಾಡಿ.",
    more: "ಬೇರೆ ಪ್ರಶ್ನೆಗಳು", close: "ಮುಚ್ಚಿ",
    never: "ನಾವು ಎಂದಿಗೂ ನಿಮ್ಮ OTP, PIN, ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ವಿವರ ಕೇಳುವುದಿಲ್ಲ.",
    urgent: "ಹಣ ಹೋಯಿತೇ? ಈಗಲೇ 1930 ಗೆ ಕರೆ ಮಾಡಿ",
    formIntro: "ನಿಮ್ಮ ಮೆಸೇಜ್ ಅನ್ನು StaySafe ತಂಡದ ಒಬ್ಬ ನಿಜವಾದ ವ್ಯಕ್ತಿಗೆ ತಲುಪಿಸುತ್ತೇನೆ. ದಯವಿಟ್ಟು ತಾಳ್ಮೆಯಿಂದಿರಿ: ಅವರು ಬಿಡುವಾದಾಗ ಉತ್ತರಿಸುತ್ತಾರೆ, ಕೆಲವು ಗಂಟೆ ಅಥವಾ ಹೆಚ್ಚು ಸಮಯ ಆಗಬಹುದು, ಸಮಯದ ಭರವಸೆ ನೀಡಲಾಗದು. ಹಣ ಹೋಗಿದ್ದರೆ ನಮಗಾಗಿ ಕಾಯಬೇಡಿ, ಈಗಲೇ 1930 ಗೆ ಕರೆ ಮಾಡಿ.",
    chatNow: "ಈಗ ಲೈವ್ ಚಾಟ್ ಮಾಡಿ",
    writeToUs: "ನಮಗೆ ಬರೆಯಿರಿ",
    formTitle: "StaySafe ತಂಡಕ್ಕೆ ಬರೆಯಿರಿ",
    formName: "ನಿಮ್ಮ ಹೆಸರು (ಐಚ್ಛಿಕ)",
    formEmail: "ಇಮೇಲ್",
    formPhone: "WhatsApp ಸಂಖ್ಯೆ",
    formEither: "ನಾವು ಉತ್ತರಿಸಲು ಕನಿಷ್ಠ ಒಂದನ್ನು ನೀಡಿ.",
    formLost: "ನಿಮ್ಮ ಹಣ ಹೋಯಿತೇ?",
    lostYes: "ಹೌದು",
    lostNo: "ಇಲ್ಲ",
    lostUnsure: "ಖಚಿತವಿಲ್ಲ",
    formMessage: "ಏನಾಯಿತು?",
    formMessagePh: "ನಿಮ್ಮ ಮಾತುಗಳಲ್ಲೇ, ಯಾವುದೇ ಭಾಷೆಯಲ್ಲಿ ಹೇಳಿ.",
    formSend: "ಮೆಸೇಜ್ ಕಳುಹಿಸಿ",
    formSending: "ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ...",
    formBack: "ಹಿಂದೆ",
    sent: "ನಿಮ್ಮ ಮೆಸೇಜ್ ಒಬ್ಬ ನಿಜವಾದ ವ್ಯಕ್ತಿಗೆ ತಲುಪಿದೆ. ನಿಮ್ಮ ರೆಫರೆನ್ಸ್ ಸಂಖ್ಯೆ {ref}. ಅವರು ಬಿಡುವಾದಾಗ ಇಮೇಲ್ ಅಥವಾ WhatsApp ನಲ್ಲಿ ಉತ್ತರಿಸುತ್ತಾರೆ. ಯಾವಾಗ ಎಂದು ಹೇಳಲಾಗದು, ಆದರೆ ನಿಮ್ಮನ್ನು ಮರೆಯುವುದಿಲ್ಲ.",
    sentUrgent: "ಹಣ ಹೋಗಿರುವುದರಿಂದ ಈಗಲೇ 1930 ಗೂ ಕರೆ ಮಾಡಿ. ಮೊದಲ ಗಂಟೆಗಳು ತುಂಬಾ ಮುಖ್ಯ.",
    aiLabel: "ಇದು StaySafe AI ಸಹಾಯಕನ ಉತ್ತರ, ವ್ಯಕ್ತಿಯದಲ್ಲ. ಇದರಲ್ಲಿ ತಪ್ಪುಗಳಿರಬಹುದು.",
    aiName: "StaySafe AI ಸಹಾಯಕ",
    typing: "ಯೋಚಿಸುತ್ತಿದೆ...",
    actIncident: "ಚೇತರಿಕೆಯ ಹಂತಗಳು",
    actCheckMessage: "ಮೆಸೇಜ್ ಪರಿಶೀಲಿಸಿ",
    actCheckLink: "ಲಿಂಕ್ ಪರಿಶೀಲಿಸಿ",
    actPassword: "ಪಾಸ್‌ವರ್ಡ್ ಮತ್ತು ಇಮೇಲ್ ಪರಿಶೀಲಿಸಿ",
    actLibrary: "ಮೋಸಗಳ ಬಗ್ಗೆ ತಿಳಿಯಿರಿ",
    stillNeed: "ಇನ್ನೂ ಒಬ್ಬ ವ್ಯಕ್ತಿಯ ಸಹಾಯ ಬೇಕೇ?",
    writeTeam: "ನಮ್ಮ ತಂಡಕ್ಕೆ ಬರೆಯಿರಿ",
    langAsk: "ನಾನು ಯಾವ ಭಾಷೆಯಲ್ಲಿ ಉತ್ತರಿಸಲಿ?",
    commonTitle: "ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆಗಳು",
  },
  tcy: {
    title: "StaySafe AI ಕೇನುಲೆ", subtitle: "ಏಪ ಬೋಡಾಂಡಲಾ, ಈರೆನ ಭಾಷೆಡ್ ಉತ್ತರ",
    hello: "ನಮಸ್ಕಾರ! ದಾದ ಆಂಡ್ ಪಂದ್ ಓವು ಭಾಷೆಡ್‌ಲಾ ಪನ್ಲೆ. ಯಾನ್ ಇತ್ತೆನೇ ಸಹಾಯ ಮಲ್ಪುವೆ.",
    pick: "ತಿರ್ತ್ ಬರೆಲೆ, ಅತ್ತಂಡ ಒಂಜಿ ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆ ಆಯ್ಕೆ ಮಲ್ಪುಲೆ.",
    placeholder: "ಈರೆನ ಸಮಸ್ಯೆ ಮುಲ್ಪ ಬರೆಲೆ...",
    send: "ಕೇನುಲೆ",
    noMatch: "ಎಂಕ್ ಸರಿಯಾದ್ ಅರ್ಥ ಆಯಿಜಿ. ಉಂದೆಟ್ ಸಹಾಯ ಮಲ್ಪುವೆ, ಅತ್ತಂಡ ಒರಿ ವ್ಯಕ್ತಿನೊಟ್ಟುಗು ಪಾತೆರೊಲಿ.",
    linkSeen: "ಉಂದೆಟ್ ಒಂಜಿ ವೆಬ್ ವಿಳಾಸ ಉಂಡು. ಅವು ಸುರಕ್ಷಿತನಾ ತೂಕ.",
    messageSeen: "ಉಂದು ಈರೆಗ್ ಬತ್ತಿನ ಮೆಸೇಜ್ ಲೆಕ್ಕ ತೋಜುಂಡು. ಅಯಿಟ್ ಮೋಸದ ಲಕ್ಷಣೊಲು ಉಂಡಾ ತೂಕ.",
    checkThisLink: "ಈ ಲಿಂಕ್ ಇತ್ತೆನೇ ಪರಿಶೀಲನೆ", checkThisMessage: "ಈ ಮೆಸೇಜ್ ಇತ್ತೆನೇ ಪರಿಶೀಲನೆ",
    person: "ಒರಿ ವ್ಯಕ್ತಿನೊಟ್ಟುಗು ಪಾತೆರ್ಲೆ",
    personOnline: "ಎಂಕ್ಲೆನ ತಂಡದಕುಲು ಇತ್ತೆ ಆನ್‌ಲೈನ್‌ಡ್ ಉಲ್ಲೆರ್.",
    personOffline: "ಎಂಕ್ಲೆನ ತಂಡ ಇತ್ತೆ ಆನ್‌ಲೈನ್‌ಡ್ ಇಜ್ಜಿ. ಈರೆನ ಇಮೇಲ್ ಒಟ್ಟುಗು ಮೆಸೇಜ್ ಬುಡ್ಲೆ, ಬತ್ತಿನ ಕೂಡಲೇ ಉತ್ತರ ಕೊರ್ಪ. ದುಡ್ಡು ಪೋದಿತ್ತುಂಡ ಎಂಕ್ಲೆಗಾದ್ ಕಾಪೊಡ್ಚಿ, ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ.",
    personNotReady: "ಇತ್ತೆ ಮುಲ್ಪಡ್ದ್ ಎಂಕ್ಲೆನ ತಂಡೊಗು ಮೆಸೇಜ್ ಕಡಪುಡೆರೆ ಆವೊಂದಿಜ್ಜಿ. ಕೊಂಚ ಪೊರ್ತು ಕಳೆದ್ ಪ್ರಯತ್ನ ಮಲ್ಪುಲೆ. ದುಡ್ಡು ಪೋದಿತ್ತುಂಡ ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ.",
    more: "ಬೇತೆ ಪ್ರಶ್ನೆಲು", close: "ಮುಚ್ಚುಲೆ",
    never: "ಎಂಕುಲು ಏಪಲಾ ಈರೆನ OTP, PIN, ಪಾಸ್‌ವರ್ಡ್ ಅತ್ತಂಡ ಬ್ಯಾಂಕ್ ವಿವರ ಕೇನುಜ.",
    urgent: "ದುಡ್ಡು ಪೋಂಡಾ? ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ",
    formIntro: "ಈರೆನ ಮೆಸೇಜ್‌ನ್ StaySafe ತಂಡದ ಒರಿ ನಿಜವಾಯಿನ ವ್ಯಕ್ತಿಗ್ ಎತ್ತಾವೆ. ತಾಳ್ಮೆಡ್ ಇಪ್ಪುಲೆ: ಅಕುಲು ಪುರುಸೊತ್ತು ಆನಗ ಉತ್ತರ ಕೊರ್ಪೆರ್, ಕೆಲವು ಗಂಟೆ ಅತ್ತಂಡ ಜಾಸ್ತಿ ಆವೊಲಿ, ಪೊರ್ತುದ ಭರವಸೆ ಕೊರೆರೆ ಆಪುಜಿ. ದುಡ್ಡು ಪೋದಿತ್ತುಂಡ ಎಂಕ್ಲೆಗಾದ್ ಕಾಪೊಡ್ಚಿ, ಇತ್ತೆನೇ 1930 ಗ್ ಕಾಲ್ ಮಲ್ಪುಲೆ.",
    chatNow: "ಇತ್ತೆ ಲೈವ್ ಚಾಟ್ ಮಲ್ಪುಲೆ",
    writeToUs: "ಎಂಕ್ಲೆಗ್ ಬರೆಲೆ",
    formTitle: "StaySafe ತಂಡೊಗು ಬರೆಲೆ",
    formName: "ಈರೆನ ಪುದರ್ (ಬೋಡಾಂಡ ಮಾತ್ರ)",
    formEmail: "ಇಮೇಲ್",
    formPhone: "WhatsApp ನಂಬರ್",
    formEither: "ಎಂಕುಲು ಉತ್ತರ ಕೊರೆರೆ ಕಡಿಮೆಡ್ ಒಂಜಿನ್ ಕೊರ್ಲೆ.",
    formLost: "ಈರೆನ ದುಡ್ಡು ಪೋಂಡಾ?",
    lostYes: "ಅಂದ್",
    lostNo: "ಇಜ್ಜಿ",
    lostUnsure: "ಗೊತ್ತಿಜ್ಜಿ",
    formMessage: "ದಾದ ಆಂಡ್?",
    formMessagePh: "ಈರೆನ ಪಾತೆರೊಡೇ, ಓವು ಭಾಷೆಡ್‌ಲಾ ಪನ್ಲೆ.",
    formSend: "ಮೆಸೇಜ್ ಕಡಪುಡ್ಲೆ",
    formSending: "ಕಡಪುಡೊಂದುಲ್ಲ...",
    formBack: "ಪಿರ",
    sent: "ಈರೆನ ಮೆಸೇಜ್ ಒರಿ ನಿಜವಾಯಿನ ವ್ಯಕ್ತಿಗ್ ಎತ್ತ್‌ದ್ಂಡ್. ಈರೆನ ರೆಫರೆನ್ಸ್ ನಂಬರ್ {ref}. ಅಕುಲು ಪುರುಸೊತ್ತು ಆನಗ ಇಮೇಲ್ ಅತ್ತಂಡ WhatsApp ಡ್ ಉತ್ತರ ಕೊರ್ಪೆರ್. ಏಪ ಪಂದ್ ಪನರೆ ಆಪುಜಿ, ಆಂಡ ಈರೆನ್ ಮದಪುಜ.",
    sentUrgent: "ದುಡ್ಡು ಪೋತಿನೆಡ್ದಾವರ ಇತ್ತೆನೇ 1930 ಗ್‌ಲಾ ಕಾಲ್ ಮಲ್ಪುಲೆ. ಸುರುತ ಗಂಟೆಲು ಮಸ್ತ್ ಮುಖ್ಯ.",
    aiLabel: "ಉಂದು StaySafe AI ಸಹಾಯಕನ ಉತ್ತರ, ವ್ಯಕ್ತಿದ್ ಅತ್ತ್. ಅಯಿಟ್ ತಪ್ಪು ಇಪ್ಪೊಲಿ.",
    aiName: "StaySafe AI ಸಹಾಯಕ",
    typing: "ಯೋಚನೆ ಮಲ್ಪುಂಡು...",
    actIncident: "ಚೇತರಿಕೆದ ಹಂತೊಲು",
    actCheckMessage: "ಮೆಸೇಜ್ ಪರಿಶೀಲನೆ",
    actCheckLink: "ಲಿಂಕ್ ಪರಿಶೀಲನೆ",
    actPassword: "ಪಾಸ್‌ವರ್ಡ್ ಬೊಕ್ಕ ಇಮೇಲ್ ಪರಿಶೀಲನೆ",
    actLibrary: "ಮೋಸೊಲೆನ ಬಗ್ಗೆ ತೆರಿಯೊನ್ಲೆ",
    stillNeed: "ನನಲಾ ಒರಿ ವ್ಯಕ್ತಿನ ಸಹಾಯ ಬೋಡಾ?",
    writeTeam: "ಎಂಕ್ಲೆನ ತಂಡೊಗು ಬರೆಲೆ",
    langAsk: "ಯಾನ್ ಓವು ಭಾಷೆಡ್ ಉತ್ತರ ಕೊರೊಡು?",
    commonTitle: "ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆಲು",
  },
};

export function helpTopics(lang: Lang): HelpTopic[] {
  return TOPICS[lang] ?? TOPICS.en;
}

const LINK_RE = /\b(?:https?:\/\/|www\.)\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|in|net|org|xyz|top|info|co|app|site|online|link|live|shop|club|io|me|cc|ly)\b(?:\/\S*)?/i;

export type BotReply =
  | { kind: "tool"; tools: ToolId[] }
  | { kind: "topic"; topic: HelpTopic; strong: boolean }
  | { kind: "link"; link: string }
  | { kind: "message"; text: string }
  | { kind: "none" };

const SMS_SIGNS = /\b(dear (customer|user|sir|madam)|your (a\/c|account|card|parcel|order|kyc|number|sim)|a\/c|kyc|click (here|on|the)|verify|update (your|now)|otp (is|for)|blocked|suspended|won|winner|prize|lottery|refund|cashback|electricity|disconnect|last date|immediately|call (on|us)|rs\.?\s?\d|inr\s?\d|₹\s?\d|https?:\/\/|www\.)/gi;

/**
 * Does this look like a message someone RECEIVED and pasted (an SMS/WhatsApp), rather than a
 * question they typed? Long questions in any language are NOT treated as pasted messages.
 */
export function looksLikePastedMessage(text: string): boolean {
  if (text.length < 50) return false;
  const signs = new Set((text.match(SMS_SIGNS) || []).map((s) => s.toLowerCase().slice(0, 6))).size;
  const hasLink = LINK_RE.test(text);
  return (hasLink && signs >= 1) || signs >= 3;
}

/** Just a web address (maybe with a few words like "is this safe?"). */
export function justALink(text: string): string | null {
  const link = text.match(LINK_RE)?.[0];
  if (!link) return null;
  return text.replace(link, "").trim().length <= 30 ? link : null;
}

/**
 * Understands what someone typed: a pasted link or message goes to the matching check;
 * otherwise the topic whose words match best (in any of the four languages).
 */
export function understand(input: string, lang: Lang): BotReply {
  const text = input.trim();
  const low = ` ${text.toLowerCase()} `;
  const link = justALink(text);

  const topics = helpTopics(lang);
  let best: HelpTopic | null = null;
  let bestScore = 0;
  for (const tp of topics) {
    const words = [...tp.words, ...(COMMON[tp.id] ?? [])];
    // words from the other languages too, so someone writing Kannada on the English site is understood
    for (const other of Object.values(TOPICS)) {
      const same = other.find((o) => o.id === tp.id);
      if (same && same !== tp) words.push(...same.words);
    }
    let score = 0;
    for (const w of words) if (w && low.includes(w.toLowerCase())) score += w.length > 5 ? 2 : 1;
    if (score > bestScore) { bestScore = score; best = tp; }
  }

  if (link) return { kind: "link", link };
  if (looksLikePastedMessage(text)) return { kind: "message", text };
  const tools = toolRequest(text);
  if (tools) return { kind: "tool", tools };
  if (best && bestScore > 0) return { kind: "topic", topic: best, strong: bestScore >= 4 };
  return { kind: "none" };
}

// ---- "Check this mail / message / link": point to the tool, no AI needed ----
export type ToolId = "message" | "link" | "email" | "qr" | "file" | "password" | "leak" | "network";

export const TOOL_PATHS: Record<ToolId, string> = {
  message: "/scan-message", link: "/scan-url", email: "/scan-email", qr: "/scan-qr", file: "/scan-file",
  password: "/check-password", leak: "/check-password", network: "/check-network",
};

/** Tools that live on a tab of a shared page. */
export const TOOL_TABS: Partial<Record<ToolId, [string, string]>> = {
  leak: ["password", "email"],
  password: ["password", "password"],
};

/** Words for each tool, in English, Hindi, Kannada and Tulu (and typed in English letters). Most specific first. */
const TOOL_WORDS: [ToolId, RegExp][] = [
  ["leak", /(leak|breach|pwned|hacked|exposed).{0,25}(e-?mail|mail|account)|(e-?mail|mail|account).{0,25}(leak|breach|pwned|exposed)|लीक|ಲೀಕ್/],
  ["qr", /\bq\.?r\b|qr ?code|क्यूआर|ಕ್ಯೂ ?ಆರ್/],
  ["password", /pass ?word|passcode|पासवर्ड|ಪಾಸ್‌?ವರ್ಡ್|ಪಾಸ್ ವರ್ಡ್/],
  ["network", /wi-?fi|wireless|hotspot|\bvpn\b|network|internet connection|my connection|नेटवर्क|वाई-?फ़?फाई|ವೈ-?ಫೈ|ನೆಟ್‌?ವರ್ಕ್/],
  ["file", /\bapk\b|\bfiles?\b|\bpdf\b|attachment|document|फ़ाइल|फाइल|ಫೈಲ್|ಎಪಿಕೆ/],
  ["email", /e-?mail|\bmails?\b|gmail|inbox|ईमेल|ई-मेल|मेल|ಇ-?ಮೇಲ್|ಮೇಲ್/],
  ["message", /messages?|\bmsg\b|\bsms\b|whats ?app|\btexts?\b|screen ?shot|मैसेज|मेसेज|संदेश|एसएमएस|व्हाट्सएप|ಮೆಸೇಜ್|ಮೆಸೆಜ್|ಸಂದೇಶ|ಎಸ್‌?ಎಂಎಸ್|ವಾಟ್ಸ್|ಸ್ಕ್ರೀನ್‌?ಶಾಟ್/],
  ["link", /\blinks?\b|\burls?\b|website|web site|\bsite\b|लिंक|वेबसाइट|ಲಿಂಕ್|ವೆಬ್‌?ಸೈಟ್/],
];

/** Asking to check something ("check", "is it safe", "how can I check", Hindi/Kannada/Tulu words too). */
const CHECK_WORDS = /check|chek|chk|scan|verify|test|safe|genuine|legit|fake|real|trust|is (this|it)|jaa?n?ch|dekh|nodi|nodu|parishil|pariks|malpu|maadi|madi|tupu|toole|where|how (can|do|to|i)|kaise|hege|yencha|enchi|जाँच|जांच|चेक|देख|सुरक्षित|असली|नकली|कैसे|कहाँ|ಚೆಕ್|ಪರಿಶೀಲ|ಪರೀಕ್ಷ|ನೋಡ|ಸುರಕ್ಷಿತ|ಸೇಫ್|ನಕಲಿ|ಅಸಲಿ|ಮಲ್ಪು|ತೂಲೆ|ತೂಪು|ಹೇಗೆ|ಎಂಚ|ಎಲ್ಲಿ|ಓಲು/;

/** Signs of a real problem or a question the tool can't answer: those always go to StaySafe AI. */
const NEEDS_AI = /lost|paid|\bpay|sent (the )?money|transfer|debit|deduct|\botp\b|\bpin\b|cvv|clicked|shared|gave|told|police|1930|complain|report|what (should|to|do|now)|\bwhy\b|what does|mean|result|said|says|show|how does|\bwork(s|ing|ed)?\b|error|not (open|work|load)|help me|scared|worried|money|saying|asking|asked|lottery|\bwon\b|prize|\bjob\b|\bkyc\b|\bbank|arrest|parcel|courier|refund|\bloan|rupees|\brs\b|₹|पैसे|पैसा|कट|क्यों|मतलब|डर|ಹಣ|ದುಡ್ಡು|ಕಳೆದ|ಕ್ಲಿಕ್|ಏಕೆ|ಯಾಕೆ|ಅರ್ಥ|ಭಯ|ದಾಯೆ|ಬಾರ್ನ/;

/**
 * A short request to use one of our checks ("check this mail", "ee message check maadi",
 * "is this QR safe?"). Returns the matching tools (at most two) or null. Anything longer,
 * or about something that happened, is left for StaySafe AI.
 */
export function toolRequest(input: string): ToolId[] | null {
  const text = input.trim().toLowerCase();
  if (!text || text.length > 100 || text.split(/\s+/).length > 16) return null;
  if (LINK_RE.test(text)) return null;
  if (NEEDS_AI.test(text)) return null;
  // "was my email leaked?" is a request by itself; everything else needs a "check / is it safe" word
  if (!CHECK_WORDS.test(text) && !TOOL_WORDS[0][1].test(text)) return null;
  const found: ToolId[] = [];
  for (const [id, re] of TOOL_WORDS) {
    if (re.test(text) && !found.includes(id) && !(id === "email" && found.includes("leak"))) found.push(id);
    if (found.length === 2) break;
  }
  return found.length ? found : null;
}

export interface ToolTexts { intro: string; hint: Record<ToolId, string>; askAi: string }

export const TOOL_TEXTS: Record<Lang, ToolTexts> = {
  en: {
    intro: "You can check this yourself right here on StaySafe. Tap the button below to open it.",
    hint: {
      message: "Paste the message there, or upload a screenshot of it.",
      link: "Paste the link there and we'll check it carefully.",
      email: "Paste the email there, or its full details, to see if it's a scam.",
      qr: "Upload a photo of the QR code there, or scan it with your camera.",
      file: "Choose the file there. We check it without opening it.",
      password: "Type the password there to see if it's strong and safe.",
      leak: "Enter your email there to see if it showed up in a data leak.",
      network: "Open it while you're on the Wi-Fi or network you want to check.",
    },
    askAi: "Ask StaySafe AI instead",
  },
  hi: {
    intro: "आप इसे यहीं StaySafe पर खुद जाँच सकते हैं। खोलने के लिए नीचे का बटन दबाएँ।",
    hint: {
      message: "वहाँ मैसेज पेस्ट करें, या उसका स्क्रीनशॉट अपलोड करें।",
      link: "वहाँ लिंक पेस्ट करें, हम उसे ध्यान से जाँचेंगे।",
      email: "वहाँ ईमेल या उसकी पूरी जानकारी पेस्ट करें, ताकि पता चले कि यह धोखा है या नहीं।",
      qr: "वहाँ QR कोड की फ़ोटो अपलोड करें, या कैमरे से स्कैन करें।",
      file: "वहाँ फ़ाइल चुनें। हम उसे खोले बिना जाँचते हैं।",
      password: "वहाँ पासवर्ड लिखें और देखें कि वह मज़बूत और सुरक्षित है या नहीं।",
      leak: "वहाँ अपना ईमेल डालें और देखें कि वह किसी डेटा लीक में आया है या नहीं।",
      network: "जिस वाई-फ़ाई या नेटवर्क को जाँचना है, उस पर रहते हुए इसे खोलें।",
    },
    askAi: "इसके बजाय StaySafe AI से पूछें",
  },
  kn: {
    intro: "ಇದನ್ನು ನೀವೇ ಇಲ್ಲೇ StaySafe ನಲ್ಲಿ ಪರಿಶೀಲಿಸಬಹುದು. ತೆರೆಯಲು ಕೆಳಗಿನ ಬಟನ್ ಒತ್ತಿ.",
    hint: {
      message: "ಅಲ್ಲಿ ಮೆಸೇಜ್ ಅಂಟಿಸಿ, ಅಥವಾ ಅದರ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
      link: "ಅಲ್ಲಿ ಲಿಂಕ್ ಅಂಟಿಸಿ, ನಾವು ಅದನ್ನು ಜಾಗ್ರತೆಯಿಂದ ಪರಿಶೀಲಿಸುತ್ತೇವೆ.",
      email: "ಅದು ಮೋಸವೇ ಎಂದು ತಿಳಿಯಲು ಅಲ್ಲಿ ಇಮೇಲ್ ಅಥವಾ ಅದರ ಪೂರ್ತಿ ವಿವರ ಅಂಟಿಸಿ.",
      qr: "ಅಲ್ಲಿ QR ಕೋಡ್‌ನ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ಅಥವಾ ಕ್ಯಾಮೆರಾದಿಂದ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ.",
      file: "ಅಲ್ಲಿ ಫೈಲ್ ಆರಿಸಿ. ನಾವು ಅದನ್ನು ತೆರೆಯದೆ ಪರಿಶೀಲಿಸುತ್ತೇವೆ.",
      password: "ಪಾಸ್‌ವರ್ಡ್ ಬಲವಾಗಿದೆಯೇ, ಸುರಕ್ಷಿತವೇ ಎಂದು ನೋಡಲು ಅಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ.",
      leak: "ನಿಮ್ಮ ಇಮೇಲ್ ಯಾವುದಾದರೂ ಡೇಟಾ ಲೀಕ್‌ನಲ್ಲಿ ಬಂದಿದೆಯೇ ಎಂದು ನೋಡಲು ಅಲ್ಲಿ ಹಾಕಿ.",
      network: "ಪರಿಶೀಲಿಸಬೇಕಾದ ವೈ-ಫೈ ಅಥವಾ ನೆಟ್‌ವರ್ಕ್‌ನಲ್ಲಿ ಇರುವಾಗಲೇ ಇದನ್ನು ತೆರೆಯಿರಿ.",
    },
    askAi: "ಬದಲಿಗೆ StaySafe AI ಕೇಳಿ",
  },
  tcy: {
    intro: "ಉಂದೆನ್ ಈರ್ ಮಾತ್ರ ಇಡೆಗೇ StaySafe ಡ್ ಪರಿಶೀಲನೆ ಮಲ್ಪೊಲಿ. ದೆಪ್ಪೆರೆ ತಿರ್ತ್‌ದ ಬಟನ್ ಒತ್ತುಲೆ.",
    hint: {
      message: "ಅಲ್ಪ ಮೆಸೇಜ್ ಅಂಟಿಸಲೆ, ಇಜ್ಜಂಡ ಅಯಿತ ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಅಪ್‌ಲೋಡ್ ಮಲ್ಪುಲೆ.",
      link: "ಅಲ್ಪ ಲಿಂಕ್ ಅಂಟಿಸಲೆ, ಎಂಕುಲು ಜಾಗ್ರತೆಡ್ ಪರಿಶೀಲನೆ ಮಲ್ಪುವ.",
      email: "ಅವು ಮೋಸನಾ ಪಂದ್ ತೆರಿಯೆರೆ ಅಲ್ಪ ಇಮೇಲ್ ಇಜ್ಜಂಡ ಅಯಿತ ಪೂರ ವಿವರ ಅಂಟಿಸಲೆ.",
      qr: "ಅಲ್ಪ QR ಕೋಡ್‌ದ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಲ್ಪುಲೆ, ಇಜ್ಜಂಡ ಕ್ಯಾಮೆರಾಡ್ ಸ್ಕ್ಯಾನ್ ಮಲ್ಪುಲೆ.",
      file: "ಅಲ್ಪ ಫೈಲ್ ಆಯ್ಕೆ ಮಲ್ಪುಲೆ. ಎಂಕುಲು ಅವೆನ್ ದೆಪ್ಪಂದೆ ಪರಿಶೀಲನೆ ಮಲ್ಪುವ.",
      password: "ಪಾಸ್‌ವರ್ಡ್ ಗಟ್ಟಿ ಉಂಡಾ, ಸುರಕ್ಷಿತ ಉಂಡಾ ಪಂದ್ ತೂಯೆರೆ ಅಲ್ಪ ಟೈಪ್ ಮಲ್ಪುಲೆ.",
      leak: "ಇರೆನ ಇಮೇಲ್ ಏರೆನಾಂಡಲ ಡೇಟಾ ಲೀಕ್‌ಡ್ ಬೈದ್ಂಡಾ ಪಂದ್ ತೂಯೆರೆ ಅಲ್ಪ ಪಾಡ್ಲೆ.",
      network: "ಪರಿಶೀಲನೆ ಮಲ್ಪೊಡಾಯಿನ ವೈ-ಫೈ ಇಜ್ಜಂಡ ನೆಟ್‌ವರ್ಕ್‌ಡ್ ಉಪ್ಪುನಗನೇ ಉಂದೆನ್ ದೆಪ್ಪುಲೆ.",
    },
    askAi: "ಅವೆತ ಬದಲ್ StaySafe AI ಡ್ ಕೇನುಲೆ",
  },
};

// ---- Hand a link or message over to the check pages ----
const PREFILL_KEY = "staysafe.prefill.v1";

export function setPrefill(kind: "url" | "message", value: string): void {
  try { sessionStorage.setItem(PREFILL_KEY, JSON.stringify({ kind, value: value.slice(0, 5000) })); } catch { /* ignore */ }
}

/** Tell an already open check page about a new link or message. */
export function announcePrefill(): void {
  try { window.dispatchEvent(new Event("staysafe:prefill")); } catch { /* ignore */ }
}

/** The link or message handed over by the helper (read once). */
export function takePrefill(kind: "url" | "message"): string {
  try {
    const raw = sessionStorage.getItem(PREFILL_KEY);
    if (!raw) return "";
    const data = JSON.parse(raw) as { kind: string; value: string };
    if (data.kind !== kind) return "";
    sessionStorage.removeItem(PREFILL_KEY);
    return data.value || "";
  } catch {
    return "";
  }
}

/** For the check pages: fill the box with what the helper handed over (now and later). */
export function usePrefill(kind: "url" | "message", fill: (value: string) => void): void {
  useEffect(() => {
    const apply = () => {
      const v = takePrefill(kind);
      if (v) fill(v);
    };
    apply();
    window.addEventListener("staysafe:prefill", apply);
    return () => window.removeEventListener("staysafe:prefill", apply);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);
}

// ---- Open a page on the right tab (e.g. "was my email leaked" -> the email tab) ----
const TAB_KEY = "staysafe.tab.v1";

export function setStartTab(page: string, tab: string): void {
  try { sessionStorage.setItem(TAB_KEY, JSON.stringify({ page, tab })); } catch { /* ignore */ }
}

/** For pages with tabs: switch to the tab the helper asked for (now and later). */
export function useStartTab(page: string, pick: (tab: string) => void): void {
  useEffect(() => {
    const apply = () => {
      try {
        const raw = sessionStorage.getItem(TAB_KEY);
        if (!raw) return;
        const data = JSON.parse(raw) as { page: string; tab: string };
        if (data.page !== page) return;
        sessionStorage.removeItem(TAB_KEY);
        if (data.tab) pick(data.tab);
      } catch { /* ignore */ }
    };
    apply();
    window.addEventListener("staysafe:prefill", apply);
    return () => window.removeEventListener("staysafe:prefill", apply);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);
}
