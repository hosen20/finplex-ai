from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.routers import auth, customers, health, invoices, reviews, tenants, users
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Finplex AI backend API for tenants, invoices, reviews, and audit.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tenants.router)
app.include_router(customers.router)
app.include_router(invoices.router)
app.include_router(reviews.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "running",
        "environment": settings.environment,
    }