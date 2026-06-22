"""Invoice AI pipeline service backed by LangGraph orchestration."""

from app.schemas import InvoicePipelineRequest, InvoicePipelineResponse
from app.services.drafting_service import DraftingService
from app.services.evidence_service import EvidenceService
from app.services.extraction_service import InvoiceExtractionService
from app.services.langgraph_pipeline import LangGraphInvoiceOrchestrator
from app.services.risk_service import RiskScoringService


class InvoicePipelineService:
    """Facade used by the API route to run the LangGraph invoice workflow."""

    def __init__(
        self,
        *,
        extraction_service: InvoiceExtractionService | None = None,
        risk_service: RiskScoringService | None = None,
        evidence_service: EvidenceService | None = None,
        drafting_service: DraftingService | None = None,
    ) -> None:
        self.orchestrator = LangGraphInvoiceOrchestrator(
            extraction_service=extraction_service,
            risk_service=risk_service,
            evidence_service=evidence_service,
            drafting_service=drafting_service,
        )

    def process_invoice(
        self,
        request: InvoicePipelineRequest,
    ) -> InvoicePipelineResponse:
        """Run the LangGraph workflow for one invoice."""
        return self.orchestrator.process_invoice(request)
