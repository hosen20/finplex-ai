# Finplex AI

Finplex AI is a local-first FinTech SaaS product for invoice intelligence and responsible payment follow-up. It connects invoice uploads, ERP-style payment records, CRM-style customer context, AI extraction, risk scoring, retrieval, draft generation, guardrails, and human approval into one tenant-isolated workflow.

The product has two user surfaces:

- **Streamlit Platform Admin** for internal Finplex operators. Platform admins create tenants, create the first tenant admin, inspect tenant status, and monitor system health.
- **React Tenant Workspace** for finance teams. Tenant users upload invoices, inspect customer intelligence, review AI recommendations, approve or reject follow-up drafts, and view decision history.

There is no public sign-up. A platform admin creates a tenant first, then creates the first tenant admin. Tenant admins manage users inside their own tenant.

## Product Flow

```text
Platform Admin creates tenant
        ↓
Platform Admin creates first tenant admin
        ↓
Tenant Admin creates managers and reviewers
        ↓
Tenant user uploads invoice
        ↓
Backend stores invoice and publishes processing event
        ↓
Workers call OCR, retrieval, ML risk scoring, LLM drafting, and guardrails
        ↓
Reviewer sees extracted fields, evidence, risk reasons, and draft
        ↓
Human approves, edits, or rejects
        ↓
Audit log stores the decision with tenant_id and trace_id
```

## Architecture

```text
apps/admin        Streamlit platform admin console
apps/web          React tenant workspace
services/api      FastAPI product API, auth, RBAC, tenant isolation
services/workers  Kafka consumers for invoice processing jobs
services/model-server  OCR, extraction, retrieval, risk scoring, drafting
services/guardrails    Policy checks for safe customer-facing drafts
infra             Local Docker infrastructure scripts
models            Trained risk model artifacts and metadata
notebooks         Training and evaluation notebooks
evals             Golden evaluation scripts and thresholds
docs              Architecture, setup, security, runbook, and review docs
```

## Core Technologies

| Layer | Tools |
|---|---|
| Frontend | React, TypeScript, Vite |
| Admin console | Streamlit |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Data | PostgreSQL, pgvector, Redis, MinIO |
| Events | Apache Kafka, Zookeeper |
| AI | OCR, ML risk model, retrieval, LLM drafting, guardrails |
| Quality | pytest, ruff, TypeScript build, golden evals |

## Prerequisites

Install these before running the project:

- Git
- Docker and Docker Compose
- Python managed by `uv`
- Node.js 20+
- npm
- GitHub CLI, only if you want to create pull requests from the terminal

## Local Setup

Clone the repository and enter it:

```bash
cd ~
git clone git@github.com:hosen20/finplex-ai.git
cd finplex-ai
```

Create a local environment file:

```bash
cp -n .env.example .env
```

Install Python dependencies:

```bash
uv sync --all-packages
```

Install React dependencies:

```bash
cd apps/web
npm install
cd ../..
```

Start infrastructure:

```bash
make infra-up
```

Apply database migrations:

```bash
cd services/api
uv run alembic -c alembic.ini upgrade head
cd ../..
```

Create or update the first platform admin:

```bash
uv run --project services/api python scripts/bootstrap-platform-admin.py \
  --email platform.admin@finplexai.com \
  --full-name "Finplex Platform Admin" \
  --password "FinplexAdmin123!"
```

Seed local sample data:

```bash
bash scripts/seed-local-data.sh
```

## Running The Product

Use separate terminals.

Terminal 1: API

```bash
cd ~/finplex-ai
make api
```

Terminal 2: model server

```bash
cd ~/finplex-ai
make model-server
```

Terminal 3: guardrails service

```bash
cd ~/finplex-ai
make guardrails
```

Terminal 4: workers

```bash
cd ~/finplex-ai
make workers
```

Terminal 5: Streamlit admin console

```bash
cd ~/finplex-ai
make admin
```

Open:

```text
http://localhost:8501
```

Terminal 6: React tenant workspace

```bash
cd ~/finplex-ai/apps/web
npm run dev
```

Open:

```text
http://localhost:5173
```

## First Product Walkthrough

1. Log in to Streamlit as the platform admin.
2. Create a tenant, for example `Cedar Finance Group`.
3. Create the first `tenant_admin` for that tenant.
4. Open the React workspace.
5. Sign in as the tenant admin.
6. Create tenant users such as manager and reviewer.
7. Upload an invoice.
8. Wait for the invoice processing job.
9. Open the review queue.
10. Inspect extracted invoice fields, ERP facts, CRM notes, evidence, risk score, guardrails status, and draft.
11. Approve, edit, or reject the draft.
12. Review the audit trail.

## Useful Commands

Check local services:

```bash
make health
```

Run API tests:

```bash
uv run --project services/api pytest tests/unit
```

Run API linting:

```bash
uv run --project services/api ruff check services/api tests
```

Build React:

```bash
cd apps/web
npm run build
cd ../..
```

Compile Streamlit files:

```bash
uv run --project apps/admin python -m py_compile \
  apps/admin/app.py \
  apps/admin/finplex_admin/client.py
```

Stop infrastructure:

```bash
make infra-down
```

Reset infrastructure:

```bash
make infra-reset
```

## Authentication And Roles

| Role | Product area | Main permissions |
|---|---|---|
| platform_admin | Streamlit admin | Create tenants, create tenant admins, manage tenant status |
| tenant_admin | React workspace | Manage tenant users and tenant operations |
| manager | React workspace | View invoices, customers, AI review queue, and decisions |
| reviewer | React workspace | Review, approve, edit, and reject AI drafts |
| auditor | React workspace | Read audit and decision history |

## Tenant Isolation

Every important record is scoped by `tenant_id`: users, customers, invoices, ERP records, CRM records, RAG documents, reviews, audit events, Kafka events, cache keys, and file paths. The backend must derive tenant scope from the authenticated user, not from user-controlled input.

## Data And AI

Finplex AI uses privacy-safe local data:

- invoice images and PDFs for upload and OCR-style extraction
- ERP-style invoice and payment records
- CRM-style notes, disputes, contacts, and relationship status
- policy documents for retrieval and guardrail checks
- trained risk model artifacts in `models/`
- notebooks that explain training and evaluation work

Raw downloaded datasets should be placed in `data/external/` locally and should not be committed unless they are small, license-safe, and necessary for reproduction.

## Documentation

Start here:

- `docs/LOCAL_SETUP.md` for setup and running steps
- `docs/ARCHITECTURE.md` for system design
- `docs/STREAMLIT_ADMIN.md` for platform admin usage
- `docs/TENANT_WEB_APP.md` for tenant workspace usage
- `docs/AI_PIPELINE.md` for OCR, retrieval, ML, LLM, and guardrails flow
- `docs/SECURITY.md` for tenant isolation and security rules
- `docs/EVALUATIONS.md` for quality gates and golden sets
- `docs/RUNBOOK.md` for troubleshooting
- `docs/PROJECT_REVIEW_GUIDE.md` for reviewer navigation

## Repository Hygiene

Do not commit:

- `.env`
- generated frontend builds
- dependency folders
- Python cache files
- large raw datasets
- model provider secrets
- local database or object storage files

## Current Product Scope

Finplex AI is focused on a complete local SaaS experience: platform administration, tenant workspace, invoice intelligence, evidence retrieval, responsible AI drafting, human approval, and auditability.
