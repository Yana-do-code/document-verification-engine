from fastapi import APIRouter, UploadFile, File, HTTPException
from src.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
service = DocumentService()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    result = await service.process(file)
    return result


@router.get("/{document_id}/status")
async def get_status(document_id: str):
    status = service.get_status(document_id)
    if not status:
        raise HTTPException(status_code=404, detail="Document not found")
    return status
