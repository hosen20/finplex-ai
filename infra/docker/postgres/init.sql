CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS finplex;

CREATE TABLE IF NOT EXISTS finplex.infra_health_check (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO finplex.infra_health_check (service_name)
VALUES ('postgres-pgvector')
ON CONFLICT DO NOTHING;