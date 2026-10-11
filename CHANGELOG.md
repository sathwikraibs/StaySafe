# Changelog

All notable changes to TrustLight are listed here. Versions follow
[Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH. Each release is tagged in git
(for example `v1.0.0`). Small fixes go live between releases and are collected under
"Unreleased" until the next version.

## [Unreleased]

Nothing yet.

## [1.0.0] - 2026-10-11

The first numbered release of TrustLight (previously called StaySafe).

### Checks
- Link, message (text and screenshot), QR code, file, email, phone number and UPI ID checks,
  each with a plain-language verdict and the reasons behind it.
- Password and email leak check that never sends the password itself (k-anonymity).
- Connection check (VPN, proxy and insecure connection signs).
- Each check notices input meant for another check (a link in the email check, a QR code
  uploaded as a message screenshot) and offers to open the right one.

### Help and learning
- "I clicked a scam" recovery plan with the 1930 helpline and cybercrime.gov.in.
- Scam library, safety dashboard and an AI safety assistant.

### Languages
- The whole site in English, Hindi, Kannada and Tulu (beta), including results and recovery plans.
- Messages in other languages, or typed in English letters, are translated before checking.

### Privacy and security
- No sign-up. Check history stays only on the visitor's device.
- Phone numbers, account numbers, OTPs, email addresses and UPI IDs are masked before any
  text is sent to an outside service.
- Strict security headers (Content Security Policy, HSTS), rate limits and input checks.

### Independent checks
- "Checked by others, not just us" on the About & Privacy page: live links to independent
  security checks of the website.
- Automatic code security scan (CodeQL) on every change and every week.

### Security fixes
- Text patterns rewritten so very long or specially built input can no longer slow the server down
  (found by the new code scan).
- The visitor's internet address is now accepted only when it is a real IP address before it is
  used to look up connection details.
- The link certificate check refuses outdated TLS versions.

[Unreleased]: https://github.com/sathwikraibs/StaySafe/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sathwikraibs/StaySafe/releases/tag/v1.0.0
