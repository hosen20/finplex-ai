# Demo Invoices

This folder contains invoice files used for the local Finplex AI demo.

The main uploaded invoice images are expected under:

```text
data/demo_invoices/new_uploaded_invoices/
```

The demo seed script expects these invoice images:

```text
NEW-00001.png
NEW-00002.png
NEW-00003.png
```

## Recommended Demo Invoice

Use this invoice first during the presentation:

```text
NEW-00001.png
```

It represents the strongest demo scenario:

- High payment risk
- Overdue invoice
- Open CRM dispute
- ERP balance still open
- RAG evidence available
- Guardrails-safe follow-up draft
- Human review needed

## Demo Story

Explain it like this:

A customer has an overdue invoice, but the CRM shows that they also raised a pricing question. Finplex AI does not simply generate a harsh reminder. It retrieves the ERP and CRM evidence, drafts a respectful clarification-first follow-up, validates it with guardrails, and sends it to a human reviewer.
