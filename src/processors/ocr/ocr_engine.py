import os
from pathlib import Path

import pytesseract
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

# Tesseract is installed to this path by the Windows installer
_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_PATH


class OCREngine:

    def extract_text(self, image_path: str, confidence_threshold: float = 0.3) -> str:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}"
            )

        # Use Tesseract with layout analysis for documents (PSM 6 = uniform block of text)
        # OEM 3 = default (LSTM + legacy), best accuracy
        custom_config = r"--oem 3 --psm 6"
        with Image.open(str(path)) as img:
            data = pytesseract.image_to_data(
                img,
                config=custom_config,
                output_type=pytesseract.Output.DICT,
            )

        # Reconstruct text with line breaks by grouping on (block, par, line)
        current_line_key = None
        lines: list[str] = []
        current_words: list[str] = []
        min_conf = int(confidence_threshold * 100)

        for i, word in enumerate(data["text"]):
            word = word.strip()
            conf = int(data["conf"][i])
            line_key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])

            if line_key != current_line_key:
                if current_words:
                    lines.append(" ".join(current_words))
                current_words = []
                current_line_key = line_key

            if word and conf >= min_conf:
                current_words.append(word)

        if current_words:
            lines.append(" ".join(current_words))

        return "\n".join(lines)
