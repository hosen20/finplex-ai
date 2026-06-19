import json

import httpx
from app.clients.model_server_client import ModelServerClient


def test_model_server_client_posts_to_score_risk() -> None:
    captured_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "invoice_id": "inv_1",
                "tenant_id": "tenant_1",
                "risk_level": "high",
                "risk_score": 0.9,
                "reasons": [],
                "evidence_ids": ["ev_1"],
                "model_version": "test",
                "model_loaded": True,
                "model_name": "fake",
                "probabilities": {"high": 0.9},
                "feature_source": "trained_notebook_artifact",
                "top_risk_signals": [],
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://model-server.test",
    )
    model_client = ModelServerClient(
        base_url="http://model-server.test",
        client=client,
    )

    response = model_client.score_risk(
        invoice_id="inv_1",
        tenant_id="tenant_1",
        extracted_fields={},
        risk_features={"amount_due": 100.0},
    )

    assert response["risk_level"] == "high"
    assert captured_payloads[0]["risk_features"]["amount_due"] == 100.0


def test_model_server_client_posts_to_search_evidence() -> None:
    captured_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "invoice_id": "inv_1",
                "tenant_id": "tenant_1",
                "query": "Acme late payment evidence",
                "citations": [
                    {
                        "evidence_id": "ev_evidence",
                        "source_type": "erp",
                        "title": "Historical Erp Payments",
                        "snippet": "Acme invoice INV-1 was late.",
                        "score": 0.81,
                        "metadata": {
                            "retrieval_method": "hybrid_sparse_dense_local",
                        },
                    }
                ],
                "evidence_ids": ["ev_evidence"],
                "retrieval_method": "hybrid_sparse_dense_local",
                "model_version": "test",
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://model-server.test",
    )
    model_client = ModelServerClient(
        base_url="http://model-server.test",
        client=client,
    )

    response = model_client.search_evidence(
        invoice_id="inv_1",
        tenant_id="tenant_1",
        query="Acme late payment evidence",
        source_types=["regulation", "erp", "crm"],
        top_k=3,
        context={"risk_level": "high"},
    )

    assert response["retrieval_method"] == "hybrid_sparse_dense_local"
    assert response["evidence_ids"] == ["ev_evidence"]
    assert captured_payloads[0]["source_types"] == [
        "regulation",
        "erp",
        "crm",
    ]
    assert captured_payloads[0]["context"]["risk_level"] == "high"


def test_model_server_client_posts_to_draft_message_with_evidence() -> None:
    captured_payloads = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "invoice_id": "inv_1",
                "tenant_id": "tenant_1",
                "draft_message": "Please review invoice INV-1.",
                "guardrails_required": True,
                "evidence_ids": ["ev_evidence"],
                "citations": [
                    {
                        "evidence_id": "ev_evidence",
                        "source_type": "erp",
                        "title": "Historical Erp Payments",
                        "snippet": "Acme invoice INV-1 was late.",
                        "score": 0.81,
                        "metadata": {},
                    }
                ],
                "model_version": "test",
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://model-server.test",
    )
    model_client = ModelServerClient(
        base_url="http://model-server.test",
        client=client,
    )

    response = model_client.draft_message(
        invoice_id="inv_1",
        tenant_id="tenant_1",
        extracted_fields={
            "invoice_number": "INV-1",
            "customer_name": "Acme",
            "amount_due": 1200.0,
            "currency": "USD",
            "due_date": "2026-07-01",
        },
        risk_level="high",
        evidence_ids=["ev_evidence"],
        evidence_context=[
            {
                "evidence_id": "ev_evidence",
                "source_type": "erp",
                "title": "Historical Erp Payments",
                "snippet": "Acme invoice INV-1 was late.",
                "score": 0.81,
                "metadata": {},
            }
        ],
    )

    assert response["draft_message"] == "Please review invoice INV-1."
    assert captured_payloads[0]["customer_name"] == "Acme"
    assert captured_payloads[0]["evidence_ids"] == ["ev_evidence"]
    assert captured_payloads[0]["evidence_context"][0][
        "evidence_id"
    ] == "ev_evidence"