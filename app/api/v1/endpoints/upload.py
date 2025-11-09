from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas import UploadResponse, DocumentStatus, DocumentResponse
from app.services.upload_service import UploadService
from app.services.textract_service import TextractService

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    return await service.upload_document(file, user_id)

@router.post("/process/{job_id}")
async def process_document(
    job_id: str,
    mode: str = Query(default="fast", regex="^(fast|smart)$"),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    textract_service = TextractService(db)
    return textract_service.process_document(job_id, user_id, mode)

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

@router.get("/markdown/{job_id}")
async def get_markdown(
    job_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    document = service.get_document(job_id, user_id)

    if not document.markdown_output:
        raise HTTPException(
            status_code=404,
            detail={"error": "MarkdownNotAvailable", "message": "Markdown not generated yet"}
        )

    return {
        "job_id": job_id,
        "markdown": document.markdown_output,
        "status": document.status
    }

@router.get("/download/{job_id}/markdown")
async def download_markdown(
    job_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    document = service.get_document(job_id, user_id)

    if not document.markdown_output:
        raise HTTPException(status_code=404, detail="Markdown not available")

    filename = f"{document.original_filename.rsplit('.', 1)[0]}.md"

    return Response(
        content=document.markdown_output,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/download/{job_id}/json")
async def download_json(
    job_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UploadService(db)
    document = service.get_document(job_id, user_id)

    if not document.json_output:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "JsonNotAvailable",
                "message": "No extracted JSON data available. Please run extraction first."
            }
        )

    import json
    filename = f"{document.original_filename.rsplit('.', 1)[0]}.json"
    json_content = json.dumps(document.json_output, indent=2)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )