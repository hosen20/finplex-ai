from fastapi import Depends, FastAPI

from app.config import settings
from app.schemas import MessageValidationRequest, MessageValidationResponse
from app.services.guardrail_service import GuardrailService

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "NeMo-first guardrails service for compliant debt-collection drafts."
    ),
)

_guardrail_service: GuardrailService | None = None


def get_guardrail_service() -> GuardrailService:
    """Create the guardrail service lazily.

    NeMo is still required. Lazy creation only makes tests and health checks
    easier because the app can be imported before the service is used.
    """
    global _guardrail_service

    if _guardrail_service is None:
        _guardrail_service = GuardrailService()

    return _guardrail_service


@app.get("/health")
def health() -> dict[str, str | bool]:
    """Basic service health endpoint."""
    return {
        "service": "guardrails",
        "status": "ok",
        "environment": settings.environment,
        "nemo_required": True,
    }


@app.get("/health/ready")
def readiness() -> dict[str, str | bool]:
    """Readiness endpoint used by local and deployment checks."""
    get_guardrail_service()

    return {
        "service": "guardrails",
        "status": "ready",
        "policy_version": settings.policy_version,
        "nemo_first": True,
        "deterministic_checks_enabled": True,
    }


@app.post("/validate-message", response_model=MessageValidationResponse)
def validate_message(
    request: MessageValidationRequest,
    guardrail_service: GuardrailService = Depends(get_guardrail_service),
) -> MessageValidationResponse:
    """Validate a generated follow-up message before human review."""
    return guardrail_service.validate(request)