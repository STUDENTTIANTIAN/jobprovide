import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("subtitle_segments.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    rank = Column(Integer, nullable=True)
    model = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
