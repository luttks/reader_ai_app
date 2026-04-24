from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chapter import Chapter
from app.models.document import Document
from app.schemas.chapter import ChapterResponse, ChapterListItemResponse
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentDetailResponse
from fastapi import Query

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    from app.services.document_service import get_all_documents
    return get_all_documents(db)


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/documents/{document_id}/chapters", response_model=list[ChapterListItemResponse])
def list_document_chapters_api(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.document_id == document_id)
        .order_by(Chapter.chapter_index.asc())
        .all()
    )

    return chapters


@router.post("/documents/{document_id}/chapters", response_model=list[ChapterListItemResponse])
def rebuild_chapters_api(document_id: int, db: Session = Depends(get_db)):
    """
    Rebuild chapters from cached layout_json — applies title fixes
    for documents uploaded before the fix was deployed.
    """
    try:
        from app.services.document_service import rebuild_chapters
        chapters = rebuild_chapters(db, document_id)
        return chapters
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebuild chapters: {str(e)}"
        ) from e


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


# ---------------------------------------------------------------------------
# Layout — served from DB cache (instant, no re-parsing)
# ---------------------------------------------------------------------------
@router.get("/documents/{document_id}/layout")
def inspect_document_layout_api(document_id: int, db: Session = Depends(get_db)):
    """
    Returns cached layout_json from DB.
    If not cached yet (e.g. document was uploaded before this fix),
    parses on-demand and caches it for next time.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.file_type.lower() != "pdf":
        raise HTTPException(status_code=400,
                          detail="Layout inspection is only available for PDF files")

    # Serve from cache
    if document.layout_json is not None:
        return document.layout_json

    # First-time parse + cache (backwards compat for existing documents)
    from app.services.layout_service import inspect_pdf_layout
    layout = inspect_pdf_layout(document.file_path)
    document.layout_json = layout
    db.commit()
    return layout


# ---------------------------------------------------------------------------
# Full document data — raw_text + layout + chapters from DB in one call
# ---------------------------------------------------------------------------
@router.get("/documents/{document_id}/full")
def get_document_full(document_id: int, db: Session = Depends(get_db)):
    """
    Returns everything about a document in one call — no re-parsing.
    Includes: raw_text, semantic_blocks, paragraphs, pages, and chapters.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.document_id == document_id)
        .order_by(Chapter.chapter_index.asc())
        .all()
    )

    layout = document.layout_json

    return {
        "id": document.id,
        "title": document.title,
        "file_name": document.file_name,
        "file_type": document.file_type,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        # Text
        "raw_text": document.raw_text or "",
        # Layout (from DB cache — instant)
        "layout": layout,
        # Chapters
        "chapters": chapters,
    }

@router.get("/documents/{document_id}/chunks")
def get_document_chunks(
    document_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    layout = document.layout_json or {}

    blocks = layout.get("semantic_blocks") or []

    readable_blocks = [
        block.get("text", "").strip()
        for block in blocks
        if block.get("text", "").strip()
        and block.get("type") not in {"toc_heading", "toc_item", "ebook_info"}
    ]

    if not readable_blocks:
        readable_blocks = [
            p.strip()
            for p in (document.raw_text or "").split("\n\n")
            if p.strip()
        ]

    start = (page - 1) * size
    end = start + size

    return {
        "document_id": document.id,
        "page": page,
        "size": size,
        "total": len(readable_blocks),
        "chunks": readable_blocks[start:end],
        "has_more": end < len(readable_blocks),
    }