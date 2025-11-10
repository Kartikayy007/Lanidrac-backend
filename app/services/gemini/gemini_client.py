import google.generativeai as genai
import base64
import signal
from typing import Dict, Any
from contextlib import contextmanager
from app.core.config import settings

class TimeoutException(Exception):
    pass

@contextmanager
def timeout_handler(seconds):
    def _timeout_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")

    original_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

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

            with timeout_handler(self.timeout):
                response = self.model.generate_content(
                    [prompt, image_part],
                    request_options={"timeout": self.timeout}
                )

            return response.text

        except TimeoutException:
            raise Exception(f"AI refinement timeout. Document may be too complex. Please try a smaller file.")
        except Exception as e:
            error_msg = str(e).lower()
            if 'quota' in error_msg or 'rate' in error_msg:
                raise Exception("AI service quota exceeded. Using standard OCR.")
            elif 'api key' in error_msg:
                raise Exception("AI service configuration error. Using standard OCR.")
            else:
                raise Exception(f"AI refinement failed: {str(e)}")

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

            with timeout_handler(self.timeout):
                response = self.model.generate_content(
                    [full_prompt, image_part],
                    request_options={"timeout": self.timeout}
                )

            return response.text

        except TimeoutException:
            raise Exception(f"AI refinement timeout. Document may be too complex. Please try a smaller file.")
        except Exception as e:
            error_msg = str(e).lower()
            if 'quota' in error_msg or 'rate' in error_msg:
                raise Exception("AI service quota exceeded. Using standard OCR.")
            elif 'api key' in error_msg:
                raise Exception("AI service configuration error. Using standard OCR.")
            else:
                raise Exception(f"AI refinement failed: {str(e)}")
