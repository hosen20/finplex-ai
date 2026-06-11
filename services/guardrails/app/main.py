from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Policy checks for evidence-based debt-collection drafts.",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "service": "guardrails",
        "status": "ok",
        "environment": settings.environment,
        "regulations_dir": str(settings.regulations_dir),
    }


@app.get("/health/ready")
def readiness_check() -> dict[str, str]:
    return {
        "service": "guardrails",
        "status": "ready",
    }