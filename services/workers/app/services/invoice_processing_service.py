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
    def process_invoice(
        self,
        *,
        invoice_id: str,
        tenant_id: str,
        file_name: str,
        storage_key: str,
        text: str,
        risk_features: dict[str, Any] | None = None,
        pipeline_context: dict[str, Any] | None = None,
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
    """Coordinates invoice AI processing as one product workflow.

    The worker keeps HTTP upload fast. After Kafka receives an invoice upload
    event, the worker reads OCR text, calls the model-server pipeline once
    for extraction, risk, RAG evidence, and draft generation, validates the
    draft through guardrails, then creates a human review task.
    """

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
                status="PROCESSING",
            )
            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="invoice_processing_started",
                actor_user_id=event.uploaded_by_user_id,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={
                    "file_name": event.file_name,
                    "content_type": event.content_type,
                    "size_bytes": event.size_bytes,
                    "pipeline_mode": "model_server_process_invoice",
                },
            )

            ocr_result = self._read_invoice_text(event)
            invoice_text = str(ocr_result["text"])

            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="ocr_text_extracted",
                actor_user_id=None,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={
                    "ocr_engine": ocr_result["engine"],
                    "ocr_source": ocr_result["source"],
                    "ocr_confidence": ocr_result["confidence"],
                    "text_length": len(invoice_text),
                },
            )

            pipeline = self.model_client.process_invoice(
                invoice_id=event.invoice_id,
                tenant_id=event.tenant_id,
                file_name=event.file_name,
                storage_key=event.storage_key,
                text=invoice_text,
                pipeline_context={
                    "trace_id": trace_id,
                    "uploaded_by_user_id": event.uploaded_by_user_id,
                    "content_type": event.content_type,
                    "size_bytes": event.size_bytes,
                    "ocr_engine": ocr_result["engine"],
                    "ocr_source": ocr_result["source"],
                    "ocr_confidence": ocr_result["confidence"],
                    "ocr_text_length": len(invoice_text),
                },
            )

            extraction = dict(pipeline.get("extraction", {}))
            risk = dict(pipeline.get("risk", {}))
            draft = dict(pipeline.get("draft", {}))
            citations = list(pipeline.get("citations", []))

            extracted_fields = dict(extraction.get("extracted_fields", {}))
            risk_level = self._normalize_risk_level(str(risk["risk_level"]))
            draft_message = str(draft["draft_message"])

            evidence_ids = self._merge_evidence_ids(
                extraction.get("evidence_ids", []),
                risk.get("evidence_ids", []),
                draft.get("evidence_ids", []),
                [citation.get("evidence_id") for citation in citations],
            )

            self.repository.record_audit(
                tenant_id=event.tenant_id,
                action="evidence_retrieved",
                actor_user_id=None,
                entity_type="invoice",
                entity_id=event.invoice_id,
                trace_id=trace_id,
                metadata_json={
                    "retrieval_method": self._pipeline_retrieval_method(pipeline),
                    "evidence_count": len(citations),
                    "evidence_ids": evidence_ids,
                    "pipeline_version": self._pipeline_version(pipeline),
                },
            )

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
                    "retrieval_method": self._pipeline_retrieval_method(pipeline),
                    "pipeline_version": self._pipeline_version(pipeline),
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
                status="REVIEW_PENDING",
                extracted_fields=self._enrich_extracted_fields(
                    extracted_fields=extracted_fields,
                    pipeline=pipeline,
                    guardrails=guardrails,
                    risk_level=risk_level,
                    review_id=review_id,
                    ocr_result=ocr_result,
                ),
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
                    "risk_score": risk.get("risk_score"),
                    "model_loaded": risk.get("model_loaded", False),
                    "model_name": risk.get("model_name"),
                    "guardrails_passed": guardrails_passed,
                    "guardrail_decision": guardrails.get("decision"),
                    "evidence_count": len(citations),
                    "pipeline_version": self._pipeline_version(pipeline),
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
            status="FAILED",
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

    def _read_invoice_text(
        self,
        event: InvoiceUploadedEvent,
    ) -> dict[str, Any]:
        reader_with_result = getattr(self.text_reader, "read_result", None)
        if callable(reader_with_result):
            result = reader_with_result(event)
            metadata_method = getattr(result, "to_pipeline_metadata", None)
            metadata = metadata_method() if callable(metadata_method) else {}
            return {
                "text": getattr(result, "text", ""),
                "engine": getattr(result, "engine", "unknown"),
                "source": getattr(result, "source", "unknown"),
                "confidence": float(getattr(result, "confidence", 0.0)),
                "text_length": len(getattr(result, "text", "")),
                "metadata": metadata,
            }

        text = self.text_reader.read_text(event)
        return {
            "text": text,
            "engine": "legacy_text_reader",
            "source": "text_reader",
            "confidence": 0.7,
            "text_length": len(text),
            "metadata": {},
        }

    def _enrich_extracted_fields(
        self,
        *,
        extracted_fields: dict[str, Any],
        pipeline: dict[str, Any],
        guardrails: dict[str, Any],
        risk_level: str,
        review_id: str,
        ocr_result: dict[str, Any],
    ) -> dict[str, Any]:
        risk = dict(pipeline.get("risk", {}))
        draft = dict(pipeline.get("draft", {}))
        citations = list(pipeline.get("citations", []))

        return {
            **extracted_fields,
            "ai_pipeline": {
                "pipeline_version": self._pipeline_version(pipeline),
                "risk_level": risk_level,
                "risk_score": risk.get("risk_score"),
                "risk_reasons": risk.get("reasons", []),
                "top_risk_signals": risk.get("top_risk_signals", []),
                "model_name": risk.get("model_name"),
                "model_loaded": risk.get("model_loaded", False),
                "retrieval_method": self._pipeline_retrieval_method(pipeline),
                "citation_count": len(citations),
                "draft_model_version": draft.get("model_version"),
                "guardrails_passed": bool(guardrails.get("passed", False)),
                "guardrail_decision": guardrails.get("decision"),
                "review_id": review_id,
                "ocr": {
                    "engine": ocr_result["engine"],
                    "source": ocr_result["source"],
                    "confidence": ocr_result["confidence"],
                    "text_length": ocr_result["text_length"],
                },
            },
        }

    def _pipeline_version(self, pipeline: dict[str, Any]) -> str | None:
        extraction = dict(pipeline.get("extraction", {}))
        risk = dict(pipeline.get("risk", {}))
        draft = dict(pipeline.get("draft", {}))
        return (
            draft.get("model_version")
            or risk.get("model_version")
            or extraction.get("model_version")
        )

    def _pipeline_retrieval_method(self, pipeline: dict[str, Any]) -> str | None:
        citations = pipeline.get("citations", [])
        if not citations:
            return None

        first_citation = citations[0]
        if isinstance(first_citation, dict):
            metadata = first_citation.get("metadata", {})
            if isinstance(metadata, dict):
                return metadata.get("retrieval_method")

        return "model_server_pipeline"

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
                if evidence_id is None:
                    continue

                evidence_id_text = str(evidence_id)
                if evidence_id_text not in merged:
                    merged.append(evidence_id_text)

        return merged
