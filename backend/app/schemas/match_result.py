from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class MatchResultResponse(BaseModel):
    id: UUID
    segment_id: UUID
    media_id: UUID
    score: Optional[float]
    keyword_score: Optional[float]
    semantic_score: Optional[float]
    reason: Optional[str]
    rank: Optional[int]
    model: Optional[str]

    class Config:
        from_attributes = True
