import re
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.chapter import Chapter
from app.schemas.document import DocumentCreate
from app.nlp.chapter_splitter import split_chapters
from app.nlp.paragraph_splitter import split_paragraphs
from app.nlp.sentence_splitter import split_sentences


SKIP_BLOCK_TYPES = {
    "toc_heading",
    "toc_item",
    "ebook_info",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def extract_chapter_number(text: str) -> int | None:
    match = re.search(r"CHƯƠNG\s+(\d+)", text, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def clean_toc_item(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"^[•·\-\–\—]\s*", "", text)
    return text.strip()


def clean_chapter_title(text: str) -> str:
    """
    Tách title khỏi body từ heading block bị dính body (OCR/PDF layout).

    Heading block PDF thường dính đầu body text khi heading nằm cuối trang.
    Dùng NFC normalization để xử lý đúng Vietnamese characters.

    Chiến lược:
    1. lowercase→TitleCase transition (2+ lowercase words) → body starts after 2nd lowercase word
    2. Single UPPERCASE + lowercase word (OCR artifact) → body starts after uppercase letter
    3. Sentence punctuation → body starts after period (remaining >= 25 to confirm)
    4. Closing quote at end → body starts before quote
    5. Fallback: giữ nguyên
    """
    import unicodedata

    text = text.strip()
    if not text:
        return text

    text = unicodedata.normalize("NFC", text)

    # Build word list with their character positions
    words: list[tuple[str, int, int]] = []
    for m in re.finditer(r"\w+", text):
        words.append((m.group(), m.start(), m.end()))

    if len(words) > 2:
        # P1: lowercase→TitleCase transition where prev word is also lowercase
        # e.g. "...gọi lạnh Chỉ cần..." → lạnh(lowercase)→Chỉ(TitleCase), prev=gọi(lowercase)
        for i in range(1, len(words) - 1):
            w_prev = words[i - 1][0]
            w_curr = words[i][0]
            w_next = words[i + 1][0]
            is_prev_lower = w_prev[0].islower()
            is_curr_lower = w_curr[0].islower()
            is_next_title = w_next[0].isupper()
            if is_prev_lower and is_curr_lower and is_next_title:
                title = text[:words[i][2]].strip()
                if len(text) - len(title) >= 10:
                    return title

        # P2: Single uppercase letter + lowercase word (OCR artifact)
        # e.g. "kết C húng" → title="...kết", body="C húng..."
        # e.g. "thảo N hững" → title="...thảo", body="N hững..."
        for m2 in re.finditer(r"\s([A-ZÀ-Ỹ])\s+([a-zà-ỹ])", text):
            title = text[:m2.start(1)].strip()
            if len(title) > 15 and len(text) - len(title) >= 1:
                return title

    # P3: Heading ends with closing quote (no period after)
    # e.g. '..."thương hiệu."' (closing curly quote at end)
    for quote in ("\u201d", '"', "\u201c"):
        lq = text.rfind(quote)
        if lq > 15:
            return text[:lq].strip()

    # P4: Sentence punctuation, remaining >= 25 chars
    m4 = re.search(r"^([^.?!]*[.?!])\s+([A-ZÀ-Ỹ].*)$", text)
    if m4 and len(m4.group(2)) >= 25:
        return m4.group(1).strip()

    return text


def collect_toc_chapter_titles(blocks: list[dict]) -> dict[int, str]:
    toc_titles = {}

    for block in blocks:
        text = block.get("text", "").strip()
        if not text:
            continue

        text = re.sub(r"^[•·\-\–]\s*", "", text)

        if not text.upper().startswith("CHƯƠNG"):
            continue

        chapter_no = extract_chapter_number(text)
        if chapter_no is None:
            continue

        # 🔥 CLEAN TITLE
        clean_title = clean_chapter_title(text)

        toc_titles[chapter_no] = clean_title

    return toc_titles


def infer_book_title(payload: DocumentCreate) -> str:
    text = payload.raw_text or ""

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("• Tên sách:"):
            return line.replace("• Tên sách:", "").strip()

    return payload.title.replace("-", " ").strip()


def split_chapter_heading_and_body(text: str, toc_titles: dict[int, str]):
    text = text.strip()
    chapter_no = extract_chapter_number(text)

    if chapter_no and chapter_no in toc_titles:
        title = toc_titles[chapter_no]

        # 🔥 HARD CUT (quan trọng)
        pattern = re.escape(title) + r"(.*)"
        match = re.match(pattern, text, re.DOTALL)

        if match:
            body = match.group(1).strip()

            # nếu body bắt đầu bằng chữ hoa -> OK
            return title, body

    return text, ""


def build_chapter_item(title: str, lines: list[str]) -> dict:
    raw_text = "\n\n".join(line.strip() for line in lines if line.strip())
    paragraphs = split_paragraphs(raw_text)
    sentences = split_sentences(raw_text)

    return {
        "title": title,
        "raw_text": raw_text,
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
    }


def build_chapters_from_semantic_blocks(layout_json: dict | None) -> list[dict]:
    if not layout_json:
        return []

    blocks = layout_json.get("semantic_blocks") or []

    # Collect indices of blocks to skip
    skip_indices: set[int] = set()
    for i, block in enumerate(blocks):
        if block.get("type") in SKIP_BLOCK_TYPES or block.get("type") == "part_heading":
            skip_indices.add(i)

    chapters = []
    current_title: str | None = None
    current_lines: list[str] = []

    for i, block in enumerate(blocks):
        block_type = block.get("type")
        text = normalize_text(block.get("text") or "")

        if not text or i in skip_indices:
            continue

        if block_type == "chapter_heading":
            if current_title and current_lines:
                chapters.append(build_chapter_item(current_title, current_lines))

            # Extract title (strips body contamination if heading is corrupted)
            title = clean_chapter_title(text)

            # Remaining text after title = potential body from the heading block itself
            body_from_heading = ""
            if len(text) > len(title):
                body_from_heading = text[len(title):].strip()
                body_from_heading = re.sub(r"^[:.\-–—\s]+", "", body_from_heading).strip()

            current_title = title
            current_lines = []

            # Only add body_from_heading if the NEXT BLOCK IS A PARAGRAPH
            # This means the heading block is at the bottom of a page and the body
            # text was split across the heading block + the paragraph block below.
            # If the next block is a quote/author/other → it's a separate block type,
            # not a continuation, so we should NOT add body_from_heading.
            if body_from_heading:
                next_idx = _find_next_non_skip_index(blocks, i, skip_indices)
                next_block = blocks[next_idx] if next_idx is not None else None
                if next_block and next_block.get("type") == "paragraph":
                    current_lines.append(body_from_heading)

            continue

        if current_title:
            current_lines.append(text)

    if current_title and current_lines:
        chapters.append(build_chapter_item(current_title, current_lines))

    return chapters


def _find_next_non_skip_index(blocks: list[dict], current_i: int, skip_indices: set[int]) -> int | None:
    """Find the next block index that is not in skip_indices."""
    for j in range(current_i + 1, len(blocks)):
        if j not in skip_indices:
            return j
    return None


def create_document(
    db: Session,
    payload: DocumentCreate,
    layout_json: dict | None = None,
) -> Document:
    document = Document(
        title=infer_book_title(payload),
        file_name=payload.file_name,
        file_type=payload.file_type,
        file_path=payload.file_path,
        raw_text=payload.raw_text,
        layout_json=layout_json,
    )

    db.add(document)
    db.flush()

    chapter_items = build_chapters_from_semantic_blocks(layout_json)

    if not chapter_items:
        chapter_items = split_chapters(payload.raw_text)

    for idx, item in enumerate(chapter_items, start=1):
        chapter = Chapter(
            document_id=document.id,
            chapter_index=idx,
            title=item["title"],
            raw_text=item["raw_text"],
            paragraph_count=item["paragraph_count"],
            sentence_count=item["sentence_count"],
        )
        db.add(chapter)

    db.commit()
    db.refresh(document)
    return document


def rebuild_chapters(db: Session, document_id: int) -> list[Chapter]:
    """
    Xóa chapters cũ và tạo lại từ layout_json đã cache.
    Dùng để apply title fix cho documents đã upload trước đó.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")

    # Xóa chapters cũ
    db.query(Chapter).filter(Chapter.document_id == document_id).delete()

    chapter_items = build_chapters_from_semantic_blocks(document.layout_json)

    if not chapter_items:
        chapter_items = split_chapters(document.raw_text)

    new_chapters = []
    for idx, item in enumerate(chapter_items, start=1):
        chapter = Chapter(
            document_id=document_id,
            chapter_index=idx,
            title=item["title"],
            raw_text=item["raw_text"],
            paragraph_count=item["paragraph_count"],
            sentence_count=item["sentence_count"],
        )
        db.add(chapter)
        new_chapters.append(chapter)

    db.commit()
    return new_chapters


def get_all_documents(db: Session) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()