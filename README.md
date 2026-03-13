# Document Verification Engine

## Overview

An OCR-powered document verification pipeline for Indian identity documents (Aadhaar, PAN, Passport, Driving License). Extracts structured fields from uploaded images or PDFs, validates them, and stores results in MongoDB.

---

## Tech Stack

### Backend
- **Python + FastAPI** — REST API
- **Tesseract OCR** (via pytesseract) — text extraction from images
- **pypdfium2** — direct text extraction from text-based PDFs (e-Aadhaar, e-PAN, etc.)
- **OpenCV** — image preprocessing (denoise, deskew, binarize)
- **Motor** — async MongoDB driver
- **RapidFuzz** — fuzzy name matching in validation

### Frontend
- **Next.js 14** (App Router) + **React** + **TypeScript**
- **Tailwind CSS** — styling
- Deployed to **Vercel**

### Database
- **MongoDB** — stores uploaded document metadata and verification results
- Run locally via **Docker** (`docker-compose up mongo -d`)
- Deployed via **MongoDB Atlas** (production)

### Deployment
- Frontend → Vercel
- Backend → Render
- Database → MongoDB Atlas

---

## System Architecture

```
Browser (Next.js frontend)
        │
        │  HTTP / multipart upload
        ▼
FastAPI Backend
        │
        ├─ PDF? → pypdfium2 direct text extraction
        │         (falls back to image OCR for scanned PDFs)
        │
        ├─ Image? → OpenCV preprocessing → Tesseract OCR
        │
        ├─ Field Extraction + Document Classification
        │
        ├─ Validation (required fields, fuzzy name match)
        │
        └─ MongoDB  ──► documents collection
                    ──► verification_results collection
```

---

## Project Structure

```
document-verification-engine/
├── src/
│   ├── config/           # Settings (pydantic-settings) + constants
│   ├── database/         # MongoDB connection, repository, models
│   ├── processors/
│   │   ├── ocr/          # Tesseract OCR engine
│   │   ├── preprocessing/# OpenCV image pipeline
│   │   ├── extraction/   # Document classifier + field extractors
│   │   └── pdf_converter.py
│   ├── routes/           # FastAPI route handlers
│   ├── services/         # DocumentService (orchestrates pipeline)
│   ├── validation/       # DocumentValidator
│   └── main.py
├── frontend/             # Next.js app
├── tests/                # pytest test suite (54 tests)
├── docker-compose.yml    # MongoDB + API services
├── Dockerfile
└── render.yaml           # Render deployment config
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Tesseract 5](https://github.com/UB-Mannheim/tesseract/wiki) installed (Windows: `winget install tesseract-ocr.tesseract`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for MongoDB)

---

### 1. Clone and install backend

```bash
git clone <repository-url>
cd document-verification-engine

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
APP_ENV=development

UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=5
IMAGE_MAX_WIDTH=1600
OCR_LANG=en
LOG_LEVEL=INFO

# MongoDB — use Docker URI for local dev, Atlas URI for production
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=doc_verification
```

### 3. Start MongoDB with Docker

```bash
# Start MongoDB in the background
docker-compose up mongo -d

# Verify it's running
docker-compose ps
```

MongoDB will be available at `mongodb://localhost:27017`.
Data is persisted in a Docker volume (`mongo_data`) — it survives container restarts.

### 4. Start the backend

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Successful startup looks like:
```
INFO:     Application startup complete.
```

API docs: http://localhost:8000/docs

### 5. Install and start the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # contains NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000

---

## Database

MongoDB is used with two collections:

### `documents`
Stores metadata for every uploaded file.

| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Auto-generated |
| `filename` | string | Saved filename on disk |
| `original_filename` | string | Original filename from upload |
| `file_size_bytes` | int | File size in bytes |
| `mime_type` | string | e.g. `image/jpeg`, `application/pdf` |
| `uploaded_at` | datetime | UTC timestamp |

### `verification_results`
Stores the full result of each verification.

| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Auto-generated |
| `document_id` | string | References `documents._id` |
| `document_type` | string | `AADHAAR`, `PAN`, `PASSPORT`, `DRIVING_LICENSE`, `UNKNOWN` |
| `confidence` | float | 0.0 – 1.0 classifier confidence |
| `extracted_data` | object | All extracted fields (name, dob, etc.) |
| `validation` | object | `status`, `missing_fields`, `field_checks` |
| `verified_at` | datetime | UTC timestamp |

### Useful Docker commands

```bash
docker-compose up mongo -d      # start MongoDB
docker-compose stop mongo       # stop MongoDB
docker-compose down -v          # stop and delete all data (fresh reset)
docker-compose logs mongo       # view MongoDB logs
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/verify-document` | Upload and verify a document |
| `GET` | `/api/v1/results` | List recent verification results (default 20) |
| `GET` | `/api/v1/results/{id}` | Get a single result by ID |

Supported file types: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.pdf`
Max file size: 5 MB

---

## Running Tests

```bash
pytest tests/ -v
```

54 tests covering OCR pipeline, field extraction, document classification, validation, and API endpoints.

---

## Production Deployment

### Backend → Render
Configured via `render.yaml`. Set these env vars in the Render dashboard:
```
MONGODB_URI=<your MongoDB Atlas connection string>
MONGODB_DB_NAME=doc_verification
CORS_ORIGINS=https://your-app.vercel.app
```

### Frontend → Vercel
Set in Vercel project settings:
```
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

### Database → MongoDB Atlas
1. Create a free M0 cluster at https://www.mongodb.com/atlas
2. Whitelist Render's IPs (or allow all: `0.0.0.0/0` for simplicity)
3. Copy the connection string into `MONGODB_URI`

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` or `production` |
| `UPLOAD_DIR` | `uploads` | Directory for saved uploads |
| `MAX_UPLOAD_SIZE_MB` | `5` | Max allowed upload size |
| `IMAGE_MAX_WIDTH` | `1600` | Max image width before downscaling |
| `OCR_LANG` | `en` | Tesseract language |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `doc_verification` | Database name |
