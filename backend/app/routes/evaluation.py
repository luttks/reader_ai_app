from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.services.evaluation_service import evaluate_summary

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


@router.post("/summary", response_model=EvaluationResponse)
def evaluate_summary_api(payload: EvaluationRequest, db: Session = Depends(get_db)):
    try:
        return evaluate_summary(
            db=db,
            document_id=payload.document_id,
            chapter_id=payload.chapter_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate summary: {str(e)}") from e