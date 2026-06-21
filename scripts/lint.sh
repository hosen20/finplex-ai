#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running Python lint checks..."
uv run --project services/api ruff check \
  services/api \
  services/model-server \
  services/guardrails \
  services/workers \
  apps/admin \
  evals \
  scripts/bootstrap-platform-admin.py \
  scripts/seed_product_data.py \
  tests/unit

echo "Running TypeScript build check..."
(
  cd apps/web
  npm run build
)
