from app.parsers.pdf_layout_parser import parse_pdf_layout


def inspect_pdf_layout(file_path: str) -> dict:
    return parse_pdf_layout(file_path)