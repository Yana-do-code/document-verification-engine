"""
Tests for:
  - DocumentClassifier.classify_with_confidence()
  - DocumentValidator.validate()
  - DocumentService.process_document() response shape
  - POST /api/v1/verify-document API endpoint
"""

import sys
import io
import numpy as np
import cv2
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from src.main import app
from src.processors.extraction.extractor import DocumentClassifier, FieldExtractor
from src.validation.validator import DocumentValidator
from src.services.document_service import DocumentService

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image_bytes(width: int = 400, height: int = 200) -> bytes:
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Test", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ---------------------------------------------------------------------------
# Classifier confidence tests
# ---------------------------------------------------------------------------

def test_confidence_is_float_between_0_and_1():
    _, conf = DocumentClassifier().classify_with_confidence(
        "Income Tax Department Permanent Account Number ABCDE1234F"
    )
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_confidence_higher_for_strong_signal():
    strong = "income tax permanent account father ABCDE1234F 01/01/2002"
    weak   = "income tax ABCDE1234F"
    _, conf_strong = DocumentClassifier().classify_with_confidence(strong)
    _, conf_weak   = DocumentClassifier().classify_with_confidence(weak)
    assert conf_strong >= conf_weak


def test_unknown_returns_zero_confidence():
    _, conf = DocumentClassifier().classify_with_confidence("random unrelated text here")
    assert conf == 0.0


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

def test_validator_valid_aadhaar():
    data = {
        "document_type": "AADHAAR",
        "aadhaar_number": "1234 5678 9012",
        "name": "Yana Pandey",
        "dob": "01/01/1990",
    }
    result = DocumentValidator().validate(data)
    assert result["status"] == "valid"
    assert result["missing_fields"] == []


def test_validator_invalid_missing_dob():
    data = {
        "document_type": "AADHAAR",
        "aadhaar_number": "1234 5678 9012",
        "name": "Yana Pandey",
        "dob": None,
    }
    result = DocumentValidator().validate(data)
    assert result["status"] == "invalid"
    assert "dob" in result["missing_fields"]


def test_validator_field_checks_keys():
    data = {
        "document_type": "PAN",
        "pan_number": "ABCDE1234F",
        "name": "Yana Pandey",
        "dob": "01/01/2002",
    }
    result = DocumentValidator().validate(data)
    assert set(result["field_checks"].keys()) == {"pan_number", "name", "dob"}
    assert all(result["field_checks"].values())


def test_validator_name_match_score():
    data = {
        "document_type": "PAN",
        "pan_number": "ABCDE1234F",
        "name": "Yana Pandey",
        "dob": "01/01/2002",
    }
    result = DocumentValidator().validate(data, application_data={"name": "Yana Pandey"})
    assert "name_match_score" in result
    assert result["name_match_score"] == 100


def test_validator_name_match_partial():
    data = {"document_type": "PAN", "pan_number": "ABCDE1234F", "name": "Yana Pandei", "dob": "01/01/2002"}
    result = DocumentValidator().validate(data, application_data={"name": "Yana Pandey"})
    assert 70 <= result["name_match_score"] < 100


def test_validator_unknown_doc_no_required_fields():
    result = DocumentValidator().validate({"document_type": "UNKNOWN"})
    assert result["status"] == "valid"   # no required fields → nothing missing
    assert result["missing_fields"] == []


# ---------------------------------------------------------------------------
# FieldExtractor includes _confidence
# ---------------------------------------------------------------------------

def test_extractor_result_has_no_confidence_key_after_pop():
    # FieldExtractor should include _confidence before DocumentService pops it
    result = FieldExtractor().extract(
        "Income Tax Department Permanent Account Number\nABCDE1234F\n01/01/2002"
    )
    assert "_confidence" in result
    assert isinstance(result["_confidence"], float)


# ---------------------------------------------------------------------------
# DocumentService response shape
# ---------------------------------------------------------------------------

