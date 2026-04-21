from datetime import datetime
from pydantic import BaseModel, Field

class EvaluationRequest(BaseModel):
    document_id: int = Field(..., gt=0)
    chapter_id: int | None = None
    
class LevelEvaluationResult(BaseModel):
    level: str
    summary_text: str
    processing_time_ms: float
    original_sentence_count: int
    summary_sentence_count: int
    original_word_count: int
    summary_word_count: int
    compression_ratio: float


class EvaluationResponse(BaseModel):
    document_id: int
    chapter_id: int | None
    scope: str
    title: str
    evaluated_at: datetime
    results: list[LevelEvaluationResult]
    log_file: str