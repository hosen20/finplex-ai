from app.config import settings
from app.schemas import (
    DraftMessageRequest,
    EvidenceSearchRequest,
    InvoicePipelineRequest,
    InvoicePipelineResponse,
    RiskScoreRequest,
)
from app.services.drafting_service import DraftingService
from app.services.evidence_service import EvidenceService
from app.services.extraction_service import InvoiceExtractionService
from app.services.risk_service import RiskScoringService


class InvoicePipelineService:
    """Runs extraction, risk scoring, evidence retrieval, and drafting."""

    def __init__(
        self,
        *,
        extraction_service: InvoiceExtractionService | None = None,
        risk_service: RiskScoringService | None = None,
        evidence_service: EvidenceService | None = None,
        drafting_service: DraftingService | None = None,
    ) -> None:
        self.extraction_service = extraction_service or InvoiceExtractionService()
        self.risk_service = risk_service or RiskScoringService()
        self.evidence_service = evidence_service or EvidenceService()
        self.drafting_service = drafting_service or DraftingService()

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
                risk_features=request.risk_features,
            )
        )

        evidence = self.evidence_service.search(
            EvidenceSearchRequest(
                tenant_id=request.tenant_id,
                invoice_id=request.invoice_id,
                query=self._build_evidence_query(request, extraction, risk),
                source_types=["regulation", "invoice", "erp", "crm"],
                top_k=settings.evidence_max_results,
                context={
                    "risk_level": risk.risk_level,
                    "invoice_number": extraction.extracted_fields.invoice_number,
                    "customer_name": extraction.extracted_fields.customer_name,
                },
            )
        )

        draft = self.drafting_service.create_draft(
            DraftMessageRequest(
                invoice_id=request.invoice_id,
                tenant_id=request.tenant_id,
                customer_name=extraction.extracted_fields.customer_name
                or "Customer",
                invoice_number=extraction.extracted_fields.invoice_number,
                amount_due=extraction.extracted_fields.amount_due,
                currency=extraction.extracted_fields.currency,
                due_date=extraction.extracted_fields.due_date,
                risk_level=risk.risk_level,
                evidence_ids=[
                    *extraction.evidence_ids,
                    *risk.evidence_ids,
                    *evidence.evidence_ids,
                ],
                evidence_context=evidence.citations,
            )
        )

        return InvoicePipelineResponse(
            extraction=extraction,
            risk=risk,
            draft=draft,
            citations=evidence.citations,
        )

    def _build_evidence_query(
        self,
        request: InvoicePipelineRequest,
        extraction,
        risk,
    ) -> str:
        fields = extraction.extracted_fields

        parts = [
            request.invoice_id,
            fields.invoice_number or "",
            fields.customer_name or "",
            str(fields.amount_due or ""),
            fields.due_date or "",
            risk.risk_level,
            " ".join(risk.reasons),
        ]

        if request.risk_features is not None:
            feature_payload = request.risk_features.model_dump()
            parts.extend(
                [
                    str(feature_payload.get("previous_late_payments", "")),
                    str(feature_payload.get("previous_disputed_count", "")),
                    str(feature_payload.get("previous_dispute_rate", "")),
                    str(
                        feature_payload.get(
                            "previous_crm_negative_signal_score",
                            "",
                        )
                    ),
                ]
            )

        return " ".join(part for part in parts if part)