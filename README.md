# Intelligent Document Verification & Upload Optimization Engine

## Overview

This project implements an intelligent document processing pipeline designed to optimize and verify citizen-uploaded identity documents. The system compresses uploaded documents, extracts structured information using OCR, and performs automatic validation to assist government officers in faster verification.

The goal is to reduce upload sizes, automate document analysis, and improve verification efficiency in public service portals.

---

## Problem Statement

Government service portals require citizens to upload documents such as Aadhaar cards, PAN cards, domicile certificates, and income certificates.

Two major issues arise:

- Uploaded files are often very large (5MB+), causing slow uploads and increased storage usage.
- Document verification is usually manual, which is slow and prone to errors.

This system solves these problems by creating an automated pipeline that:

- Compresses documents during upload
- Extracts structured fields using OCR
- Validates extracted information
- Generates a verification report

---

## System Architecture

```
Frontend (React / Next.js)
        │
        │ API calls
        ▼
FastAPI Backend
        │
        ▼
Document Processing Pipeline
   ├─ Compression
   ├─ Image Preprocessing
   ├─ OCR Extraction
   ├─ Field Extraction
   └─ Validation
```

---

## Tech Stack

### Backend
- Python
- FastAPI
- OpenCV
- PaddleOCR
- Pytesseract

### Frontend (planned)
- React / Next.js

### Deployment
- Frontend: Vercel
- Backend: Render

---

## Project Structure

```
src
 ├── config
 ├── processors
 │   ├── compression
 │   ├── preprocessing
 │   ├── ocr
 │   └── extraction
 ├── routes
 ├── services
 ├── utils
 ├── validation
 └── main.py
```

---

## Local Setup

### Clone the repository

```
git clone <repository-url>
cd document-verification-engine
```

### Create virtual environment

```
python -m venv venv
```

### Activate environment

Windows:

```
venv\Scripts\activate
```

Mac/Linux:
```
source venv/bin/activate
```

### Install dependencies

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Enable pre-commit hooks

```
pre-commit install
```

### Run the server

```
uvicorn src.main:app --reload
```

### Open API documentation

```
http://127.0.0.1:8000/docs
```

---

## Environment Variables

Create a `.env` file in the project root.

Example:

```
APP_NAME=Document Verification Engine
APP_ENV=development

UPLOAD_DIR=uploads
COMPRESSED_DIR=uploads/compressed

MAX_UPLOAD_SIZE_MB=5
IMAGE_MAX_WIDTH=1600
IMAGE_QUALITY=70

OCR_LANG=en
LOG_LEVEL=INFO
```

---
