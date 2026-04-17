from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.document_service import (
    create_document,
    get_all_documents,
    get_document_by_id,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse)
def create_document_api(
    payload: DocumentCreate,
    db: Session = Depends(get_db)
):
    return create_document(db, payload)


@router.get("", response_model=list[DocumentResponse])
def list_documents_api(db: Session = Depends(get_db)):
    return get_all_documents(db)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_api(document_id: int, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document