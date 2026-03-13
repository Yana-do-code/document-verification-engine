from pathlib import Path

from src.processors.preprocessing.preprocessor import ImagePreprocessor
from src.processors.ocr.ocr_engine import OCREngine
from src.processors.extraction.extractor import FieldExtractor
from src.processors.pdf_converter import PDFConverter
from src.validation.validator import DocumentValidator


class DocumentService:

    def __init__(self):
        self.pdf_converter = PDFConverter()
        self.preprocessor = ImagePreprocessor()
        self.ocr = OCREngine()
        self.extractor = FieldExtractor()
        self.validator = DocumentValidator()

    def process_document(self, file_path: str, application_data: dict | None = None) -> dict:
        """
        Pipeline: [pdf→image →] preprocess → OCR → extract → validate.

        Returns:
            {
                "document_type": str,
                "extracted_data": { field: value | null, ... },
                "validation": {
                    "status": "valid" | "invalid",
                    "missing_fields": [...],
                    "field_checks": { field: bool },
                    "name_match_score": int   # only when application_data supplied
                },
                "confidence": float  # 0.0 – 1.0
            }
        """
        if Path(file_path).suffix.lower() == ".pdf":
            # Try direct text extraction first (works for all official e-PDFs
            # like Aadhaar, PAN, Passport that have embedded text layers).
            # Fall back to image-based OCR only for scanned/image-only PDFs.
            direct_text = self.pdf_converter.extract_text_direct(file_path)
            if len(direct_text.strip()) > 30:
                ocr_text = direct_text
            else:
                file_path = self.pdf_converter.to_image(file_path)
                processed = self.preprocessor.preprocess(file_path)
                ocr_text = self.ocr.extract_text(processed)
        else:
            processed = self.preprocessor.preprocess(file_path)
            ocr_text = self.ocr.extract_text(processed)

        raw = self.extractor.extract(ocr_text)
        doc_type = raw.pop("document_type")
        confidence = raw.pop("_confidence", 0.0)

        extracted_data = raw
        validation = self.validator.validate(
            {"document_type": doc_type, **extracted_data},
            application_data,
        )

        return {
            "document_type": doc_type,
            "extracted_data": extracted_data,
            "validation": validation,
            "confidence": confidence,
        }
