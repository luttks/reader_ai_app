import re

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "then", "than", "of", "to", "in", "on", "at",
    "for", "with", "by", "from", "as", "it", "this", "that", "these", "those",
    "we", "you", "they", "he", "she", "i", "my", "our", "your", "their",
    "can", "could", "should", "would", "will", "may", "might", "must",
    "do", "does", "did", "have", "has", "had",
}

def tokenize(text: str) -> list[str]:
    if not text:
        return []

    tokens = re.findall(r"[a-zA-ZÀ-ỹ0-9]+", text.lower())
    return tokens

def filter_tokens(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]