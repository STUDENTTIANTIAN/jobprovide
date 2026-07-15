from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class MediaCreate(BaseModel):
    name: Optional[str]
    tags: Optional[List[str]] = []

class MediaResponse(BaseModel):
    id: UUID
    type: str
    url: str
    thumbnail_url: Optional[str]
    name: Optional[str]
    tags: Optional[List[str]]
    keywords: Optional[List[str]]
    duration: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class MediaListResponse(BaseModel):
    items: List[MediaResponse]
    total: int
