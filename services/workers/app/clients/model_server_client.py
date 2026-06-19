from typing import Any

import httpx

from app.config import settings


class ModelServerClient:
    """HTTP client used by workers to call the model-server pipeline endpoints."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.model_server_url).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds or settings.model_server_timeout_seconds
        )
        self._client = client

    def extract_invoice(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        file_name: str,
        storage_key: str,
        text: str,
    ) -> dict[str, Any]:
        return self._post(
            "/extract-invoice",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "file_name": file_name,
                "storage_key": storage_key,
                "text": text,
            },
        )

    def score_risk(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        extracted_fields: dict[str, Any],
        risk_features: dict[str, Any],
    ) -> dict[str, Any]:
        return self._post(
            "/score-risk",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "extracted_fields": extracted_fields,
                "risk_features": risk_features,
            },
        )

    def search_evidence(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        query: str,
        source_types: list[str],
        top_k: int = 5,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/search-evidence",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "query": query,
                "source_types": source_types,
                "top_k": top_k,
                "context": context or {},
            },
        )

    def draft_message(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        extracted_fields: dict[str, Any],
        risk_level: str,
        evidence_ids: list[str],
        evidence_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        customer_name = extracted_fields.get("customer_name") or "Customer"

        return self._post(
            "/draft-message",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "customer_name": customer_name,
                "invoice_number": extracted_fields.get("invoice_number"),
                "amount_due": extracted_fields.get("amount_due"),
                "currency": extracted_fields.get("currency", "USD"),
                "due_date": extracted_fields.get("due_date"),
                "risk_level": risk_level,
                "evidence_ids": evidence_ids,
                "evidence_context": evidence_context or [],
            },
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        close_after_request = self._client is None

        try:
            response = client.post(f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return dict(response.json())
        finally:
            if close_after_request:
                client.close()