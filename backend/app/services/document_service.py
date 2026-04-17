from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate


def create_document(db: Session, payload: DocumentCreate) -> Document:
    document = Document(
        title=payload.title,
        file_name=payload.file_name,
        file_type=payload.file_type,
        file_path=payload.file_path,
        raw_text=payload.raw_text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_all_documents(db: Session) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()