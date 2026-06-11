#!/usr/bin/env bash
set -euo pipefail

docker compose \
  --env-file .env \
  -f docker-compose.infra.yml \
  up -d

echo
echo "Finplex infrastructure is starting."
echo
echo "Postgres: localhost:${POSTGRES_PORT:-5432}"
echo "Redis:    localhost:${REDIS_PORT:-6379}"
echo "MinIO:    http://localhost:${MINIO_API_PORT:-9000}"
echo "MinIO UI: http://localhost:${MINIO_CONSOLE_PORT:-9001}"
echo "Kafka:    localhost:${KAFKA_LOCAL_PORT:-29092}"