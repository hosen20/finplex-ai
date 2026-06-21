# API

The FastAPI service is the product gateway for both Streamlit Platform Admin and React Tenant Workspace.

Base URL:

```text
http://localhost:8000
```

Interactive API docs are available while the API is running:

```text
http://localhost:8000/docs
```

## Authentication

Most endpoints require a bearer token.

```http
Authorization: Bearer <access_token>
```

Login:

```http
POST /auth/login
```

Current user:

```http
GET /auth/me
```

The frontend must not invent tenant scope. Tenant scope comes from the authenticated user.

## Main Resources

| Resource | Purpose |
|---|---|
| `/health` | API health check |
| `/auth` | login and current-user information |
| `/tenants` | platform-admin tenant management |
| `/users` | tenant user management |
| `/customers` | customer intelligence records |
| `/invoices` | invoice records and upload workflow |
| `/reviews` | AI draft review and human decisions |
| `/audit` | audit events and traceability |
| `/integrations` | local ERP/CRM status and settings |
| `/rag` | evidence retrieval endpoints |

## Role Rules

| Role | API behavior |
|---|---|
| platform_admin | Can manage tenants and create first tenant admins |
| tenant_admin | Can manage users inside own tenant |
| manager | Can inspect invoices, customers, and AI outputs |
| reviewer | Can approve, edit, or reject review items |
| auditor | Can read audit and decision history |

## Error Format

User-facing API errors should return safe messages and should not expose stack traces, SQL text, or local file paths.

Example:

```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Tenant Safety Rules

API endpoints must follow these rules:

1. Resolve the current user from JWT.
2. Resolve tenant scope from the current user.
3. Check role permissions before data access.
4. Use repository methods that filter by tenant.
5. Write audit events for high-impact actions.
6. Never trust a user-provided `tenant_id` for normal tenant-user workflows.

Platform admin endpoints are the only exception where cross-tenant actions are allowed, and those endpoints must require the `platform_admin` role.

## Upload Flow

Invoice files should be uploaded through the backend, not directly to object storage from the browser.

```text
React upload form
  → FastAPI validation
  → MinIO object write
  → invoice row creation
  → Kafka processing event
  → worker processing
  → review queue item
```

## API Development Guidelines

When adding an endpoint:

- add a Pydantic request/response schema
- keep the router thin
- place business logic in an application service
- keep SQL in repositories
- add unit tests or router tests
- add a security or RBAC test when permissions matter
- add audit logging for high-impact actions
