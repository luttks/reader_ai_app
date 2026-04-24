import re
from app.nlp.vietnamese_encoding_recover import fix_broken_vietnamese


def normalize_space(text: str) -> str:
    if not text:
        return ""

    text = fix_broken_vietnamese(text) 
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_part_heading(text: str) -> bool:
    """Detect part headings: PHẦN N: NAME or PART N: NAME"""
    text = normalize_space(text)
    # Try exact match first
    if re.match(r"^PHẦN\s+\d+[\s:.-].*", text, re.IGNORECASE):
        return True
    if re.match(r"^PART\s+\d", text, re.IGNORECASE):
        return True
    # Handle OCR: strip all accents from PHẦN and check for PHAN
    import unicodedata
    text_nfd = unicodedata.normalize('NFD', text)
    # Extract first word and check if NFD form looks like PHAN
    words = text_nfd.upper().split()
    if words and len(words[0]) >= 4:
        first_word = words[0]
        # Check if NFD form matches PHẦN (P + combining acute + A + combining grave + N)
        # or already corrupted forms like PHẬN, PHẨN, etc.
        has_P = 'P' in first_word
        has_H = 'H' in first_word
        has_A_or_combining = any(c in first_word for c in ['A', '\u0300', '\u0301', '\u0302', '\u0303', '\u0306', '\u0309', '\u030B', '\u030C', '\u0312', '\u0313', '\u031B'])
        has_N = 'N' in first_word
        if has_P and has_H and has_A_or_combining and has_N:
            # Now check it has a number after
            if re.search(r"(PHẦN|PHAN|PH[À-Ỹ]N)\s+\d", text):
                return True
    return False


def is_chapter_heading(text: str) -> bool:
    text = normalize_space(text)
    return bool(re.match(r"^CHƯƠNG\s+\d+[\s:.-].*", text, re.IGNORECASE))


def is_toc_heading(text: str) -> bool:
    text = normalize_space(text).upper()
    # Handle common Vietnamese TOC patterns (including OCR artifacts with wrong diacritics)
    # Normalize common OCR errors
    text = text.replace("Ụ", "Ụ").replace("Ụ", "Ụ")
    text = text.replace("Ụ", "Ụ").replace("Ụ", "Ụ")
    text = text.replace("Ử", "Ụ").replace("Ử", "Ụ")
    text = text.replace("Ự", "Ự").replace("Ự", "Ự")
    text = text.replace("Ữ", "Ữ").replace("Ữ", "Ữ")
    text = text.replace("Ủ", "Ủ").replace("Ủ", "Ủ")
    # Remove punctuation for comparison
    text_clean = text.replace(":", "").replace(".", "").strip()
    toc_variants = ["MỤC LỤC", "MUC LUC", "MỤC LỤC", "MUC LUC",
                   "TABLE OF CONTENTS", "CONTENTS", "MUC LUC"]
    return text_clean in toc_variants


def is_toc_item(text: str) -> bool:
    text = normalize_space(text)
    # Match bullet points in TOC: • CHƯƠNG X or • PHẦN X or - CHƯƠNG X
    if re.match(r"^[•·\-\–\—]\s*(CHƯƠNG|PHẦN)\s+\d+", text, re.IGNORECASE):
        return True
    # Match numbered TOC items: 1. Chapter Title, I. Section Title
    if re.match(r"^\d+\.\s+", text) and any(
        kw in text.upper() for kw in ["CHƯƠNG", "PHẦN", "CHAPTER", "SECTION"]
    ):
        return True
    if re.match(r"^[IVXLCDM]+\.\s+", text, re.IGNORECASE) and len(text) < 100:
        return True
    return False


def is_ebook_info(text: str) -> bool:
    """
    Detect thong tin sach / ebook metadata:
    • Tên sách: ..., • Tác giả: ..., http://..., • Số trang: ...
    """
    text = normalize_space(text)
    # Bullet point metadata lines - allow arbitrary text between keyword and colon
    # e.g., "• Gõ ebook và soát chính tả: hoatigon"
    if re.match(r"^[•·\-\–\—]\s*(Tên|Tác|Dịch|Gõ|Sửa|Ngày|Số|Hình|Kích|Nhà|Trọng|Giá|Nxb|NXB)[^:]*:", text):
        return True
    # URL links (ebook library)
    if re.match(r"^https?://", text):
        return True
    # Short copyright/credits lines
    if re.match(r"^Copyright|©|\d{4}\s*-\s*\d{4}", text, re.IGNORECASE):
        return True
    return False


