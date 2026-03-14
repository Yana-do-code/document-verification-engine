# Project Contributions

## Team: Uttaranchal Coders

**Yana Pandey** — 2nd Year BTech CSE, Uttaranchal University, Dehradun
**Kangpila Sangtam** — 2nd Year BTech CSE, Uttaranchal University, Dehradun

---

## About the Project

This project is a Document Verification Engine — a full-stack web application that lets users upload Indian identity documents (Aadhaar, PAN Card, Passport, Driving License) and automatically extracts the important fields, validates them, and stores the results. The idea came from a real problem: government portals require citizens to upload documents manually, and officers have to verify them one by one. We wanted to automate that process using OCR and make it accessible through a clean web interface.

---

## How We Built It — Stage by Stage

### Stage 1 — Setting Up the OCR Core

The first challenge was getting OCR (Optical Character Recognition) to work reliably. We initially tried **PaddleOCR** but ran into serious compatibility issues — the library had breaking changes in version 3.4.0 that conflicted with PaddlePaddle 2.6.x on Windows. We spent time debugging errors like `set_optimization_level AttributeError` and tried monkey-patching, downgrading, and other workarounds.

Eventually we made the decision to switch to **Tesseract OCR** (an open-source OCR engine by Google). We installed Tesseract 5 on Windows and rewrote the OCR engine to use `pytesseract`. This turned out to be more stable, faster, and easier to work with.

We also faced a Windows-specific issue where PIL (Python Imaging Library) was keeping image files locked after reading them, causing temporary directory cleanup to fail. We fixed this by using Python's `with` statement to properly close image files after use.

### Stage 2 — Field Extraction Logic

Once we had clean OCR text, the next task was to extract structured fields from it. Raw OCR output is just a big blob of text — we needed to identify things like names, dates of birth, document numbers, and addresses.

We built a `DocumentClassifier` that scores the text against keyword signals for each document type (Aadhaar, PAN, Passport, Driving License) and returns a confidence score. Then we built separate field extractors for each document type using regex patterns.

Some tricky problems we solved here:
- **Passport vs Driving License confusion** — the passport number pattern was accidentally matching inside Driving License numbers. Fixed by adding word boundaries so it only matches standalone passport numbers and not ones buried inside longer strings.
- **Name extraction bleeding across lines** — the regex `[A-Za-z\s]` includes newline characters, so name fields were sometimes pulling in text from the next line. Fixed by using `[A-Za-z ]` with a literal space instead.
- **OCR text losing line structure** — the OCR engine was joining all words with spaces, losing newlines. This broke patterns that relied on line breaks. Fixed by grouping words by block/line numbers from Tesseract's output and reconstructing the text with proper newlines.

### Stage 3 — Document Classification with Confidence Scoring

We improved the classifier to return not just the document type but also a confidence score between 0 and 1. This score is based on how many keyword signals matched out of the total signals for that document type, with a penalty if the runner-up document type was close.

We also discovered a bug where the classifier was converting all text to uppercase but searching with lowercase signals — so keyword matching was never working. The fix was adding `re.IGNORECASE` to the search.

### Stage 4 — Validation

We built a `DocumentValidator` that checks whether all required fields for a given document type are present. For example, an Aadhaar card needs `aadhaar_number`, `name`, and `dob`. If any are missing, the validation status is set to `invalid` and the missing fields are listed.

We also added **fuzzy name matching** using RapidFuzz — so if the name on the document is "Yana Pandei" and the expected name is "Yana Pandey", it still gives a high match score instead of failing outright.

### Stage 5 — FastAPI Backend

We built the full REST API using FastAPI. The main endpoint is `POST /api/v1/verify-document` which accepts an uploaded file and runs the full pipeline — OCR → extraction → validation → response.

We added guards for:
- Unsupported file types (returns HTTP 415)
- Files too large (returns HTTP 413)
- Processing errors (returns HTTP 500 with a clear message)

We also configured CORS middleware so the frontend can talk to the backend across different domains.

### Stage 6 — PDF Support

Many official Indian e-documents (Aadhaar PDFs downloaded from UIDAI, PAN PDFs) are text-based PDFs, not scanned images. This means there is already text embedded in the PDF — we don't need OCR at all.

We added **direct PDF text extraction** using `pypdfium2`. The pipeline now tries to extract text directly from a PDF first. If the extracted text is long enough (more than 30 characters), it uses that. Otherwise it falls back to rendering the PDF as an image and running OCR on it.

This solved the "UNKNOWN document type" problem that was happening with e-Aadhaar PDFs — the OCR was struggling with the masked number format (`XXXX XXXX 1234`), but direct text extraction reads it perfectly.

