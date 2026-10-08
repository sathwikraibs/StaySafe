# TrustLight — Backend

Flask API with one module per checker in `scanners/`.

| Module | What it checks |
|---|---|
| `url_scanner.py` | Link structure, brand look-alikes (e.g. `amaz0n-offers.com`, `sbi-kyc-update.in`), risky words and endings, free-hosting pages, domain age (WHOIS), Google Safe Browsing, VirusTotal |
| `message_scanner.py` | Scam patterns in English, Hinglish, Kannada (also much Tulu), Hindi, Tamil, Telugu, Malayalam and Marathi (KYC, OTP requests, electricity cut-off, courier / digital arrest, task jobs, lottery, investment, remote-access apps, "new number" family scams), plus genuine-message signals. Up to 3 links in the message get the full link check (rules, Google Safe Browsing, VirusTotal). Screenshots are read with Tesseract OCR (English + Kannada + Hindi) first. Messages in other scripts get "couldn't fully check" instead of "safe"; "click here" messages with no visible link get a copy-the-link tip |
| `qr_scanner.py` | Decodes QR codes (zbar, falling back to OpenCV) and checks the link or UPI payment request |
| `file_scanner.py` | File name tricks, what the file *really* is from its contents, macros, programs hidden in ZIPs, risky PDFs, VirusTotal hash lookup |
| `translator.py` | ₹0 translation chain — Google Cloud Translation → free MyMemory → built-in rules. Translates messages to English so the same rules can check them, and into the visitor's language for "What this message says". Each provider pauses itself automatically when its free limit runs out |
| `password_checker.py` | Strength rules (common words, leetspeak, years, sequences) and HIBP k-anonymity breach check |
| `email_analyzer.py` | SPF/DKIM/DMARC, Reply-To mismatch, body text, and links — including links hidden behind "Click here" buttons in the HTML part |
| `network_checker.py` | VPN / proxy / datacenter IP detection |
| `risk_engine.py` | Per-visitor scan history and safety score |
| `incident_wizard.py`, `knowledge_base.py` | Recovery plans and scam library |

## Run locally
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
sudo apt install tesseract-ocr libzbar0   # macOS: brew install tesseract zbar
cp .env.example .env          # optional API keys
python app.py
```

For Kannada/Hindi screenshots locally, also install `tesseract-ocr-kan tesseract-ocr-hin`.

Open http://localhost:5000 — `"ocr": true` and `"qr": true` mean image checks are ready; `"ocr_languages"` shows which scripts screenshots can be read in.

## Deploy (Render, Docker)
Root Directory `staysafe-full/backend`, Runtime `Docker`. The `Dockerfile` installs Tesseract and zbar.

## Test
```bash
python tests/test_scanners.py
```
