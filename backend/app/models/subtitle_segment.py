import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base

class SubtitleSegment(Base):
    __tablename__ = "subtitle_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    start_time = Column(Integer, nullable=True)  # 毫秒
    end_time = Column(Integer, nullable=True)  # 毫秒
    keywords = Column(JSONB, nullable=True)
    embedding = Column(ARRAY(Float), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    selected_media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
