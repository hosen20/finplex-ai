#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Applying API database migrations..."
cd "${ROOT_DIR}/services/api"
uv run alembic upgrade head

echo "Seeding Finplex AI demo data..."
cd "${ROOT_DIR}"
uv run --project services/api python3 scripts/seed_demo_data.py

echo "Demo seed complete."
