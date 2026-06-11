from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("")
def health_check() -> dict[str, str]:
    return {
        "service": "api",
        "status": "ok",
        "environment": settings.environment,
    }


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    return {
        "service": "api",
        "status": "ready",
        "database_url": settings.database_url,
        "redis_url": settings.redis_url,
        "kafka": settings.kafka_bootstrap_servers,
        "minio": settings.minio_endpoint,
        "model_server": settings.model_server_url,
        "guardrails": settings.guardrails_url,
    }