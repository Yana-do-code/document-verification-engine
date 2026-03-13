from pathlib import Path


def preprocess(file_path: str) -> str:
    """Apply image corrections: deskew, denoise, binarise."""
    path = Path(file_path)
    # Placeholder: integrate OpenCV / Pillow transforms
    processed_path = path.with_stem(path.stem + "_preprocessed")
    processed_path.write_bytes(path.read_bytes())
    return str(processed_path)
