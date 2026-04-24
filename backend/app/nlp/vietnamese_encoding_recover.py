import re

# mapping phổ biến PDF lỗi tiếng Việt
VIETNAMESE_FIXES = {
    "ö": "o",
    "ü": "u",
    "ä": "a",
    "ï": "i",
    "ê": "e",
    "å": "a",
    "ã": "a",
    "â": "a",
    "î": "i",
    "û": "u",
    "ù": "u",
    "ñ": "n",
    "ç": "c",
    "ð": "đ",
}

def basic_char_fix(text: str) -> str:
    for k, v in VIETNAMESE_FIXES.items():
        text = text.replace(k, v)
    return text


def fix_broken_vietnamese(text: str) -> str:
    """
    Fix các lỗi kiểu:
    Cöng -> Công
    Trñ -> Trí
    Viït -> Việt
    """

    if not text:
        return ""

    text = basic_char_fix(text)

    # fix pattern phổ biến
    patterns = [
        (r"C[oö]ng", "Công"),
        (r"Tr[iï] ", "Trí "),
        (r"Vi[eï]t", "Việt"),
        (r"Th[oö]i", "Thói"),
        (r"quen", "quen"),
        (r"th[aà]nh", "thành"),
        (r"đ[aà]t", "đạt"),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text