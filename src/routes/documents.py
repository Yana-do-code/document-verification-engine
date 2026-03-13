import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status

from src.config.constants import ALLOWED_EXTENSIONS
from src.config.settings import settings
from src.database.connection import get_db
from src.database import repository as repo
from src.services.document_service import DocumentService
from src.utils.helpers import save_upload

router = APIRouter()
service = DocumentService()

_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post(
    "/verify-document",
    summary="Upload a document image and receive structured extracted data",
    status_code=status.HTTP_200_OK,
)
async def verify_document(file: UploadFile = File(...)):
    # --- File type guard ---
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File type '{ext}' is not supported. "
                f"Allowed types: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    # --- File size guard (read into memory once, then rewind) ---
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )
    await file.seek(0)

    # --- Save and process ---
    try:
        file_path = await save_upload(file)
        result = service.process_document(file_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {exc}",
        )

    # --- Persist to MongoDB ---
    try:
        db = get_db()
        mime_type = ALLOWED_EXTENSIONS.get(ext, "application/octet-stream")
        doc_id = await repo.insert_document(
            db,
            filename=os.path.basename(file_path),
            original_filename=file.filename or "",
            file_size_bytes=len(content),
            mime_type=mime_type,
        )
        result_id = await repo.insert_verification_result(db, document_id=doc_id, result=result)
        result["result_id"] = result_id
        result["document_id"] = doc_id
    except Exception:
        # DB failure must not block the verification response
        pass

    return result


@router.get(
    "/results",
    summary="List the most recent verification results",
    status_code=status.HTTP_200_OK,
)
async def list_results(limit: int = 20):
    db = get_db()
    return await repo.list_verification_results(db, limit=min(limit, 100))


@router.get(
    "/results/{result_id}",
    summary="Get a single verification result by ID",
    status_code=status.HTTP_200_OK,
)
async def get_result(result_id: str):
    db = get_db()
    doc = await repo.get_verification_result(db, result_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")
    return doc
