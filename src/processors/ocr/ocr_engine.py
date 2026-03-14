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

    def extract_text(self, image_path: str, confidence_threshold: float = 0.05) -> str:
        """
        Run Tesseract with three PSM modes and return the result that contains
        the most words.  Trying multiple modes handles the variety of layouts
        found on Indian identity cards (Aadhaar, PAN, Passport, DL).
        """
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}"
            )

        best_text = ""
        # PSM 6 = single uniform block  (good for clean card scans)
        # PSM 3 = fully automatic       (good for mixed layouts)
        # PSM 11 = sparse text          (finds text anywhere on the page)
        for psm in (6, 3, 11):
            try:
                text = self._run(path, psm, confidence_threshold)
                if len(text.split()) > len(best_text.split()):
                    best_text = text
            except Exception:
                continue

        return best_text

    # ------------------------------------------------------------------

    def _run(self, path: Path, psm: int, confidence_threshold: float) -> str:
        config = f"--oem 3 --psm {psm}"
        min_conf = int(confidence_threshold * 100)

        with Image.open(str(path)) as img:
            data = pytesseract.image_to_data(
                img,
                config=config,
                output_type=pytesseract.Output.DICT,
            )

        current_line_key = None
        lines: list[str] = []
        current_words: list[str] = []

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
