from typing import Any

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
        extracted_fields = extraction.extracted_fields.model_dump()
        risk_features = request.risk_features or self._build_risk_features(
            extracted_fields
        )
        risk = self.risk_service.score(
            RiskScoreRequest(
                invoice_id=request.invoice_id,
                tenant_id=request.tenant_id,
                extracted_fields=extracted_fields,
                days_overdue=request.days_overdue,
                has_dispute=request.has_dispute,
                previous_late_payments=request.previous_late_payments,
                customer_relationship_status=request.customer_relationship_status,
                risk_features=risk_features,
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

    def _build_risk_features(self, extracted_fields: dict[str, Any]):
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