def is_quote_author(text: str) -> bool:
    text = normalize_space(text)
    # Starts with underscore = author attribution (most reliable)
    if text.startswith("_"):
        return True
    # Short ALL CAPS text that looks like an author name
    # Be conservative: must NOT match heading patterns
    if len(text) < 60 and len(text) > 1:
        # Skip if it looks like a heading
        if re.match(r"^(PHẦN|PHAN|PART|CHƯƠNG|CHAPTER|SECTION)", text, re.IGNORECASE):
            return False
        if re.match(r"^\d+[\s.:-]", text):  # numbered heading
            return False
        # Count uppercase letters vs total letters
        letters = [c for c in text if c.isalpha() or c.isspace()]
        if letters:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio >= 0.7 and len([c for c in text if c.isalpha()]) >= 2:
                # Additional heuristic: author names typically don't have numbers or colons in the middle
                if not re.search(r"\d", text) or re.match(r"^[A-Z\s_]+$", text):
                    return True
    return False


def is_quote(text: str) -> bool:
    text = normalize_space(text)
    # Double curly quotes
    if text.startswith('"') and text.endswith('"'):
        return True
    # Left double curly quote
    if text.startswith('"') or text.startswith('\u201c'):
        return text.endswith('"') or text.endswith('\u201d')
    return False


def has_quote_markers(text: str) -> bool:
    """Check if text contains any quote markers anywhere."""
    text = normalize_space(text)
    return (
        '"' in text
        or '"' in text
        or '"' in text
        or '"' in text
        or '"' in text
        or '\u201c' in text
        or '\u201d' in text
    )


def is_drop_cap_line(line: dict) -> bool:
    """Detect drop cap: single large uppercase letter."""
    text = normalize_space(line.get("text", ""))
    font_size = line.get("font_size") or 0
    # Drop cap: single letter, uppercase, large font
    if len(text) == 1 and text.isupper() and font_size >= 30:
        return True
    # Vietnamese drop cap: single letter (may have diacritics)
    if len(text) == 1 and font_size >= 30:
        # Check if it's an uppercase letter (Latin or Vietnamese)
        if text.isupper() or re.match(r"^[A-ZÀ-Ỹ]$", text):
            return True
    return False


def is_page_number_line(text: str) -> bool:
    """Detect standalone page number lines."""
    text = normalize_space(text)
    # Just a number or dashes around a number: - 12 -, 12
    if re.fullmatch(r"-?\s*\d+\s*-?", text):
        return True
    return False


def is_running_header(text: str) -> bool:
    """
    Detect common running header/footer patterns:
    - Book title appearing on every page
    - Designer credits
    - Page number patterns
    - Document URLs
    """
    text = normalize_space(text)
    
    # Page number patterns: "- 2 -" or just "- 2 -"
    if re.match(r"^-?\s*\d+\s*-$", text):
        return True
    
    # Short URLs
    if re.match(r"^(https?://|www\.)[^\s]+$", text):
        return True
    
    # Common ebook design credits
    if re.match(r"^[Dd]esigned\s+by\s+", text):
        return True
    
    # Short book/app titles appearing alone
    book_titles = ["Never Eat Alone", "Đừng Bao Giờ Đi Ăn Một Mình", "Đừng bao giờ đi ăn một mình"]
    if text in book_titles:
        return True
    
    return False


def fix_broken_dropcap_word(text: str) -> str:
    """
    Fix broken drop cap words where the PDF split them across lines:
    "S ao" -> "Sao"
    "K hi" -> "Khi"
    "N hững" -> "Những"
    Works with Vietnamese diacritics.
    """
    # Pattern: single uppercase letter followed by lowercase/Vietnamese, separated by space
    # [A-Z] or Vietnamese uppercase [À-Ỹ] followed by space then lowercase [a-zà-ỹ]
    text = re.sub(r"\b([A-ZÀ-Ỹ])\s+([a-zà-ỹ]{1,3})\b", r"\1\2", text)
    # Also fix case where there's no space but text got broken weirdly
    # Single letter at start followed directly by lowercase (should be merged already)
    return normalize_space(text)


