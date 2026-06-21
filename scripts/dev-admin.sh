#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv run --project apps/admin streamlit run apps/admin/app.py \
  --server.port "${ADMIN_PORT:-8501}"
