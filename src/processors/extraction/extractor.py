"""
Field extraction from raw OCR text.

Pipeline:
  1. DocumentClassifier  — detects document type from keyword signals
  2. Per-document extractor (Aadhaar / PAN / Passport / DrivingLicense)
  3. FieldExtractor       — public facade, returns structured JSON-ready dict
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Shared regex helpers
# ---------------------------------------------------------------------------

# DOB: DD/MM/YYYY  |  DD-MM-YYYY  |  DD Month YYYY
_DOB_PATTERN = (
    r"\b(\d{2}[/\-]\d{2}[/\-]\d{4})\b"
    r"|\b(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s+\d{4})\b"
)

# Expiry same format as DOB
_EXPIRY_PATTERN = _DOB_PATTERN

_GENDER_PATTERN = r"\b(MALE|FEMALE|TRANSGENDER|M|F)\b"

# Name: word(s) after "Name" / "नाम" label — single line only (no \n)
_NAME_AFTER_LABEL = r"(?:Name|नाम)\s*[:\-]?\s*([A-Za-z][A-Za-z ]{1,48})"


def _first_group(pattern: str, text: str, flags: int = re.IGNORECASE) -> Optional[str]:
    """Return first non-None group from a match, stripped."""
    m = re.search(pattern, text, flags)
    if not m:
        return None
    value = next((g for g in m.groups() if g is not None), None)
    return value.strip() if value else None


def _search(pattern: str, text: str, flags: int = re.IGNORECASE) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group().strip() if m else None


# ---------------------------------------------------------------------------
# Document classifier
# ---------------------------------------------------------------------------

class DocumentClassifier:
    """
    Detects document type by scoring keyword signals in OCR text.
    Returns one of: "AADHAAR", "PAN", "PASSPORT", "DRIVING_LICENSE", "UNKNOWN"
    """

    _SIGNALS: dict[str, list[str]] = {
        "AADHAAR": [
            "uidai", "unique identification", "aadhaar", "आधार",
            "enrollment", "government of india",
            r"\d{4}\s\d{4}\s\d{4}",                          # full aadhaar number
            r"(?:xxxx|[Xx]{4})\s(?:xxxx|[Xx]{4})\s\d{4}",  # masked aadhaar (e-PDF)
        ],
        "PAN": [
            "income tax", "permanent account", "pan", "father",
            r"[A-Z]{5}\d{4}[A-Z]",            # PAN number shape
        ],
        "PASSPORT": [
            "passport", "republic of india", "nationality",
            "place of issue", "place of birth", "expiry", "mrz",
            r"\b[A-Z]\d{7}\b",                # passport number shape (word-bounded)
        ],
        "DRIVING_LICENSE": [
            "driving licence", "driving license", "motor vehicle",
            "transport", "badge no", "dl no", "licence no",
            r"[A-Z]{2}\d{2}\s?\d{11}",
        ],
    }

    def classify(self, text: str) -> str:
        return self.classify_with_confidence(text)[0]

    def classify_with_confidence(self, text: str) -> tuple[str, float]:
        """Return (document_type, confidence) where confidence is 0.0–1.0."""
        scores: dict[str, int] = {k: 0 for k in self._SIGNALS}

        for doc_type, signals in self._SIGNALS.items():
            for sig in signals:
                if re.search(sig, text, re.IGNORECASE):
                    scores[doc_type] += 1

        best = max(scores, key=lambda k: scores[k])
        if scores[best] == 0:
            return "UNKNOWN", 0.0

        total = len(self._SIGNALS[best])
        raw = scores[best] / total

        # Penalise ambiguity: if runner-up is within 1 signal, reduce confidence
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[1] >= sorted_scores[0] - 1:
            raw = max(0.0, raw - 0.15)

        return best, round(min(raw, 1.0), 2)


# ---------------------------------------------------------------------------
# Per-document field extractors
# ---------------------------------------------------------------------------

@dataclass
class AadhaarFields:
    aadhaar_number: Optional[str] = None
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None


@dataclass
class PANFields:
    pan_number: Optional[str] = None
    name: Optional[str] = None
    fathers_name: Optional[str] = None
    dob: Optional[str] = None


@dataclass
class PassportFields:
    passport_number: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    dob: Optional[str] = None
    expiry: Optional[str] = None
    place_of_birth: Optional[str] = None
    place_of_issue: Optional[str] = None


@dataclass
class DrivingLicenseFields:
    dl_number: Optional[str] = None
    name: Optional[str] = None
    dob: Optional[str] = None
    expiry: Optional[str] = None
    vehicle_classes: Optional[str] = None


def _extract_aadhaar(text: str) -> AadhaarFields:
    f = AadhaarFields()

    # Match full Aadhaar (1234 5678 9012) or masked e-PDF format (XXXX XXXX 1234)
    f.aadhaar_number = _search(
        r"(?:\d{4}|[Xx]{4})\s(?:\d{4}|[Xx]{4})\s\d{4}", text
    )
    f.name = _first_group(_NAME_AFTER_LABEL, text)
    f.dob = _first_group(_DOB_PATTERN, text)
    f.gender = _search(_GENDER_PATTERN, text)

    # Address: everything after "Address" / "पता" until end or next known label
    addr_m = re.search(
        r"(?:Address|पता)\s*[:\-]?\s*(.+?)(?=\n(?:Pin|Mobile|VID|$)|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if addr_m:
        f.address = " ".join(addr_m.group(1).split())  # collapse whitespace

    return f


def _extract_pan(text: str) -> PANFields:
    f = PANFields()

    f.pan_number = _search(r"[A-Z]{5}\d{4}[A-Z]", text)
    f.dob = _first_group(_DOB_PATTERN, text)

    # PAN cards list name then father's name on successive lines after labels
    # Layout: "Name\n<NAME>\nFather's Name\n<FNAME>" (label on its own line)
    name_block = re.search(
        r"(?:^|\n)([A-Z][A-Z\s]{2,40})\n([A-Z][A-Z\s]{2,40})\n",
        text,
        re.MULTILINE,
    )
    if name_block:
        f.name = name_block.group(1).strip()
        f.fathers_name = name_block.group(2).strip()
    else:
        f.name = _first_group(_NAME_AFTER_LABEL, text)
        father_m = re.search(
            r"(?:Father(?:'s)?(?:\s+Name)?|S/O|D/O)\s*[:\-]?\s*([A-Za-z][A-Za-z\s]{1,48})",
            text,
            re.IGNORECASE,
        )
        f.fathers_name = father_m.group(1).strip() if father_m else None

    return f


def _extract_passport(text: str) -> PassportFields:
    f = PassportFields()

    f.passport_number = _search(r"\b[A-Z]\d{7}\b", text)
    f.name = _first_group(_NAME_AFTER_LABEL, text)
    f.dob = _first_group(_DOB_PATTERN, text)

    # Expiry — find the SECOND date occurrence (first = DOB, second = expiry)
    all_dates = re.findall(
        r"\b\d{2}[/\-]\d{2}[/\-]\d{4}\b"
        r"|\b\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s+\d{4}\b",
        text,
        re.IGNORECASE,
    )
    if len(all_dates) >= 2:
        f.expiry = all_dates[1].strip()

    nat_m = re.search(r"(?:Nationality|National)[:\s]+([A-Za-z]+)", text, re.IGNORECASE)
    f.nationality = nat_m.group(1).strip() if nat_m else _search(r"\bINDIAN\b", text)

    pob_m = re.search(r"(?:Place of Birth|Birth Place)[:\s]+([^\n]+)", text, re.IGNORECASE)
    f.place_of_birth = pob_m.group(1).strip() if pob_m else None

    poi_m = re.search(r"(?:Place of Issue|Issued at)[:\s]+([^\n]+)", text, re.IGNORECASE)
    f.place_of_issue = poi_m.group(1).strip() if poi_m else None

    return f


def _extract_driving_license(text: str) -> DrivingLicenseFields:
    f = DrivingLicenseFields()

    f.dl_number = _search(r"[A-Z]{2}\d{2}\s?\d{11}", text)
    f.name = _first_group(_NAME_AFTER_LABEL, text)

    # DL may have multiple dates — first = DOB, last = expiry
    all_dates = re.findall(
        r"\b\d{2}[/\-]\d{2}[/\-]\d{4}\b"
        r"|\b\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\.?\s+\d{4}\b",
        text,
        re.IGNORECASE,
    )
    if all_dates:
        f.dob = all_dates[0].strip()
        f.expiry = all_dates[-1].strip() if len(all_dates) > 1 else None

    vc_m = re.search(
        r"(?:Vehicle Class(?:es)?|Auth(?:orized)? to Drive)[:\s]+([A-Za-z0-9,\s]+)",
        text,
        re.IGNORECASE,
    )
    f.vehicle_classes = vc_m.group(1).strip() if vc_m else None

    return f


# ---------------------------------------------------------------------------
# Public facade
# ---------------------------------------------------------------------------

class FieldExtractor:
    """
    Accepts raw OCR text, classifies the document, extracts structured fields.

    Returns a dict with the shape:
        {
            "document_type": "AADHAAR" | "PAN" | "PASSPORT" | "DRIVING_LICENSE" | "UNKNOWN",
            <field>: <value> | null,
            ...
        }
    """

    _classifier = DocumentClassifier()

    _EXTRACTORS = {
        "AADHAAR":          _extract_aadhaar,
        "PAN":              _extract_pan,
        "PASSPORT":         _extract_passport,
        "DRIVING_LICENSE":  _extract_driving_license,
    }

    def extract(self, ocr_text: str) -> dict:
        """
        Returns:
            {
                "document_type": str,
                "_confidence": float,   # internal — popped by DocumentService
                <field>: value | None,
                ...
            }
        """
        doc_type, confidence = self._classifier.classify_with_confidence(ocr_text)

        extractor_fn = self._EXTRACTORS.get(doc_type)
        if extractor_fn is None:
            return {"document_type": "UNKNOWN", "_confidence": 0.0}

        fields_obj = extractor_fn(ocr_text)
        result = {"document_type": doc_type, "_confidence": confidence}
        result.update(asdict(fields_obj))
        return result
