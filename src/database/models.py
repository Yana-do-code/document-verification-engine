"""
Pydantic models that represent MongoDB documents as returned by the API.

These are *response* models — they include the generated _id as a string `id`.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    """Metadata record created when a file is uploaded."""
    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: datetime


class ValidationOut(BaseModel):
    status: str
    missing_fields: list[str]
    field_checks: dict[str, bool]
    name_match_score: int | None = None


class VerificationResultOut(BaseModel):
    """Full verification result as stored in MongoDB."""
    id: str
    document_id: str
    document_type: str
    confidence: float
    extracted_data: dict[str, Any]
    validation: ValidationOut
    verified_at: datetime
