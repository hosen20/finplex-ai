# React Tenant Workspace

The React app is the product workspace for tenant users.

## Run

```bash
cd apps/web
npm run dev
```

Open:

```text
http://localhost:5173
```

## Login

Users log in with accounts created by a platform admin or tenant admin. There is no public sign-up.

## Main User Workflows

### Tenant Admin

- manage tenant users
- assign roles
- view invoices
- view customers
- inspect review queue
- review audit history

### Manager

- view dashboard metrics
- inspect invoices
- inspect customer intelligence
- track review status

### Reviewer

- open AI review queue
- inspect invoice fields
- inspect ERP and CRM evidence
- inspect retrieved evidence
- review risk score and reasons
- approve, edit, or reject draft

### Auditor

- view decision history
- view audit logs
- inspect trace information

## Important Product Rules

- The app uses the logged-in user's tenant.
- The app must not hardcode tenant ids.
- The app must not expose platform admin features.
- Tenant creation happens in Streamlit Platform Admin.
- Customer-facing drafts require human approval.

## Recommended Review Flow

1. Open review queue.
2. Select invoice.
3. Check invoice preview and extracted fields.
4. Check ERP payment facts.
5. Check CRM notes and disputes.
6. Check retrieved evidence.
7. Check risk score and reasons.
8. Read generated draft.
9. Confirm guardrails passed.
10. Approve, edit, or reject.