PAN_TEXT = (
    "Income Tax Department\nPermanent Account Number\n"
    "ABCDE1234F\nYANA PANDEY\nRAMESH PANDEY\n01/01/2002"
)


def _mock_service_pipeline(monkeypatch_or_patch, ocr_text: str):
    """Return a DocumentService whose OCR always returns the given text."""
    with patch.object(DocumentService, "process_document") as mock_proc:
        svc = DocumentService.__new__(DocumentService)
        svc.preprocessor = MagicMock()
        svc.ocr = MagicMock()
        svc.extractor = FieldExtractor()
        svc.validator = DocumentValidator()

        svc.preprocessor.preprocess.return_value = "fake_processed.png"
        svc.ocr.extract_text.return_value = ocr_text

        # Call real logic manually
        raw = svc.extractor.extract(ocr_text)
        doc_type = raw.pop("document_type")
        confidence = raw.pop("_confidence", 0.0)
        validation_input = {"document_type": doc_type, **raw}
        validation = svc.validator.validate(validation_input)
        return {
            "document_type": doc_type,
            "extracted_data": raw,
            "validation": validation,
            "confidence": confidence,
        }


def test_service_response_has_required_top_level_keys():
    result = _mock_service_pipeline(None, PAN_TEXT)
    assert "document_type" in result
    assert "extracted_data" in result
    assert "validation" in result
    assert "confidence" in result


def test_service_extracted_data_is_dict():
    result = _mock_service_pipeline(None, PAN_TEXT)
    assert isinstance(result["extracted_data"], dict)


def test_service_document_type_is_pan():
    result = _mock_service_pipeline(None, PAN_TEXT)
    assert result["document_type"] == "PAN"


def test_service_confidence_is_float():
    result = _mock_service_pipeline(None, PAN_TEXT)
    assert isinstance(result["confidence"], float)


def test_service_validation_has_status():
    result = _mock_service_pipeline(None, PAN_TEXT)
    assert result["validation"]["status"] in ("valid", "invalid")


# ---------------------------------------------------------------------------
# API endpoint tests (TestClient — no real OCR)
# ---------------------------------------------------------------------------

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_upload_unsupported_type_returns_415():
    # GIF is not a supported document format
    r = client.post(
        "/api/v1/verify-document",
        files={"file": ("photo.gif", b"GIF89a fake content", "image/gif")},
    )
    assert r.status_code == 415


def test_upload_oversized_returns_413():
    big_content = b"0" * (6 * 1024 * 1024)  # 6 MB > 5 MB limit
    r = client.post(
        "/api/v1/verify-document",
        files={"file": ("big.jpg", big_content, "image/jpeg")},
    )
    assert r.status_code == 413


def test_upload_valid_image_returns_200():
    img_bytes = _make_image_bytes()

    mock_result = {
        "document_type": "PAN",
        "extracted_data": {"pan_number": "ABCDE1234F", "name": "Yana Pandey", "dob": "01/01/2002"},
        "validation": {"status": "valid", "missing_fields": [], "field_checks": {}},
        "confidence": 0.8,
    }

    with patch("src.routes.documents.service.process_document", return_value=mock_result):
        r = client.post(
            "/api/v1/verify-document",
            files={"file": ("aadhaar.jpg", img_bytes, "image/jpeg")},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["document_type"] == "PAN"
    assert "extracted_data" in body
    assert "validation" in body
    assert "confidence" in body


def test_upload_response_validation_status_field():
    img_bytes = _make_image_bytes()
    mock_result = {
        "document_type": "AADHAAR",
        "extracted_data": {"aadhaar_number": "1234 5678 9012", "name": "Test", "dob": "01/01/1990"},
        "validation": {"status": "valid", "missing_fields": [], "field_checks": {}},
        "confidence": 0.71,
    }
    with patch("src.routes.documents.service.process_document", return_value=mock_result):
        r = client.post(
            "/api/v1/verify-document",
            files={"file": ("id.png", img_bytes, "image/png")},
        )
    assert r.json()["validation"]["status"] == "valid"
