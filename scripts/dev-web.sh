#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/apps/web"

if [ ! -f .env ]; then
  cp .env.example .env
fi

npm run dev -- --host 0.0.0.0 --port 5173
