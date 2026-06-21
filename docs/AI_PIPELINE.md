# AI Pipeline

Finplex AI uses AI to support finance teams, not to bypass human judgment. The AI pipeline extracts invoice information, retrieves ERP/CRM evidence, estimates payment risk, drafts a respectful follow-up, checks policy constraints, and sends the result to a human reviewer.

## Pipeline Overview

```text
Invoice file
  → OCR / text extraction
  → structured invoice extraction
  → ERP payment lookup
  → CRM context lookup
  → RAG evidence retrieval
  → ML risk scoring
  → LLM draft generation
  → guardrails validation
  → human review
  → audit event
```

## OCR And Extraction

The extraction stage reads invoice files and produces structured fields such as:

- invoice number
- invoice date
- due date
- customer name
- supplier name
- amount due
- currency
- line-item summary when available

The extraction result should include confidence scores and raw text references where possible.

## ERP And CRM Evidence

The ERP-style data contains payment facts:

- invoice amount
- due date
- outstanding balance
- payment status
- partial payments
- historical delays

The CRM-style data contains relationship context:

- customer notes
- disputes
- promises to pay
- support tickets
- relationship status
- previous follow-up outcomes

The AI draft must be grounded in these facts.

## Retrieval

Retrieval should use tenant-scoped evidence. Useful evidence sources include:

- policy documents
- CRM notes
- CRM disputes
- ERP invoice facts
- ERP payment facts
- extracted invoice text
- previous human review decisions

A retrieved evidence item should include:

- evidence id
- tenant id
- source type
- source record id
- text chunk
- relevance score

## Risk Scoring

The ML risk model estimates late-payment or collection-risk level from structured features.

Typical features:

- days overdue
- amount due
- partial payment status
- dispute count
- previous delays
- number of CRM notes
- recent promise-to-pay signal
- customer relationship status

The model output should include:

- risk score
- risk level
- top signals
- model version
- feature schema version

## Draft Generation

The LLM draft should:

- stay respectful and professional
- mention only supported facts
- avoid unsupported threats
- avoid harassment or pressure language
- cite evidence ids internally
- remain editable by a human
- never send automatically

## Guardrails

The guardrails service checks generated messages before they reach review.

Checks include:

- evidence grounding
- respectful tone
- human review requirement
- privacy and sensitive data handling
- prohibited collection language
- unsupported legal or payment claims

A failed guardrail should block approval until the issue is fixed.

## Human Approval

Every customer-facing draft requires human approval. The reviewer can:

- approve as written
- edit and approve
- reject with a reason
- request reprocessing

The final decision is stored in the audit trail.

## Audit Requirements

Each AI run should record:

- tenant id
- invoice id
- customer id
- trace id
- model version
- prompt version
- retrieved evidence ids
- risk score
- guardrail result
- reviewer id
- decision timestamp
