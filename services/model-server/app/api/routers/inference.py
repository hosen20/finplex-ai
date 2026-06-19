from app.schemas import (
    DraftMessageRequest,
    DraftMessageResponse,
    EvidenceSearchRequest,
    EvidenceSearchResponse,
    InvoiceExtractionRequest,
    InvoiceExtractionResponse,
    InvoicePipelineRequest,
    InvoicePipelineResponse,
    RiskScoreRequest,
    RiskScoreResponse,
)
from app.services.drafting_service import DraftingService
from app.services.evidence_service import EvidenceService
from app.services.extraction_service import InvoiceExtractionService
from app.services.pipeline_service import InvoicePipelineService
from app.services.risk_service import RiskScoringService
from fastapi import APIRouter

router = APIRouter(tags=["ai-pipeline"])


@router.post("/extract-invoice", response_model=InvoiceExtractionResponse)
def extract_invoice(payload: InvoiceExtractionRequest):
    return InvoiceExtractionService().extract(payload)


@router.post("/score-risk", response_model=RiskScoreResponse)
def score_risk(payload: RiskScoreRequest):
    return RiskScoringService().score(payload)


@router.post("/search-evidence", response_model=EvidenceSearchResponse)
def search_evidence(payload: EvidenceSearchRequest):
    return EvidenceService().search(payload)


@router.post("/draft-message", response_model=DraftMessageResponse)
def draft_message(payload: DraftMessageRequest):
    return DraftingService().create_draft(payload)


@router.post("/process-invoice", response_model=InvoicePipelineResponse)
def process_invoice(payload: InvoicePipelineRequest):
    return InvoicePipelineService().process_invoice(payload)