from typing import Any

import httpx

from app.config import settings


class ModelServerClient:
    """HTTP client for calling the Finplex model server."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or settings.model_server_url).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def extract_invoice(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        file_name: str,
        storage_key: str,
        text: str | None = None,
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
        days_overdue: int = 0,
        has_dispute: bool = False,
        previous_late_payments: int = 0,
        customer_relationship_status: str = "normal",
    ) -> dict[str, Any]:
        return self._post(
            "/score-risk",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "extracted_fields": extracted_fields,
                "days_overdue": days_overdue,
                "has_dispute": has_dispute,
                "previous_late_payments": previous_late_payments,
                "customer_relationship_status": customer_relationship_status,
            },
        )

    def draft_message(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        customer_name: str,
        invoice_number: str | None = None,
        amount_due: float | None = None,
        currency: str = "USD",
        due_date: str | None = None,
        risk_level: str = "low",
        evidence_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/draft-message",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "customer_name": customer_name,
                "invoice_number": invoice_number,
                "amount_due": amount_due,
                "currency": currency,
                "due_date": due_date,
                "risk_level": risk_level,
                "evidence_ids": evidence_ids or [],
            },
        )

    def process_invoice(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        file_name: str,
        storage_key: str,
        text: str | None = None,
        days_overdue: int = 0,
        has_dispute: bool = False,
        previous_late_payments: int = 0,
        customer_relationship_status: str = "normal",
    ) -> dict[str, Any]:
        return self._post(
            "/process-invoice",
            {
                "invoice_id": invoice_id,
                "tenant_id": tenant_id,
                "file_name": file_name,
                "storage_key": storage_key,
                "text": text,
                "days_overdue": days_overdue,
                "has_dispute": has_dispute,
                "previous_late_payments": previous_late_payments,
                "customer_relationship_status": customer_relationship_status,
            },
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()