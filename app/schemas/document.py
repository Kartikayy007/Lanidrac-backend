from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Union
from uuid import UUID
import json

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
    processing_mode: Optional[str] = None
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

class DocumentListItem(BaseModel):
    """Lightweight response model for document listing - excludes heavy fields"""
    id: UUID
    job_id: str
    user_id: str
    status: str
    processing_mode: Optional[str] = None
    filename: str
    original_filename: str
    file_size_bytes: int
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
    processing_mode: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    markdown_output: Optional[str] = None
    json_output: Optional[Union[dict, str]] = None
    textract_response: Optional[Union[dict, str]] = None
    gemini_response: Optional[Union[dict, str]] = None
    bbox_image_url: Optional[str] = None
    error_message: Optional[str] = None

    @field_validator('json_output', 'textract_response', 'gemini_response', mode='before')
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

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