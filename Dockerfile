FROM python:3.11-slim

# System deps: libgl1 + libglib2.0-0 required by OpenCV; curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN mkdir -p uploads/compressed

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
