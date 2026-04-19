import re

def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []


    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = [p.strip() for p in parts if p.strip()]
    return sentences