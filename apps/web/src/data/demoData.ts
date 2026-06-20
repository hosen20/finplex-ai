import type { Customer, DashboardData, Invoice, Review, Tenant } from "../types";

export const demoTenant: Tenant = {
  tenant_id: "tenant_demo",
  name: "Finplex Demo Workspace",
  erp_provider: "Oracle ERP Cloud",
  crm_provider: "Salesforce CRM",
  status: "active"
};

export const demoCustomers: Customer[] = [
  {
    customer_id: "cust_acme",
    tenant_id: demoTenant.tenant_id,
    company_name: "Acme Distribution",
    contact_name: "Maya Carter",
    contact_email: "maya.carter@acme.example",
    preferred_contact_channel: "email",
    relationship_status: "active",
    tags: ["enterprise", "payment-plan"]
  },
  {
    customer_id: "cust_nova",
    tenant_id: demoTenant.tenant_id,
    company_name: "Nova Retail Group",
    contact_name: "Samir Haddad",
    contact_email: "samir.haddad@nova.example",
    preferred_contact_channel: "email",
    relationship_status: "watchlist",
    tags: ["retail", "recent-dispute"]
  }
];

export const demoInvoices: Invoice[] = [
  {
    invoice_id: "new_inv_001",
    tenant_id: demoTenant.tenant_id,
    customer_id: "cust_acme",
    file_name: "NEW-00001.png",
    storage_key: "tenant_demo/invoices/new_inv_001/NEW-00001.png",
    status: "review_pending",
    extracted_fields: {
      invoice_number: "NEW-00001",
      customer_name: "Acme Distribution",
      amount_due: 13600,
      currency: "USD",
      due_date: "2026-07-01",
      payment_terms: "net_30"
    },
    evidence_ids: ["ev_invoice", "ev_erp", "ev_crm", "ev_policy"]
  },
  {
    invoice_id: "new_inv_002",
    tenant_id: demoTenant.tenant_id,
    customer_id: "cust_nova",
    file_name: "NEW-00002.png",
    status: "processing",
    extracted_fields: {
      invoice_number: "NEW-00002",
      customer_name: "Nova Retail Group",
      amount_due: 4200,
      currency: "USD",
      due_date: "2026-07-10"
    },
    evidence_ids: ["ev_invoice", "ev_crm"]
  },
  {
    invoice_id: "new_inv_003",
    tenant_id: demoTenant.tenant_id,
    file_name: "NEW-00003.png",
    status: "uploaded",
    extracted_fields: {
      invoice_number: "NEW-00003",
      customer_name: "Atlas Supplies",
      amount_due: 950,
      currency: "USD",
      due_date: "2026-07-15"
    },
    evidence_ids: []
  }
];

export const demoReviews: Review[] = [
  {
    review_id: "review_001",
    tenant_id: demoTenant.tenant_id,
    invoice_id: "new_inv_001",
    risk_level: "high",
    guardrails_passed: true,
    status: "pending",
    evidence_ids: ["ev_invoice", "ev_erp", "ev_crm", "ev_policy"],
    draft_message:
      "Hello Maya Carter,\n\nI hope you are well. We are following up on invoice NEW-00001 for USD 13,600.00 due on 2026-07-01. We would appreciate a short update so we can resolve this responsibly. This message is based on available supporting records from invoice, ERP, CRM, and regulation evidence.\n\nPlease let us know if payment has already been arranged or if there is anything we should review with your team.\n\nThank you."
  },
  {
    review_id: "review_002",
    tenant_id: demoTenant.tenant_id,
    invoice_id: "new_inv_002",
    risk_level: "medium",
    guardrails_passed: true,
    status: "pending",
    evidence_ids: ["ev_invoice", "ev_crm"],
    draft_message:
      "Hello Samir Haddad,\n\nThis is a respectful reminder for invoice NEW-00002. Could you please share the expected payment timing or tell us if anything needs review?\n\nThank you."
  }
];

export const demoDashboardData: DashboardData = {
  tenants: [demoTenant],
  customers: demoCustomers,
  invoices: demoInvoices,
  reviews: demoReviews
};
