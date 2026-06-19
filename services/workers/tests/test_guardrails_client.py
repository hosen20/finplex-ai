import json

import httpx
from app.clients.guardrails_client import GuardrailsClient


def test_guardrails_client_posts_to_validate_message() -> None:
    captured_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "tenant_id": "tenant_1",
                "invoice_id": "inv_1",
                "passed": True,
                "decision": "send_to_human_review",
                "findings": [],
                "redacted_message": "Please review invoice INV-1 for 1200.",
                "evidence_ids": ["ev_invoice"],
                "policy_version": "guardrails_policy_v0.1.0",
                "human_review_required": True,
                "nemo_passed": True,
                "nemo_messages": ["NeMo first-pass validation passed."],
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://guardrails.test",
    )
    guardrails_client = GuardrailsClient(
        base_url="http://guardrails.test",
        client=client,
    )

    response = guardrails_client.validate_message(
        tenant_id="tenant_1",
        invoice_id="inv_1",
        draft_message="Please review invoice INV-1 for 1200.",
        risk_level="medium",
        evidence_ids=["ev_invoice"],
        customer_name="Acme",
        amount_due=1200.0,
        metadata={"trace_id": "evt_1"},
    )

    assert response["passed"] is True
    assert captured_payloads[0]["tenant_id"] == "tenant_1"
    assert captured_payloads[0]["invoice_id"] == "inv_1"
    assert captured_payloads[0]["metadata"]["trace_id"] == "evt_1"