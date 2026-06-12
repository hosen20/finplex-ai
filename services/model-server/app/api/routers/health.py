from app.config import settings
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "service": "model-server",
        "status": "ok",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
    }


@router.get("/health/ready")
def readiness_check() -> dict[str, str]:
    return {
        "service": "model-server",
        "status": "ready",
        "pipeline_version": settings.pipeline_version,
    }