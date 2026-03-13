import uuid
from fastapi import UploadFile
from src.processors.compression.compressor import compress
from src.processors.preprocessing.preprocessor import preprocess
from src.processors.ocr.ocr_engine import run_ocr
from src.processors.extraction.extractor import extract_fields
from src.validation.validator import validate_document
from src.utils.helpers import save_upload


class DocumentService:
    _store: dict = {}

    async def process(self, file: UploadFile) -> dict:
        doc_id = str(uuid.uuid4())
        path = await save_upload(file)

        compressed = compress(path)
        preprocessed = preprocess(compressed)
        text = run_ocr(preprocessed)
        fields = extract_fields(text)
        result = validate_document(fields)

        self._store[doc_id] = {"status": "completed", "fields": fields, "valid": result}
        return {"document_id": doc_id, **self._store[doc_id]}

    def get_status(self, document_id: str) -> dict | None:
        return self._store.get(document_id)
