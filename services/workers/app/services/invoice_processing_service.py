from typing import Any, Protocol

from app.events import InvoiceUploadedEvent


class InvoiceRepositoryProtocol(Protocol):
    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        ...

    def update_invoice_processing(
        self,
        *,
        invoice_id: str,
        status: str,
        extracted_fields: dict[str, Any] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> None:
        ...

    def create_review(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        draft_message: str,
        risk_level: str,
        guardrails_passed: bool,
        evidence_ids: list[str],
    ) -> str:
        ...

    def record_audit(
        self,
        *,
        tenant_id: str,
        action: str,
        actor_user_id: str | None,
        entity_type: str,
        entity_id: str,
        trace_id: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


class ModelServerClientProtocol(Protocol):
    def extract_invoice(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        file_name: str,
        storage_key: str,
        text: str,
    ) -> dict[str, Any]:
        ...

    def score_risk(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        extracted_fields: dict[str, Any],
        risk_features: dict[str, Any],
    ) -> dict[str, Any]:
        ...

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
        ...

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
        ...


class GuardrailsClientProtocol(Protocol):
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
        ...


class InvoiceTextReaderProtocol(Protocol):
    def read_text(self, event: InvoiceUploadedEvent) -> str:
        ...


class InvoiceProcessingService:
    """Coordinates extraction, risk, evidence retrieval, guardrails, and review."""

    def __init__(
        self,
        *,
        repository: InvoiceRepositoryProtocol,
        model_client: ModelServerClientProtocol,
        guardrails_client: GuardrailsClientProtocol,
        text_reader: InvoiceTextReaderProtocol,
    ) -> None:
        self.repository = repository
        self.model_client = model_client
        self.guardrails_client = guardrails_client
        self.text_reader = text_reader

    def process_event(self, event: InvoiceUploadedEvent) -> str:
        invoice = self.repository.get_invoice(event.invoice_id)
        if invoice is None:
            raise ValueError(f"Invoice {event.invoice_id} was not found.")

        trace_id = event.event_id

        try:
            self.repository.update_invoice_processing(
                invoice_id=event.invoice_id,
                status="processing",
            )
            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="invoice_processing_started",
                actor_user_id=event.uploaded_by_user_id,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={"file_name": event.file_name},
            )

            invoice_text = self.text_reader.read_text(event)

            extraction = self.model_client.extract_invoice(
                invoice_id=event.invoice_id,
                tenant_id=event.tenant_id,
                file_name=event.file_name,
                storage_key=event.storage_key,
                text=invoice_text,
            )
            extracted_fields = dict(extraction.get("extracted_fields", {}))
            risk_features = self._build_risk_features(extracted_fields)

            risk = self.model_client.score_risk(
                invoice_id=event.invoice_id,
                tenant_id=event.tenant_id,
                extracted_fields=extracted_fields,
                risk_features=risk_features,
            )
            risk_level = self._normalize_risk_level(str(risk["risk_level"]))

            evidence_ids = self._merge_evidence_ids(
                extraction.get("evidence_ids", []),
                risk.get("evidence_ids", []),
            )

            evidence = self.model_client.search_evidence(
                invoice_id=event.invoice_id,
                tenant_id=event.tenant_id,
                query=self._build_evidence_query(
                    event=event,
                    extracted_fields=extracted_fields,
                    risk=risk,
                ),
                source_types=["regulation", "invoice", "erp", "crm"],
                top_k=5,
                context={
                    "trace_id": trace_id,
                    "risk_level": risk_level,
                    "customer_name": extracted_fields.get("customer_name"),
                    "invoice_number": extracted_fields.get("invoice_number"),
                },
            )
            evidence_citations = list(evidence.get("citations", []))

            evidence_ids = self._merge_evidence_ids(
                evidence_ids,
                evidence.get("evidence_ids", []),
            )

            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="evidence_retrieved",
                actor_user_id=None,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={
                    "retrieval_method": evidence.get("retrieval_method"),
                    "evidence_count": len(evidence_citations),
                    "evidence_ids": evidence.get("evidence_ids", []),
                },
            )

            draft = self.model_client.draft_message(
                invoice_id=event.invoice_id,
                tenant_id=event.tenant_id,
                extracted_fields=extracted_fields,
                risk_level=risk_level,
                evidence_ids=evidence_ids,
                evidence_context=evidence_citations,
            )

            evidence_ids = self._merge_evidence_ids(
                evidence_ids,
                draft.get("evidence_ids", []),
            )
            draft_message = str(draft["draft_message"])

            guardrails = self.guardrails_client.validate_message(
                tenant_id=event.tenant_id,
                invoice_id=event.invoice_id,
                draft_message=draft_message,
                risk_level=risk_level,
                evidence_ids=evidence_ids,
                customer_name=extracted_fields.get("customer_name"),
                amount_due=extracted_fields.get("amount_due"),
                metadata={
                    "trace_id": trace_id,
                    "model_loaded": risk.get("model_loaded", False),
                    "model_name": risk.get("model_name"),
                    "retrieval_method": evidence.get("retrieval_method"),
                },
            )

            guardrails_passed = bool(guardrails.get("passed", False))
            review_message = str(
                guardrails.get("redacted_message") or draft_message
            )
            policy_version = str(guardrails.get("policy_version", "unknown"))

            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="guardrails_validated",
                actor_user_id=None,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={
                    "passed": guardrails_passed,
                    "decision": guardrails.get("decision"),
                    "policy_version": policy_version,
                    "finding_count": len(guardrails.get("findings", [])),
                    "nemo_passed": guardrails.get("nemo_passed"),
                },
            )

            review_id = self.repository.create_review(
                tenant_id=event.tenant_id,
                invoice_id=event.invoice_id,
                draft_message=review_message,
                risk_level=risk_level,
                guardrails_passed=guardrails_passed,
                evidence_ids=evidence_ids,
            )

            self.repository.update_invoice_processing(
                invoice_id=event.invoice_id,
                status="review_pending",
                extracted_fields=extracted_fields,
                evidence_ids=evidence_ids,
            )
            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="invoice_processed",
                actor_user_id=None,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={
                    "review_id": review_id,
                    "risk_level": risk_level,
                    "model_loaded": risk.get("model_loaded", False),
                    "guardrails_passed": guardrails_passed,
                    "guardrail_decision": guardrails.get("decision"),
                    "evidence_count": len(evidence_citations),
                },
            )

            self.repository.commit()
            return review_id

        except Exception as exc:
            self.repository.rollback()
            self._mark_failed(event, trace_id, exc)
            raise

    def _mark_failed(
        self,
        event: InvoiceUploadedEvent,
        trace_id: str,
        exc: Exception,
    ) -> None:
        self.repository.update_invoice_processing(
            invoice_id=event.invoice_id,
            status="failed",
        )
        self.repository.record_audit(
            tenant_id=event.tenant_id,
            action="invoice_processing_failed",
            actor_user_id=None,
            entity_type="invoice",
            entity_id=event.invoice_id,
            trace_id=trace_id,
            metadata_json={"error": str(exc)},
        )
        self.repository.commit()

    def _build_risk_features(
        self,
        extracted_fields: dict[str, Any],
    ) -> dict[str, Any]:
        amount_due = float(extracted_fields.get("amount_due") or 0.0)
        payment_terms_days = self._payment_terms_days(
            extracted_fields.get("payment_terms")
        )
        high_amount_signal = amount_due >= 10_000

        previous_invoice_count = 12 if high_amount_signal else 4
        previous_late_payments = 5 if high_amount_signal else 1
        previous_disputed_count = 2 if high_amount_signal else 0
        previous_average_amount = amount_due or 1_000.0

        return {
            "amount_due": amount_due,
            "payment_terms_days": payment_terms_days,
            "paperless_bill": 0,
            "country_code": "US",
            "previous_invoice_count": previous_invoice_count,
            "previous_late_payments": previous_late_payments,
            "previous_disputed_count": previous_disputed_count,
            "previous_total_amount": (
                previous_average_amount * previous_invoice_count
            ),
            "previous_average_invoice_amount": previous_average_amount,
            "previous_average_days_late": 9.5 if high_amount_signal else 1.0,
            "previous_max_days_late": 34.0 if high_amount_signal else 5.0,
            "previous_on_time_payment_rate": (
                0.58 if high_amount_signal else 0.88
            ),
            "previous_dispute_rate": 0.16 if high_amount_signal else 0.0,
            "previous_crm_negative_signal_score": (
                0.42 if high_amount_signal else 0.05
            ),
            "relationship_age_days": 950 if high_amount_signal else 420,
        }

    def _build_evidence_query(
        self,
        *,
        event: InvoiceUploadedEvent,
        extracted_fields: dict[str, Any],
        risk: dict[str, Any],
    ) -> str:
        query_parts = [
            event.invoice_id,
            event.file_name,
            str(extracted_fields.get("invoice_number") or ""),
            str(extracted_fields.get("customer_name") or ""),
            str(extracted_fields.get("amount_due") or ""),
            str(extracted_fields.get("due_date") or ""),
            str(risk.get("risk_level") or ""),
            " ".join(str(reason) for reason in risk.get("reasons", [])),
        ]

        for signal in risk.get("top_risk_signals", []):
            if isinstance(signal, dict):
                query_parts.extend(
                    [
                        str(signal.get("name") or ""),
                        str(signal.get("reason") or ""),
                        str(signal.get("value") or ""),
                    ]
                )

        return " ".join(part for part in query_parts if part)

    def _payment_terms_days(self, payment_terms: Any) -> int:
        if payment_terms is None:
            return 30

        text = str(payment_terms).lower()
        for token in text.replace("_", " ").split():
            if token.isdigit():
                return int(token)

        return 30

    def _normalize_risk_level(self, risk_level: str) -> str:
        normalized = risk_level.lower()

        if normalized == "critical":
            return "high"

        if normalized in {"low", "medium", "high"}:
            return normalized

        return "medium"

    def _merge_evidence_ids(self, *groups: Any) -> list[str]:
        merged: list[str] = []

        for group in groups:
            if group is None:
                continue

            for evidence_id in group:
                evidence_id_text = str(evidence_id)
                if evidence_id_text not in merged:
                    merged.append(evidence_id_text)

        return merged