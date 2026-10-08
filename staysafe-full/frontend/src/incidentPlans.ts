// Recovery plans (English). Translations: i18n/content-*.ts "incidents". Kept here so the page opens instantly.
export interface IncidentPlan { id: string; label: string; steps: string[] }

export const INCIDENT_PLANS_EN: IncidentPlan[] = [
  {
    "id": "clicked_link",
    "label": "I clicked a suspicious link",
    "steps": [
      "Don't enter any information if a page asks for login or payment details.",
      "Close the browser tab immediately.",
      "Run a virus scan on your device. No antivirus app? Download a free, trusted one from the links below.",
      "Check your bank, Google (Gmail) and WhatsApp accounts for any recent activity you don't recognise.",
      "Avoid using that device for banking until you've scanned it."
    ]
  },
  {
    "id": "entered_password",
    "label": "I entered my password on a suspicious site",
    "steps": [
      "Change that password immediately using the app or the site's real address (type it yourself, don't click a link).",
      "If you reuse that password anywhere else (especially email), change it there too.",
      "Turn on 2-step verification on the affected account.",
      "Check that account's recent sign-ins (Google/Gmail, Facebook, Instagram and so on) and sign out any phones or laptops you don't recognise.",
      "Monitor the account for a few days for anything unusual."
    ]
  },
  {
    "id": "entered_card_details",
    "label": "I entered my card or bank details",
    "steps": [
      "Call your bank's official number (from the back of your card, not from the message) immediately.",
      "Ask them to block or freeze the card if you think it has been misused.",
      "Check recent transactions and dispute anything you didn't make.",
      "Do not share any OTP that arrives after this, even if someone calls claiming to be your bank.",
      "Turn on transaction alerts if they aren't on already."
    ]
  },
  {
    "id": "shared_otp",
    "label": "I shared an OTP or PIN",
    "steps": [
      "If this was for a payment, check immediately whether money was deducted.",
      "Call your bank's official helpline right now to flag possible fraud.",
      "Change your net banking and UPI app passwords.",
      "If money was lost, report it to India's cyber crime helpline immediately: dial 1930 or visit cybercrime.gov.in. The faster you report, the better the chance of getting it back.",
      "Don't respond to more calls or messages asking for codes. This is a common follow-up scam trick."
    ]
  },
  {
    "id": "installed_app",
    "label": "I installed a suspicious app or APK file",
    "steps": [
      "Turn off Wi-Fi and mobile data on the device so the app can't send anything.",
      "Don't log in to banking or email apps on this device until it's cleaned.",
      "Uninstall the app immediately if the device still lets you.",
      "Check Settings > Apps for unfamiliar 'Device Admin' or 'Accessibility' permissions and revoke them.",
      "Run a mobile security scan (Google Play Protect or a trusted antivirus app).",
      "Change your important passwords from a different, clean device."
    ]
  },
  {
    "id": "gave_remote_access",
    "label": "I gave someone remote access to my device (AnyDesk, TeamViewer, etc.)",
    "steps": [
      "Uninstall the remote-access app immediately.",
      "Turn off Wi-Fi and mobile data to end the session right now.",
      "Restart your device.",
      "Change all important passwords from a different device. Assume anything typed during the session was seen.",
      "Contact your bank if any banking app was open during the session.",
      "Report it to the cyber crime helpline (1930) or cybercrime.gov.in if this involved a 'bank support' or 'refund' call."
    ]
  },
  {
    "id": "money_transferred",
    "label": "Money was already transferred or lost",
    "steps": [
      "Call your bank's fraud helpline immediately to ask them to hold or reverse the transaction.",
      "Report immediately at cybercrime.gov.in or call 1930 (India's national cyber fraud helpline). The first few hours matter most for recovery.",
      "Save all evidence: screenshots of messages, transaction ID, the scammer's number or UPI ID.",
      "File a complaint at your local police station if the portal advises it.",
      "Change the passwords of all your money apps and turn on 2-step verification."
    ]
  },
  {
    "id": "account_accessed",
    "label": "Someone accessed my account without permission",
    "steps": [
      "Change the password immediately from a trusted device.",
      "Sign out of all phones and laptops from the account's security settings (for Google: myaccount.google.com > Security).",
      "Turn on 2-step verification if it isn't on already.",
      "Check that the attacker hasn't changed the account's recovery details (backup email or phone).",
      "Look for anything you didn't do (sent emails, posts, purchases) and report or undo it where possible."
    ]
  }
];
