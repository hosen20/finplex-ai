# Datasets

Finplex AI uses privacy-safe local data for invoice intelligence, customer context, payment history, and AI evaluation.

## Data Sources

| Data type | Purpose |
|---|---|
| Invoice images/PDFs | OCR and structured invoice extraction |
| ERP-style invoices | Amounts, due dates, balances, payment status |
| ERP-style payments | Payment history and partial payment signals |
| CRM-style notes | Customer context and previous interactions |
| CRM-style disputes | Risk signals and evidence for careful follow-up |
| Policy documents | Retrieval and guardrails evidence |
| IBM customer dataset | Customer-risk and churn-style features for realistic account behavior |
| Synthetic records | Privacy-safe local product testing |

## Folder Policy

```text
data/external     raw downloaded datasets kept locally
data/processed    cleaned files produced from notebooks or scripts
data/seed         small seed files used by local setup
data/golden       expected outputs for evaluation cases
```

Raw downloaded datasets should stay in `data/external/` and should not be committed unless they are small, license-safe, and necessary for reproduction.

## Seeding

Run:

```bash
bash scripts/seed-local-data.sh
```

The seed flow should prepare:

- tenants
- users
- customers
- ERP invoices
- ERP payments
- CRM notes
- CRM disputes
- invoice records
- policy documents
- RAG chunks
- review queue items
- audit events

## Dataset Design Rules

- Do not include private customer data.
- Prefer public or synthetic records.
- Keep seed data small enough for fast local setup.
- Keep raw datasets separate from processed seed data.
- Document transformations in notebooks or scripts.
- Make evaluation cases deterministic.

## Evaluation Sets

Golden sets should cover:

- invoice extraction fields
- retrieval hit quality
- risk score expectations
- guardrails policy outcomes
- end-to-end invoice-to-review workflow
