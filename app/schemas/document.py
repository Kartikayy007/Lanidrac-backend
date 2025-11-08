from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class DocumentBase(BaseModel):
    filename: str
    mime_type: str
    file_size_bytes: int

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    file_size_bytes: int
    mime_type: str
    status: str
    created_at: datetime
    message: str = "File uploaded successfully"

    class Config:
        from_attributes = True

class DocumentStatus(BaseModel):
    job_id: str
    filename: str
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: UUID
    job_id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    markdown_output: Optional[str] = None
    json_output: Optional[str] = None
    bbox_image_url: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ProcessingResponse(BaseModel):
    job_id: str
    status: str
    markdown: Optional[str] = None
    json_data: Optional[dict] = None
    bbox_image_url: Optional[str] = None
    textract_confidence: Optional[float] = None
    gemini_used: Optional[bool] = False
    validation_score: Optional[float] = None
    error_message: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None