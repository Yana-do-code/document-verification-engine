from src.processors.compression.compressor import ImageCompressor
from src.processors.preprocessing.preprocessor import ImagePreprocessor
from src.processors.ocr.ocr_engine import OCREngine
from src.processors.extraction.extractor import FieldExtractor
from src.validation.validator import DocumentValidator


class DocumentService:

    def __init__(self):

        self.compressor = ImageCompressor()
        self.preprocessor = ImagePreprocessor()
        self.ocr = OCREngine()
        self.extractor = FieldExtractor()
        self.validator = DocumentValidator()

    def process_document(self, file_path):

        compressed = self.compressor.compress(file_path)

        processed = self.preprocessor.preprocess(compressed)

        ocr_data = self.ocr.extract_text(processed)

        fields = self.extractor.extract(ocr_data)

        validation = self.validator.validate(fields)

        return {
            "compressed_file": compressed,
            "ocr_data": ocr_data,
            "extracted_fields": fields,
            "validation": validation,
        }