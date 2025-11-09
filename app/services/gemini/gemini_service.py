from typing import Dict, Any
from app.core.config import settings
from app.services.gemini.refinement_engine import RefinementEngine

class GeminiService:
    def __init__(self):
        self.refinement_engine = RefinementEngine()

    def refine_markdown(
        self,
        textract_markdown: str,
        image_bytes: bytes,
        file_size_bytes: int,
        page_count: int,
        mime_type: str = "image/png"
    ) -> Dict[str, Any]:
        if not self._is_eligible(file_size_bytes, page_count):
            return {
                "success": False,
                "reason": "Document not eligible for Gemini refinement",
                "final_markdown": textract_markdown,
                "source": "textract",
                "skipped": True
            }

        try:
            refinement_result = self.refinement_engine.refine_markdown(
                textract_markdown=textract_markdown,
                image_bytes=image_bytes,
                mime_type=mime_type
            )

            if not refinement_result["success"]:
                return {
                    "success": False,
                    "reason": refinement_result.get("error", "Refinement failed"),
                    "final_markdown": textract_markdown,
                    "source": "textract"
                }

            gemini_markdown = refinement_result["markdown"]

            return {
                "success": True,
                "final_markdown": gemini_markdown,
                "source": "gemini",
                "textract_markdown": textract_markdown,
                "gemini_markdown": gemini_markdown,
                "gemini_raw_response": refinement_result.get("raw_response", "")
            }

        except Exception as e:
            return {
                "success": False,
                "reason": f"Gemini service error: {str(e)}",
                "final_markdown": textract_markdown,
                "source": "textract"
            }

    def _is_eligible(self, file_size_bytes: int, page_count: int) -> bool:
        if not settings.ENABLE_GEMINI_REFINEMENT:
            return False

        max_size_bytes = settings.GEMINI_MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            return False

        if page_count > settings.GEMINI_MAX_PAGES:
            return False

        return True
