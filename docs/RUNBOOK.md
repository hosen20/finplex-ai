# Runbook

This runbook helps diagnose common local issues.

## Infrastructure Does Not Start

Run:

```bash
make infra-up
docker compose -f docker-compose.infra.yml ps
```

If containers are unhealthy, reset:

```bash
make infra-reset
make infra-up
```

## Alembic Cannot Connect To PostgreSQL

Error example:

```text
connection to server at "127.0.0.1", port 5432 failed
```

Fix:

```bash
cd ~/finplex-ai
make infra-up
docker compose -f docker-compose.infra.yml ps
cd services/api
uv run alembic -c alembic.ini upgrade head
```

## Alembic Says `Path doesn't exist: migrations`

Run Alembic from `services/api`:

```bash
cd ~/finplex-ai/services/api
uv run alembic -c alembic.ini upgrade head
```

## API Import Error

Run:

```bash
cd ~/finplex-ai
uv run --project services/api ruff check services/api tests
uv run --project services/api pytest tests/unit
```

Check the traceback for the first missing import or stale schema export.

## React Build Fails Because Node Types Are Missing

Run:

```bash
cd ~/finplex-ai/apps/web
npm install
npm install -D @types/node
npm run build
```

## Streamlit Cannot Log In

Check that the API is running:

```bash
curl http://localhost:8000/health
```

Recreate or update the platform admin:

```bash
cd ~/finplex-ai
uv run --project services/api python scripts/bootstrap-platform-admin.py \
  --email platform.admin@finplexai.com \
  --full-name "Finplex Platform Admin" \
  --password "FinplexAdmin123!"
```

Then restart Streamlit:

```bash
make admin
```

## Kafka Worker Does Not Process Jobs

Check infrastructure:

```bash
docker compose -f docker-compose.infra.yml ps
```

Restart workers:

```bash
make workers
```

Check API, model-server, and guardrails are also running.

## MinIO File Upload Fails

Check MinIO container health:

```bash
docker compose -f docker-compose.infra.yml ps
```

Check environment variables in `.env` match `.env.example`.

## Reset Local Product Data

Use this when you want a clean local database and object store:

```bash
make infra-reset
make infra-up
cd services/api
uv run alembic -c alembic.ini upgrade head
cd ../..
bash scripts/seed-local-data.sh
```

## Pre-PR Verification

Before pushing a PR:

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
