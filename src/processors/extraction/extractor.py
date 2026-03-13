import re


def extract_fields(text: str) -> dict:
    """Parse structured fields from raw OCR text."""
    fields = {}

    date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if date_match:
        fields["date"] = date_match.group(1)

    id_match = re.search(r"\b([A-Z]{1,3}\d{6,10})\b", text)
    if id_match:
        fields["document_id"] = id_match.group(1)

    return fields
