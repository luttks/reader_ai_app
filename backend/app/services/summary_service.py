from sqlalchemy.orm import Session

from app.models.summary import Summary
from app.models.document import Document
from app.models.chapter import Chapter
from app.nlp.keyword_scorer import summarize_extractive

def summarize_chapter(db: Session,document_id: int, chapter_id: int, level: str) -> Summary:
    chapter = (
        db.query(Chapter)
        .filter(Chapter.document_id == document_id, Chapter.id == chapter_id)
        .first()
    )
    if not chapter:
        raise ValueError("Chapter not found")

    summary_text = summarize_extractive(chapter.raw_text, level=level)

    summary = Summary(
        document_id=document_id,
        chapter_id=chapter_id,
        level=level,
        summary_text=summary_text,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary

def summarize_document(db: Session, document_id: int, level: str) -> Summary:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError("Document not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.document_id == document_id)
        .order_by(Chapter.chapter_index.asc())
        .all()
    )

    if not chapters:
        text = document.raw_text
    else:
        text = "\n\n".join(ch.raw_text for ch in chapters if ch.raw_text.strip())

    summary_text = summarize_extractive(text, level=level)

    summary = Summary(
        document_id=document_id,
        chapter_id=None,
        level=level,
        summary_text=summary_text,
    )
    
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary
