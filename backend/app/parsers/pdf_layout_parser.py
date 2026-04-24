import re
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any
from app.parsers.layout_cleaner import (
    clean_semantic_blocks,
    semantic_blocks_to_text,
    normalize_space,
    is_page_number_line,
)
import fitz
from app.nlp.vietnamese_encoding_recover import fix_broken_vietnamese


@dataclass
class LayoutLine:
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

def normalize_line(text: str) -> str:
    text = fix_broken_vietnamese(text)
    return normalize_space(text)


def get_page_dimensions(lines: list[LayoutLine]) -> tuple[float, float]:
    """Get estimated page dimensions from lines."""
    if not lines:
        return (612.0, 792.0)  # Default Letter size
    
    # Get max y1 across all lines as page height
    max_y = max(line.y1 for line in lines if line.page_number == lines[0].page_number)
    return (612.0, max_y * 1.1)  # Estimate height with margin


def extract_lines_from_pdf(file_path: str) -> list[LayoutLine]:
    """Extract all text lines from PDF with layout information."""
    doc = fitz.open(file_path)
    lines: list[LayoutLine] = []

    try:
        for page_idx, page in enumerate(doc, start=1):
            page_dict: dict[str, Any] = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            for block_idx, block in enumerate(blocks):
                if block.get("type") != 0:
                    continue

                for line_idx, line in enumerate(block.get("lines", [])):
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    text = normalize_line("".join(span.get("text", "") for span in spans))
                    if not text:
                        continue

                    x0, y0, x1, y1 = line.get("bbox", [0, 0, 0, 0])

                    font_sizes = [
                        span.get("size")
                        for span in spans
                        if span.get("size") is not None
                    ]
                    avg_font_size = (
                        sum(font_sizes) / len(font_sizes)
                        if font_sizes
                        else None
                    )

                    is_pg_num = is_page_number_line(text)

                    lines.append(
                        LayoutLine(
                            page_number=page_idx,
                            text=text,
                            x0=round(x0, 2),
                            y0=round(y0, 2),
                            x1=round(x1, 2),
                            y1=round(y1, 2),
                            block_index=block_idx,
                            line_index=line_idx,
                            font_size=round(avg_font_size, 2) if avg_font_size else None,
                            is_page_number=is_pg_num,
                        )
                    )
    finally:
        doc.close()

    return lines


def detect_repeated_headers_footers(lines: list[LayoutLine]) -> set[str]:
    """
    Detect running header/footer lines that repeat across pages.
    
    Strategy:
    - Lines appearing in top 12% or bottom 88% of page
    - Repeated across multiple pages (count >= 3 or >= 15% of pages)
    - Common patterns: book title, author name, chapter name
    """
    if not lines:
        return set()

    # Group by page
    page_to_lines: dict[int, list[LayoutLine]] = {}
    for line in lines:
        page_to_lines.setdefault(line.page_number, []).append(line)

    if not page_to_lines:
        return set()

    # Estimate page height from first page
    first_page_lines = page_to_lines.get(1, [])
    if not first_page_lines:
        first_page_lines = list(page_to_lines.values())[0]
    
    estimated_page_height = max((line.y1 for line in first_page_lines), default=792.0)
    
    top_threshold = estimated_page_height * 0.12
    bottom_threshold = estimated_page_height * 0.88

    candidate_texts = []
    for page_number, page_lines in page_to_lines.items():
        if not page_lines:
            continue

        for line in page_lines:
            text = normalize_line(line.text).lower()
            if not text:
                continue

            # Check if line is in header or footer zone
            in_top = line.y0 <= top_threshold
            in_bottom = line.y1 >= bottom_threshold

            if in_top or in_bottom:
                candidate_texts.append(text)

    # Count occurrences
    counts = Counter(candidate_texts)
    total_pages = len(page_to_lines)
    min_occurrences = max(3, int(total_pages * 0.15))

    repeated = {
        text
        for text, count in counts.items()
        if count >= min_occurrences
    }

    return repeated


def detect_running_chapter_headers(lines: list[LayoutLine]) -> set[str]:
    """
    Detect running chapter/part headings that appear at top of content pages.
    
    These are NOT headers in the technical sense (header zone), but
    chapter names that PDF readers display at top of pages.
    
    Example: "PHẦN 1: XÁC ĐỊNH QUAN ĐIỂM" appears on pages 3,4,5
    Pages 3-4: TOC pages (real)
    Page 5: Content page (running header - should be removed)
    """
    if not lines:
        return set()

    # Group lines by page
    page_to_lines: dict[int, list[LayoutLine]] = {}
    for line in lines:
        page_to_lines.setdefault(line.page_number, []).append(line)

    # Find all heading-like lines
    heading_pattern = re.compile(
        r"^(PHẦN|CHƯƠNG)\s+\d+", re.IGNORECASE
    )

    heading_candidates: dict[str, dict] = {}

    for page_number, page_lines in page_to_lines.items():
        # Sort by y position
        page_lines_sorted = sorted(page_lines, key=lambda x: x.y0)
        
        for i, line in enumerate(page_lines_sorted):
            text = normalize_line(line.text)
            if not text:
                continue

            if not heading_pattern.match(text):
                continue

            # Check if it's near top of page (first 15%)
            estimated_page_height = max((l.y1 for l in page_lines), default=792.0)
            if line.y0 > estimated_page_height * 0.15:
                continue  # Not a running header

            if text not in heading_candidates:
                heading_candidates[text] = {
                    "count": 0,
                    "pages": [],
                    "line_index": i,
                }
            heading_candidates[text]["count"] += 1
            heading_candidates[text]["pages"].append(page_number)

    # If a heading appears 3+ times and NOT in first few pages, it's running header
    result = set()
    for text, info in heading_candidates.items():
        if info["count"] >= 3:
            # Check if it appears in early pages (pages 1-4 are usually real headings)
            early_pages = [p for p in info["pages"] if p <= 4]
            if len(early_pages) < info["count"]:
                # Some occurrences are NOT in early pages = running header
                result.add(text)

    return result


