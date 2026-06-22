# Finplex AI Notebooks

This folder keeps only the notebooks that directly produced the committed demo data, model artifacts, and AI evaluation outputs.

| Notebook | Purpose | Main outputs |
|---|---|---|
| `01_invoice_document_extraction.ipynb` | Builds the historical ERP/CRM seed data, generates new uploaded invoices, extracts invoice fields, and matches customers. | `data/seed/`, `data/demo_invoices/`, `artifacts/invoice_extraction/` |
| `02_late_payment_risk_model.ipynb` | Trains and evaluates the late-payment risk model from historical ERP/CRM behavior. | `models/`, `artifacts/risk_model/` |
| `03_llm_draft_generation_eval.ipynb` | Generates responsible follow-up drafts and evaluates guardrail pass rates for human review. | `artifacts/draft_generation/` |

RAG, policy, and end-to-end checks are covered by versioned evaluation scripts instead of empty notebooks:

~~~text
evals/run_rag_eval.py
evals/run_policy_eval.py
evals/run_end_to_end_eval.py
~~~

Empty placeholder notebooks were removed so reviewers only see notebooks that are actually used.
