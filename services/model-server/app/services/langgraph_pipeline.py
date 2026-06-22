"""LangGraph orchestration for the invoice AI pipeline.

The graph keeps the model-server pipeline explicit and reviewable:
extract_invoice -> score_risk -> retrieve_evidence -> draft_message -> build_response.
Each node is deterministic in tests and can later be replaced by richer tools or agents.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph

from app.config import settings
from app.schemas import (
    DraftMessageRequest,
    EvidenceSearchRequest,
    EvidenceSearchResponse,
    InvoiceExtractionResponse,
    InvoicePipelineRequest,
    InvoicePipelineResponse,
    RiskScoreRequest,
    RiskScoreResponse,
)
from app.services.drafting_service import DraftingService
from app.services.evidence_service import EvidenceService
from app.services.extraction_service import InvoiceExtractionService
from app.services.risk_service import RiskScoringService

RAG_ORCHESTRATION_ENGINE = "langgraph"
RAG_ORCHESTRATION_VERSION = "langgraph_invoice_pipeline_v1"


class InvoicePipelineState(TypedDict, total=False):
    """Typed state passed between LangGraph invoice-pipeline nodes."""

    request: InvoicePipelineRequest
    extraction: InvoiceExtractionResponse
    extracted_fields: dict[str, Any]
    risk_features: dict[str, Any]
    risk: RiskScoreResponse
    evidence: EvidenceSearchResponse
    draft_evidence_ids: list[str]
    draft: Any
    response: InvoicePipelineResponse
    orchestration_trace: list[dict[str, Any]]


class LangGraphInvoiceOrchestrator:
    """Orchestrates invoice processing as an explicit LangGraph workflow."""

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
        self._graph = self._build_graph()

    def process_invoice(
        self,
        request: InvoicePipelineRequest,
    ) -> InvoicePipelineResponse:
        """Run the compiled LangGraph and return the product pipeline response."""
        final_state = self._graph.invoke(
            {
                "request": request,
                "orchestration_trace": [],
            }
        )
        response = final_state.get("response")
        if not isinstance(response, InvoicePipelineResponse):
            raise RuntimeError("LangGraph invoice pipeline did not build a response.")
        return response

    def _build_graph(self):
        graph = StateGraph(InvoicePipelineState)

        graph.add_node("extract_invoice", RunnableLambda(self._extract_invoice))
        graph.add_node("score_risk", RunnableLambda(self._score_risk))
        graph.add_node("retrieve_evidence", RunnableLambda(self._retrieve_evidence))
        graph.add_node("draft_message", RunnableLambda(self._draft_message))
        graph.add_node("build_response", RunnableLambda(self._build_response))

        graph.set_entry_point("extract_invoice")
        graph.add_edge("extract_invoice", "score_risk")
        graph.add_edge("score_risk", "retrieve_evidence")
        graph.add_edge("retrieve_evidence", "draft_message")
        graph.add_edge("draft_message", "build_response")
        graph.add_edge("build_response", END)

        return graph.compile()

    def _extract_invoice(
        self,
        state: InvoicePipelineState,
    ) -> dict[str, Any]:
        request = state["request"]
        extraction = self.extraction_service.extract(request)
        extracted_fields = extraction.extracted_fields.model_dump()

        return {
            "extraction": extraction,
            "extracted_fields": extracted_fields,
            "orchestration_trace": self._append_trace(
                state,
                "extract_invoice",
                {
                    "model_version": extraction.model_version,
                    "confidence": extraction.confidence,
                },
            ),
        }

    def _score_risk(
        self,
        state: InvoicePipelineState,
    ) -> dict[str, Any]:
        request = state["request"]
        extracted_fields = state["extracted_fields"]
        risk_features = self._normalize_risk_features(
            request.risk_features or self._build_risk_features(extracted_fields)
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

        return {
            "risk_features": risk_features,
            "risk": risk,
            "orchestration_trace": self._append_trace(
                state,
                "score_risk",
                {
                    "risk_level": risk.risk_level,
                    "risk_score": risk.risk_score,
                    "model_version": risk.model_version,
                },
            ),
        }

    def _retrieve_evidence(
        self,
        state: InvoicePipelineState,
    ) -> dict[str, Any]:
        request = state["request"]
        extraction = state["extraction"]
        risk = state["risk"]

        evidence = self.evidence_service.search(
            EvidenceSearchRequest(
                tenant_id=request.tenant_id,
                invoice_id=request.invoice_id,
                query=self._build_evidence_query(request, extraction, risk, state),
                source_types=["regulation", "invoice", "erp", "crm"],
                top_k=settings.evidence_max_results,
                context={
                    "risk_level": risk.risk_level,
                    "invoice_number": extraction.extracted_fields.invoice_number,
                    "customer_name": extraction.extracted_fields.customer_name,
                    **request.context,
                },
            )
        )

        draft_evidence_ids = [
            *extraction.evidence_ids,
            *risk.evidence_ids,
            *evidence.evidence_ids,
        ]

        return {
            "evidence": evidence,
            "draft_evidence_ids": draft_evidence_ids,
            "orchestration_trace": self._append_trace(
                state,
                "retrieve_evidence",
                {
                    "retrieval_method": evidence.retrieval_method,
                    "citation_count": len(evidence.citations),
                },
            ),
        }

    def _draft_message(
        self,
        state: InvoicePipelineState,
    ) -> dict[str, Any]:
        request = state["request"]
        extraction = state["extraction"]
        risk = state["risk"]
        evidence = state["evidence"]

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
                evidence_ids=state["draft_evidence_ids"],
                evidence_context=evidence.citations,
            )
        )

        return {
            "draft": draft,
            "orchestration_trace": self._append_trace(
                state,
                "draft_message",
                {
                    "model_version": draft.model_version,
                    "guardrails_required": draft.guardrails_required,
                },
            ),
        }

    def _build_response(
        self,
        state: InvoicePipelineState,
    ) -> dict[str, Any]:
        evidence = state["evidence"]
        trace = self._append_trace(
            state,
            "build_response",
            {"status": "completed"},
        )

        response = InvoicePipelineResponse(
            extraction=state["extraction"],
            risk=state["risk"],
            draft=state["draft"],
            citations=evidence.citations,
            orchestration={
                "engine": RAG_ORCHESTRATION_ENGINE,
                "version": RAG_ORCHESTRATION_VERSION,
                "nodes": [step["node"] for step in trace],
                "trace": trace,
            },
        )
        return {"response": response, "orchestration_trace": trace}

    def _append_trace(
        self,
        state: InvoicePipelineState,
        node: str,
        metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        trace = list(state.get("orchestration_trace", []))
        trace.append(
            {
                "node": node,
                "engine": RAG_ORCHESTRATION_ENGINE,
                "version": RAG_ORCHESTRATION_VERSION,
                "metadata": metadata,
            }
        )
        return trace

    def _normalize_risk_features(self, risk_features: Any) -> dict[str, Any]:
        if hasattr(risk_features, "model_dump"):
            return dict(risk_features.model_dump())
        return dict(risk_features)

    def _build_risk_features(self, extracted_fields: dict[str, Any]) -> dict[str, Any]:
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
            "previous_total_amount": previous_average_amount
            * previous_invoice_count,
            "previous_average_invoice_amount": previous_average_amount,
            "previous_average_days_late": 9.5 if high_amount_signal else 1.0,
            "previous_max_days_late": 34.0 if high_amount_signal else 5.0,
            "previous_on_time_payment_rate": 0.58 if high_amount_signal else 0.88,
            "previous_dispute_rate": 0.16 if high_amount_signal else 0.0,
            "previous_crm_negative_signal_score": 0.42
            if high_amount_signal
            else 0.05,
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
        extraction: InvoiceExtractionResponse,
        risk: RiskScoreResponse,
        state: InvoicePipelineState,
    ) -> str:
        fields = extraction.extracted_fields
        risk_features = state.get("risk_features") or {}

        parts = [
            request.invoice_id,
            fields.invoice_number or "",
            fields.customer_name or "",
            str(fields.amount_due or ""),
            fields.due_date or "",
            risk.risk_level,
            " ".join(risk.reasons),
            str(risk_features.get("previous_late_payments", "")),
            str(risk_features.get("previous_disputed_count", "")),
            str(risk_features.get("previous_dispute_rate", "")),
            str(risk_features.get("previous_crm_negative_signal_score", "")),
        ]

        return " ".join(part for part in parts if part)
