from docx import Document as DocxDocument
from app.parsers.base_parser import BaseParser

class DOCXParser(BaseParser):
    def parse(self, file_path: str) -> str:
        doc = DocxDocument(file_path)
        paragraphs = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        return "\n".join(paragraphs).strip()