from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

class SummaryRequest(BaseModel):
    document_id: int = Field(..., gt=0)
    chapter_id: int | None = None
    level: Literal["short", "medium", "long"] = "medium"

class SummaryResponse(BaseModel):
    id: int
    document_id: int
    chapter_id: int | None
    level: str
    summary_text: str
    created_at: datetime

    model_config = {"from_attributes": True}