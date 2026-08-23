# StaySafe

**A digital safety checkup tool for non-technical, first-time internet users.**

StaySafe helps everyday people — especially those unfamiliar with online scams — check whether a link, message, QR code, file, password, network, or email is safe, in plain, non-technical language. Built as a final-year Cyber Security project.

🔗 **Live demo:** [staysafe-tool.vercel.app](https://staysafe-tool.vercel.app)

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

    staysafe-full/
    ├── backend/          Flask API — see backend/README.md
    │   ├── app.py
    │   ├── requirements.txt
    │   └── scanners/      one module per feature
    └── frontend/         React app — see frontend/README.md
        └── src/
            ├── pages/      one page per feature
            ├── components/
            └── config.ts   ← backend URL is set here

## Running locally

**Backend:**

    cd staysafe-full/backend
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # optional: add GSB_API_KEY / VT_API_KEY
    python app.py

**Frontend:**

    cd staysafe-full/frontend
    npm install
    npm run dev

Set `API_BASE` in `src/config.ts` to your backend URL before running.

## Deployment

- **Backend → Render:** Root Directory `staysafe-full/backend`, Build Command `pip install -r requirements.txt`, Start Command `gunicorn app:app`
- **Frontend → Vercel:** Root Directory `staysafe-full/frontend`, framework auto-detected as Vite

## Notes

- The risk engine uses deterministic rules and weighted scoring, not AI/ML — this keeps verdicts explainable and auditable, which matters for a security tool.
- The scam knowledge base is manually curated content, not sourced from an external threat-intel framework (e.g. MITRE ATT&CK, which is enterprise/network-intrusion focused and not suited to consumer scam education).
- Password breach checks use k-anonymity (only a hash prefix is sent) — the real password never leaves the server.
