from fastapi import FastAPI

from app.api.routers import health, inference
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI service for extraction, risk scoring, RAG, and drafting.",
)

app.include_router(health.router)
app.include_router(inference.router)