We also handled the masked Aadhaar number format in the classifier and extractor by adding a pattern that accepts both `1234 5678 9012` and `XXXX XXXX 1234`.

### Stage 7 — Next.js Frontend

We built a clean, dark-themed web interface using **Next.js 14** with the App Router, TypeScript, and Tailwind CSS.

The UI has:
- A drag-and-drop file upload zone
- A document preview panel
- A results panel showing document type, confidence bar, extracted fields, and validation status
- Loading states and error handling

We hit a TypeScript error where the state machine union type wasn't being narrowed correctly — `hasFile && state.phase !== "idle"` caused a TypeScript complaint because it knew the second check was impossible. Fixed by using `"file" in state` as a type guard instead.

We also fixed a bug where clicking "Clear" didn't reset the file input — the browser remembers the selected file even after React state is reset. Fixed by adding a `resetKey` prop to the upload component that forces it to remount when the key changes.

### Stage 8 — MongoDB Database Integration

We integrated **MongoDB** as the database to store every verification result. We used **Motor**, an async MongoDB driver that works well with FastAPI's async architecture.

Two collections were created:
- `documents` — stores metadata about every uploaded file
- `verification_results` — stores the full extraction and validation result

We also added two new API endpoints:
- `GET /api/v1/results` — list recent verifications
- `GET /api/v1/results/{id}` — get a specific result

The app is set up so that if MongoDB is unreachable for any reason, the verification still works — the database save is wrapped in a try/except so it never blocks the response.

### Stage 9 — Deployment

Getting everything deployed took the most troubleshooting.

**Backend (Railway):**
- We initially tried Render but it wasn't loading, so we switched to Railway.
- First build failed because `requirements.txt` was encoded in UTF-16 (a Windows encoding issue) — pip on Linux couldn't read it. We rewrote the file in clean UTF-8.
- Second failure: the Docker `CMD` instruction was using JSON array form `["sh", "-c", "..."]` which doesn't expand environment variables like `$PORT`. Railway injects `PORT` as an env var, and the app was crashing with `$PORT is not a valid integer`. Fixed by switching to shell form `CMD uvicorn ... --port ${PORT:-8000}`.
- We also trimmed `requirements.txt` from 70+ packages (leftover from PaddleOCR) down to just the 16 packages the project actually uses, making builds much faster.

**Frontend (Vercel):**
- First deployment failed because `frontend/lib/api.ts` was blocked by a `.gitignore` rule (`lib/`) that was meant for Python build folders, not the frontend. Fixed by making the rule root-relative (`/lib/`).

**Database (MongoDB Atlas):**
- Used an existing free Atlas cluster to avoid creating a new paid one.
- Connected Railway to Atlas by setting `MONGODB_URI` as an environment variable on Railway.

---

## Key Challenges

1. **PaddleOCR compatibility on Windows** — ABI incompatibility between PaddleOCR 3.x and PaddlePaddle 2.6.x forced a full OCR engine switch to Tesseract.

2. **OCR text quality** — Raw Tesseract output needed careful post-processing to be useful for extraction. Line structure was being lost, confidence thresholds were too strict, and PDF rendering DPI was too low.

3. **Document classification accuracy** — Early versions were returning UNKNOWN for real documents. The bugs were: case-insensitive matching not applied, masked Aadhaar number not handled, and OCR text losing newlines.

4. **TypeScript strict typing** — The React state machine required careful use of discriminated union types to keep TypeScript happy without unsafe casts.

5. **Windows file locking** — PIL keeping image files open after OCR prevented temp file cleanup on Windows. Required using context managers properly.

6. **Deployment configuration** — Multiple issues across Railway (PORT env var, UTF-16 requirements.txt) and Vercel (gitignore blocking frontend files) that each needed a separate fix and redeploy.

7. **requirements.txt encoding** — The file was saved in UTF-16 by the Windows environment, which Linux pip couldn't parse. Had to rewrite it in UTF-8 using a bash heredoc.

---

## What We Learned

- How OCR pipelines work end to end — from raw image to structured data
- How to build and structure a production FastAPI backend
- How to use MongoDB with async Python (Motor)
- How React state machines with TypeScript discriminated unions work
- How to containerize an app with Docker including system dependencies like Tesseract
- How to deploy a full-stack app across Railway, Vercel, and MongoDB Atlas
- How to debug deployment failures by reading build logs carefully

---

## Contributors

| Name | Role |
|---|---|
| Yana Pandey | Full-stack development, OCR pipeline, frontend, deployment |
| Kangpila Sangtam | Full-stack development, backend API, database, deployment |

**Team:** Uttaranchal Coders
**Institution:** Uttaranchal University, Dehradun
**Programme:** BTech Computer Science and Engineering, 2nd Year
