# TrustLight

[![Tests](https://github.com/sathwikraibs/StaySafe/actions/workflows/tests.yml/badge.svg)](https://github.com/sathwikraibs/StaySafe/actions/workflows/tests.yml)

**A light you can trust. A free scam checker for everyday people in India.**

TrustLight helps everyday people, especially those new to the internet, check whether a link, message, QR code, file, phone number, UPI ID, password or email is safe, in plain language, in English, Hindi, Kannada and Tulu. It is free to use, needs no sign-up, and keeps your check history only on your own device.

🔗 **Use it:** [staysafe-tool.vercel.app](https://staysafe-tool.vercel.app)

- Found a security problem? Please read [SECURITY.md](SECURITY.md) and report it privately.
- Found a bug, a wrong result or a bad translation? [Open an issue](https://github.com/sathwikraibs/StaySafe/issues). See [CONTRIBUTING.md](CONTRIBUTING.md).

## What it does

| Feature | Description |
|---|---|
| 🔗 Link Checker | Scans URLs for phishing/malware risk using structure analysis, domain age, Google Safe Browsing, and VirusTotal |
| 💬 Message Checker | Detects scam patterns (urgency, OTP requests, fake refunds, etc.) in English, Hinglish, Kannada and Hindi: pasted text or screenshots (OCR). Messages in any other language are understood via Google Translation, and every message is explained ("What this message says") in the visitor's language. Explains how to check links hidden behind "Click here" |
| 📱 QR Code Checker | Decodes QR codes and checks the destination URL or UPI payment request before you scan |
| 📄 File Checker | Checks file hashes against VirusTotal and flags risky extensions and double-extension disguises |
| 🔒 Password Checker | Rates password strength and checks breach exposure via HIBP's privacy-safe k-anonymity API |
| 🌐 Network Checker | Flags VPN/proxy/datacenter IPs and insecure connections |
| ✉️ Email Checker | Parses SPF/DKIM/DMARC results and sender spoofing from raw email source |
| 📊 Safety Dashboard | A running safety score based on your recent checks |
| 🆘 Incident Wizard | Step-by-step recovery plan for "I think I clicked a scam", with 1930 helpline and cybercrime.gov.in shortcuts |
| 📞 Number / UPI ID Checker | Checks phone numbers and UPI IDs against known scam patterns and reports |
| 🤖 Ask AI | A safety assistant that answers scam questions in the visitor's language, with "Write to us" as a second option |
| 🌐 Languages | English, हिन्दी (Hindi), ಕನ್ನಡ (Kannada) and ತುಳು (Tulu, beta): the whole site including results, recovery plans and scam library. Change it in Settings |
| 🔒 About & Privacy | Plain-language explanation of what is checked where and what is (not) stored |
| 📚 Scam Knowledge Base | Searchable library of common scam patterns (KYC scams, fake refunds, job scams, etc.) |

## Tech stack

- **Frontend:** React + TypeScript + Tailwind CSS, built with Vite, deployed on Vercel
- **Backend:** Python Flask, modular scanner architecture, deployed on Render with Docker (Tesseract OCR + zbar for images)

## Project structure

    staysafe-full/          (folder name kept from the project's first name, StaySafe)
    ├── backend/          Flask API, see backend/README.md
    │   ├── app.py
    │   ├── requirements.txt
    │   └── scanners/      one module per feature
    └── frontend/         React app, see frontend/README.md
        └── src/
            ├── pages/      one page per feature
            ├── components/
            └── config.ts   backend URL is set here

## Running locally

**Backend:**

    cd staysafe-full/backend
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # optional: add GSB_API_KEY / VT_API_KEY
    # screenshot + QR checks also need: sudo apt install tesseract-ocr libzbar0  (macOS: brew install tesseract zbar)
    python app.py

**Frontend:**

    cd staysafe-full/frontend
    npm install
    npm run dev

To use a local backend, create `frontend/.env.local` with `VITE_API_BASE=http://localhost:5000`.

## Deployment

**Backend → Render (Docker)**

Screenshot reading and QR decoding need system programs (Tesseract OCR, zbar) that Render's plain Python runtime cannot install, so the backend ships with a `Dockerfile`.

1. Render → **New → Web Service** → connect this repo.
2. **Root Directory:** `staysafe-full/backend` · **Runtime/Language:** `Docker` (Render finds the `Dockerfile`).
3. Optional environment variables: `GSB_API_KEY`, `VT_API_KEY`, `TRANSLATE_API_KEY`, `TRANSLATE_DAILY_CHAR_LIMIT` (see `backend/.env.example`).
4. After it deploys, open the service URL. You should see `"ocr": true` and `"qr": true`.

(Render can't switch an existing Python service to Docker from the dashboard, so create a new service and point the frontend at its URL.)

**Frontend → Vercel**

- Root Directory `staysafe-full/frontend`, framework auto-detected as Vite.
- Set the environment variable `VITE_API_BASE` to your Render backend URL (Project → Settings → Environment Variables), then redeploy. Without it, the frontend uses the URL in `src/config.ts`.

## Languages

All website text lives in `frontend/src/i18n/`:

- `en.ts`: English source text; `hi.ts`, `kn.ts`, `tcy.ts`: translations (TypeScript checks that nothing is missing)
- `content-*.ts`: translations of server results, recovery plans and the scam library. Server messages are matched against the English text the backend sends, so **if you change a message in the backend, update the same text in these files**.

To add a language: copy `hi.ts` and `content-hi.ts`, translate, and register it in `i18n/index.tsx` (`LANGUAGES`, `DICTS`, `CONTENT`). The Tulu translation is marked beta, corrections from native speakers are welcome.

## Testing

    cd staysafe-full/backend
    python tests/run_all.py

Runs every backend test offline (outside services are faked, no API keys needed): real-world scam and genuine samples for messages, links, files, passwords, numbers, UPI QR codes and emails, plus translation, security and wrong-section checks. The same tests and a full website build run automatically on GitHub for every change (see the Tests badge above).

## Notes

The verdict comes from deterministic rules and weighted scoring, so every result can be explained point by point. An AI second opinion can add a warning, but it never overrules the rules on its own.

The scam knowledge base is manually curated content, not sourced from an external threat-intel framework such as MITRE ATT&CK, which is enterprise and network-intrusion focused and not suited to consumer scam education.

Password breach checks use k-anonymity, meaning only a hash prefix is sent. The real password never leaves the server.
