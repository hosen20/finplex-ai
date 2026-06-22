# Final Review Checklist

Use this checklist before sharing Finplex AI on a hiring portal or with a reviewer.

## 1. Repository State

```bash
git switch main
git pull
git status
```

Expected result:

```text
On branch main
nothing to commit, working tree clean
```

## 2. Product Quality Gate

```bash
bash scripts/check-secrets.sh
bash scripts/lint.sh
bash scripts/test.sh
bash scripts/run-evals.sh
cd apps/web && npm run build && cd ../..
```

## 3. Product Surface Check

Start the product locally:

```bash
make infra-up
cd services/api && uv run alembic -c alembic.ini upgrade head && cd ../..
bash scripts/seed-local-data.sh
```

Run these in separate terminals:

```bash
make api
make model-server
make guardrails
make workers
make admin
cd apps/web && npm run dev
```

Open:

```text
Streamlit Platform Admin: http://localhost:8501
React Tenant Workspace:  http://localhost:5173
```

## 4. Screenshot Refresh

The README embeds images from:

```text
docs/assets/screenshots/streamlit-platform-admin.svg
docs/assets/screenshots/react-tenant-workspace.svg
```

For a final hiring submission, it is safe to replace these SVG previews with real screenshots captured from your local browser. Keep the same filenames or update the README links.

## 5. Final Grep Checks

Check that final docs mention the current product stack:

```bash
grep -RInE "LangGraph|LangChain|pgvector|OCR|guardrails|human review"   README.md docs services/model-server services/workers | head -80
```

Check for stale unsupported product claims:

```bash
grep -RInE "public sign-up|Capacitor|Ionic|mobile app|AWS deployment required"   README.md docs apps services scripts || true
```

It is fine for old migration IDs or sample data filenames to include historical words such as `demo`; do not present them as the product scope in the README.

## 6. Reviewer Story

The product story should be:

```text
A platform admin creates a tenant.
A tenant finance user uploads an invoice.
The worker extracts OCR text asynchronously.
The model-server runs a LangGraph/LangChain AI pipeline.
The system retrieves ERP/CRM/policy evidence, scores risk, and drafts a response.
Guardrails validate the draft.
A human reviewer approves, edits, or rejects it.
The audit trail records the decision.
```
