import re

def split_paragraphs(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    blocks = re.split(r"\n\s*\n+", text)
    paragraphs = [block.strip() for block in blocks if block.strip()]
    return paragraphs