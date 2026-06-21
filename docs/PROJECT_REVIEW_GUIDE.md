# Project Review Guide

This guide helps reviewers inspect Finplex AI quickly.

## What This Project Shows

Finplex AI shows:

- SaaS tenant onboarding
- tenant-scoped authentication and authorization
- invoice upload workflow
- async processing with Kafka workers
- invoice intelligence with OCR and extraction
- ERP/CRM evidence usage
- retrieval-assisted drafting
- ML risk scoring
- guardrails for responsible follow-up
- human approval workflow
- auditability
- local reproducibility

## Best Files To Inspect First

| Area | Files |
|---|---|
| Product overview | `README.md` |
| Setup | `docs/LOCAL_SETUP.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Backend app | `services/api/app/main.py` |
| Auth and RBAC | `services/api/app/api/routers/auth.py`, `services/api/app/dependencies.py` |
| Tenant management | `services/api/app/api/routers/tenants.py`, `apps/admin/app.py` |
| React workspace | `apps/web/src/App.tsx` |
| Workers | `services/workers/app/services/invoice_processing_service.py` |
| Model server | `services/model-server/app/services/` |
| Guardrails | `services/guardrails/app/services/guardrail_service.py` |
| Tests | `tests/unit/`, service-specific `tests/` folders |
| AI notebooks | `notebooks/` |
| Model artifacts | `models/` |

## Suggested Local Review Path

1. Start infrastructure.
2. Run migrations.
3. Bootstrap platform admin.
4. Seed local sample data.
5. Start API, model-server, guardrails, workers, Streamlit, and React.
6. Create a tenant from Streamlit.
7. Create tenant users.
8. Log in to React.
9. Upload or inspect an invoice.
10. Review AI output and approve or reject.
11. Check audit history.
12. Run tests and React build.

## Quality Checks

```bash
uv run --project services/api ruff check services/api tests
uv run --project services/api pytest tests/unit
cd apps/web
npm run build
cd ../..
uv run --project apps/admin python -m py_compile \
  apps/admin/app.py \
  apps/admin/finplex_admin/client.py
```

## What To Look For

- Is tenant isolation enforced?
- Are roles separated clearly?
- Does the API own business logic instead of the frontend?
- Are AI outputs grounded in evidence?
- Is human approval required?
- Are important actions auditable?
- Can a reviewer run the product locally?
