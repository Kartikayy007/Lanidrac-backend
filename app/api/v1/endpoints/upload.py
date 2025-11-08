from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas import UploadResponse, DocumentStatus, DocumentResponse
from app.services.upload_service import UploadService

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    return await service.upload_document(file, user_id)

@router.get("/status/{job_id}", response_model=DocumentStatus)
async def get_document_status(
    job_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    return service.get_document_status(job_id, user_id)

@router.get("/document/{job_id}", response_model=DocumentResponse)
async def get_document(
    job_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    return service.get_document(job_id, user_id)

@router.get("/list")
async def list_documents(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    return service.list_documents(user_id)