def clean_layout_lines(lines: list[LayoutLine]) -> list[LayoutLine]:
    """Remove headers, footers, and page numbers from lines."""
    repeated = detect_repeated_headers_footers(lines)
    running_chapters = detect_running_chapter_headers(lines)

    cleaned = []
    prev_was_header = False

    for line in lines:
        normalized = normalize_line(line.text).lower()

        # Check if line is a running header
        is_running_chapter = normalize_line(line.text) in running_chapters

        # Check if line is repeated header/footer
        is_repeated_hf = normalized in repeated

        # Check if page number
        is_pg_num = line.is_page_number

        # Mark as header/footer
        if is_repeated_hf or is_running_chapter:
            line.is_header_footer = True

        # Skip header/footer and page number lines
        if line.is_header_footer or is_pg_num:
            prev_was_header = True
            continue

        # Reset flag on real content
        prev_was_header = False
        cleaned.append(line)

    return cleaned


def merge_lines_to_paragraphs(
    lines: list[LayoutLine],
    vertical_gap_threshold: float = 12.0,
) -> list[dict]:
    """
    Merge lines into paragraphs based on vertical proximity.
    
    Args:
        lines: List of layout lines
        vertical_gap_threshold: Gap (in points) that triggers new paragraph.
                              Default 12pt works for most book layouts.
    """
    paragraphs = []

    # Group by page
    page_groups: dict[int, list[LayoutLine]] = {}
    for line in lines:
        page_groups.setdefault(line.page_number, []).append(line)

    for page_number, page_lines in page_groups.items():
        # Sort by vertical position (y0), then horizontal (x0)
        page_lines = sorted(page_lines, key=lambda x: (x.y0, x.x0))

        current_lines: list[LayoutLine] = []
        prev_line: LayoutLine | None = None

        for line in page_lines:
            if prev_line is None:
                current_lines = [line]
                prev_line = line
                continue

            vertical_gap = line.y0 - prev_line.y1

            # Check horizontal alignment (should be same column)
            # If gap is large, start new paragraph
            if vertical_gap > vertical_gap_threshold:
                paragraphs.append(build_paragraph(page_number, current_lines))
                current_lines = [line]
            else:
                current_lines.append(line)

            prev_line = line

        if current_lines:
            paragraphs.append(build_paragraph(page_number, current_lines))

    return paragraphs


def build_paragraph(page_number: int, lines: list[LayoutLine]) -> dict:
    """Build a paragraph dict from sorted lines."""
    text = " ".join(line.text.strip() for line in lines)
    text = re.sub(r"\s+", " ", text).strip()

    return {
        "page_number": page_number,
        "text": text,
        "line_count": len(lines),
        "bbox": {
            "x0": min(line.x0 for line in lines),
            "y0": min(line.y0 for line in lines),
            "x1": max(line.x1 for line in lines),
            "y1": max(line.y1 for line in lines),
        },
        "lines": [asdict(line) for line in lines],
    }


def parse_pdf_layout(file_path: str) -> dict:
    """
    Full PDF layout parsing pipeline.
    
    Steps:
    1. Extract all lines with layout info
    2. Clean: remove headers, footers, page numbers
    3. Merge lines into paragraphs
    4. Semantic classification and cleaning
    5. Convert to readable text
    """
    # Extract raw lines
    raw_lines = extract_lines_from_pdf(file_path)
    
    # Clean: remove headers/footers
    cleaned_lines = clean_layout_lines(raw_lines)
    
    # Build paragraphs
    paragraphs = merge_lines_to_paragraphs(cleaned_lines)
    
    # Semantic classification
    semantic_blocks = clean_semantic_blocks(paragraphs)
    
    # Convert to text
    raw_text = semantic_blocks_to_text(semantic_blocks)

    return {
        "line_count_raw": len(raw_lines),
        "line_count_cleaned": len(cleaned_lines),
        "paragraph_count": len(paragraphs),
        "semantic_block_count": len(semantic_blocks),
        "raw_text": raw_text,
        "paragraphs": paragraphs,
        "semantic_blocks": semantic_blocks,
        "pages": build_pages(cleaned_lines),
    }


def build_pages(lines: list[LayoutLine]) -> list[dict]:
    """Build page representations from cleaned lines."""
    page_groups: dict[int, list[LayoutLine]] = {}

    for line in lines:
        page_groups.setdefault(line.page_number, []).append(line)

    pages = []
    for page_number, page_lines in sorted(page_groups.items()):
        page_lines = sorted(page_lines, key=lambda x: (x.y0, x.x0))
        pages.append({
            "page_number": page_number,
            "text": "\n".join(line.text for line in page_lines),
            "lines": [asdict(line) for line in page_lines],
        })

    return pages


# def is_text_broken(text: str) -> bool:
#     if not text:
#         return False

#     broken_chars = "öüäïåîûùñçð"
#     count = sum(1 for c in text if c in broken_chars)

#     return count >= 5