import os
from pathlib import Path

from src.processors.preprocessing.preprocessor import ImagePreprocessor
from src.processors.ocr.ocr_engine import OCREngine
from src.processors.extraction.extractor import FieldExtractor, DocumentClassifier
from src.processors.pdf_converter import PDFConverter
from src.validation.validator import DocumentValidator

_classifier = DocumentClassifier()


class DocumentService:

    def __init__(self):
        self.pdf_converter = PDFConverter()
        self.preprocessor = ImagePreprocessor()
        self.ocr = OCREngine()
        self.extractor = FieldExtractor()
        self.validator = DocumentValidator()

    def process_document(self, file_path: str, application_data: dict | None = None) -> dict:
        original_size = os.path.getsize(file_path)
        compressed_size = original_size
        ocr_text = ""

        if Path(file_path).suffix.lower() == ".pdf":
            ocr_text, compressed_size = self._process_pdf(file_path, original_size)
        else:
            ocr_text, compressed_size = self._process_image(file_path, original_size)

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
            "file_info": {
                "original_size_bytes": original_size,
                "compressed_size_bytes": compressed_size,
            },
            "ocr_text": ocr_text,
        }

    # ------------------------------------------------------------------

    def _ocr_image(self, image_path: str) -> tuple[str, float]:
        """
        Run OCR using BOTH preprocessing modes; return the text with the
        higher classifier confidence (or more words if both score the same).
        """
        results: list[tuple[str, float]] = []

        for preprocess_fn in (self.preprocessor.preprocess, self.preprocessor.preprocess_light):
            try:
                processed = preprocess_fn(image_path)
                text = self.ocr.extract_text(processed)
                _, conf = _classifier.classify_with_confidence(text)
                results.append((text, conf))
            except Exception:
                continue

        if not results:
            return "", 0.0

        # Pick best: highest confidence, then most words
        results.sort(key=lambda x: (x[1], len(x[0].split())), reverse=True)
        return results[0]

    def _process_image(self, file_path: str, original_size: int) -> tuple[str, int]:
        text, _ = self._ocr_image(file_path)
        try:
            processed = self.preprocessor.preprocess(file_path)
            compressed_size = self.preprocessor.compressed_size(processed)
        except Exception:
            compressed_size = original_size
        return text, compressed_size

    def _process_pdf(self, file_path: str, original_size: int) -> tuple[str, int]:
        """
        Multi-strategy PDF text extraction.
        Strategy 1 — PyMuPDF/pypdfium2 direct text (best for text-based PDFs).
        Strategy 2 — Image OCR with both preprocessing modes on every page.
        Always returns the candidate with the highest classifier confidence.
        """
        compressed_size = original_size
        best_text = ""
        best_conf = -1.0

        # ── Strategy 1: direct text extraction ───────────────────────────────
        try:
            direct = self.pdf_converter.extract_text_direct(file_path)
            if len(direct.strip()) > 20:
                _, conf = _classifier.classify_with_confidence(direct)
                if conf > best_conf or (conf == best_conf and len(direct) > len(best_text)):
                    best_conf = conf
                    best_text = direct
        except Exception:
            pass

        if best_conf >= 0.25:
            return best_text, compressed_size

        # ── Strategy 2: image OCR on every page ──────────────────────────────
        for _idx, image_path in self.pdf_converter.to_images(file_path, max_pages=4):
            try:
                text, conf = self._ocr_image(image_path)

                is_better = conf > best_conf or (
                    conf == best_conf and len(text.split()) > len(best_text.split())
                )
                if is_better:
                    best_conf = conf
                    best_text = text
                    try:
                        processed = self.preprocessor.preprocess(image_path)
                        compressed_size = self.preprocessor.compressed_size(processed)
                    except Exception:
                        pass

                if best_conf >= 0.25:
                    break
            except Exception:
                continue

        return best_text, compressed_size
