from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from datetime import datetime, timezone

from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="uploaded", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    raw_text = Column(Text, nullable=True)
    markdown_output = Column(Text, nullable=True)
    json_output = Column(JSON, nullable=True)
    bbox_image_url = Column(Text, nullable=True)
    textract_response = Column(JSON, nullable=True)
    gemini_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Document(job_id={self.job_id}, filename={self.filename}, status={self.status})>"