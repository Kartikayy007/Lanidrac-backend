from fastapi import APIRouter

from app.api.v1.endpoints import health, upload, extract

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["health"]
)

api_router.include_router(
    upload.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    extract.router,
    prefix="/documents",
    tags=["extract"]
)