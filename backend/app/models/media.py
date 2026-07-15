import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base

class Media(Base):
    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(10), nullable=False)  # image, video
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    name = Column(String(255), nullable=True)
    tags = Column(JSONB, nullable=True)
    keywords = Column(JSONB, nullable=True)
    embedding = Column(ARRAY(Float), nullable=True)
    duration = Column(Integer, nullable=True)  # 秒
    created_at = Column(DateTime, default=datetime.utcnow)
