#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

printf 'Removing local generated files and folders that should not be committed...\n'

rm -f .env
rm -f apps/web/.env
rm -f apps/web/tsconfig.tsbuildinfo
rm -f apps/web/vite.config.d.ts
rm -rf apps/web/dist
rm -rf apps/web/node_modules
rm -rf apps/web/android
rm -f apps/web/capacitor.config.ts

find . -type d -name '__pycache__' -prune -exec rm -rf {} +
find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

printf 'Local artifact cleanup complete.\n'
