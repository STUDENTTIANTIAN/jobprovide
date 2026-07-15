from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TaskCreate(BaseModel):
    type: str  # video, audio, text
    content: Optional[str] = None  # 文本内容

class TaskResponse(BaseModel):
    id: UUID
    type: str
    status: str
    input_text: Optional[str]
    input_file_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskStatus(BaseModel):
    task_id: UUID
    status: str
    progress: Optional[int] = None
    segments_count: Optional[int] = None
