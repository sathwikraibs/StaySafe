// English: result reports, check lists, waiting messages and recovery links.
// Other languages copy this shape in report-hi.ts, report-kn.ts and report-tcy.ts.

export const reportEn = {
  report: {
    checkedCount: "{n} checks",
    riskLow: "Low risk",
    riskMedium: "Medium risk",
    riskHigh: "High risk",
    riskOf: "Risk {score} out of 100",
    checked: "What we checked",
    chipOk: "Fine: {n}",
    chipWarn: "To watch: {n}",
    chipFail: "Problems: {n}",
    statOk: "Fine",
    statWarn: "To watch",
    statFail: "Problems",
    chipSkip: "Not checked: {n}",
    noticed: "What we noticed",
    todo: "What you should do now",
    recovery: "Already clicked, paid or shared something? Get a recovery plan",
    askUs: "Not sure? Ask a real person",
    stamp: {
      safe: "Safe",
      caution: "Careful",
      danger: "Risky",
    },
    slip: "StaySafe report",
    toolName: {
      link: "Link",
      message: "Message",
      qr: "QR code",
      file: "File",
      password: "Password",
      network: "Connection",
      email: "Email",
      number: "Number or UPI ID",
    },
    bill: {
      title: "How we got this score",
      none: "No warning signs, so nothing was added.",
      adjust: "Adjusted after all checks",
      total: "Risk score",
      more: "Show {n} more",
      less: "Show less",
    },
    groups: {
      fail: "Problems",
      warn: "To watch",
      pass: "Fine",
      info: "Good to know",
    },
    alsoKnow: "Also good to know",
    todoHint: "Tick them off as you go",
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
      number: {
        safe: "We found no warning signs. Remember, a number alone can't prove who someone is.",
        caution: "There are warning signs. Don't pay, share an OTP or install anything until you're sure.",
        danger: "This looks like a scam. Stop talking to them, don't pay and don't share any codes.",
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
      number: {
        safe: [
          "Never share an OTP, PIN or card details on a call, whoever it is.",
          "Before paying a UPI ID, check the name your UPI app shows.",
        ],
        caution: [
          "Hang up and call the bank or office yourself, on the number from their official app or website.",
          "Don't install any app or share your screen because a caller asked you to.",
        ],
        danger: [
          "Stop replying and block the number.",
          "Report it on Sanchar Saathi (Chakshu). If you paid or shared details, call 1930 right away.",
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
    rbi: {
      fail: "On RBI's Alert List of unauthorised forex trading platforms",
      failV: "On RBI's Alert List: {value}",
    },
    num_reputation: {
      pass: "No recent fraud or spam reports for this number",
      fail: "Recently linked to fraud or spam calls",
    },
    otx: {
      pass: "No reports from security researchers",
      warn: "Reported by security researchers",
      warnV: "Reported by security researchers ({value} reports)",
    },
    cfscan: {
      pass: "Cloudflare opened the page in a safe browser and found nothing harmful",
      fail: "Cloudflare found the page harmful",
      failV: "Cloudflare found the page harmful: {value}",
    },
    community: {
      warn: "Reported as a scam by StaySafe users",
      warnV: "Reported as a scam by {value} StaySafe users",
      fail: "Reported as a scam by StaySafe users",
      failV: "Reported as a scam by {value} StaySafe users",
    },
    num_type: {
      pass: "A real official or bank number",
      info: "Checked what kind of number this is",
      warn: "Unusual or foreign number",
      warnV: "Foreign or unusual number: {value}",
    },
    upi_handle: {
      pass: "Known UPI app or bank",
      passV: "UPI app or bank: {value}",
      warn: "Unknown UPI app or bank",
      warnV: "Unknown UPI ending: @{value}",
    },
    upi_words: {
      pass: "No official-sounding words like 'refund' or 'support' in the ID",
      fail: "Pretends to be a refund, support or official ID",
      failV: "Official-sounding word in the ID: {value}",
    },
    upi_person: {
      info: "Belongs to a person (made from a mobile number)",
    },
    num_ask: {
      fail: "They asked for something only scammers ask for",
    },
    num_registry: {
      info: "A number alone can't prove who someone is. Check the government's list below too",
    },
    msg_ai: {
      pass: "An AI review found no scam signs",
      warn: "An AI review thinks it looks suspicious",
      fail: "An AI review thinks it is a scam",
      info: "The AI review wasn't sure",
    },
    urlscan: {
      pass: "No scam pages found in security scans (urlscan.io)",
      fail: "Security scans found scam pages on this website",
    },
    server: {
      pass: "The website's server has no abuse reports",
      warn: "The website's server was reported for attacks",
      warnV: "The website's server was reported for attacks ({value}% confidence)",
    },
    net_exposed: {
      pass: "Nothing risky on your connection is open to the whole internet",
      warn: "Something on your connection is open to the whole internet",
      warnV: "Open to the whole internet: {value}",
    },
    net_abuse: {
      pass: "Your internet address has no abuse reports",
      warn: "Your internet address was reported for abuse",
      warnV: "Your internet address was reported for abuse ({value}% confidence)",
    },
    file_bazaar: {
      fail: "Known malware sample",
      failV: "Known malware sample: {value}",
    },
    file_apk: {
      pass: "The app doesn't ask for risky permissions",
      warn: "The app asks for some risky permissions",
      fail: "The app asks for permissions scam apps use to steal money",
    },
    file_known: {
      pass: "Known genuine software",
      passV: "Known genuine software: {value}",
    },
    pw_crack: {
      pass: "A computer would need years to guess it",
      warn: "A computer could guess it within a month",
      fail: "A computer could guess it within a day",
    },
    feeds: {
      pass: "Not on public lists of scam and malware links",
      warn: "Scam pages on this website were reported recently",
      fail: "On a public list of scam and malware links: {value}",
      skip: "Public scam lists could not be checked this time",
    },
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
    email_sender: {
      warn: "The sender's name and address don't quite match",
      warnV: "The sender's name and address don't quite match: {value}",
      pass: "Sender's address looks normal: {value}",
      fail: "The sender is not who they claim to be: {value}",
      skip: "No sender address given",
    },
    email_auth: {
      info: "Technical sender checks need the full email source (optional)",
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
      "Double-checking with more safety sources.",
      "Taking extra care to get this right.",
    ],
    link: [
      "Reading the web address",
      "Checking the website really exists",
      "Looking for fake bank and brand names",
      "Asking Google's list of dangerous sites",
      "Searching more than a million known scam links",
      "Asking 70+ security companies",
      "Looking at past security scans of this website",
      "Checking RBI's list and reports from other StaySafe users",
      "Opening the page safely for you",
      "Checking how old the website is",
      "Putting your report together",
    ],
    message: [
      "Reading your message",
      "Looking for OTP and PIN requests",
      "Checking for threats and pressure",
      "Looking for fake prizes, jobs and refunds",
      "Checking phone numbers, email addresses and UPI IDs",
      "Checking every link inside",
      "Getting a second opinion",
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
      "Checking it against known malware",
      "Comparing it with security companies' records",
      "Checking any links inside the file",
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
      "Checking the sender's website against scam lists",
      "Looking for scam wording",
      "Checking numbers and UPI IDs inside",
      "Checking every link inside",
      "Putting your report together",
    ],
    number: [
      "Reading the number or ID",
      "Checking what kind of number it is",
      "Checking who they said they are",
      "Checking what they asked for",
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

  siteInfo: {
    title: "Website details",
    addressTitle: "The link",
    ownerTitle: "Who registered it",
    registered: "Registered on",
    ago: "{age} ago",
    registrar: "Registered through",
    owner: "Owner",
    ownerHidden: "Hidden by a privacy service",
    country: "Country",
    updated: "Last changed",
    expires: "Registration ends",
    inTime: "in {age}",
    nameServers: "Name servers",
    noWhois: "The public registration record isn't available for this website.",
    certTitle: "Security certificate (HTTPS licence)",
    certValid: "Valid",
    certInvalid: "Not valid",
    issuer: "Issued by",
    issuedTo: "Issued to",
    validFrom: "Valid from",
    validTo: "Valid until",
    certBroken: "The certificate is broken or not trusted. Don't type anything on this site.",
    noCert: "No security certificate found. Anything you type here is not protected.",
    serverTitle: "Where it's hosted",
    serverIp: "Server address",
    location: "Location",
    company: "Hosting company",
    tlCreated: "Created",
    tlToday: "Today",
    tlEnds: "Ends",
    show: "Show website details",
    hide: "Hide website details",
  },

  emailForm: {
    senderEmail: "Sender's email address",
    senderEmailHint: "Tap the sender's name in your email app to see the full address.",
    senderName: "Sender's name (as shown)",
    senderNamePh: "e.g. SBI Customer Care",
    subject: "Subject",
    subjectPh: "e.g. Your account will be blocked",
    body: "Message",
    bodyPh: "Paste the email text here, including any links",
    replyTo: "Reply-to address (if different)",
    required: "Required",
    optional: "Optional",
    more: "More details (optional)",
    simple: "Fill in the form",
    advanced: "Paste full source (advanced)",
    advancedNote: "The full source also lets us check the technical sender checks (SPF, DKIM, DMARC).",
    badEmail: "Please enter a full email address, like name@example.com",
    cleaned: "We used: {email}",
    movedName: "We moved “{name}” to the sender's name. Now type their email address here.",
  },

  homeX: {
    askTitle: "What happened? Ask StaySafe AI",
    askIntro: "Describe your problem in any language, or paste a message or link you got. You'll get an answer right away.",
    askPlaceholder: "For example: someone called and asked for my OTP...",
    askButton: "Ask",
    checkTitle: "Or check something yourself",
    moreTitle: "More tools",
    chip1: "No sign-up",
    chip2: "Private",
    chip3: "4 languages",
    urgent: "Clicked a scam or lost money?",
    talk: "Talk to us",
    desc: {
      link: "Is this website real or fake?",
      message: "SMS, WhatsApp or a screenshot",
      qr: "Before you scan and pay",
      file: "Attachments and downloads",
      password: "Strong enough? Ever leaked?",
      network: "Is your internet connection safe?",
      email: "Fake senders and phishing",
      number: "Calls, WhatsApp numbers and UPI IDs",
      dashboard: "Your checks and safety score",
      library: "Learn the common tricks",
    },
  },

  helpX: {
    call: "Call 1930",
    report: "Report online",
    chat: "Chat with us",
    urgentShort: "Call 1930 right away. The sooner you report, the better the chance of stopping the money.",
  },

  libraryX: {
    example: "What the message looks like",
    exampleNote: "Made-up example. Real ones change the names and numbers.",
    check: "How to check",
    level3: "Very common now",
    level2: "Common",
    level1: "Seen sometimes",
    report: "Report it",
    reportChakshu: "Report the message",
    lostMoney: "Lost money? Call 1930",
    tryTool: "Got something like this? Check it now",
    count: "{n} scams to know about",
    tipTitle: "The golden rule",
    tip: "If someone rushes you, asks for an OTP or PIN, or asks you to pay to receive money, it's a scam. Stop and check.",
  },

  vt: {
    showLess: "Show fewer",
    names: "Known names",
    pageTitle: "Page title",
    categories: "Listed as",
    websiteScope: "This exact link hasn't been scanned before, so this is the result for the whole website.",
    cleanLink: "No security company flagged this ({total} checked)",
    flaggedLink: "{n} of {total} security companies flagged this link",
    newFile: "New file",
    title: "Checked by 70+ antivirus companies",
    notSeen: "None of the antivirus companies have seen this exact file before. That doesn't make it safe, so only open it if you trust where it came from.",
    queued: "The file was sent for a full scan. It can take a few minutes. Open the full report to see the result.",
    tooBig: "This file is too big to send for a full scan. We checked it with our own tests instead.",
    busy: "The antivirus check is busy right now. Please try again in a minute.",
    open: "See the full report",
    flagged: "{n} of {total} security companies flagged this file",
    clean: "No security company flagged this file ({total} checked)",
    type: "File type",
    firstSeen: "First seen",
    lastScan: "Last scanned",
    submitted: "Times checked",
    engines: "What each company said",
    showAll: "Show all {n}",
    cat: {
      malicious: "Dangerous",
      suspicious: "Suspicious",
      harmless: "Safe",
      undetected: "Nothing found",
    },
    uploadTitle: "Also send the file for a full antivirus scan if it is new",
    uploadNote: "Only do this for files that are not private. Anyone with the report link can see the file.",
  },

  qrCam: {
    noCamera: "We couldn't open the camera. Please allow camera access, or upload a photo of the QR code instead.",
    pointAuto: "Point at the QR code. It reads by itself.",
    point: "Point at the QR code, then tap Take photo",
    close: "Close camera",
    capture: "Take photo",
    open: "Scan with camera",
    openHint: "Point your camera at the QR code",
  },

  incidentX: {
    moreLinks: "{n} more places to get help",
    done: "Done",
    markDone: "Mark as done",
    lostMoney: "Lost money in the last few hours?",
    progress: "{done} of {total} done",
    firstThis: "Do this first",
    allDone: "All steps done. Well done.",
  },

  urlX: {
    cleaned: "We found this link in what you pasted: {url}",
  },

  messageX: {
    senderLabel: "Who sent it?",
    senderPh: "e.g. AX-HDFCBK-S or +91 98765 43210",
    senderHint: "The name or number shown at the top of the message. It helps us spot fake bank and government messages.",
  },

  fileX: {
    linksTitle: "Links inside this file",
    appId: "App ID",
    permissions: "What this app asks to do ({n})",
  },

  leak: {
    title: "Has your email been in a data leak?",
    subtitle: "When a website is hacked, the email addresses on it often leak. Check if yours was one of them.",
    button: "Check my email",
    found: "Found in {n} data leaks",
    notFound: "Not found in any known data leak",
    todo: "Change the password on these websites, and on any other site where you used the same password. Turn on two-step verification where you can.",
    source: "Checked with {source}",
    privacy: "We only get back the names of the leaks, never your leaked data. We don't store your email.",
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
