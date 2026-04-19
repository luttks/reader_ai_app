import re

from app.nlp.paragraph_splitter import split_paragraphs
from app.nlp.sentence_splitter import split_sentences


def is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    if len(stripped) > 120:
        return False

    lowered = stripped.lower()

    patterns = [
        r"^chapter\s+\d+[\s:.-]*.*$",
        r"^chapter\s+[ivxlcdm]+[\s:.-]*.*$",
        r"^chương\s+\d+[\s:.-]*.*$",
        r"^chương\s+[ivxlcdm]+[\s:.-]*.*$",
        r"^\d+\.\s+.+$",
        r"^[ivxlcdm]+\.\s+.+$",
        r"^section\s+\d+[\s:.-]*.*$",
    ]

    for pattern in patterns:
        if re.match(pattern, lowered, re.IGNORECASE):
            return True

    words = stripped.split()
    if 1 <= len(words) <= 10 and stripped.isupper():
        return True

    return False


def build_chapter(title: str, lines: list[str]) -> dict | None:
    text = "\n".join(line.rstrip() for line in lines).strip()
    if not text:
        return None

    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)

    return {
        "title": title,
        "raw_text": text,
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
    }


def split_chapters(text: str) -> list[dict]:
    if not text or not text.strip():
        return [{
            "title": "Full Document",
            "raw_text": "",
            "paragraph_count": 0,
            "sentence_count": 0,
        }]

    lines = text.splitlines()

    chapters: list[dict] = []
    current_title: str | None = None
    current_lines: list[str] = []
    preface_lines: list[str] = []
    found_heading = False

    for raw_line in lines:
        stripped = raw_line.strip()

        if not stripped:
            # giữ ranh giới paragraph
            if current_title is not None:
                current_lines.append("")
            elif preface_lines:
                preface_lines.append("")
            continue

        if is_heading(stripped):
            found_heading = True

            # nếu đang có chapter trước đó, chốt nó lại
            if current_title is not None:
                chapter = build_chapter(current_title, current_lines)
                if chapter:
                    chapters.append(chapter)

            # nếu có phần mở đầu trước chapter đầu tiên, lưu thành preface
            elif preface_lines:
                preface = build_chapter("Preface", preface_lines)
                if preface:
                    chapters.append(preface)
                preface_lines = []

            current_title = stripped
            current_lines = []
        else:
            if current_title is not None:
                current_lines.append(raw_line)
            else:
                preface_lines.append(raw_line)

    # chốt chapter cuối
    if current_title is not None:
        chapter = build_chapter(current_title, current_lines)
        if chapter:
            chapters.append(chapter)

    # nếu không có heading nào, trả full document
    if not found_heading:
        paragraphs = split_paragraphs(text)
        sentences = split_sentences(text)
        return [{
            "title": "Full Document",
            "raw_text": text.strip(),
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
        }]

    # nếu có heading nhưng chapter body rỗng, ít nhất vẫn fallback an toàn
    if not chapters:
        paragraphs = split_paragraphs(text)
        sentences = split_sentences(text)
        return [{
            "title": "Full Document",
            "raw_text": text.strip(),
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
        }]

    return chapters