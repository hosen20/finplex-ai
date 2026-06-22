# LangGraph AI Orchestration

Finplex AI uses LangGraph inside the model-server to make the invoice AI workflow explicit, inspectable, and testable. The graph nodes are implemented with LangChain Core `RunnableLambda` wrappers so the project can accurately claim both LangGraph orchestration and LangChain Core usage.

## Why LangGraph Was Added

The previous model-server pipeline was a normal Python service that ran extraction, risk scoring, evidence retrieval, and drafting in sequence. That worked, but the orchestration was hidden inside one method.

LangGraph makes the workflow visible as named nodes:

```text
extract_invoice -> score_risk -> retrieve_evidence -> draft_message -> build_response
```

This is useful for a hiring review because the pipeline can be explained as a graph, tested node-by-node, and extended later with retries, conditional paths, or human-in-the-loop branches.

## Where It Lives

```text
services/model-server/app/services/langgraph_pipeline.py
services/model-server/app/services/pipeline_service.py
services/model-server/tests/test_langgraph_pipeline.py
```

The FastAPI route remains the same:

```text
POST /process-invoice
```

The worker does not need to know about LangGraph. It still calls the model-server product pipeline endpoint.

## Graph Nodes

| Node | Responsibility |
| --- | --- |
| `extract_invoice` | Extract invoice number, customer, amount, due date, and terms from OCR/text input. |
| `score_risk` | Build or accept risk features, then score late-payment risk. |
| `retrieve_evidence` | Retrieve invoice, ERP, CRM, and regulation evidence for grounded drafting. |
| `draft_message` | Draft a respectful follow-up using extracted facts, risk, and citations. |
| `build_response` | Package extraction, risk, draft, citations, and orchestration trace. |

## LangChain Usage

The graph nodes are wrapped with `langchain-core` `RunnableLambda` objects in `services/model-server/app/services/langgraph_pipeline.py`. This keeps the implementation simple and testable now while leaving room to replace deterministic service calls with LangChain tools or provider-backed runnables later.

## Response Metadata

`/process-invoice` now returns an `orchestration` object:

```json
{
  "engine": "langgraph",
  "version": "langgraph_invoice_pipeline_v1",
  "nodes": [
    "extract_invoice",
    "score_risk",
    "retrieve_evidence",
    "draft_message",
    "build_response"
  ],
  "trace": []
}
```

The trace is also useful for audit/debugging because it records the graph node names, model versions, risk scores, retrieval method, citation count, and drafting metadata.

## Important Design Choice

LangGraph orchestrates the AI workflow, but it does not remove the product guardrails:

```text
React upload -> FastAPI -> Kafka worker -> model-server LangGraph -> guardrails service -> human review
```

Customer-facing messages still require guardrails validation and human approval before being considered complete.
