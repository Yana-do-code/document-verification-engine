"""
Database CRUD operations for documents and verification results.
"""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


# ---------------------------------------------------------------------------
# documents collection
# ---------------------------------------------------------------------------

async def insert_document(
    db: AsyncIOMotorDatabase,
    *,
    filename: str,
    original_filename: str,
    file_size_bytes: int,
    mime_type: str,
) -> str:
    """Insert a document record and return its inserted _id as a string."""
    doc = {
        "filename": filename,
        "original_filename": original_filename,
        "file_size_bytes": file_size_bytes,
        "mime_type": mime_type,
        "uploaded_at": datetime.now(timezone.utc),
    }
    result = await db.documents.insert_one(doc)
    return str(result.inserted_id)


# ---------------------------------------------------------------------------
# verification_results collection
# ---------------------------------------------------------------------------

async def insert_verification_result(
    db: AsyncIOMotorDatabase,
    *,
    document_id: str,
    result: dict[str, Any],
) -> str:
    """Insert a verification result and return its _id as a string."""
    record = {
        "document_id": document_id,
        "document_type": result["document_type"],
        "confidence": result["confidence"],
        "extracted_data": result["extracted_data"],
        "validation": result["validation"],
        "verified_at": datetime.now(timezone.utc),
    }
    res = await db.verification_results.insert_one(record)
    return str(res.inserted_id)


async def get_verification_result(
    db: AsyncIOMotorDatabase, result_id: str
) -> dict[str, Any] | None:
    """Fetch a single verification result by its _id."""
    if not ObjectId.is_valid(result_id):
        return None
    doc = await db.verification_results.find_one({"_id": ObjectId(result_id)})
    if doc is None:
        return None
    doc["id"] = str(doc.pop("_id"))
    return doc


async def list_verification_results(
    db: AsyncIOMotorDatabase, limit: int = 20
) -> list[dict[str, Any]]:
    """Return the most recent `limit` verification results, newest first."""
    cursor = db.verification_results.find().sort("verified_at", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results
