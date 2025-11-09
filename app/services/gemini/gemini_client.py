import google.generativeai as genai
import base64
from typing import Dict, Any
from app.core.config import settings

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.timeout = settings.GEMINI_TIMEOUT_SECONDS

    def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> str:
        try:
            image_part = {
                "mime_type": mime_type,
                "data": image_bytes
            }

            response = self.model.generate_content(
                [prompt, image_part]
            )

            return response.text

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def generate_with_markdown(
        self,
        prompt: str,
        markdown: str,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> str:
        try:
            image_part = {
                "mime_type": mime_type,
                "data": image_bytes
            }

            full_prompt = f"{prompt}\n\nCurrent Markdown:\n```markdown\n{markdown}\n```"

            response = self.model.generate_content(
                [full_prompt, image_part]
            )

            return response.text

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
