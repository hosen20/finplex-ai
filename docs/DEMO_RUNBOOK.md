# Finplex AI Local Demo Runbook

This runbook explains how to run the final Finplex AI local demo after the `feature/demo-seed-data-and-e2e-flow` files are added and merged.

The goal is to show Finplex AI as one finished product: a professional dashboard connected to the API, model-server, guardrails service, workers, Kafka, Postgres, and local demo data.

## What The Demo Shows

The final demo story is:

1. A tenant team logs into Finplex AI.
2. The dashboard shows invoice intelligence metrics.
3. A user views realistic invoices and customer records.
4. The system has ERP payment data and CRM dispute notes.
5. The AI pipeline extracts invoice fields.
6. The risk service predicts late-payment risk.
7. Hybrid RAG retrieves supporting evidence and citations.
8. The draft message is generated using the evidence.
9. Guardrails validate the draft for safe collection language.
10. A human reviewer approves, rejects, or asks for changes.

## Demo Accounts

See `docs/DEMO_ACCOUNTS.md`.

Main demo accounts:

- Admin: `clinadmin@example.com`
- Manager: `manager@example.com`
- Password for both: `FinplexDemo123!`

## Terminal Layout

For the cleanest demo, use six terminals:

- Terminal 1: API
- Terminal 2: model-server
- Terminal 3: guardrails
- Terminal 4: workers
- Terminal 5: dashboard
- Terminal 6: health checks and demo commands

## Step 1 — Pull Latest Main

```bash
cd ~/finplex-ai

git checkout main
git pull origin main
```

## Step 2 — Prepare Environment

If `.env` does not exist, create it from the example:

```bash
cd ~/finplex-ai

cp .env.example .env
```

Important local values:

```text
API_PORT=8000
MODEL_SERVER_PORT=8001
GUARDRAILS_PORT=8002
WEB_PORT=5173
MODEL_SERVER_URL=http://localhost:8001
GUARDRAILS_URL=http://localhost:8002
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
```

## Step 3 — Start Infrastructure

For normal development:

```bash
cd ~/finplex-ai

bash infra/scripts/start-infra.sh
```

For a clean final demo database, use reset:

```bash
cd ~/finplex-ai

bash infra/scripts/reset-infra.sh
```

When asked to continue, type:

```text
y
```

## Step 4 — Apply Database Migrations

```bash
cd ~/finplex-ai

uv run --project services/api alembic upgrade head
```

## Step 5 — Seed Demo Data

```bash
cd ~/finplex-ai

uv run --project services/api python scripts/seed_demo_data.py
```

Expected result:

```text
Finplex demo data is ready.
```

The seed script creates:

- Demo tenant
- Admin user
- Manager user
- Demo customers
- ERP invoice records
- ERP payment records
- CRM notes and disputes
- Uploaded invoice records
- Review queue records
- RAG evidence records
- Audit events

## Step 6 — Start API

Open Terminal 1:

```bash
cd ~/finplex-ai

bash scripts/dev-api.sh
```

Expected service:

```text
http://localhost:8000
```

## Step 7 — Start Model Server

Open Terminal 2:

```bash
cd ~/finplex-ai

bash scripts/dev-model-server.sh
```

Expected service:

```text
http://localhost:8001
```

## Step 8 — Start Guardrails

Open Terminal 3:

```bash
cd ~/finplex-ai

bash scripts/dev-guardrails.sh
```

Expected service:

```text
http://localhost:8002
```

## Step 9 — Start Workers

Open Terminal 4:

```bash
cd ~/finplex-ai

bash scripts/dev-workers.sh
```

The worker waits for Kafka invoice events and processes uploaded invoices.

## Step 10 — Start Dashboard

Open Terminal 5:

```bash
cd ~/finplex-ai/apps/web

npm run dev -- --host 0.0.0.0
```

Open:

```text
http://localhost:5173
```

## Step 11 — Check Health

Open Terminal 6:

```bash
cd ~/finplex-ai

bash scripts/check-health.sh
```

Expected result:

```text
{"service":"api","status":"ok",...}
{"service":"model-server","status":"ok",...}
{"service":"guardrails","status":"ok",...}
```

## Step 12 — Run Demo Smoke Flow

```bash
cd ~/finplex-ai

uv run --project services/api python scripts/run_demo_flow.py
```

Expected checks:

```text
API health ok
model-server health ok
guardrails health ok
invoice extraction ok
risk scoring ok
hybrid RAG evidence ok
draft generation ok
guardrails validation ok
demo flow complete
```

## Dashboard Presentation Flow

Use this order in the video or live presentation:

1. Open `http://localhost:5173`.
2. Login as `clinadmin@example.com`.
3. Show the overview metrics.
4. Open the invoices page and show the high-risk invoice.
5. Open the evidence center and explain the citations.
6. Open the human review queue.
7. Show the AI-generated follow-up draft.
8. Show that the wording is safe and professional.
9. Approve or reject the draft.
10. Logout and login as `manager@example.com`.
11. Show that a non-technical manager can understand the same workflow.

## What To Emphasize During The Demo

Explain that Finplex AI is not just extracting text from invoices. It connects invoice data with ERP payment status, CRM customer history, risk scoring, RAG evidence, guardrails, and human approval.

Use simple language:

- ERP tells us what is owed and paid.
- CRM tells us the customer relationship and disputes.
- AI reads the invoice and predicts risk.
- RAG shows the evidence behind the decision.
- Guardrails make sure the message is safe.
- A human approves before anything is sent.

## Troubleshooting

### API does not start

Check that Postgres is running:

```bash
docker ps
```

Then rerun migrations:

```bash
uv run --project services/api alembic upgrade head
```

### Dashboard shows fallback demo data

This means the dashboard is running, but the API may not be reachable. Check:

```bash
curl http://localhost:8000/health
```

### Model-server errors

Check:

```bash
curl http://localhost:8001/health
```

Also confirm that model artifacts exist:

```text
models/risk_model.joblib
models/risk_feature_schema.json
models/risk_label_mapping.json
models/risk_model_metadata.json
```

### Guardrails errors

Check:

```bash
curl http://localhost:8002/health
```

### Kafka or worker not processing

Check that infrastructure is running:

```bash
docker ps
```

Restart infrastructure if needed:

```bash
bash infra/scripts/start-infra.sh
```

## Final Demo Success Criteria

The demo is successful when:

- All services return healthy.
- Demo accounts exist.
- Dashboard opens without errors.
- Invoices and reviews are visible.
- Evidence/citations appear clearly.
- Draft messages appear in friendly text, not raw JSON.
- Guardrails output confirms safe messaging.
