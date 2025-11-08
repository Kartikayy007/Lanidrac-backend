from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {
        "status": "Lanidrac Backend Running",
        "version": "1.0.0",
        "api_version": "v1"
    }

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "lanidrac-backend"
    }

@router.get("/ready")
def readiness_check():
    return {
        "status": "ready",
        "database": "connected",
        "storage": "available"
    }