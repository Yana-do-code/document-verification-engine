from src.processors.extraction.extractor import extract_fields
from src.validation.validator import validate_document


def test_extract_fields_finds_date_and_id():
    text = "Issued on 01/03/2025. Document ID: AB1234567."
    fields = extract_fields(text)
    assert fields.get("date") == "01/03/2025"
    assert fields.get("document_id") == "AB1234567"


def test_validate_document_passes_with_all_fields():
    assert validate_document({"date": "01/03/2025", "document_id": "AB1234567"}) is True


def test_validate_document_fails_with_missing_fields():
    assert validate_document({"date": "01/03/2025"}) is False
