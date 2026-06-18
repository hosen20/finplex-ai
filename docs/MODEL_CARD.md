# Finplex AI Late-Payment Risk Model

## Purpose

This model predicts the late-payment risk level for a new uploaded invoice.

The model does not rely on the uploaded invoice already existing in ERP. Instead, it combines the new invoice details with historical customer ERP/CRM behavior.

## Workflow

new invoice image
→ OCR extraction
→ customer matching
→ historical ERP/CRM lookup
→ risk prediction
→ follow-up draft
→ human review

## Target Labels

- low
- medium
- high
- critical

## Best Model

Selected model: `logistic_regression`

## Metrics

- Accuracy: 0.6920
- Macro F1: 0.5762
- Weighted F1: 0.7096

## Main Feature Groups

The model uses:

- new invoice amount
- payment terms
- country code
- previous invoice count
- previous late payments
- previous disputed invoice count
- previous average days late
- previous max days late
- previous on-time payment rate
- previous CRM negative signal score
- relationship age

## Limitations

This model is trained on a public accounts-receivable dataset transformed into local ERP/CRM seed data.

The model should not automatically send debt-collection messages. It should support a human-reviewed workflow.

## Responsible Use

Predictions must be used as decision support only. Final customer communication must pass guardrails and human approval.
