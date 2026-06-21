#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Applying API database migrations..."
cd "${ROOT_DIR}/services/api"
uv run alembic upgrade head

echo "Seeding manual upload demo context..."
cd "${ROOT_DIR}"
uv run --project services/api python3 scripts/seed_manual_upload_demo_context.py

echo "Manual upload demo context seed complete."
