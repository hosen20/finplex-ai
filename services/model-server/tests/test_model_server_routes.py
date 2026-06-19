from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def build_score_payload() -> dict:
    return {
        "invoice_id": "new_inv_001",
        "tenant_id": "tenant_demo",
        "risk_features": {
            "amount_due": 13600.0,
            "payment_terms_days": 30,
            "paperless_bill": 0,
            "country_code": "US",
            "previous_invoice_count": 12,
            "previous_late_payments": 5,
            "previous_disputed_count": 2,
            "previous_total_amount": 120000.0,
            "previous_average_invoice_amount": 10000.0,
            "previous_average_days_late": 9.5,
            "previous_max_days_late": 34.0,
            "previous_on_time_payment_rate": 0.58,
            "previous_dispute_rate": 0.16,
            "previous_crm_negative_signal_score": 0.42,
            "relationship_age_days": 950,
        },
    }


def test_health_route_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "model-server"
    assert response.json()["status"] == "ok"


def test_score_risk_route_returns_prediction() -> None:
    response = client.post("/score-risk", json=build_score_payload())

    assert response.status_code == 200

    body = response.json()

    assert body["risk_level"] in {"low", "medium", "high", "critical"}
    assert isinstance(body["risk_score"], float)
    assert isinstance(body["probabilities"], dict)
    assert "model_loaded" in body
    assert body["top_risk_signals"]


def test_search_evidence_route_returns_citations() -> None:
    response = client.post(
        "/search-evidence",
        json={
            "invoice_id": "new_inv_001",
            "tenant_id": "tenant_demo",
            "query": (
                "Customer 1001 late payment dispute collection evidence "
                "invoice ERP CRM regulation"
            ),
            "source_types": ["regulation", "erp", "crm", "invoice"],
            "top_k": 4,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["retrieval_method"] == "hybrid_sparse_dense_local"
    assert isinstance(body["citations"], list)
    assert body["citations"]
    assert body["evidence_ids"] == [
        citation["evidence_id"] for citation in body["citations"]
    ]


def test_process_invoice_route_returns_full_ai_payload() -> None:
    response = client.post(
        "/process-invoice",
        json={
            "invoice_id": "new_inv_001",
            "tenant_id": "tenant_demo",
            "file_name": "NEW-00001.png",
            "storage_key": "tenant_demo/invoices/new_inv_001/NEW-00001.png",
            "text": "\n".join(
                [
                    "Invoice Number: NEW-00001",
                    "Customer: Customer 1001",
                    "Total: 13600.00",
                    "Due Date: 2026-07-01",
                ]
            ),
            "risk_features": build_score_payload()["risk_features"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["extraction"]["extracted_fields"]["invoice_number"] == "NEW-00001"
    assert body["risk"]["risk_level"] in {"low", "medium", "high", "critical"}
    assert "draft_message" in body["draft"]
    assert isinstance(body["citations"], list)
    assert body["citations"]
    assert body["draft"]["citations"]