FROM python:3.11-slim

# System deps:
#   tesseract-ocr  — OCR engine
#   libgl1         — required by OpenCV
#   libglib2.0-0   — required by OpenCV
#   curl           — Docker healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir PyMuPDF==1.24.14

COPY src/ ./src/

RUN mkdir -p uploads

CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}
