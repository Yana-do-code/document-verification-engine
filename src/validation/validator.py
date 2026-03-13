REQUIRED_FIELDS = ["date", "document_id"]


def validate_document(fields: dict) -> bool:
    """Return True if all required fields are present and non-empty."""
    return all(fields.get(f) for f in REQUIRED_FIELDS)
