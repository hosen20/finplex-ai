#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
cd "${ROOT_DIR}"

set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running API/root unit tests..."
uv run --project services/api pytest tests/unit

echo "Running model-server tests..."
uv run --project services/model-server pytest services/model-server/tests

echo "Running guardrails tests..."
uv run --project services/guardrails pytest services/guardrails/tests

echo "Running worker tests..."
uv run --project services/workers pytest services/workers/tests

echo "Checking Streamlit admin imports..."
uv run --project apps/admin python -m py_compile \
  apps/admin/app.py \
  apps/admin/finplex_admin/client.py
