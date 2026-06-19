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