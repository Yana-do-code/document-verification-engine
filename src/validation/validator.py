from rapidfuzz import fuzz
from src.config.constants import REQUIRED_FIELDS


class DocumentValidator:
    """
    Validates extracted document fields.

    validate() returns:
        {
            "status":        "valid" | "invalid",
            "missing_fields": [...],          # required fields that are None/empty
            "field_checks":  { field: bool }, # True = present, False = missing
            "name_match_score": int           # 0-100, only when application_data provided
        }
    """

    def validate(self, extracted_data: dict, application_data: dict | None = None) -> dict:
        doc_type = extracted_data.get("document_type", "UNKNOWN")
        required = REQUIRED_FIELDS.get(doc_type, [])

        field_checks: dict[str, bool] = {}
        missing: list[str] = []

        for field in required:
            value = extracted_data.get(field)
            present = bool(value and str(value).strip())
            field_checks[field] = present
            if not present:
                missing.append(field)

        result: dict = {
            "status": "invalid" if (missing or doc_type == "UNKNOWN") else "valid",
            "missing_fields": missing,
            "field_checks": field_checks,
        }

        if application_data and "name" in application_data:
            extracted_name = extracted_data.get("name") or ""
            score = fuzz.ratio(extracted_name.upper(), application_data["name"].upper())
            result["name_match_score"] = score

        return result
