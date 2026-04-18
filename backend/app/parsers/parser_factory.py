from app.parsers.txt_parser import TXTParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser

class ParserFactory:
    @staticmethod
    def get_parser(file_ext: str):
        file_ext = file_ext.lower()

        if file_ext == ".txt":
            return TXTParser()
        if file_ext == ".pdf":
            return PDFParser()
        if file_ext == ".docx":
            return DOCXParser()
        
        raise ValueError(f"Unsupported file type: {file_ext}")