#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}/services/api"
uv run alembic -c alembic.ini upgrade head

cd "${ROOT_DIR}"
uv run --project services/api python scripts/seed_demo_data.py

echo "Local seed data is ready."
