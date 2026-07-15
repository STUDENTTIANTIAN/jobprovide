import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Uuid, JSON
from app.database import Base

class Media(Base):
    __tablename__ = "media"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    type = Column(String(10), nullable=False)  # image, video
    url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    name = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)
    duration = Column(Integer, nullable=True)  # 秒
    created_at = Column(DateTime, default=datetime.utcnow)
