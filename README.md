# StaySafe

**A digital safety checkup tool for non-technical, first-time internet users.**

StaySafe helps everyday people — especially those unfamiliar with online scams — check whether a link, message, QR code, file, password, network, or email is safe, in plain, non-technical language. Built as a final-year Cyber Security project.

🔗 **Live demo:** [staysafe-beryl.vercel.app](https://staysafe-beryl.vercel.app)

---

## What it does

| Feature | Description |
|---|---|
| 🔗 Link Checker | Scans URLs for phishing/malware risk using structure analysis, domain age, Google Safe Browsing, and VirusTotal |
| 💬 Message Checker | Detects scam patterns (urgency, OTP requests, fake refunds, etc.) in pasted text or screenshots (OCR) |
| 📱 QR Code Checker | Decodes QR codes and checks the destination URL or UPI payment request before you scan |
| 📄 File Checker | Checks file hashes against VirusTotal and flags risky extensions / double-extension disguises |
| 🔒 Password Checker | Rates password strength and checks breach exposure via HIBP's privacy-safe k-anonymity API |
| 🌐 Network Checker | Flags VPN/proxy/datacenter IPs and insecure connections |
| ✉️ Email Checker | Parses SPF/DKIM/DMARC results and sender spoofing from raw email source |
| 📊 Safety Dashboard | A running safety score based on your recent checks |
| 🆘 Incident Wizard | Step-by-step recovery plan for "I think I clicked a scam" |
| 📚 Scam Knowledge Base | Searchable library of common scam patterns (KYC scams, fake refunds, job scams, etc.) |

## Tech stack

- **Frontend:** React + TypeScript + Tailwind CSS, built with Vite → deployed on Vercel
- **Backend:** Python Flask, modular scanner architecture → deployed on Render

## Project structure
