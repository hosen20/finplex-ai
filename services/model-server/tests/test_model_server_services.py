from app.schemas import (
    DraftMessageRequest,
    InvoiceExtractionRequest,
    RiskScoreRequest,
)
from app.services.drafting_service import DraftingService
from app.services.extraction_service import InvoiceExtractionService
from app.services.risk_service import RiskScoringService


def test_extraction_service_extracts_basic_invoice_fields() -> None:
    response = InvoiceExtractionService().extract(
        InvoiceExtractionRequest(
            invoice_id="inv_001",
            tenant_id="tenant_001",
            file_name="invoice.pdf",
            storage_key="tenant_001/invoices/inv_001/invoice.pdf",
            text=(
                "Invoice Number: INV-2026 Customer: Acme SARL "
                "Total: 1200.50 Due Date: 2026-07-15"
            ),
        )
    )

    assert response.extracted_fields.invoice_number == "INV-2026"
    assert response.extracted_fields.customer_name == "Acme SARL"
    assert response.extracted_fields.amount_due == 1200.50
    assert response.confidence > 0.5


def test_risk_service_scores_high_when_overdue_and_disputed() -> None:
    response = RiskScoringService().score(
        RiskScoreRequest(
            invoice_id="inv_001",
            tenant_id="tenant_001",
            days_overdue=65,
            has_dispute=True,
            previous_late_payments=2,
        )
    )

    assert response.risk_level in {"high", "critical"}
    assert response.risk_score >= 0.65
    assert response.reasons


def test_drafting_service_creates_guardrails_required_message() -> None:
    response = DraftingService().create_draft(
        DraftMessageRequest(
            invoice_id="inv_001",
            tenant_id="tenant_001",
            customer_name="Acme SARL",
            invoice_number="INV-2026",
            amount_due=1200.50,
            due_date="2026-07-15",
            risk_level="medium",
            evidence_ids=["ev_001"],
        )
    )

    assert "INV-2026" in response.draft_message
    assert "Acme SARL" in response.draft_message
    assert response.guardrails_required is True
    assert response.evidence_ids == ["ev_001"]

def test_pipeline_service_builds_risk_features_from_extraction() -> None:
    from app.schemas import InvoicePipelineRequest
    from app.services.pipeline_service import InvoicePipelineService

    response = InvoicePipelineService().process_invoice(
        InvoicePipelineRequest(
            invoice_id="inv_pipeline_001",
            tenant_id="tenant_001",
            file_name="invoice.txt",
            storage_key="tenant_001/invoices/inv_pipeline_001/invoice.txt",
            text=(
                "Invoice Number: INV-PIPE Customer: Cedar Clinic "
                "Total: 15000.00 Due Date: 2026-07-15 Net 30"
            ),
        )
    )

    assert response.extraction.extracted_fields.amount_due == 15000.0
    assert response.risk.risk_level in {"medium", "high", "critical"}
    assert response.risk.top_risk_signals
    assert response.draft.evidence_ids
    assert response.orchestration["engine"] == "langgraph"
