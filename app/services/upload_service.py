import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session, load_only

from app.models import Document
from app.schemas import UploadResponse, DocumentStatus, DocumentResponse
from app.core.config import settings
from app.utils.file_utils import (
    generate_job_id,
    generate_safe_filename,
    validate_file,
    validate_file_size
)

class UploadService:
    def __init__(self, db: Session):
        self.db = db

    async def upload_document(self, file: UploadFile, user_id: str) -> UploadResponse:
        try:
            validate_file(file)
            validate_file_size(file)

            job_id = generate_job_id()
            safe_filename = generate_safe_filename(file.filename)
            file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size = os.path.getsize(file_path)

            document = Document(
                job_id=job_id,
                user_id=user_id,
                filename=safe_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size_bytes=file_size,
                mime_type=file.content_type,
                status="uploaded"
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            return UploadResponse(
                job_id=document.job_id,
                filename=document.original_filename,
                file_size_bytes=document.file_size_bytes,
                mime_type=document.mime_type,
                status=document.status,
                created_at=document.created_at
            )

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "InternalServerError",
                    "message": "Failed to upload document",
                    "details": str(e)
                }
            )

    def get_document_status(self, job_id: str, user_id: str) -> DocumentStatus:
        document = self.db.query(Document).filter(
            Document.job_id == job_id,
            Document.user_id == user_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DocumentNotFound",
                    "message": f"Document with job_id '{job_id}' not found"
                }
            )

        return DocumentStatus(
            job_id=document.job_id,
            filename=document.original_filename,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            error_message=document.error_message
        )

    def get_document(self, job_id: str, user_id: str) -> DocumentResponse:
        document = self.db.query(Document).filter(
            Document.job_id == job_id,
            Document.user_id == user_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DocumentNotFound",
                    "message": f"Document with job_id '{job_id}' not found"
                }
            )

        return DocumentResponse.from_orm(document)

    def update_document_status(self, job_id: str, status: str, error_message: str = None) -> None:
        document = self.db.query(Document).filter(Document.job_id == job_id).first()
        if document:
            document.status = status
            if error_message:
                document.error_message = error_message
            self.db.commit()

    def list_documents(self, user_id: str):
        """Get list of documents with only essential fields (optimized for performance)"""
        documents = self.db.query(Document).options(
            load_only(
                Document.id,
                Document.job_id,
                Document.user_id,
                Document.status,
                Document.processing_mode,
                Document.filename,
                Document.original_filename,
                Document.file_size_bytes,
                Document.created_at,
                Document.updated_at,
                Document.error_message
            )
        ).filter(
            Document.user_id == user_id
        ).order_by(Document.created_at.desc()).limit(5).all()
        return documents