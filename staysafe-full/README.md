# StaySafe

A digital safety checkup tool for non-technical, first-time internet users.
Checks links, messages, screenshots, QR codes, files, passwords, network
connections, and emails for scam/phishing risk — in plain language.

## Structure

```
staysafe-full/
├── backend/     Flask API — 10 scanner modules, deploy to Render
└── frontend/    React + TypeScript + Tailwind — deploy to Vercel
```

## 1. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in GSB_API_KEY and VT_API_KEY (both optional but recommended)
python app.py
```

Screenshot and QR checks also need two system programs:
`sudo apt install tesseract-ocr libzbar0` (macOS: `brew install tesseract zbar`).

Runs on `http://localhost:5000` by default. Deploy to Render as a **Docker**
web service with Root Directory `staysafe-full/backend` (the included
`Dockerfile` installs Tesseract and zbar). Visit the service URL afterwards —
`"ocr": true` and `"qr": true` confirm image checks will work.

Run the checker tests with `python tests/test_scanners.py`.

## 2. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Point the frontend at your backend by setting the `VITE_API_BASE` environment
variable (in Vercel: Project → Settings → Environment Variables; locally: a
`frontend/.env.local` file):

```
VITE_API_BASE=https://your-actual-backend.onrender.com
```

If it isn't set, the default URL in `frontend/src/config.ts` is used.

Deploy `frontend/` to Vercel — no extra build config needed (Vite is
auto-detected, `vercel.json` is included as a fallback).

## Backend endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/scan-url` | POST | Check a link |
| `/api/scan-message` | POST | Check pasted message text |
| `/api/scan-screenshot` | POST | Check a message screenshot (OCR) |
| `/api/scan-qr` | POST | Check a QR code image |
| `/api/scan-file` | POST | Check a downloaded file |
| `/api/check-password` | POST | Check password strength + breach status |
| `/api/check-network` | GET | Check current connection safety |
| `/api/scan-email` | POST | Check raw email source |
| `/api/dashboard` | GET | Safety score + recent activity (per visitor, via `X-Client-Id` header) |
| `/api/history` | GET | Full scan history (per visitor) |
| `/api/incident-options` | GET | List of "I clicked a scam" scenarios |
| `/api/incident-plan` | POST | Step-by-step recovery plan |
| `/api/scam-library` | GET | Searchable scam knowledge base |
| `/api/scam-library/categories` | GET | Scam category list |

The dashboard is computed in the browser from each visitor's own saved checks,
so it's private per person and survives the free Render server going to sleep.
Uploads are limited to 20 MB.

CORS is enabled on the backend (`flask-cors`) so the Vercel frontend can
call the Render backend across origins.
