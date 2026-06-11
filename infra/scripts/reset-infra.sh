#!/usr/bin/env bash
set -euo pipefail

echo "This will stop infrastructure and remove local Docker volumes."
read -r -p "Continue? [y/N] " answer

if [[ "${answer}" != "y" && "${answer}" != "Y" ]]; then
  echo "Cancelled."
  exit 0
fi

docker compose \
  --env-file .env \
  -f docker-compose.infra.yml \
  down -v

docker compose \
  --env-file .env \
  -f docker-compose.infra.yml \
  up -d

echo "Finplex infrastructure reset complete."