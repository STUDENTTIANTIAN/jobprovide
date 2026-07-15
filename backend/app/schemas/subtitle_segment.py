from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class SubtitleSegmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    content: str
    start_time: Optional[int]
    end_time: Optional[int]
    keywords: Optional[List[str]]
    sort_order: int
    selected_media_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

class SubtitleSegmentUpdate(BaseModel):
    content: Optional[str]
    sort_order: Optional[int]
    selected_media_id: Optional[UUID]
