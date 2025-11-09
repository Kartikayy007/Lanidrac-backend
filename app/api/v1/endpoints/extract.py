from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Document
from app.services.extract import SchemaValidator, ExtractEngine
from app.services.textract.document_processor import DocumentProcessor

router = APIRouter()

class ExtractRequest(BaseModel):
    schema: Dict[str, Any]

class ExtractResponse(BaseModel):
    job_id: str
    extracted_data: Dict[str, Any]
    confidence: float
    status: str
    message: Optional[str] = None

@router.post("/extract/{job_id}", response_model=ExtractResponse)
async def extract_with_schema(
    job_id: str,
    request: ExtractRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
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

    if document.status != "complete":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "DocumentNotReady",
                "message": f"Document must be processed first. Current status: {document.status}"
            }
        )

    validator = SchemaValidator()
    is_valid, errors = validator.validate_schema(request.schema)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "InvalidSchema",
                "message": "Schema validation failed",
                "errors": errors
            }
        )

    if not document.markdown_output:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "NoMarkdownAvailable",
                "message": "Document has no markdown output. Please process the document first."
            }
        )

    try:
        processor = DocumentProcessor()
        image_bytes_list, page_count = processor.process_document(document.file_path)

        if not image_bytes_list or len(image_bytes_list) == 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "ImageProcessingFailed",
                    "message": "Failed to read document image for extraction"
                }
            )

        image_bytes = image_bytes_list[0]

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "FileNotFound",
                "message": f"Document file not found at path: {document.file_path}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ImageProcessingError",
                "message": f"Failed to process document image: {str(e)}"
            }
        )

    engine = ExtractEngine()

    textract_data = None
    if document.textract_response and isinstance(document.textract_response, dict):
        pages = document.textract_response.get('pages', [])
        if pages and len(pages) > 0:
            textract_data = pages[0].get('parsed_data', {})

    extracted_data, confidence = engine.extract_with_schema(
        schema=request.schema,
        image_bytes=image_bytes,
        mime_type="image/png",
        textract_data=textract_data
    )

    document.json_output = extracted_data
    db.commit()

    return ExtractResponse(
        job_id=job_id,
        extracted_data=extracted_data,
        confidence=round(confidence, 3),
        status="success",
        message=f"Data extracted with {round(confidence * 100, 1)}% confidence"
    )

@router.get("/extract/examples")
async def get_schema_examples():
    return {
        "examples": [
            {
                "name": "Invoice",
                "description": "Extract data from an invoice",
                "schema": {
                    "invoice_number": "string",
                    "date": "date",
                    "vendor": {
                        "name": "string",
                        "address": "string"
                    },
                    "items": [{
                        "description": "string",
                        "quantity": "number",
                        "price": "number"
                    }],
                    "subtotal": "number",
                    "tax": "number",
                    "total": "number"
                }
            },
            {
                "name": "Receipt",
                "description": "Extract data from a restaurant receipt",
                "schema": {
                    "restaurant_name": "string",
                    "date": "date",
                    "time": "string",
                    "items": [{
                        "name": "string",
                        "price": "number"
                    }],
                    "subtotal": "number",
                    "tax": "number",
                    "tip": "number",
                    "total": "number"
                }
            },
            {
                "name": "Medical Form",
                "description": "Extract data from a medical intake form",
                "schema": {
                    "patient": {
                        "name": "string",
                        "date_of_birth": "date",
                        "gender": "string"
                    },
                    "symptoms": [{
                        "symptom": "string",
                        "severity": "string"
                    }],
                    "medications": [{
                        "name": "string",
                        "dosage": "string"
                    }],
                    "allergies": ["string"],
                    "insurance": {
                        "provider": "string",
                        "policy_number": "string"
                    }
                }
            }
        ]
    }