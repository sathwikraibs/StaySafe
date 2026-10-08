# TrustLight backend — Docker image for Render
# Render's normal Python runtime can't install system programs, but screenshot
# reading needs Tesseract OCR (with English, Kannada and Hindi language packs) and QR decoding works best with the zbar library.
# This image installs both, so image uploads work in production.
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd tesseract-ocr-kan tesseract-ocr-hin libzbar0 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Open Tulu and Kannada word lists (Wikilangs, MIT): help tell Tulu from Kannada. Optional: the
# build carries on without them. pyarrow is only needed for this step, so it is removed after.
RUN (pip install --no-cache-dir pyarrow && python scripts/fetch_lang_vocab.py; pip uninstall -y pyarrow) || true

ENV PYTHONUNBUFFERED=1
# Tesseract otherwise starts one thread per CPU it *thinks* it has; on Render's small
# shared machine those threads fight each other and reading a screenshot takes minutes.
ENV OMP_THREAD_LIMIT=1
# One worker keeps the in-memory scan history in a single process; threads handle concurrency.
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 8 --timeout 180
