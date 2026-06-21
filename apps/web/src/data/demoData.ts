import type { Customer, Invoice, Review, User } from "../types";

export type Tenant = {
  tenant_id: string;
  name: string;
  status: string;
};

export type DashboardData = {
  tenant: Tenant;
  users: User[];
  customers: Customer[];
  invoices: Invoice[];
  reviews: Review[];
};

const now = new Date().toISOString();

export const DEMO_TENANT_ID = "tenant_demo_clinic";

export const demoTenant: Tenant = {
  tenant_id: DEMO_TENANT_ID,
  name: "Finplex Manual Upload Demo",
  status: "ACTIVE"
};

export const demoUsers: User[] = [
  {
    user_id: "user_demo_admin",
    tenant_id: DEMO_TENANT_ID,
    email: "clinadmin@example.com",
    full_name: "Clinical Admin Demo",
    role: "TENANT_ADMIN",
    is_active: true
  },
  {
    user_id: "user_demo_manager",
    tenant_id: DEMO_TENANT_ID,
    email: "manager@example.com",
    full_name: "Operations Manager Demo",
    role: "MANAGER",
    is_active: true
  }
];

export const demoCustomers: Customer[] = [
  {
    customer_id: "cust_demo_accept",
    tenant_id: DEMO_TENANT_ID,
    company_name: "Aurora Medical Supplies",
    contact_name: "Maya Haddad",
    contact_email: "maya.haddad@aurora-demo.example",
    preferred_contact_channel: "email",
    relationship_status: "healthy",
    tags: ["approval-demo", "invoice-follow-up"],
    created_at: now,
    updated_at: null
  },
  {
    customer_id: "cust_demo_reject",
    tenant_id: DEMO_TENANT_ID,
    company_name: "Cedar Retail Group",
    contact_name: "Omar Nasser",
    contact_email: "omar.nasser@cedar-demo.example",
    preferred_contact_channel: "email",
    relationship_status: "open_dispute",
    tags: ["rejection-demo", "open-dispute"],
    created_at: now,
    updated_at: null
  }
];

export const demoInvoices: Invoice[] = [
  {
    invoice_id: "demo_invoice_accept_placeholder",
    tenant_id: DEMO_TENANT_ID,
    uploaded_by_user_id: "user_demo_admin",
    customer_id: "cust_demo_accept",
    file_name: "NEW-00001.png",
    storage_key: "manual-demo/NEW-00001.png",
    status: "UPLOADED",
    payment_status: "UNPAID",
    extracted_fields: {
      invoice_number: "NEW-00001",
      amount_due: "12450.00",
      currency: "USD"
    },
    evidence_ids: [],
    created_at: now,
    updated_at: null
  },
  {
    invoice_id: "demo_invoice_reject_placeholder",
    tenant_id: DEMO_TENANT_ID,
    uploaded_by_user_id: "user_demo_admin",
    customer_id: "cust_demo_reject",
    file_name: "NEW-00002.png",
    storage_key: "manual-demo/NEW-00002.png",
    status: "UPLOADED",
    payment_status: "UNPAID",
    extracted_fields: {
      invoice_number: "NEW-00002",
      amount_due: "8700.00",
      currency: "USD"
    },
    evidence_ids: [],
    created_at: now,
    updated_at: null
  }
];

export const demoReviews: Review[] = [];

export const demoDashboardData: DashboardData = {
  tenant: demoTenant,
  users: demoUsers,
  customers: demoCustomers,
  invoices: demoInvoices,
  reviews: demoReviews
};

export default demoDashboardData;
