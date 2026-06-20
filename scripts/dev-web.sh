#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${ROOT_DIR}/apps/web"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

cd "${WEB_DIR}"

if [[ ! -d node_modules ]]; then
  echo "Installing dashboard dependencies..."
  npm install
fi

npm run dev -- --host 0.0.0.0 --port "${WEB_PORT:-5173}"
