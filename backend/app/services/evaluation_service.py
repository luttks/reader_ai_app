import json
import os
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chapter import Chapter
from app.models.document import Document
from app.nlp.keyword_scorer import summarize_extractive
from app.nlp.sentence_splitter import split_sentences
from app.nlp.tokenizer import tokenize
from app.schemas.evaluation import EvaluationResponse, LevelEvaluationResult


LEVELS = ["short", "medium", "long"]


def ensure_log_dir() -> None:
    os.makedirs(settings.LOG_DIR, exist_ok=True)


def count_words(text: str) -> int:
    return len(tokenize(text))


def evaluate_text_levels(
    text: str,
    document_id: int,
    chapter_id: int | None,
    scope: str,
    title: str,
) -> EvaluationResponse:
    ensure_log_dir()

    original_sentences = split_sentences(text)
    original_sentence_count = len(original_sentences)
    original_word_count = count_words(text)

    results: list[LevelEvaluationResult] = []

    for level in LEVELS:
        start = time.perf_counter()
        summary_text = summarize_extractive(text, level=level)
        elapsed_ms = (time.perf_counter() - start) * 1000

        summary_sentence_count = len(split_sentences(summary_text))
        summary_word_count = count_words(summary_text)

        compression_ratio = 0.0
        if original_word_count > 0:
            compression_ratio = round(summary_word_count / original_word_count, 4)

        results.append(
            LevelEvaluationResult(
                level=level,
                summary_text=summary_text,
                processing_time_ms=round(elapsed_ms, 3),
                original_sentence_count=original_sentence_count,
                summary_sentence_count=summary_sentence_count,
                original_word_count=original_word_count,
                summary_word_count=summary_word_count,
                compression_ratio=compression_ratio,
            )
        )

    evaluated_at = datetime.now(timezone.utc)
    log_path = os.path.join(settings.LOG_DIR, "evaluation_logs.jsonl")

    log_record = {
        "document_id": document_id,
        "chapter_id": chapter_id,
        "scope": scope,
        "title": title,
        "evaluated_at": evaluated_at.isoformat(),
        "results": [result.model_dump() for result in results],
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_record, ensure_ascii=False) + "\n")

    return EvaluationResponse(
        document_id=document_id,
        chapter_id=chapter_id,
        scope=scope,
        title=title,
        evaluated_at=evaluated_at,
        results=results,
        log_file=log_path,
    )


def evaluate_summary(db: Session, document_id: int, chapter_id: int | None) -> EvaluationResponse:
    if chapter_id is not None:
        chapter = (
            db.query(Chapter)
            .filter(Chapter.id == chapter_id, Chapter.document_id == document_id)
            .first()
        )
        if not chapter:
            raise ValueError("Chapter not found")

        return evaluate_text_levels(
            text=chapter.raw_text,
            document_id=document_id,
            chapter_id=chapter_id,
            scope="chapter",
            title=chapter.title,
        )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.document_id == document_id)
        .order_by(Chapter.chapter_index.asc())
        .all()
    )

    if chapters:
        text = "\n\n".join(ch.raw_text for ch in chapters if ch.raw_text.strip())
    else:
        text = document.raw_text

    return evaluate_text_levels(
        text=text,
        document_id=document_id,
        chapter_id=None,
        scope="document",
        title=document.title,
    )