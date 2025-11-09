import re
from typing import Dict, Any
from app.services.gemini.gemini_client import GeminiClient

class RefinementEngine:
    def __init__(self):
        self.client = GeminiClient()

    def refine_markdown(
        self,
        textract_markdown: str,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> Dict[str, Any]:
        prompt = self._build_refinement_prompt()

        try:
            response = self.client.generate_with_markdown(
                prompt=prompt,
                markdown=textract_markdown,
                image_bytes=image_bytes,
                mime_type=mime_type
            )

            refined_markdown = self._extract_markdown(response)

            return {
                "success": True,
                "markdown": refined_markdown,
                "raw_response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "markdown": textract_markdown
            }

    def _build_refinement_prompt(self) -> str:
        return """You are an expert OCR refinement assistant. Your task is to review and improve the provided Markdown output from AWS Textract.

INSTRUCTIONS:
1. Compare the current Markdown with the original image
2. Fix OCR errors (typos, misread characters, incorrect spacing)
3. Verify that tables, forms, and checkboxes are correctly structured
4. Preserve ALL information from the original document
5. Maintain the existing Markdown structure (tables, headings, lists)
6. Do NOT add information that isn't in the image
7. Do NOT remove information that is present
8. Do NOT hallucinate or invent content

OUTPUT FORMAT:
- Return ONLY the refined Markdown
- Do NOT include explanations, comments, or meta-text
- Do NOT wrap the output in code blocks
- Just return the pure Markdown content

If the current Markdown is already accurate, return it unchanged."""

    def _extract_markdown(self, response: str) -> str:
        cleaned = response.strip()

        if cleaned.startswith("```markdown"):
            cleaned = cleaned[len("```markdown"):].strip()

        if cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        return cleaned
