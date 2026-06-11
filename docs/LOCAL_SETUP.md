# Local Setup

Finplex AI uses a hybrid local development setup.

Infrastructure runs in Docker:

- PostgreSQL with pgvector
- Redis
- MinIO
- Zookeeper
- Kafka

Application services run locally:

- FastAPI API with uv
- Model server with uv
- Guardrails service with uv
- Workers with uv
- React web app with npm

This avoids slow application image rebuilds during early development while still using the real infrastructure services required by the project.

## 1. Prepare environment

```bash
cp .env.example .env