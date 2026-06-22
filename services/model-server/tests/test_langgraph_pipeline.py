from app.schemas import InvoicePipelineRequest
from app.services.langgraph_pipeline import (
    RAG_ORCHESTRATION_ENGINE,
    RAG_ORCHESTRATION_VERSION,
    LangGraphInvoiceOrchestrator,
)
from app.services.pipeline_service import InvoicePipelineService


def build_pipeline_request() -> InvoicePipelineRequest:
    return InvoicePipelineRequest(
        invoice_id="inv_langgraph_001",
        tenant_id="tenant_graph",
        file_name="invoice.txt",
        storage_key="tenant_graph/invoices/inv_langgraph_001/invoice.txt",
        text="\n".join(
            [
                "Invoice Number: LG-1001",
                "Customer: Cedar Clinic",
                "Total: 15000.00",
                "Due Date: 2026-07-15",
                "Payment Terms: Net 30",
            ]
        ),
        context={"source": "unit_test"},
    )


def test_langgraph_orchestrator_runs_expected_nodes() -> None:
    response = LangGraphInvoiceOrchestrator().process_invoice(
        build_pipeline_request()
    )

    assert response.extraction.extracted_fields.invoice_number == "LG-1001"
    assert response.risk.risk_level in {"medium", "high", "critical"}
    assert response.draft.draft_message
    assert response.citations
    assert response.orchestration["engine"] == RAG_ORCHESTRATION_ENGINE
    assert response.orchestration["version"] == RAG_ORCHESTRATION_VERSION
    assert response.orchestration["nodes"] == [
        "extract_invoice",
        "score_risk",
        "retrieve_evidence",
        "draft_message",
        "build_response",
    ]


def test_pipeline_service_uses_langgraph_orchestration() -> None:
    response = InvoicePipelineService().process_invoice(build_pipeline_request())

    assert response.orchestration["engine"] == "langgraph"
    assert response.orchestration["trace"]
    assert response.draft.guardrails_required is True
