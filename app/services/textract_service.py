from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Dict, Any

from app.models import Document
from app.services.textract.textract_client import TextractClient
from app.services.textract.document_processor import DocumentProcessor
from app.services.textract.response_parser import TextractResponseParser
from app.services.markdown.markdown_converter import MarkdownConverter
from app.services.gemini.gemini_service import GeminiService

class TextractService:
    def __init__(self, db: Session):
        self.db = db
        self.textract_client = TextractClient()
        self.processor = DocumentProcessor()
        self.gemini_service = GeminiService()

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

    def process_document(self, job_id: str, user_id: str, mode: str = "fast") -> Dict[str, Any]:
        document = self._get_document(job_id, user_id)

        try:
            document.processing_mode = mode
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
            all_pages_markdown = []

            for page in all_pages_data:
                page_text = page['parsed_data'].get('text', '')
                if page_text:
                    all_pages_text.append(f"--- Page {page['page_number']} ---\n{page_text}")

                converter = MarkdownConverter(
                    parsed_data=page['parsed_data'],
                    page_number=page['page_number']
                )
                page_markdown = converter.convert()
                if page_markdown:
                    all_pages_markdown.append(page_markdown)

            full_text = '\n\n'.join(all_pages_text)
            full_markdown = '\n\n---\n\n'.join(all_pages_markdown)

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
            document.markdown_output = full_markdown

            gemini_result = None
            final_status = "complete"

            if mode == "fast":
                document.gemini_response = {
                    "skipped": True,
                    "reason": "Fast mode - Gemini refinement disabled"
                }
            elif mode == "smart":
                try:
                    if page_count == 1:
                        gemini_result = self.gemini_service.refine_markdown(
                            textract_markdown=full_markdown,
                            image_bytes=image_bytes_list[0],
                            file_size_bytes=document.file_size_bytes,
                            page_count=page_count,
                            mime_type="image/png"
                        )

                        if gemini_result.get("success"):
                            document.markdown_output = gemini_result["final_markdown"]
                            document.gemini_response = gemini_result
                        else:
                            document.gemini_response = {
                                "skipped": True,
                                "reason": gemini_result.get("reason", "Not eligible")
                            }
                    else:
                        document.gemini_response = {
                            "skipped": True,
                            "reason": f"Multi-page document ({page_count} pages) - Smart mode only supports single-page"
                        }

                except Exception as gemini_error:
                    document.gemini_response = {
                        "error": str(gemini_error),
                        "fallback_to_textract": True
                    }

            self._update_status(document, final_status)

            response_data = {
                "job_id": job_id,
                "status": final_status,
                "mode": mode,
                "pages_processed": page_count,
                "summary": aggregated_data['summary']
            }

            if gemini_result and gemini_result.get("success"):
                response_data["gemini_refinement"] = {
                    "source": gemini_result.get("source"),
                    "applied": True
                }

            if mode == "fast":
                response_data["source"] = "textract"
            elif mode == "smart" and gemini_result and gemini_result.get("success"):
                response_data["source"] = gemini_result.get("source", "gemini")

            return response_data

        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            self._update_status(document, "failed", error_msg)
            raise HTTPException(status_code=404, detail={"error": "FileNotFound", "message": error_msg})

        except Exception as e:
            error_msg = f"Textract processing failed: {str(e)}"
            self._update_status(document, "failed", error_msg)
            raise HTTPException(status_code=500, detail={"error": "ProcessingError", "message": error_msg})
