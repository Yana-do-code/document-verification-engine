from pathlib import Path
from typing import Iterator

try:
    import fitz  # PyMuPDF — better font/encoding handling for Indian govt PDFs
    _PYMUPDF = True
except ImportError:
    _PYMUPDF = False

import pypdfium2 as pdfium


class PDFConverter:
    """Handles PDF → text and PDF → image conversion."""

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def extract_text_direct(self, pdf_path: str) -> str:
        """
        Extract embedded text from a PDF using PyMuPDF (preferred) or
        pypdfium2 (fallback).  Returns the text from the page with the
        most ASCII-printable content — i.e. the most readable English page.
        """
        text = ""
        if _PYMUPDF:
            text = self._extract_fitz(pdf_path)
        if not text.strip():
            text = self._extract_pdfium(pdf_path)
        return text

    def _extract_fitz(self, pdf_path: str) -> str:
        try:
            doc = fitz.open(str(pdf_path))
            best_text = ""
            best_score = -1
            for page in doc:
                t = page.get_text("text") or ""
                score = sum(1 for c in t if 32 <= ord(c) < 127)
                if score > best_score:
                    best_score = score
                    best_text = t
            doc.close()
            return best_text
        except Exception:
            return ""

    def _extract_pdfium(self, pdf_path: str) -> str:
        try:
            pdf = pdfium.PdfDocument(str(pdf_path))
            best_text = ""
            best_score = -1
            for i in range(len(pdf)):
                try:
                    t = pdf[i].get_textpage().get_text_range() or ""
                    score = sum(1 for c in t if 32 <= ord(c) < 127)
                    if score > best_score:
                        best_score = score
                        best_text = t
                except Exception:
                    continue
            pdf.close()
            return best_text
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Image conversion
    # ------------------------------------------------------------------

    def page_count(self, pdf_path: str) -> int:
        try:
            pdf = pdfium.PdfDocument(str(pdf_path))
            n = len(pdf)
            pdf.close()
            return n
        except Exception:
            return 1

    def to_image(self, pdf_path: str, page_index: int = 0, scale: float = 3.0) -> str:
        """Convert one PDF page to PNG. Returns the path to the saved PNG."""
        path = Path(pdf_path)
        suffix = f"_p{page_index}" if page_index > 0 else ""
        output_path = path.with_stem(path.stem + suffix).with_suffix(".png")

        # Try PyMuPDF first (often better rendering for complex layouts)
        if _PYMUPDF:
            try:
                doc = fitz.open(str(path))
                page = doc[page_index]
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
                pix.save(str(output_path))
                doc.close()
                return str(output_path)
            except Exception:
                pass

        # Fallback: pypdfium2
        try:
            pdf = pdfium.PdfDocument(str(path))
            page = pdf[page_index]
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            pil_image.save(str(output_path))
            pdf.close()
        except Exception as exc:
            raise ValueError(f"Could not render PDF page {page_index}: {exc}") from exc

        return str(output_path)

    def to_images(self, pdf_path: str, max_pages: int = 3) -> Iterator[tuple[int, str]]:
        """Yield (page_index, image_path) for up to max_pages pages."""
        count = min(self.page_count(pdf_path), max_pages)
        for i in range(count):
            yield i, self.to_image(pdf_path, page_index=i)
