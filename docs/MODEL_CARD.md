# Model Card

This model card documents the AI components used by Finplex AI.

## AI Components

| Component | Purpose |
|---|---|
| OCR / extraction | Read invoice files and extract structured fields |
| Retrieval | Find tenant-scoped ERP, CRM, invoice, and policy evidence |
| Risk model | Estimate payment risk using structured features |
| LLM drafting | Draft respectful follow-up messages grounded in evidence |
| Guardrails | Validate safety, tone, evidence, and human-review requirements |

## Intended Use

The AI system is intended to assist finance teams by summarizing evidence, estimating risk, and drafting reviewable payment follow-up messages.

It is not intended to automatically contact customers or make final collection decisions without human approval.

## Risk Model

The risk model predicts a risk score and risk level from structured features such as:

- days overdue
- amount due
- payment status
- dispute count
- previous delays
- CRM note count
- recent promise-to-pay signal
- relationship status

Artifacts:

```text
models/risk_model.joblib
models/risk_model_metadata.json
models/risk_feature_schema.json
models/risk_label_mapping.json
```

## Drafting Model

The drafting model produces a suggested follow-up message. It must use retrieved evidence and avoid unsupported claims.

Drafts must be reviewed by a human before use.

## Retrieval

Retrieval uses tenant-scoped evidence. Evidence can come from ERP records, CRM notes, policy documents, invoice text, and previous decisions.

## Guardrails

Guardrails check:

- respectful tone
- evidence grounding
- prohibited language
- privacy concerns
- human review requirement

## Limitations

- OCR quality depends on invoice image quality.
- Retrieval is only as complete as the indexed evidence.
- Risk scoring supports prioritization, not final judgment.
- LLM drafts can be incomplete or overly generic.
- Human reviewers remain responsible for final decisions.

## Monitoring

Each AI run should log:

- model version
- prompt version
- evidence ids
- risk score
- guardrail status
- reviewer decision
- trace id
