from typing import Any

import httpx

from app.config import settings


class GuardrailsClient:
    """HTTP client used by workers to validate draft messages."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.guardrails_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.model_server_timeout_seconds
        self._client = client

    def validate_message(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        draft_message: str,
        risk_level: str,
        evidence_ids: list[str],
        customer_name: str | None = None,
        amount_due: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/validate-message",
            {
                "tenant_id": tenant_id,
                "invoice_id": invoice_id,
                "draft_message": draft_message,
                "risk_level": risk_level,
                "evidence_ids": evidence_ids,
                "customer_name": customer_name,
                "amount_due": amount_due,
                "metadata": metadata or {},
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