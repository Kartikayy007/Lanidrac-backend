from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Dict, Any

from app.models import Document
from app.services.textract.textract_client import TextractClient
from app.services.textract.document_processor import DocumentProcessor
from app.services.textract.response_parser import TextractResponseParser

class TextractService:
    def __init__(self, db: Session):
        self.db = db
        self.textract_client = TextractClient()
        self.processor = DocumentProcessor()

    def _update_status(self, document: Document, status: str, error_message: str = None):
        document.status = status
        if error_message:
            document.error_message = error_message
        self.db.commit()
        self.db.refresh(document)

    def _get_document(self, job_id: str, user_id: str) -> Document:
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
        return document

    def process_document(self, job_id: str, user_id: str) -> Dict[str, Any]:
        document = self._get_document(job_id, user_id)

        try:
            self._update_status(document, "processing")

            image_bytes_list, page_count = self.processor.process_document(document.file_path)

            textract_responses = self.textract_client.analyze_document_batch(image_bytes_list)

            all_pages_data = []
            failed_pages = []

            for page_data in textract_responses:
                if page_data['status'] == 'success':
                    parser = TextractResponseParser(page_data['response'])
                    parsed_data = parser.parse()
                    all_pages_data.append({
                        'page_number': page_data['page_number'],
                        'raw_response': page_data['response'],
                        'parsed_data': parsed_data
                    })
                else:
                    failed_pages.append({
                        'page_number': page_data['page_number'],
                        'error': page_data['error']
                    })

            if failed_pages:
                error_msg = f"Failed to process {len(failed_pages)} page(s): {failed_pages}"
                self._update_status(document, "failed", error_msg)
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": error_msg
                }

            all_pages_text = []
            for page in all_pages_data:
                page_text = page['parsed_data'].get('text', '')
                if page_text:
                    all_pages_text.append(f"--- Page {page['page_number']} ---\n{page_text}")

            full_text = '\n\n'.join(all_pages_text)

            aggregated_data = {
                'total_pages': page_count,
                'pages': all_pages_data,
                'summary': {
                    'total_tables': sum(len(page['parsed_data']['tables']) for page in all_pages_data),
                    'total_forms': sum(len(page['parsed_data']['forms']) for page in all_pages_data),
                    'total_checkboxes': sum(len(page['parsed_data']['checkboxes']) for page in all_pages_data),
                    'total_text_length': len(full_text)
                }
            }

            document.textract_response = aggregated_data
            document.raw_text = full_text
            self._update_status(document, "textract_complete")

            return {
                "job_id": job_id,
                "status": "textract_complete",
                "pages_processed": page_count,
                "summary": aggregated_data['summary']
            }

        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            self._update_status(document, "failed", error_msg)
            raise HTTPException(status_code=404, detail={"error": "FileNotFound", "message": error_msg})

        except Exception as e:
            error_msg = f"Textract processing failed: {str(e)}"
            self._update_status(document, "failed", error_msg)
            raise HTTPException(status_code=500, detail={"error": "ProcessingError", "message": error_msg})