def fix_broken_quote(text: str) -> str:
    """
    Reconstruct broken quotes split across lines:
    Multiple lines that together form a quoted paragraph.
    """
    # If text starts with opening quote but no closing, leave as-is
    # If text has closing quote but no opening, might need to look at neighbors
    # This is handled at paragraph level
    return text


def classify_text(text: str) -> str:
    text = normalize_space(text)

    # Check TOC elements first
    if is_toc_heading(text):
        return "toc_heading"
    if is_toc_item(text):
        return "toc_item"
    if is_ebook_info(text):
        return "ebook_info"
    if is_part_heading(text):
        return "part_heading"
    if is_chapter_heading(text):
        return "chapter_heading"

    # Check quote-related
    if is_quote_author(text):
        return "quote_author"
    if is_quote(text):
        return "quote"

    return "paragraph"


def build_semantic_block(
    block_type: str,
    text: str,
    paragraph: dict,
    lines: list[dict] | None = None,
    source: str = "semantic_cleaner",
) -> dict:
    return {
        "type": block_type,
        "text": normalize_space(text),
        "page_number": paragraph.get("page_number"),
        "line_count": len(lines) if lines is not None else paragraph.get("line_count"),
        "bbox": paragraph.get("bbox"),
        "lines": lines if lines is not None else paragraph.get("lines", []),
        "source": source,
    }


def split_author_and_dropcap(paragraph: dict) -> list[dict]:
    """
    Handle paragraphs that mix quote author + drop cap + body text.
    Example:
        _MARGARET WHEATLEY
        S                 (large font)
        ao tôi lại...
        trong những ngày...
    
    Output:
    - quote_author: _MARGARET WHEATLEY
    - paragraph: Sao tôi lại... trong những ngày...
    """
    lines = paragraph.get("lines", [])
    result = []

    # Step 1: Separate ebook info, author line, and body
    ebook_info_line = None
    author_line = None
    body_lines = []

    for line in lines:
        line_text = normalize_space(line.get("text", ""))
        if not line_text:
            continue
        if is_ebook_info(line_text):
            ebook_info_line = line  # skip this
        elif is_quote_author(line_text):
            author_line = line
        else:
            body_lines.append(line)

    # Add author as separate block
    if author_line:
        result.append(
            build_semantic_block(
                block_type="quote_author",
                text=normalize_space(author_line.get("text", "")),
                paragraph=paragraph,
                lines=[author_line],
                source="split_author_and_dropcap",
            )
        )

    # Step 2: Merge drop cap with following line
    merged_texts = []
    merged_lines = []
    i = 0

    while i < len(body_lines):
        line = body_lines[i]
        text = normalize_space(line.get("text", ""))

        if not text:
            i += 1
            continue

        # Check for drop cap
        if is_drop_cap_line(line) and i + 1 < len(body_lines):
            next_line = body_lines[i + 1]
            next_text = normalize_space(next_line.get("text", ""))

            # Merge drop cap letter with next line
            # "S" + "ao tôi lại..." -> "Sao tôi lại..."
            combined_text = text + " " + next_text
            combined_lines = [line, next_line]

            # Also check if the next line also starts with text that should be merged
            # (for cases where drop cap span + first word span are separate)
            j = i + 2
            while j < len(body_lines):
                next_next_line = body_lines[j]
                next_next_text = normalize_space(next_next_line.get("text", ""))

                # If the text after drop cap was split again
                if next_next_text and len(next_next_text) <= 5:
                    # Likely a continuation of the first word
                    combined_text += next_next_text
                    combined_lines.append(next_next_line)
                    j += 1
                else:
                    break

            merged_texts.append(normalize_space(combined_text))
            merged_lines.extend(combined_lines)
            i = j
            continue

        merged_texts.append(text)
        merged_lines.append(line)
        i += 1

    # Step 3: Reconstruct full paragraph text
    full_text = normalize_space(" ".join(merged_texts))
    full_text = fix_broken_dropcap_word(full_text)

    if full_text:
        # Final classification
        block_type = classify_text(full_text)

        # Special case: if this is a quote (starts with opening quote)
        # but we already processed author separately, strip the opening quote
        if block_type == "quote" and author_line:
            # Remove the opening quote from body if author is separate
            full_text = full_text.lstrip('"\u201c\u2018')

        result.append(
            build_semantic_block(
                block_type=block_type,
                text=full_text,
                paragraph=paragraph,
                lines=merged_lines,
                source="dropcap_fixed",
            )
        )

    return result


