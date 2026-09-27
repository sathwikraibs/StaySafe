// English: result reports, check lists, waiting messages and recovery links.
// Other languages copy this shape in report-hi.ts, report-kn.ts and report-tcy.ts.

export const reportEn = {
  report: {
    riskLow: "Low risk",
    riskMedium: "Medium risk",
    riskHigh: "High risk",
    riskOf: "Risk {score} out of 100",
    checked: "What we checked",
    chipOk: "Fine: {n}",
    chipWarn: "To watch: {n}",
    chipFail: "Problems: {n}",
    chipSkip: "Not checked: {n}",
    noticed: "What we noticed",
    todo: "What you should do now",
    recovery: "Already clicked, paid or shared something? Get a recovery plan",
    askUs: "Not sure? Ask a real person",
    checkedItem: "Checked",
    meaning: {
      link: {
        safe: "We found no warning signs. It is still wise to type important websites yourself.",
        caution: "Some things about this link are unusual. Don't enter passwords, OTPs or card details on it.",
        danger: "This link shows strong signs of a scam or harmful website. Please don't open it.",
      },
      message: {
        safe: "We didn't find common scam tricks in this message.",
        caution: "This message has some warning signs. Don't reply, pay or share anything until you're sure.",
        danger: "This message looks like a scam. Don't reply, don't click and don't pay.",
      },
      qr: {
        safe: "Nothing worrying found in this QR code.",
        caution: "Check this QR code carefully before you scan it with a payment app.",
        danger: "This QR code looks like a trick. Don't scan it with a payment app.",
      },
      file: {
        safe: "Nothing harmful found in this file.",
        caution: "This file has some warning signs. Only open it if you trust the sender.",
        danger: "This file looks harmful. Please don't open it.",
      },
      password: {
        safe: "This is a strong password. Keep it for one account only.",
        caution: "This password could be stronger.",
        danger: "This password is easy to guess or has been leaked. Change it soon.",
      },
      network: {
        safe: "Your connection looks normal and safe.",
        caution: "Something about your connection is unusual. Read the details below.",
        danger: "Your connection looks risky. Avoid banking and payments on it for now.",
      },
      email: {
        safe: "We found no strong warning signs in this email.",
        caution: "This email has some warning signs. Don't click its links or open attachments until you're sure.",
        danger: "This email looks like a scam. Don't click, reply or download anything from it.",
      },
    },
    tips: {
      link: {
        safe: [
          "For banks and payments, type the website name yourself or use the official app.",
          "Check the address bar again before typing a password.",
        ],
        caution: [
          "Don't type passwords, OTPs, card or bank details on this site.",
          "If it claims to be a bank or company, open their official app or website yourself instead.",
          "Ask someone you trust, or chat with us, before you continue.",
        ],
        danger: [
          "Don't open this link. Delete the message that had it.",
          "If you already opened it and typed anything, change that password now.",
          "If you paid or shared an OTP, call 1930 straight away.",
          "Block and report the sender.",
        ],
      },
      message: {
        safe: [
          "Never share OTPs, PINs or passwords, even with people who say they are from your bank.",
          "If a message still feels odd, call the person or company on a number you already know.",
        ],
        caution: [
          "Don't reply or click any link yet.",
          "Contact the company yourself using their official app or the number on your card.",
          "Nobody genuine asks for your OTP, PIN or password.",
        ],
        danger: [
          "Don't reply, don't click and don't call the number in the message.",
          "Block the sender and report it on Sanchar Saathi (Chakshu).",
          "If you already paid or shared an OTP, call 1930 now.",
        ],
      },
      qr: {
        safe: [
          "Before paying, check the name your UPI app shows matches who you want to pay.",
          "Remember: you never scan a QR code to receive money.",
        ],
        caution: [
          "Check the name and amount in your UPI app very carefully before paying.",
          "If someone says scanning will send you money, it's a trick.",
        ],
        danger: [
          "Don't scan this QR code with any payment app.",
          "Scanning a QR and entering your PIN always sends money out of your account.",
          "If you already paid, call 1930 and your bank now.",
        ],
      },
      file: {
        safe: [
          "Only open files from people you know and were expecting a file from.",
          "Keep your phone and computer updated.",
        ],
        caution: [
          "Ask the sender, on a call, if they really sent this file.",
          "Don't enable macros or \"editing\" if a document asks you to.",
        ],
        danger: [
          "Don't open this file. Delete it.",
          "If you already opened it, run a virus scan (see the recovery plan).",
          "Change important passwords from a different, clean device.",
        ],
      },
      password: {
        safe: [
          "Use this password for one account only.",
          "Turn on 2-step verification for extra safety.",
        ],
        caution: [
          "Make it longer: 12 or more characters is best.",
          "Try a phrase of 3 or 4 random words, like Mango-River-Cycle-42.",
        ],
        danger: [
          "Change this password everywhere you use it, starting with email and banking.",
          "Use a different password for every account.",
          "Turn on 2-step verification.",
        ],
      },
      network: {
        safe: [
          "On public Wi-Fi (cafes, stations, hotels), avoid banking and payments.",
          "Keep your phone and browser updated.",
        ],
        caution: [
          "If you didn't turn on a VPN yourself, check which apps are using one.",
          "Avoid banking and payments until you're sure this connection is yours.",
        ],
        danger: [
          "Switch to your own mobile data for anything important.",
          "Don't log in to banking or email on this connection.",
          "Forget this Wi-Fi network in your phone settings.",
        ],
      },
      email: {
        safe: [
          "Even safe-looking emails can be faked, so never share OTPs or passwords by email.",
          "Open your bank or shop account by typing its website yourself.",
        ],
        caution: [
          "Don't click links or open attachments in this email yet.",
          "Contact the company yourself using their official website or app.",
        ],
        danger: [
          "Don't click, reply or download anything from this email.",
          "Mark it as spam or phishing in your email app.",
          "If you entered a password from it, change that password now.",
        ],
      },
    },
    age: {
      days: "{n} days",
      day1: "1 day",
      months: "{n} months",
      month1: "1 month",
      years: "{n} years",
      year1: "1 year",
    },
  },

  checks: {
    // links
    google: {
      pass: "Not on Google's list of dangerous sites",
      fail: "On Google's list of dangerous sites: {value}",
      skip: "Google's danger list could not be checked this time",
    },
    virustotal: {
      pass: "Security companies found nothing bad",
      passV: "{value} security scanners found nothing bad",
      warn: "{value} security companies think it looks suspicious",
      fail: "{value} security companies say it is dangerous",
      info: "Security companies haven't seen this link before",
      skip: "Security companies could not be asked this time",
    },
    exists: {
      pass: "The website exists and is online",
      fail: "This website doesn't exist or has been shut down",
      skip: "Could not confirm the website is online",
    },
    imitation: {
      pass: "Not pretending to be a famous brand or bank",
      fail: "Pretends to be {value}, but is not {value}'s real website",
    },
    page: {
      pass: "The page doesn't ask for passwords or bank details",
      passV: "Page opened safely: “{value}”",
      warn: "The page asks you to type a password",
      fail: "Fake page pretending to be {value}",
      failApk: "Opening it downloads an app straight away",
      failProgram: "Opening it downloads a program straight away",
      skip: "Could not open the page to look inside",
    },
    redirect: {
      pass: "Goes where it says",
      passV: "Goes where it says: {value}",
      warn: "Secretly sends you to another website: {value}",
      skip: "Could not follow the link to see where it ends up",
    },
    age: {
      pass: "Well-known website that has been around for years",
      passV: "Website has been around for {age}",
      warn: "Fairly new website: only {age} old",
      fail: "Brand-new website: only {age} old",
      skip: "Could not find out how old the website is",
    },
    https: {
      pass: "Secure connection (HTTPS)",
      warn: "Not a secure connection (no HTTPS)",
      fail: "Broken security certificate",
    },
    known: {
      pass: "Well-known website: {value}",
      info: "Website name: {value}",
      warn: "Free hosting or link-shortening service: {value}",
    },
    name_tricks: {
      pass: "No tricks in the website name",
      warn: "Tricks found in the website name: {value}",
      fail: "Many tricks found in the website name: {value}",
    },

    // messages (worked out on this page)
    msg_patterns: {
      pass: "No common scam tricks found",
      warn: "Warning signs found: {value}",
      fail: "Warning signs found: {value}",
    },
    msg_links: {
      info: "No links in this message",
      pass: "Links checked: {value}, all look fine",
      fail: "Risky links found: {value}",
    },
    msg_safe: {
      pass: "Has signs of a genuine message",
      info: "No signs of a genuine sender",
    },
    msg_language: {
      info: "Understood with automatic translation",
      warn: "This language could not be fully checked",
    },

    // QR codes
    qr_text: { pass: "Only plain text, no link or payment" },
    upi_note: {
      pass: "Payment note doesn't try to trick you",
      fail: "Payment note pretends you will receive money: “{value}”",
    },
    upi_id: {
      pass: "Valid UPI ID: {value}",
      warn: "Personal phone-number UPI ID: {value}",
      fail: "Not a valid UPI ID",
    },
    upi_name: {
      pass: "Shows who you are paying: {value}",
      warn: "Doesn't show who you are paying",
    },
    upi_amount: {
      info: "No amount filled in. You type the amount yourself",
      infoV: "Amount already filled in: ₹{value}",
      warn: "Large amount already filled in: ₹{value}",
      fail: "The amount is not a valid number",
    },

    // files
    file_vt: {
      pass: "Security companies found nothing bad",
      passV: "{value} security scanners found nothing bad",
      warn: "{value} security companies think it looks suspicious",
      fail: "{value} security companies say this file is dangerous",
      info: "Security companies haven't seen this exact file before",
      skip: "Security companies could not be asked this time",
    },
    file_type: {
      pass: "The file really is what its name says",
      passV: "The file really is: {value}",
      warn: "The name doesn't match what's inside",
      fail: "Disguised file. It is really: {value}",
    },
    file_hidden: {
      pass: "No hidden programs, macros or scripts inside",
      fail: "Hidden risky content found inside",
    },
    file_name: {
      pass: "This kind of file is normally safe to open",
      passV: "{value} files are normally safe to open",
      warn: "{value} files can hide harmful code",
      fail: "{value} files can run programs on your device",
    },

    // passwords
    pw_leaks: {
      pass: "Not found in any known leak",
      fail: "Found in {value} leaked password lists",
      skip: "The leak check was not available this time",
    },
    pw_common: {
      pass: "Not a common password",
      fail: "A very common password that hackers try first",
    },
    pw_length: {
      pass: "Long enough: {value} characters",
      warn: "A bit short: {value} characters (12 or more is better)",
      fail: "Too short: {value} characters",
    },
    pw_variety: {
      pass: "Mixes capitals, small letters, numbers and symbols",
      warn: "Uses {value} of the 4 kinds of characters",
      fail: "Uses only {value} of the 4 kinds of characters",
    },
    pw_patterns: {
      pass: "No easy-to-guess patterns",
      warn: "Has an easy-to-guess pattern",
      fail: "Has several easy-to-guess patterns",
    },

    // connection
    net_lookup: { skip: "Could not look up your connection details" },
    net_vpn: {
      pass: "No VPN or proxy in the way",
      warn: "A VPN or proxy is being used",
    },
    net_hosting: {
      pass: "Normal internet provider: {value}",
      warn: "Connection comes from a data centre: {value}",
    },
    net_type: {
      pass: "Mobile data connection",
      info: "Home, office or public Wi-Fi / broadband",
    },
    net_timezone: {
      pass: "Your connection's location matches your device's time zone",
      warn: "Your connection comes out in a different time zone ({value})",
    },
    net_https: {
      pass: "StaySafe opened securely (HTTPS)",
      warn: "This page did not open securely",
    },
    net_browser: {
      pass: "Your browser is up to date ({value})",
      warn: "Your browser looks out of date ({value}). Please update it",
      info: "Browser: {value}",
    },
    net_speed: {
      info: "Speed estimate: about {value} Mbps",
      warn: "Very slow connection: about {value} Mbps",
    },

    // email
    email_auth: {
      pass: "Sender identity checks passed (SPF, DKIM, DMARC)",
      fail: "Sender identity checks failed",
      skip: "Sender identity could not be checked (the email may be forwarded)",
    },
    email_reply: {
      pass: "Replies go back to the same sender",
      warn: "Replies go to a different address: {value}",
    },
    email_words: {
      pass: "No scam wording found",
      warn: "Scam wording found: {value}",
      fail: "Scam wording found: {value}",
    },
    email_links: {
      info: "No links in this email",
      pass: "Links checked: {value}, all look fine",
      fail: "Risky links found: {value}",
    },
  },

  waiting: {
    title: "Checking it carefully for you",
    wake: "Our free server takes a nap when nobody is using it. We're waking it up now, which can take up to a minute. Please keep this page open.",
    still: [
      "Still working on it. Thanks for waiting.",
      "Almost there.",
      "A careful check takes a few seconds.",
      "We're still here, just a moment more.",
    ],
    link: [
      "Reading the web address",
      "Checking the website really exists",
      "Looking for fake bank and brand names",
      "Asking Google's list of dangerous sites",
      "Asking 70+ security companies",
      "Opening the page safely on our server",
      "Checking how old the website is",
      "Putting your report together",
    ],
    message: [
      "Reading your message",
      "Looking for OTP and PIN requests",
      "Checking for threats and pressure",
      "Looking for fake prizes, jobs and refunds",
      "Checking every link inside",
      "Putting your report together",
    ],
    screenshot: [
      "Uploading your screenshot safely",
      "Reading the words in the picture",
      "Understanding the language",
      "Looking for scam tricks",
      "Checking any links we find",
      "Putting your report together",
    ],
    qr: [
      "Uploading your photo safely",
      "Finding the QR code",
      "Reading what's inside it",
      "Checking where it leads or who gets paid",
      "Putting your report together",
    ],
    file: [
      "Uploading your file safely",
      "Finding out what the file really is",
      "Looking for hidden programs and macros",
      "Comparing it with security companies' records",
      "Putting your report together",
    ],
    password: [
      "Scrambling your password so it stays private",
      "Checking how strong it is",
      "Searching known leaks without sending your password",
      "Putting your report together",
    ],
    network: [
      "Finding your internet address",
      "Checking for VPNs and proxies",
      "Checking your internet provider",
      "Comparing your location and time zone",
      "Checking your browser",
      "Putting your report together",
    ],
    email: [
      "Reading the email",
      "Checking who really sent it",
      "Looking for scam wording",
      "Checking every link inside",
      "Putting your report together",
    ],
    incident: [
      "Finding the right steps for you",
      "Adding helpful links",
      "Almost ready",
    ],
  },

  resources: {
    title: "Helpful links",
    note: "These go to official app stores and websites. Never install apps from links sent by strangers.",
    download: "Download here",
    open: "Open here",
    guide: "See how",
    call: "Call now",
    report: "Report here",
    android: "Android",
    iphone: "iPhone",
    windows: "Windows",
    govt: "Govt. of India",
    free: "Free",
    desc: {
      malwarebytesAndroid: "Free virus scan for Android phones",
      mkavach: "Free security app from C-DAC, Government of India",
      escan: "Free phone safety toolkit recommended by CERT-In",
      malwarebytesWindows: "Free virus scan for Windows computers",
      quickhealBot: "Free virus clean-up tool recommended by CERT-In",
      playProtect: "Run the virus scanner already built into your Android phone",
      googleCheckup: "Check and fix your Google account security in 2 minutes",
      googleDevices: "See every phone and computer signed in, and sign out the ones you don't know",
      googlePassword: "Change your Google account password",
      google2sv: "Turn on 2-step verification for your Google account",
      authenticator: "Free app that gives you login codes",
      hibp: "Check if your email was in a data leak",
      cybercrime: "National Cyber Crime Reporting Portal",
      call1930: "National cyber fraud helpline, open 24 hours",
      chakshu: "Report fraud calls, SMS and WhatsApp messages (Sanchar Saathi)",
      rbiCms: "Complain to RBI if your bank doesn't solve it within 30 days",
      fbHacked: "Recover a hacked Facebook account",
      igHacked: "Recover a hacked Instagram account",
    },
  },

  linkInfo: {
    title: "Website details",
    site: "Website",
    goesTo: "Really goes to",
    pageTitle: "Page title",
    age: "Website age",
    server: "Server address",
  },

  fileInfo: {
    name: "File name",
    really: "What it really is",
    size: "Size",
    fingerprint: "Fingerprint (SHA-256)",
  },

  emailInfo: {
    from: "From",
    replyTo: "Replies go to",
    same: "Same as sender",
    links: "Links inside",
  },

  pwInfo: {
    score: "Strength score: {score} out of 100",
    leakUnknown: "Not checked",
  },

  networkMore: {
    mobile: "Mobile data",
    detailsTitle: "Connection details",
    provider: "Internet provider",
    location: "Approximate location",
    address: "Internet address",
    version: "Address type",
    timezone: "Time zone",
    browser: "Browser",
    netType: "Network type",
    publicWifiTitle: "Using public Wi-Fi?",
    publicWifi: [
      "Avoid banking, UPI and shopping on free Wi-Fi at cafes, stations and hotels.",
      "Check the exact Wi-Fi name with staff. Scammers create look-alike networks.",
      "Turn off auto-connect to open Wi-Fi networks in your phone settings.",
      "Your own mobile data is safer for anything important.",
    ],
    safehopTitle: "Want a deeper Wi-Fi check?",
    safehopText: "SafeHop runs a detailed Wi-Fi and connection scan with a speed test, DNS check and a safety grade.",
    safehopButton: "Open SafeHop for more details",
  },
};

export type ReportDict = typeof reportEn;
