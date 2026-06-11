from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI service for extraction, RAG, risk scoring, and drafting.",
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
        "service": "model-server",
        "status": "ok",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
    }


@app.get("/health/ready")
def readiness_check() -> dict[str, str]:
    return {
        "service": "model-server",
        "status": "ready",
        "guardrails": settings.guardrails_url,
    }