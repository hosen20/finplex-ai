from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_route() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_invoice_route_returns_pipeline_outputs() -> None:
    response = client.post(
        "/process-invoice",
        json={
            "invoice_id": "inv_001",
            "tenant_id": "tenant_001",
            "file_name": "invoice.pdf",
            "storage_key": "tenant_001/invoices/inv_001/invoice.pdf",
            "text": (
                "Invoice Number: INV-2026 Customer: Acme "
                "Total: 500 Due Date: 2026-07-15"
            ),
            "days_overdue": 35,
            "has_dispute": False,
            "previous_late_payments": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["extraction"]["invoice_id"] == "inv_001"
    assert body["risk"]["risk_level"] in {"low", "medium", "high", "critical"}
    assert body["draft"]["guardrails_required"] is True