import fitz

from app.parsers.base_parser import BaseParser
from app.parsers.pdf_layout_parser import parse_pdf_layout


class PDFParser(BaseParser):
    def parse(self, file_path: str) -> str:
        """Parse PDF file using layout-aware parser."""
        try:
            layout = parse_pdf_layout(file_path)
            raw_text = layout.get("raw_text", "")

            if raw_text and raw_text.strip():
                return raw_text.strip()

        except Exception as e:
            print(f"[PDFParser] layout parser failed, fallback: {e}")

        # Fallback: simple text extraction
        return self._fallback_parse(file_path)

    def _fallback_parse(self, file_path: str) -> str:
        """Simple text fallback if layout parser fails."""
        text_parts = []
        doc = fitz.open(file_path)

        try:
            for page in doc:
                page_text = page.get_text("text")
                if page_text:
                    text_parts.append(page_text)
        finally:
            doc.close()

        return "\n\n".join(text_parts).strip()
