from pydantic import BaseModel


class LayoutLineResponse(BaseModel):
    page_number: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    block_index: int
    line_index: int
    font_size: float | None = None
    is_header_footer: bool = False
    is_page_number: bool = False


class ParagraphResponse(BaseModel):
    page_number: int
    text: str
    line_count: int
    bbox: dict
    lines: list[LayoutLineResponse]


class SemanticBlock(BaseModel):
    type: str
    text: str
    page_number: int | None = None
    line_count: int | None = None
    bbox: dict | None = None
    lines: list[dict] | None = None
    source: str | None = None


class PdfLayoutResponse(BaseModel):
    line_count_raw: int
    line_count_cleaned: int
    paragraph_count: int
    semantic_block_count: int
    raw_text: str
    paragraphs: list[ParagraphResponse]
    semantic_blocks: list[SemanticBlock]
    pages: list[dict]
