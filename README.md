# Document Verification Engine

An OCR-powered document verification system for Indian identity documents — Aadhaar, PAN Card, Passport, and Driving License. Upload a document image or PDF, and the system automatically extracts the important fields, validates them, and stores the results.

Built by **Uttaranchal Coders** — Yana Pandey & Kangpila Sangtam, 2nd Year BTech CSE, Uttaranchal University, Dehradun.

> See [CONTRIBUTIONS.md](./CONTRIBUTIONS.md) for the full project journey, stages, and challenges.

---

## What It Does

- Accepts uploaded documents as images (JPG, PNG, TIFF) or PDFs
- Automatically detects the document type (Aadhaar, PAN, Passport, Driving License)
- Extracts key fields — name, date of birth, document number, address, etc.
- Validates the extracted fields and flags missing ones
- Stores every verification result in MongoDB
- Shows everything in a clean web interface

---

## Tech Stack

### Backend
- **Python + FastAPI** — REST API
- **Tesseract OCR** (via pytesseract) — reads text from document images
- **pypdfium2** — extracts text directly from PDF files (no OCR needed for e-documents)
- **OpenCV** — cleans up images before OCR (denoise, deskew, sharpen)
- **Motor** — async MongoDB driver
- **RapidFuzz** — fuzzy name matching during validation

### Frontend
- **Next.js 14** (App Router) + **React** + **TypeScript**
- **Tailwind CSS** — styling
- Deployed on **Vercel**

### Database
- **MongoDB** — stores document metadata and verification results
- Local development: run via **Docker** (`docker-compose up mongo -d`)
- Production: **MongoDB Atlas** (free tier)

### Deployment
- Frontend → **Vercel**
- Backend → **Railway**
- Database → **MongoDB Atlas**

---

## System Architecture

```
Browser (Next.js frontend)
        │
        │  HTTP multipart upload
        ▼
FastAPI Backend
        │
        ├─ PDF? ──► pypdfium2 direct text extraction
        │           (falls back to image OCR for scanned PDFs)
        │
        ├─ Image? ─► OpenCV preprocessing → Tesseract OCR
        │
        ├─ Document Classification (keyword + regex scoring)
        │
        ├─ Field Extraction (per-document regex extractors)
        │
        ├─ Validation (required fields check + fuzzy name match)
        │
        └─ MongoDB
              ├─► documents collection
              └─► verification_results collection
```

---

## Project Structure

```
document-verification-engine/
├── src/
│   ├── config/             # App settings and constants
│   ├── database/           # MongoDB connection, models, repository
│   ├── processors/
│   │   ├── ocr/            # Tesseract OCR engine
│   │   ├── preprocessing/  # OpenCV image pipeline
│   │   ├── extraction/     # Document classifier + field extractors
│   │   └── pdf_converter.py
│   ├── routes/             # FastAPI route handlers
│   ├── services/           # DocumentService (main pipeline orchestrator)
│   ├── validation/         # DocumentValidator
│   └── main.py
├── frontend/               # Next.js app
├── tests/                  # pytest test suite (54 tests)
├── docker-compose.yml      # MongoDB + API via Docker
├── Dockerfile              # Container build config
└── railway.toml            # Railway deployment config
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Tesseract 5](https://github.com/UB-Mannheim/tesseract/wiki) — Windows: `winget install tesseract-ocr.tesseract`
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — for running MongoDB locally

---

### 1. Clone the repo

```bash
git clone <repository-url>
cd document-verification-engine
```

### 2. Set up the backend

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 3. Configure environment

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

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=doc_verification
```

### 4. Start MongoDB with Docker

```bash
docker-compose up mongo -d   # start in background
docker-compose ps            # verify it's running
```

MongoDB runs at `mongodb://localhost:27017`. Data persists across restarts via a Docker volume.

### 5. Start the backend

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Visit API docs: http://localhost:8000/docs

### 6. Set up and start the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000

---

## Database

MongoDB stores data in two collections:

### `documents`

| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Auto-generated |
| `filename` | string | Saved filename on disk |
| `original_filename` | string | Original name from upload |
| `file_size_bytes` | int | File size in bytes |
| `mime_type` | string | e.g. `image/jpeg`, `application/pdf` |
| `uploaded_at` | datetime | UTC timestamp |

### `verification_results`

| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Auto-generated |
| `document_id` | string | References `documents._id` |
| `document_type` | string | `AADHAAR`, `PAN`, `PASSPORT`, `DRIVING_LICENSE`, `UNKNOWN` |
| `confidence` | float | 0.0 – 1.0 classifier confidence score |
| `extracted_data` | object | All extracted fields |
| `validation` | object | `status`, `missing_fields`, `field_checks` |
| `verified_at` | datetime | UTC timestamp |

### Docker commands

```bash
docker-compose up mongo -d     # start MongoDB
docker-compose stop mongo      # stop MongoDB
docker-compose down -v         # wipe all data and start fresh
docker-compose logs mongo      # view logs
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/verify-document` | Upload and verify a document |
| `GET` | `/api/v1/results` | List recent verification results |
| `GET` | `/api/v1/results/{id}` | Get a single result by ID |

Supported formats: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.pdf`
Max file size: 5 MB

---

## Running Tests

```bash
pytest tests/ -v
```

54 tests covering OCR, field extraction, document classification, validation, and API endpoints.

---

## Production Deployment

### Backend → Railway

1. Connect your GitHub repo on Railway
2. Railway auto-detects the `Dockerfile`
3. Add environment variables in Railway → Variables:
   - `MONGODB_URI` — your Atlas connection string
   - `MONGODB_DB_NAME` — `doc_verification`
   - `CORS_ORIGINS` — your Vercel URL

### Frontend → Vercel

1. Import your GitHub repo on Vercel
2. Set Root Directory to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` — your Railway backend URL

### Database → MongoDB Atlas

1. Create a free M0 cluster on MongoDB Atlas
2. Allow network access from anywhere (`0.0.0.0/0`)
3. Copy the connection string and set it as `MONGODB_URI` on Railway

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` or `production` |
| `UPLOAD_DIR` | `uploads` | Folder for saved uploads |
| `MAX_UPLOAD_SIZE_MB` | `5` | Max upload file size |
| `IMAGE_MAX_WIDTH` | `1600` | Max image width before downscaling |
| `OCR_LANG` | `en` | Tesseract OCR language |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `*` | Allowed frontend origins |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `doc_verification` | MongoDB database name |

---

## Contributors

See [CONTRIBUTIONS.md](./CONTRIBUTIONS.md) for the full story of how this project was built.

| Name | University | Year |
|---|---|---|
| Yana Pandey | Uttaranchal University, Dehradun | 2nd Year BTech CSE |
| Kangpila Sangtam | Uttaranchal University, Dehradun | 2nd Year BTech CSE |

**Team:** Uttaranchal Coders
