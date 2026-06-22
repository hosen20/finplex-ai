from datetime import UTC, datetime
from typing import Any

import pytest
from app.events import InvoiceUploadedEvent
from app.services.invoice_processing_service import InvoiceProcessingService


class FakeRepository:
    def __init__(self) -> None:
        self.invoice = {"invoice_id": "inv_1", "tenant_id": "tenant_1"}
        self.statuses: list[str] = []
        self.reviews: list[dict[str, Any]] = []
        self.audits: list[dict[str, Any]] = []
        self.commits = 0
        self.rollbacks = 0

    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        if invoice_id == self.invoice["invoice_id"]:
            return self.invoice

        return None

    def update_invoice_processing(
        self,
        *,
        invoice_id: str,
        status: str,
        extracted_fields: dict[str, Any] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> None:
        self.statuses.append(status)
        self.invoice["extracted_fields"] = extracted_fields
        self.invoice["evidence_ids"] = evidence_ids

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
        review = {
            "tenant_id": tenant_id,
            "invoice_id": invoice_id,
            "draft_message": draft_message,
            "risk_level": risk_level,
            "guardrails_passed": guardrails_passed,
            "evidence_ids": evidence_ids,
        }
        self.reviews.append(review)
        return "review_1"

    def record_audit(self, **kwargs: Any) -> None:
        self.audits.append(kwargs)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeModelClient:
    def __init__(self) -> None:
        self.pipeline_calls: list[dict[str, Any]] = []

    def process_invoice(self, **kwargs: Any) -> dict[str, Any]:
        self.pipeline_calls.append(kwargs)
        assert "risk_features" not in kwargs
        assert kwargs["pipeline_context"]["trace_id"] == "evt_1"

        return {
            "extraction": {
                "invoice_id": "inv_1",
                "tenant_id": "tenant_1",
                "extracted_fields": {
                    "invoice_number": "INV-1",
                    "customer_name": "Acme",
                    "amount_due": 12_000.0,
                    "currency": "USD",
                    "due_date": "2026-07-01",
                    "payment_terms": "net_30",
                },
                "confidence": 0.95,
                "evidence_ids": ["ev_extract"],
                "model_version": "pipeline_v1",
            },
            "risk": {
                "invoice_id": "inv_1",
                "tenant_id": "tenant_1",
                "risk_level": "critical",
                "risk_score": 0.91,
                "reasons": ["High amount and previous late payments."],
                "evidence_ids": ["ev_risk"],
                "model_version": "pipeline_v1",
                "model_loaded": True,
                "model_name": "logistic_regression",
                "top_risk_signals": [
                    {
                        "name": "previous_late_payments",
                        "value": 5,
                        "reason": "Customer has previous late payments.",
                    }
                ],
            },
            "draft": {
                "invoice_id": "inv_1",
                "tenant_id": "tenant_1",
                "draft_message": "Please review invoice INV-1 for 12000.",
                "guardrails_required": True,
                "evidence_ids": ["ev_draft"],
                "citations": [],
                "model_version": "pipeline_v1",
            },
            "citations": [
                {
                    "evidence_id": "ev_evidence",
                    "source_type": "erp",
                    "title": "Historical Erp Payments",
                    "snippet": "Acme invoice INV-1 was late by 14 days.",
                    "score": 0.82,
                    "metadata": {
                        "retrieval_method": "hybrid_sparse_dense_local",
                    },
                }
            ],
        }


class FakeGuardrailsClient:
    def __init__(self, *, passed: bool = True) -> None:
        self.passed = passed
        self.calls: list[dict[str, Any]] = []

    def validate_message(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "passed": self.passed,
            "decision": (
                "send_to_human_review" if self.passed else "block_rewrite"
            ),
            "redacted_message": kwargs["draft_message"],
            "policy_version": "guardrails_policy_v0.1.0",
            "findings": [],
            "nemo_passed": self.passed,
            "nemo_messages": ["NeMo first-pass validation passed."],
        }


class FakeTextReader:
    def read_text(self, event: InvoiceUploadedEvent) -> str:
        return "Invoice number: INV-1 Customer: Acme Amount due: 12000"


def make_event() -> InvoiceUploadedEvent:
    return InvoiceUploadedEvent(
        invoice_id="inv_1",
        tenant_id="tenant_1",
        uploaded_by_user_id="user_1",
        file_name="invoice.txt",
        storage_key="tenant_1/invoices/inv_1/invoice.txt",
        content_type="text/plain",
        size_bytes=100,
        event_id="evt_1",
        occurred_at=datetime.now(UTC),
    )


def make_service(
    repository: FakeRepository,
    guardrails_client: FakeGuardrailsClient,
    model_client: FakeModelClient | None = None,
) -> InvoiceProcessingService:
    return InvoiceProcessingService(
        repository=repository,
        model_client=model_client or FakeModelClient(),
        guardrails_client=guardrails_client,
        text_reader=FakeTextReader(),
    )


def test_process_event_creates_review_and_updates_invoice() -> None:
    repository = FakeRepository()
    guardrails_client = FakeGuardrailsClient(passed=True)
    model_client = FakeModelClient()
    service = make_service(repository, guardrails_client, model_client)

    review_id = service.process_event(make_event())

    assert review_id == "review_1"
    assert repository.statuses == ["PROCESSING", "REVIEW_PENDING"]
    assert repository.reviews[0]["risk_level"] == "high"
    assert repository.reviews[0]["guardrails_passed"] is True
    assert repository.reviews[0]["evidence_ids"] == [
        "ev_extract",
        "ev_risk",
        "ev_draft",
        "ev_evidence",
    ]

    assert len(model_client.pipeline_calls) == 1
    assert model_client.pipeline_calls[0]["text"].startswith("Invoice number")
    assert model_client.pipeline_calls[0]["pipeline_context"]["ocr_engine"] == (
        "legacy_text_reader"
    )
    assert guardrails_client.calls[0]["risk_level"] == "high"
    assert guardrails_client.calls[0]["evidence_ids"] == [
        "ev_extract",
        "ev_risk",
        "ev_draft",
        "ev_evidence",
    ]

    extracted_fields = repository.invoice["extracted_fields"]
    assert extracted_fields["ai_pipeline"]["review_id"] == "review_1"
    assert extracted_fields["ai_pipeline"]["pipeline_version"] == "pipeline_v1"
    assert extracted_fields["ai_pipeline"]["guardrails_passed"] is True
    assert extracted_fields["ai_pipeline"]["ocr"]["engine"] == "legacy_text_reader"


def test_guardrail_failure_still_routes_to_human_review() -> None:
    repository = FakeRepository()
    service = make_service(repository, FakeGuardrailsClient(passed=False))

    review_id = service.process_event(make_event())

    assert review_id == "review_1"
    assert repository.reviews[0]["guardrails_passed"] is False
    assert repository.statuses[-1] == "REVIEW_PENDING"


def test_missing_invoice_raises_error() -> None:
    repository = FakeRepository()
    repository.invoice = {"invoice_id": "other", "tenant_id": "tenant_1"}
    service = make_service(repository, FakeGuardrailsClient())

    with pytest.raises(ValueError):
        service.process_event(make_event())
