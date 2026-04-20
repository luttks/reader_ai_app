from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_service import summarize_chapter, summarize_document

router = APIRouter(prefix="/summarize", tags=["summarize"])

@router.post("", response_model=SummaryResponse)
def summarize_api(payload: SummaryRequest, db: Session = Depends(get_db)):
    try: 
        if payload.chapter_id is not None:
            return summarize_chapter(
                db=db,
                document_id=payload.document_id,
                chapter_id=payload.chapter_id,
                level=payload.level,
            )
        return summarize_document(
            db=db,
            document_id=payload.document_id,
            level=payload.level,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("[SUMMARIZE ERROR]")
        raise HTTPException(status_code=500, detail=f"Failed to summarize: {str(e)}") from e