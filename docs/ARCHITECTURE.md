# Architecture

Finplex AI is split into small services so each responsibility is clear and testable.

## High-Level System

```text
Streamlit Platform Admin       React Tenant Workspace
          │                              │
          └──────────────┬───────────────┘
                         │
                    FastAPI API
        auth, RBAC, tenants, invoices, reviews
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   PostgreSQL        MinIO             Kafka
 structured data   invoice files   async events
   + pgvector                     processing jobs
        │                │                │
        └────────────────┼────────────────┘
                         │
                      Workers
              OCR/text extraction + async coordination
                         │
        ┌────────────────┼────────────────┐
        │                │                │
  Model Server      Guardrails       Audit Trail
LangGraph/RAG/ML/LLM policy checks  decisions/logs
```

## Applications

### `apps/admin`

Streamlit internal admin console. It is used by Finplex platform operators to create tenants, create first tenant admins, suspend or reactivate tenants, and inspect system health.

### `apps/web`

React tenant workspace. It is used by tenant finance teams to upload invoices, inspect customer intelligence, manage users, review AI suggestions, approve or reject drafts, and view decision history.

## Services

### `services/api`

FastAPI backend and product gateway. Responsibilities:

- JWT authentication
- RBAC checks
- tenant-scoped APIs
- invoice upload orchestration
- customer and invoice read models
- review queue actions
- audit event creation
- Kafka event publishing
- MinIO access through authorized backend paths

The API is organized by clean architecture boundaries:

```text
app/domain            entities, enums, policies, exceptions
app/application       service-level business logic
app/infrastructure    database, messaging, storage, external clients
app/api               routers, schemas, error handlers
```

Routers remain thin. Business rules live in application services and domain policies. SQL access belongs in repositories.

### `services/workers`

Kafka consumers that process invoice events asynchronously. Workers read invoice files, perform local OCR/text extraction, call the model-server product pipeline, call guardrails, and write results back to the database.

### `services/model-server`

AI service for structured extraction, LangGraph orchestration, LangChain Core node wrappers, pgvector-backed evidence retrieval, risk scoring, and draft generation. The API does not depend directly on model-server internals.

### `services/guardrails`

Policy validation service. It checks generated drafts for respectful tone, evidence grounding, human review requirement, privacy issues, and prohibited collection language.

## Data Stores

### PostgreSQL

Primary structured database. Stores tenants, users, customers, invoices, ERP records, CRM records, RAG documents, RAG chunks, reviews, and audit events.

### pgvector

Vector extension for retrieval over tenant-scoped evidence. RAG data is scoped by tenant and source type.

### MinIO

Object storage for invoice files. File paths include tenant and invoice scope.

### Redis

Short-lived cache and operational helper for local development.

### Kafka

Event broker for async invoice processing. Events carry `tenant_id`, `invoice_id`, `trace_id`, and an idempotency key.

## Tenant Boundary

Tenant isolation is the central product rule:

- every table that contains tenant data includes `tenant_id`
- every file path includes tenant scope
- every Kafka event includes tenant scope
- every vector record includes tenant scope
- every audit event includes tenant scope
- user APIs derive tenant from JWT claims or authenticated user context

## Request Flow

### Invoice Upload

```text
React user uploads invoice
FastAPI validates role and tenant
FastAPI stores file in MinIO
FastAPI creates invoice row
FastAPI publishes invoice processing event
Worker consumes event
Worker extracts OCR/text payload
Worker calls model-server /process-invoice
Model-server runs LangGraph/LangChain pipeline
Worker calls guardrails
Worker updates invoice/review records
Reviewer sees result in React
```

### Platform Tenant Creation

```text
Platform admin logs into Streamlit
Streamlit calls FastAPI using platform admin token
FastAPI checks platform_admin role
FastAPI creates tenant
FastAPI creates first tenant admin
Tenant admin signs into React
```

## Observability

Every important operation should include:

- `tenant_id`
- `user_id` when available
- `invoice_id` when available
- `trace_id`
- action name
- timestamp
- outcome

The audit trail is part of the product, not only a debug tool.
