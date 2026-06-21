# Tenant-Scoped API Contract

Finplex AI is a multitenant financial application. Tenant-facing API routes must not trust tenant identifiers sent by the browser.

## Rule

For normal tenant users, the backend resolves tenant scope from the authenticated user record behind the JWT token:

```text
JWT user -> users.tenant_id -> allowed tenant scope
```

The React tenant workspace can keep the tenant id in UI state for display, but it no longer needs to send `tenant_id` for normal list, create, or upload actions.

## Platform Admin Exception

Platform admins operate from the Streamlit admin console. They may provide a `tenant_id` when they are intentionally managing a tenant, such as creating the first tenant admin after creating a company.

If a platform admin calls a tenant-specific endpoint without a `tenant_id`, the API returns `400` instead of accidentally using the internal platform tenant.

## Protected Routes

The following route groups now resolve tenant scope server-side:

- `/customers`
- `/invoices`
- `/invoices/upload`
- `/reviews/pending`
- `/users`

If a tenant user attempts to pass another tenant id, the API returns `403`.

## Why This Matters

This prevents cross-tenant access caused by a modified browser request, a copied API call, or a frontend bug. It also keeps the product aligned with the project rule that every user, invoice, review, customer, audit event, and RAG document is tenant scoped.