def paragraph_contains_dropcap_or_author_mix(paragraph: dict) -> bool:
    """Check if paragraph has author attribution or drop cap that needs special handling."""
    lines = paragraph.get("lines", [])
    has_author = False
    has_dropcap = False
    has_quote_content = False

    for line in lines:
        text = normalize_space(line.get("text", ""))
        if is_quote_author(text):
            has_author = True
        if is_drop_cap_line(line):
            has_dropcap = True
        if has_quote_markers(text):
            has_quote_content = True

    return has_author or has_dropcap or (has_quote_content and len(lines) > 1)


def classify_paragraph(paragraph: dict) -> dict:
    text = normalize_space(paragraph.get("text", ""))
    block_type = classify_text(text)
    return build_semantic_block(
        block_type=block_type,
        text=text,
        paragraph=paragraph,
        source="classified_paragraph",
    )


def clean_semantic_blocks(paragraphs: list[dict]) -> list[dict]:
    """
    Main entry point: classify and clean semantic blocks from raw paragraphs.

    Pipeline:
    1. Identify TOC pages (by page number or high density of TOC items)
    2. Skip all content from TOC pages
    3. Skip ebook metadata throughout
    4. Skip running headers/footers
    5. Classify remaining blocks
    6. Filter duplicate running headers (keep first occurrence)
    """
    semantic_blocks: list[dict] = []

    # Group paragraphs by page number
    page_blocks: dict[int, list[tuple]] = {}
    for paragraph in paragraphs:
        text = normalize_space(paragraph.get("text", ""))
        if not text:
            continue
        page_num = paragraph.get("page_number", 0)
        block_type = classify_text(text)
        page_blocks.setdefault(page_num, []).append((paragraph, block_type, text))

    if not page_blocks:
        return []

    # Identify TOC pages: early pages with high density of TOC items
    toc_pages: set[int] = set()
    for page_num, blocks in sorted(page_blocks.items()):
        if page_num <= 5:
            toc_items_count = sum(
                1 for _, bt, _ in blocks
                if bt in ("toc_heading", "toc_item")
            )
            if len(blocks) > 0 and toc_items_count / len(blocks) > 0.4:
                toc_pages.add(page_num)
        elif page_num > 5:
            toc_items_count = sum(
                1 for _, bt, _ in blocks
                if bt in ("toc_heading", "toc_item")
            )
            if len(blocks) > 0 and toc_items_count / len(blocks) > 0.6:
                toc_pages.add(page_num)

    # Track headings by page to identify running headers
    # A heading is a running header if it appears in 3+ pages
    heading_by_page: dict[str, list[tuple[int, float]]] = {}

    # Process all paragraphs
    for page_num in sorted(page_blocks.keys()):
        blocks = page_blocks[page_num]

        for paragraph, block_type, text in blocks:
            # Skip TOC pages entirely (except TOC heading)
            if page_num in toc_pages:
                if block_type == "toc_heading":
                    semantic_blocks.append(build_semantic_block(
                        block_type="toc_heading",
                        text=text,
                        paragraph=paragraph,
                        source="toc_page",
                    ))
                continue

            # Skip ebook info
            if block_type == "ebook_info":
                continue

            # Skip running headers (constant headers like book title)
            if is_running_header(text):
                continue

            # Skip page numbers
            if is_page_number_line(text):
                continue

            # Track headings for running header detection
            if block_type in ("part_heading", "chapter_heading"):
                lines = paragraph.get("lines", [])
                first_y = lines[0].get("y0", 999) if lines else 999
                heading_by_page.setdefault(text, []).append((page_num, first_y))

            # Special handling for paragraphs with author/dropcap
            if paragraph_contains_dropcap_or_author_mix(paragraph):
                fixed_blocks = split_author_and_dropcap(paragraph)
                for block in fixed_blocks:
                    if block.get("type") == "ebook_info":
                        continue
                    semantic_blocks.append(block)
                continue

            # Normal paragraph
            semantic_blocks.append(build_semantic_block(
                block_type=block_type,
                text=text,
                paragraph=paragraph,
                source="classified_paragraph",
            ))

    # Filter running headers from semantic blocks
    # A heading is a running header if it appears 3+ times AND near top of page
    running_headers: set[str] = set()
    for heading_text, occurrences in heading_by_page.items():
        if len(occurrences) >= 3:
            positions = [y for _, y in occurrences]
            if min(positions) < 150:
                running_headers.add(heading_text)

    if running_headers:
        # Filter out duplicates, keeping only the first occurrence in content
        kept: set[str] = set()
        filtered: list[dict] = []
        for block in semantic_blocks:
            text = normalize_space(block.get("text", ""))
            btype = block.get("type", "")
            if text in running_headers and btype in ("part_heading", "chapter_heading"):
                if text not in kept:
                    kept.add(text)
                    filtered.append(block)
                # Skip duplicates
            else:
                filtered.append(block)
        semantic_blocks = filtered

    return semantic_blocks


