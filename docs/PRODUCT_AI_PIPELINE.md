# Product AI Pipeline

Finplex AI processes invoices asynchronously so the React upload request stays fast and the expensive AI work happens in the worker.

## Final local product flow

1. A tenant user uploads an invoice from the React workspace.
2. The FastAPI upload route stores the file, creates invoice metadata, and emits an `invoice.uploaded` Kafka event.
3. The worker consumes the event and marks the invoice as `processing`.
4. The worker reads invoice text from the stored file or OCR sidecar.
5. The worker calls the model-server `/process-invoice` endpoint once.
6. The model-server runs extraction, risk scoring, RAG evidence retrieval, and draft generation.
7. The worker sends the draft to the guardrails service.
8. The worker creates a human review record and updates the invoice to `review_pending`.
9. The reviewer approves, edits, or rejects the draft from the tenant workspace.
10. Audit events preserve the trace from upload to review.

## Why the worker now uses `/process-invoice`

Earlier versions called extraction, risk, RAG, and drafting as separate HTTP requests. PR9 keeps the individual model-server endpoints available for testing and debugging, but the worker now uses the full pipeline endpoint as the product path.

This gives a clearer production workflow:

```text
Kafka invoice.uploaded
  -> worker
  -> model-server /process-invoice
  -> guardrails /validate-message
  -> review queue
  -> audit trail
```

## Human approval remains mandatory

The LLM/drafting step never sends customer-facing communication directly. The result always becomes a pending review. Guardrails can pass or fail the draft, but both cases still require a human reviewer before customer communication.

## Evidence and traceability

The worker stores evidence IDs on the invoice and review. It also writes audit records for:

- invoice processing start
- evidence retrieval
- guardrails validation
- invoice processed or failed

The invoice `extracted_fields.ai_pipeline` object stores useful review metadata such as risk level, risk score, retrieval method, guardrail decision, and review ID.
