from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.chapter import ChapterResponse


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., min_length=1, max_length=20)
    file_path: str = Field(..., min_length=1, max_length=500)
    raw_text: str = ""


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_type: str
    file_path: str
    raw_text: str
    created_at: datetime

    model_config = {"from_attributes": True}

class DocumentDetailResponse(DocumentResponse):
    chapters: list[ChapterResponse] = []