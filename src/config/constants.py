# Allowed upload extensions and their MIME types
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".tiff": "image/tiff",
    ".tif":  "image/tiff",
    ".pdf":  "application/pdf",
}

# Required fields that must be present for a document to be considered valid
REQUIRED_FIELDS: dict[str, list[str]] = {
    "AADHAAR":         ["aadhaar_number", "name", "dob"],
    "PAN":             ["pan_number", "name", "dob"],
    "PASSPORT":        ["passport_number", "name", "dob", "nationality"],
    "DRIVING_LICENSE": ["dl_number", "name", "dob"],
}
