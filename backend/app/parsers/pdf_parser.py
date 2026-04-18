import fitz
from app.parsers.base_parser import BaseParser

class PDFParser(BaseParser):
    def parse(self, file_path: str) -> str:
        text_parts = []

        doc =  fitz.open(file_path)

        try:
            for page in doc:
                page_text = page.get_text("text")
                if page_text:
                    text_parts.append(page_text) 
        finally:
            doc.close()

        return "\n".join(text_parts).strip()
    