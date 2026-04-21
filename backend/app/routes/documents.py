from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chapter import Chapter
from app.models.document import Document
from app.schemas.chapter import ChapterResponse, ChapterListItemResponse
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentDetailResponse
from app.services.document_service import (
    # create_document,
    get_all_documents,
    get_document_by_id,
)

# router = APIRouter(prefix="/documents", tags=["documents"])
router = APIRouter(tags=["documents"])

# @router.post("", response_model=DocumentResponse)
# def create_document_api(
#     payload: DocumentCreate,
#     db: Session = Depends(get_db)
# ):
#     return create_document(db, payload)


# @router.get("", response_model=list[DocumentResponse])
# def list_documents_api(db: Session = Depends(get_db)):
#     return get_all_documents(db)


# @router.get("/{document_id}", response_model=DocumentDetailResponse)
# def get_document_api(document_id: int, db: Session = Depends(get_db)):
#     document = get_document_by_id(db, document_id)
#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")
#     return document

@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return get_all_documents(db)

@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
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

@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter