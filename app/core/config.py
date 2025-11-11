from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lanidrac OCR API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "postgresql://lanidrac_user:lanidrac_pass@localhost:5432/lanidrac"

    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/tiff"
    ]

    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf",
        ".png",
        ".jpeg",
        ".jpg",
        ".tiff"
    ]

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "eu-north-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"
    ENABLE_GEMINI_REFINEMENT: bool = True
    GEMINI_MAX_FILE_SIZE_MB: int = 5
    GEMINI_MAX_PAGES: int = 5
    GEMINI_TIMEOUT_SECONDS: int = 90

    FAST_MODE_ENABLED: bool = True
    SMART_MODE_ENABLED: bool = True
    SMART_MODE_DEFAULT: bool = False

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024