def filter_running_headers(blocks: list[dict]) -> list[dict]:
    """
    Remove running headers from content.
    
    Running headers appear:
    1. At top of page (high y position)
    2. Repeated across multiple pages
    3. Are headings (part_heading, chapter_heading)
    
    Strategy:
    - If a heading appears at the very top of a content page AND is short
      AND it repeats, mark as header
    """
    if len(blocks) < 4:
        return blocks
    
    # Count heading occurrences
    heading_texts: dict[str, dict] = {}
    for block in blocks:
        btype = block.get("type", "")
        if btype not in ("part_heading", "chapter_heading"):
            continue
        text = normalize_space(block.get("text", ""))
        if not text or len(text) > 80:
            continue
        
        # Check position (first block on page?)
        lines = block.get("lines", [])
        first_line_y = lines[0].get("y0", 999) if lines else 999
        
        if text not in heading_texts:
            heading_texts[text] = {
                "count": 0,
                "positions": [],
                "types": [],
            }
        heading_texts[text]["count"] += 1
        heading_texts[text]["positions"].append(first_line_y)
        heading_texts[text]["types"].append(btype)
    
    # Headings that appear multiple times are likely running headers
    running_headers = {
        text for text, info in heading_texts.items()
        if info["count"] >= 3  # Appears 3+ times = header
        and min(info["positions"]) < 200  # Always near top of page
    }
    
    if not running_headers:
        return blocks
    
    # Filter out running headers, but keep the FIRST occurrence
    # (first "PHẦN 1" on page 5 IS real content)
    kept_first: set[str] = set()
    result = []
    
    for block in blocks:
        text = normalize_space(block.get("text", ""))
        btype = block.get("type", "")
        
        if text in running_headers and btype in ("part_heading", "chapter_heading"):
            # Keep only the first occurrence
            if text not in kept_first:
                kept_first.add(text)
                result.append(block)
            # Skip duplicates
            continue
        
        result.append(block)
    
    return result


def semantic_blocks_to_text(blocks: list[dict]) -> str:
    """
    Convert semantic blocks to readable text.
    Groups: preserve structure with double newlines between blocks.
    """
    output_parts = []
    
    prev_type = None
    for block in blocks:
        text = normalize_space(block.get("text", ""))
        if not text:
            continue
        
        btype = block.get("type", "")
        
        # Add extra spacing before major headings
        if btype in ("part_heading", "chapter_heading") and prev_type in ("paragraph", "quote"):
            output_parts.append("")
        
        output_parts.append(text)
        prev_type = btype
    
    return "\n\n".join(output_parts)
