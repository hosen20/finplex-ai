import json

import httpx
from app.infrastructure.clients.model_server_client import ModelServerClient


def test_model_server_client_posts_process_invoice_payload() -> None:
    captured_payload = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "extraction": {"invoice_id": "inv_001"},
                "risk": {"risk_level": "medium"},
                "draft": {"guardrails_required": True},
            },
        )

    response = ModelServerClient(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    ).process_invoice(
        invoice_id="inv_001",
        tenant_id="tenant_001",
        file_name="invoice.pdf",
        storage_key="tenant_001/invoices/inv_001/invoice.pdf",
        text="Invoice Number: INV-2026 Total: 500",
        days_overdue=10,
    )

    assert captured_payload["invoice_id"] == "inv_001"
    assert captured_payload["days_overdue"] == 10
    assert response["risk"]["risk_level"] == "medium"