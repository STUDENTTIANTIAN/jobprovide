import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Uuid
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    type = Column(String(20), nullable=False)  # video, audio, text
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    input_text = Column(Text, nullable=True)
    input_file_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
