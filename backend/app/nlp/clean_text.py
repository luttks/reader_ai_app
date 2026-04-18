import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # remove null bytes 
    text = text.replace("\x00", " ")

    # standardize newline windows
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # remove whitespace in end of lines
    lines = [line.strip() for line in text.split("\n")]
    
    # combine lines back together
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # combine spaces 
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    return cleaned.strip()