from pathlib import Path
import pypdfium2 as pdfium


class PDFConverter:
    """Handles PDF → text and PDF → image conversion."""

    def extract_text_direct(self, pdf_path: str) -> str:
        """
        Extract embedded text from a text-based PDF (no OCR needed).

        Returns the raw text from page 0.  If the PDF has no embedded text
        (scanned document), returns an empty string.
        """
        pdf = pdfium.PdfDocument(str(pdf_path))
        try:
            page = pdf[0]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            return text or ""
        finally:
            pdf.close()

    def to_image(self, pdf_path: str, scale: float = 4.0) -> str:
        """
        Convert page 0 of a PDF to PNG.

        scale=4.0 → 288 DPI (default 72 DPI × 4), good OCR accuracy.
        Returns the path to the saved PNG.
        """
        path = Path(pdf_path)
        output_path = path.with_suffix(".png")

        pdf = pdfium.PdfDocument(str(path))
        page = pdf[0]
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        pil_image.save(str(output_path))
        pdf.close()

        return str(output_path)
