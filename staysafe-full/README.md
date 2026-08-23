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

Runs on `http://localhost:5000` by default. Deploy to Render for production
(push `backend/` as its own git repo, set the same env vars in Render's dashboard).

## 2. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Before deploying, open `frontend/src/config.ts` and set `API_BASE` to your
deployed Render backend URL:

```ts
export const API_BASE = "https://your-actual-backend.onrender.com";
```

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
| `/api/dashboard` | GET | Safety score + recent activity |
| `/api/history` | GET | Full scan history |
| `/api/incident-options` | GET | List of "I clicked a scam" scenarios |
| `/api/incident-plan` | POST | Step-by-step recovery plan |
| `/api/scam-library` | GET | Searchable scam knowledge base |
| `/api/scam-library/categories` | GET | Scam category list |

CORS is enabled on the backend (`flask-cors`) so the Vercel frontend can
call the Render backend across origins.
