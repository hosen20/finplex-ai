# Project Review Guide

This guide helps reviewers inspect Finplex AI quickly.

## What This Project Shows

Finplex AI shows:

- SaaS tenant onboarding with a separate Streamlit Platform Admin
- tenant-scoped authentication and authorization
- React tenant workspace for finance teams
- invoice upload workflow with asynchronous Kafka processing
- local OCR/text extraction before AI processing
- LangGraph orchestration with LangChain Core `RunnableLambda` nodes
- ERP/CRM evidence usage
- pgvector RAG retrieval for tenant-scoped evidence
- ML risk scoring
- guardrails for responsible follow-up
- human approval workflow
- auditability
- local reproducibility
- CI, linting, tests, and golden evaluation gates

## Best Files To Inspect First

| Area | Files |
|---|---|
| Product overview | `README.md` |
| Final checklist | `docs/FINAL_REVIEW_CHECKLIST.md` |
| Setup | `docs/LOCAL_SETUP.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Platform admin | `apps/admin/app.py`, `docs/STREAMLIT_ADMIN.md` |
| React workspace | `apps/web/src/App.tsx`, `docs/TENANT_WEB_APP.md` |
| Backend app | `services/api/app/main.py` |
| Auth and RBAC | `services/api/app/api/routers/auth.py`, `services/api/app/dependencies.py` |
| Tenant management | `services/api/app/api/routers/tenants.py` |
| Workers and OCR | `services/workers/app/services/invoice_processing_service.py`, `services/workers/app/services/ocr_service.py` |
| LangGraph pipeline | `services/model-server/app/services/langgraph_pipeline.py`, `docs/LANGGRAPH_ORCHESTRATION.md` |
| RAG | `services/api/app/application/services/rag_service.py`, `docs/RAG_PGVECTOR.md` |
| Guardrails | `services/guardrails/app/services/guardrail_service.py` |
| Tests | `tests/unit/`, service-specific `tests/` folders |
| Evals | `evals/`, `docs/EVALUATIONS.md` |
| Model artifacts | `models/` |

## Suggested Local Review Path

1. Start infrastructure.
2. Run migrations.
3. Bootstrap platform admin.
4. Seed local product data.
5. Start API, model-server, guardrails, workers, Streamlit, and React.
6. Open Streamlit and inspect tenant management.
7. Log in to React as a seeded tenant user.
8. Upload or inspect an invoice.
9. Review OCR/extraction, risk signals, citations, draft, and guardrails result.
10. Approve or reject the draft.
11. Check invoice status and audit history.
12. Run tests, linting, evals, and the React build through the project scripts.

## Quality Checks

```bash
bash scripts/check-secrets.sh
bash scripts/lint.sh
bash scripts/test.sh
bash scripts/run-evals.sh
cd apps/web && npm run build && cd ../..
```

## What To Look For

- Is tenant isolation enforced?
- Are roles separated clearly?
- Does the API own business logic instead of the frontend?
- Is invoice processing asynchronous and traceable?
- Are AI outputs grounded in OCR/extraction and retrieved evidence?
- Is LangGraph/LangChain usage real and tested?
- Is human approval required before accepting a follow-up?
- Are important actions auditable?
- Can a reviewer run the product locally?
