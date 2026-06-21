# Security

Finplex AI handles financial records, customer context, invoices, and AI-generated payment follow-up drafts. Security is a product requirement.

## Security Principles

- No public sign-up.
- Platform admin creates tenants.
- Tenant admin manages users inside one tenant.
- Users can only access tenant-scoped records.
- Customer-facing AI drafts require human approval.
- Secrets are loaded from environment variables.
- Logs must not contain passwords, tokens, API keys, or full sensitive payloads.

## Authentication

The API uses JWT authentication. A user signs in with email and password and receives an access token. Frontend apps pass the token using the bearer authorization header.

Passwords must be hashed and never stored as plaintext.

## Authorization

Roles:

| Role | Scope |
|---|---|
| platform_admin | Internal Finplex platform operations |
| tenant_admin | One tenant |
| manager | One tenant |
| reviewer | One tenant |
| auditor | One tenant |

Authorization checks must happen before data access.

## Tenant Isolation

Tenant isolation rules:

- Every tenant-owned database row must include `tenant_id`.
- Every query for tenant data must filter by tenant.
- Every invoice object path must include tenant scope.
- Every Kafka event must include tenant scope.
- Every RAG chunk must include tenant scope.
- Every audit event must include tenant scope.
- User-facing endpoints must derive tenant from the authenticated user.

## Secrets

Never commit:

- `.env`
- API keys
- model provider keys
- database passwords outside `.env.example`
- object storage secrets
- JWT signing secrets
- service account files

Use `.env.example` to document variable names without real secrets.

## Logging

Log useful operational context:

- request id
- trace id
- tenant id
- invoice id
- action name
- outcome
- error class

Do not log:

- passwords
- bearer tokens
- raw customer messages when not needed
- full invoice contents
- API keys
- database connection strings

## Guardrails And Human Approval

Generated drafts are not automatically sent. A human reviewer must approve them. Guardrails check that drafts are respectful, grounded in evidence, and do not include unsupported claims.

## Development Checklist

Before merging a security-sensitive PR:

- auth is required where needed
- role checks are tested
- tenant isolation is tested
- user input is validated
- secrets are not committed
- error messages are safe
- audit events are written for important actions
