from pathlib import Path


def compress(file_path: str) -> str:
    """Reduce file size while preserving quality for OCR processing."""
    path = Path(file_path)
    # Placeholder: integrate Pillow or ghostscript for real compression
    compressed_path = path.with_stem(path.stem + "_compressed")
    compressed_path.write_bytes(path.read_bytes())
    return str(compressed_path)
