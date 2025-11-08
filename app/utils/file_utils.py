import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings, MAX_FILE_SIZE_BYTES

def generate_job_id() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_str = str(uuid.uuid4())[:8]
    return f"DOC_{timestamp}_{random_str}"

def generate_safe_filename(original_filename: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_id = uuid.uuid4().hex[:8]
    extension = Path(original_filename).suffix
    safe_filename = f"{timestamp}_{random_id}{extension}"
    return safe_filename

def validate_file(file: UploadFile) -> None:
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "UnsupportedMediaType",
                "message": f"Unsupported file type: {file.content_type}",
                "allowed_types": settings.ALLOWED_MIME_TYPES
            }
        )

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "UnsupportedFileExtension",
                "message": f"Unsupported file extension: {file_extension}",
                "allowed_extensions": settings.ALLOWED_EXTENSIONS
            }
        )

def validate_file_size(file: UploadFile) -> int:
    file_size = 0
    for chunk in file.file:
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "FileTooLarge",
                    "message": f"File exceeds maximum size limit",
                    "max_size_mb": settings.MAX_FILE_SIZE_MB,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }
            )
    file.file.seek(0)
    return file_size

def ensure_upload_directory():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)