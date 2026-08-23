# StaySafe

A personal digital safety tool for non-technical users — checks links, messages, and screenshots for scam/phishing indicators and gives a simple risk verdict.

## Modules
- **URL Scanner** (`scanners/url_scanner.py`) — structure heuristics, WHOIS age, Google Safe Browsing, VirusTotal
- **Message/Screenshot Scanner** (`scanners/message_scanner.py`) — rule-based scam pattern detection with OCR support

## Setup
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in your API keys
python app.py
```

## API
- `POST /api/scan-url` — `{"url": "..."}`
- `POST /api/scan-message` — `{"text": "..."}`
- `POST /api/scan-screenshot` — multipart form, field `image`
