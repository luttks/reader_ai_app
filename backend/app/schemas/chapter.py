from pydantic import BaseModel

class ChapterResponse(BaseModel):
    id: int
    chapter_index: int
    title: str
    raw_text: str
    paragraph_count: int
    sentence_count: int

    model_config = {"from_attributes": True}