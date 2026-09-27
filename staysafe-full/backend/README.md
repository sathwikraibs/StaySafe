# StaySafe — Backend

Flask API with one module per checker in `scanners/`.

| Module | What it checks |
|---|---|
| `url_scanner.py` | Link structure, brand look-alikes (e.g. `amaz0n-offers.com`, `sbi-kyc-update.in`), risky words and endings, free-hosting pages, domain age (WHOIS), Google Safe Browsing, VirusTotal |
| `message_scanner.py` | Scam patterns in English and Hinglish (KYC, OTP requests, electricity cut-off, courier / digital arrest, task jobs, lottery, investment, remote-access apps, "new number" family scams), plus genuine-message signals. Screenshots are read with Tesseract OCR first |
| `qr_scanner.py` | Decodes QR codes (zbar, falling back to OpenCV) and checks the link or UPI payment request |
| `file_scanner.py` | File name tricks, what the file *really* is from its contents, macros, programs hidden in ZIPs, risky PDFs, VirusTotal hash lookup |
| `password_checker.py` | Strength rules (common words, leetspeak, years, sequences) and HIBP k-anonymity breach check |
| `email_analyzer.py` | SPF/DKIM/DMARC, Reply-To mismatch, body text and links |
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

Open http://localhost:5000 — `"ocr": true` and `"qr": true` mean image checks are ready.

## Deploy (Render, Docker)
Root Directory `staysafe-full/backend`, Runtime `Docker`. The `Dockerfile` installs Tesseract and zbar.

## Test
```bash
python tests/test_scanners.py
```
