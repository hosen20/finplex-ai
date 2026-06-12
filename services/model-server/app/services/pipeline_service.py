from app.schemas import (
    DraftMessageRequest,
    InvoicePipelineRequest,
    InvoicePipelineResponse,
    RiskScoreRequest,
)
from app.services.drafting_service import DraftingService
from app.services.extraction_service import InvoiceExtractionService
from app.services.risk_service import RiskScoringService


class InvoicePipelineService:
    """Runs the placeholder extraction, risk, and drafting pipeline."""

    def __init__(self) -> None:
        self.extraction_service = InvoiceExtractionService()
        self.risk_service = RiskScoringService()
        self.drafting_service = DraftingService()

    def process_invoice(
        self,
        request: InvoicePipelineRequest,
    ) -> InvoicePipelineResponse:
        extraction = self.extraction_service.extract(request)
        risk = self.risk_service.score(
            RiskScoreRequest(
                invoice_id=request.invoice_id,
                tenant_id=request.tenant_id,
                extracted_fields=extraction.extracted_fields.model_dump(),
                days_overdue=request.days_overdue,
                has_dispute=request.has_dispute,
                previous_late_payments=request.previous_late_payments,
                customer_relationship_status=request.customer_relationship_status,
            )
        )
        draft = self.drafting_service.create_draft(
            DraftMessageRequest(
                invoice_id=request.invoice_id,
                tenant_id=request.tenant_id,
                customer_name=extraction.extracted_fields.customer_name or "Customer",
                invoice_number=extraction.extracted_fields.invoice_number,
                amount_due=extraction.extracted_fields.amount_due,
                currency=extraction.extracted_fields.currency,
                due_date=extraction.extracted_fields.due_date,
                risk_level=risk.risk_level,
                evidence_ids=[
                    *extraction.evidence_ids,
                    f"ev_{request.invoice_id}_risk",
                ],
            )
        )

        return InvoicePipelineResponse(
            extraction=extraction,
            risk=risk,
            draft=draft,
        )