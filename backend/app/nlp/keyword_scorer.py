from collections import Counter

from app.nlp.sentence_splitter import split_sentences
from app.nlp.tokenizer import tokenize, filter_tokens


def build_frequency_map(text: str) -> Counter:
    tokens = filter_tokens(tokenize(text))
    return Counter(tokens)

def score_sentence(sentence: str, freq_map: Counter, sentence_index: int, total_sentences: int) -> float:   
    tokens = filter_tokens(tokenize(sentence))
    if not tokens:
        return 0.0

    # keyword score
    keyword_score = sum(freq_map.get(token, 0) for token in tokens ) / len(tokens)

    # length score
    length = len(tokens)
    if length < 4:
        length_score = 0.4
    elif length < 30:
        length_score = 1.0
    else:
        length_score = 0.7

    # position score: uu tien dau van ban nhe
    if total_sentences <= 1:
        position_score = 1.0
    elif sentence_index == 0:
        position_score = 1.15
    elif sentence_index == total_sentences - 1:
        position_score = 0.95
    else:
        position_score = 1.0

    # final score
    return keyword_score * length_score * position_score

def summarize_extractive(text: str, level: str = "medium") -> str:
    sentences = split_sentences(text)

    if not sentences:
        return ""
    if len(sentences) <= 2:
        return " ".join(sentences)

    ratio_map = {
        "short": 0.2,
        "medium": 0.35,
        "long": 0.5,
    }
    
    ratio = ratio_map.get(level, 0.35)

    freq_map = build_frequency_map(text)

    scored = []
    for idx, sent in enumerate(sentences):
        score = score_sentence(sent, freq_map, idx, len(sentences))
        scored.append((idx, sent, score))

    k = max(1, round(len(sentences) * ratio))
    top_sentences = sorted(scored, key=lambda x: x[2], reverse=True)[:k]
    top_sentences = sorted(top_sentences, key=lambda x: x[0])

    return " ".join(item[1].strip() for item in top_sentences)