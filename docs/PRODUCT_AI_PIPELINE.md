# Product AI Pipeline

Finplex AI processes invoices asynchronously and requires human approval before any customer-facing follow-up is accepted.

## Product Flow

```text
React upload
  -> FastAPI stores invoice and emits Kafka event
  -> worker consumes invoice.uploaded
  -> worker reads invoice text/OCR payload
  -> worker calls model-server /process-invoice
  -> model-server runs LangGraph orchestration with LangChain Core nodes
  -> worker calls guardrails
  -> worker creates human review
  -> invoice becomes review_pending
  -> reviewer approves/rejects
  -> invoice becomes approved/rejected
```

## LangGraph Model-Server Workflow

Inside the model-server, `/process-invoice` is backed by LangGraph and LangChain Core `RunnableLambda` nodes:

```text
extract_invoice -> score_risk -> retrieve_evidence -> draft_message -> build_response
```

The response includes extraction results, risk scoring, retrieved citations, the drafted message, and an `orchestration` trace.

## What Each Stage Does

| Stage | Purpose |
| --- | --- |
| Invoice extraction | Reads OCR/text and extracts invoice number, customer, amount, due date, and terms. |
| Risk scoring | Scores late-payment risk from extracted amount and customer/payment features. |
| Evidence retrieval | Retrieves invoice, ERP, CRM, and policy evidence for grounded drafting. |
| LLM-style drafting | Creates a respectful follow-up draft using only extracted facts and retrieved evidence. |
| Guardrails | Validates that the draft is respectful, evidence-based, and safe. |
| Human review | Requires a reviewer to approve, reject, or edit the draft. |

## Why This Is Product-Ready

The pipeline is not a chatbot-only path. It is event-driven, tenant-scoped, evidence-grounded, guardrailed, and human-approved. LangGraph and LangChain Core make the AI orchestration explicit while Kafka and FastAPI keep the product workflow reliable.

## OCR extraction layer

The worker now performs an explicit OCR/text-extraction step before calling the
model-server `/process-invoice` endpoint. This keeps upload fast while making the
async product pipeline clearer:

```text
invoice.uploaded event
  -> LocalOcrService extracts invoice text
  -> model-server LangGraph pipeline processes extracted text
  -> guardrails validates the draft
  -> human review is created
```

OCR metadata is stored in the invoice `ai_pipeline` object and an
`ocr_text_extracted` audit event is written for traceability.
