"""
OCR pipeline tests.

Run all tests:
    pytest tests/test_ocr_pipeline.py -v

Run the full pipeline on a real image:
    python tests/test_ocr_pipeline.py <path/to/image.jpg>
"""

import sys
import os
import numpy as np
import cv2
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.processors.preprocessing.preprocessor import ImagePreprocessor
from src.processors.extraction.extractor import FieldExtractor, DocumentClassifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_image(path: str, width: int = 400, height: int = 200) -> str:
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Test Document", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(path, img)
    return path


def run_pipeline(image_path: str) -> dict:
    """Run the full pipeline and print each step. Used as a CLI tool."""
    print(f"\n--- Pipeline start: {image_path} ---")

    preprocessor = ImagePreprocessor()
    processed = preprocessor.preprocess(image_path)
    print(f"[1] Preprocessed -> {processed}")

    from src.processors.ocr.ocr_engine import OCREngine
    ocr = OCREngine()
    text = ocr.extract_text(processed)
    print(f"[3] OCR text:\n{text}\n")

    extractor = FieldExtractor()
    fields = extractor.extract(text)
    print(f"[4] Structured output:\n{fields}")

    return {"compressed": compressed, "processed": processed, "text": text, "fields": fields}


# ---------------------------------------------------------------------------
# Preprocessor tests
# ---------------------------------------------------------------------------

def test_preprocessor_produces_output_file():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "sample.jpg")
        _make_test_image(src)
        out = ImagePreprocessor().preprocess(src)
        assert os.path.exists(out)
        assert out.endswith(".png")


# ---------------------------------------------------------------------------
# OCR engine tests
# ---------------------------------------------------------------------------

