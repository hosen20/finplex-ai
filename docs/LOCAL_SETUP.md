# Local Setup

This guide starts Finplex AI from a clean checkout.

## 1. Clone And Enter The Repo

```bash
cd ~
git clone git@github.com:hosen20/finplex-ai.git
cd finplex-ai
```

## 2. Create Environment File

```bash
cp -n .env.example .env
```

Edit `.env` only if your local ports or passwords differ from `.env.example`.

## 3. Install Dependencies

Python:

```bash
uv sync --all-packages
```

React:

```bash
cd apps/web
npm install
cd ../..
```

## 4. Start Infrastructure

```bash
make infra-up
```

Check containers:

```bash
docker compose -f docker-compose.infra.yml ps
```

Expected local services include PostgreSQL, Redis, MinIO, Zookeeper, and Kafka.

## 5. Apply Database Migrations

Run Alembic from the API folder:

```bash
cd services/api
uv run alembic -c alembic.ini upgrade head
cd ../..
```

If you see `connection refused` on port 5432, the PostgreSQL container is not running yet.

## 6. Create Platform Admin

```bash
uv run --project services/api python scripts/bootstrap-platform-admin.py \
  --email platform.admin@finplexai.com \
  --full-name "Finplex Platform Admin" \
  --password "FinplexAdmin123!"
```

The command is safe to run again. It creates or updates the local platform admin.

## 7. Seed Local Product Data

```bash
bash scripts/seed-local-data.sh
```

For a clean reseed of only the product tenants:

```bash
bash scripts/seed-local-data.sh --reset-product-tenants
```

This creates two local product tenants, tenant users, customers, ERP invoices, payments, CRM notes, disputes, policy RAG chunks, review-ready invoices, and audit examples.

## 8. Run Services

Use separate terminals.

API:

```bash
make api
```

Model server:

```bash
make model-server
```

Guardrails:

```bash
make guardrails
```

Workers:

```bash
make workers
```

Streamlit admin:

```bash
make admin
```

React workspace:

```bash
cd apps/web
npm run dev
```

## 9. Open The Apps

Streamlit Platform Admin:

```text
http://localhost:8501
```

React Tenant Workspace:

```text
http://localhost:5173
```

API health:

```text
http://localhost:8000/health
```

## 10. First Local Product Flow

1. Log in to Streamlit as `platform.admin@finplexai.com`.
2. Create a tenant.
3. Create the first tenant admin.
4. Log in to React as that tenant admin.
5. Create tenant users.
6. Upload an invoice.
7. Check the review queue.
8. Approve or reject a generated draft.
9. Inspect audit history.

## 11. Stop Services

Stop app terminals with `CTRL+C`.

Stop infrastructure:

```bash
make infra-down
```

Reset infrastructure:

```bash
make infra-reset
```

Use reset only when you want to remove local data and start fresh.
