from app.main import app, get_guardrail_service
from app.schemas import MessageValidationRequest, MessageValidationResponse
from fastapi.testclient import TestClient


class FakeGuardrailService:
    def validate(
        self,
        request: MessageValidationRequest,
    ) -> MessageValidationResponse:
        return MessageValidationResponse(
            tenant_id=request.tenant_id,
            invoice_id=request.invoice_id,
            passed=True,
            decision="send_to_human_review",
            findings=[],
            redacted_message=request.draft_message,
            evidence_ids=request.evidence_ids,
            policy_version="test_policy_v1",
            human_review_required=True,
            nemo_passed=True,
            nemo_messages=["NeMo first-pass validation passed."],
        )


def override_guardrail_service() -> FakeGuardrailService:
    return FakeGuardrailService()


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "guardrails"
    assert response.json()["nemo_required"] is True


def test_validate_message_endpoint() -> None:
    app.dependency_overrides[get_guardrail_service] = override_guardrail_service
    client = TestClient(app)

    response = client.post(
        "/validate-message",
        json={
            "tenant_id": "tenant_1",
            "invoice_id": "inv_1",
            "draft_message": "Please review invoice INV-1 for 1200.",
            "risk_level": "medium",
            "evidence_ids": ["ev_invoice"],
            "customer_name": "Acme",
            "amount_due": 1200.0,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["nemo_passed"] is True
    assert response.json()["decision"] == "send_to_human_review"