def test_ocr_engine_returns_string():
    """OCREngine.extract_text() returns a str (pytesseract mocked)."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "sample.png")
        _make_test_image(src)

        mock_data = {
            "text": ["Hello", "World", ""],
            "conf": ["99", "95", "-1"],
            "block_num": [1, 1, 1],
            "par_num": [1, 1, 1],
            "line_num": [1, 1, 2],
        }
        with patch("src.processors.ocr.ocr_engine.pytesseract.image_to_data", return_value=mock_data):
            from src.processors.ocr.ocr_engine import OCREngine
            result = OCREngine().extract_text(src)

        assert isinstance(result, str)
        assert "Hello" in result and "World" in result


# ---------------------------------------------------------------------------
# Document classifier tests
# ---------------------------------------------------------------------------

def test_classifier_detects_aadhaar():
    text = "Government of India\nUnique Identification Authority\n1234 5678 9012"
    assert DocumentClassifier().classify(text) == "AADHAAR"


def test_classifier_detects_pan():
    text = "Income Tax Department\nPermanent Account Number\nABCDE1234F"
    assert DocumentClassifier().classify(text) == "PAN"


def test_classifier_detects_passport():
    text = "Republic of India\nPassport\nNationality: INDIAN\nA1234567"
    assert DocumentClassifier().classify(text) == "PASSPORT"


def test_classifier_detects_driving_license():
    text = "Driving Licence\nMotor Vehicle Act\nDL No: MH0220123456789"
    assert DocumentClassifier().classify(text) == "DRIVING_LICENSE"


def test_classifier_returns_unknown():
    assert DocumentClassifier().classify("random text without signals") == "UNKNOWN"


# ---------------------------------------------------------------------------
# Aadhaar extraction tests
# ---------------------------------------------------------------------------

AADHAAR_TEXT = """
Government of India
Unique Identification Authority of India
Name: Yana Pandey
DOB: 01/01/1990
FEMALE
1234 5678 9012
Address: 123 MG Road, Mumbai, Maharashtra
"""

def test_aadhaar_document_type():
    assert FieldExtractor().extract(AADHAAR_TEXT)["document_type"] == "AADHAAR"

def test_aadhaar_number():
    assert FieldExtractor().extract(AADHAAR_TEXT)["aadhaar_number"] == "1234 5678 9012"

def test_aadhaar_name():
    assert FieldExtractor().extract(AADHAAR_TEXT)["name"] == "Yana Pandey"

def test_aadhaar_dob():
    assert FieldExtractor().extract(AADHAAR_TEXT)["dob"] == "01/01/1990"

def test_aadhaar_gender():
    assert FieldExtractor().extract(AADHAAR_TEXT)["gender"] == "FEMALE"


# ---------------------------------------------------------------------------
# PAN extraction tests
# ---------------------------------------------------------------------------

PAN_TEXT = """
Income Tax Department
Permanent Account Number Card
ABCDE1234F
YANA PANDEY
RAMESH PANDEY
01/01/2002
"""

def test_pan_document_type():
    assert FieldExtractor().extract(PAN_TEXT)["document_type"] == "PAN"

def test_pan_number():
    assert FieldExtractor().extract(PAN_TEXT)["pan_number"] == "ABCDE1234F"

def test_pan_dob():
    assert FieldExtractor().extract(PAN_TEXT)["dob"] == "01/01/2002"

def test_pan_name_from_label():
    text = "Income Tax\nPermanent Account Number\nName: Yana Pandey\nABCDE1234F\n01/01/2002"
    f = FieldExtractor().extract(text)
    assert f["name"] == "Yana Pandey"

def test_pan_fathers_name_from_label():
    text = "Income Tax\nPermanent Account Number\nABCDE1234F\nFather's Name: Ramesh Pandey\n01/01/2002"
    f = FieldExtractor().extract(text)
    assert f["fathers_name"] == "Ramesh Pandey"


# ---------------------------------------------------------------------------
# Passport extraction tests
# ---------------------------------------------------------------------------

PASSPORT_TEXT = """
Republic of India
Passport
Passport No: A1234567
Name: Yana Pandey
Nationality: INDIAN
Date of Birth: 01/01/1990
Place of Birth: Mumbai
Place of Issue: Delhi
Date of Expiry: 01/01/2030
"""

def test_passport_document_type():
    assert FieldExtractor().extract(PASSPORT_TEXT)["document_type"] == "PASSPORT"

def test_passport_number():
    assert FieldExtractor().extract(PASSPORT_TEXT)["passport_number"] == "A1234567"

def test_passport_name():
    assert FieldExtractor().extract(PASSPORT_TEXT)["name"] == "Yana Pandey"

def test_passport_nationality():
    assert FieldExtractor().extract(PASSPORT_TEXT)["nationality"] == "INDIAN"

def test_passport_dob():
    assert FieldExtractor().extract(PASSPORT_TEXT)["dob"] == "01/01/1990"

def test_passport_expiry():
    assert FieldExtractor().extract(PASSPORT_TEXT)["expiry"] == "01/01/2030"

def test_passport_place_of_birth():
    assert FieldExtractor().extract(PASSPORT_TEXT)["place_of_birth"] == "Mumbai"

def test_passport_place_of_issue():
    assert FieldExtractor().extract(PASSPORT_TEXT)["place_of_issue"] == "Delhi"


# ---------------------------------------------------------------------------
# Driving License extraction tests
# ---------------------------------------------------------------------------

DL_TEXT = """
Government of Maharashtra
Driving Licence
Motor Vehicle Act
Licence No: MH0220123456789
Name: Yana Pandey
DOB: 01/01/1990
Valid Till: 01/01/2040
Vehicle Classes: LMV, MCWG
"""

def test_dl_document_type():
    assert FieldExtractor().extract(DL_TEXT)["document_type"] == "DRIVING_LICENSE"

def test_dl_number():
    assert FieldExtractor().extract(DL_TEXT)["dl_number"] == "MH0220123456789"

def test_dl_name():
    assert FieldExtractor().extract(DL_TEXT)["name"] == "Yana Pandey"

def test_dl_dob():
    assert FieldExtractor().extract(DL_TEXT)["dob"] == "01/01/1990"

def test_dl_expiry():
    assert FieldExtractor().extract(DL_TEXT)["expiry"] == "01/01/2040"

def test_dl_vehicle_classes():
    assert "LMV" in FieldExtractor().extract(DL_TEXT)["vehicle_classes"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_unknown_document_returns_unknown_type():
    result = FieldExtractor().extract("some random unrelated text")
    assert result["document_type"] == "UNKNOWN"

def test_dob_dash_format():
    text = "Government of India\nUnique Identification\n1234 5678 9012\nDOB: 15-08-1995"
    assert FieldExtractor().extract(text)["dob"] == "15-08-1995"

def test_dob_month_name_format():
    text = "Republic of India\nPassport\nA9999999\nDate of Birth: 10 Jan 1985\nDate of Expiry: 10 Jan 2025"
    f = FieldExtractor().extract(text)
    assert "1985" in f["dob"]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/test_ocr_pipeline.py <image_path>")
        sys.exit(1)
    run_pipeline(sys.argv[1])
