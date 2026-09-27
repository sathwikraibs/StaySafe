# StaySafe backend — Docker image for Render
# Render's normal Python runtime can't install system programs, but screenshot
# reading needs Tesseract OCR and QR decoding works best with the zbar library.
# This image installs both, so image uploads work in production.
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng libzbar0 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PYTHONUNBUFFERED=1
# One worker keeps the in-memory scan history in a single process; threads handle concurrency.
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 120
