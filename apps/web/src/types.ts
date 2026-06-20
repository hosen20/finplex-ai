export type RiskLevel = "low" | "medium" | "high" | "critical" | string;
export type ReviewStatus = "pending" | "approved" | "rejected" | "changes_requested" | string;

export interface UserProfile {
  user_id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active?: boolean;
}

export interface Tenant {
  tenant_id: string;
  name: string;
  erp_provider?: string | null;
  crm_provider?: string | null;
  status?: string;
  created_at?: string;
}

export interface Customer {
  customer_id: string;
  tenant_id: string;
  company_name: string;
  contact_name?: string | null;
  contact_email?: string | null;
  preferred_contact_channel?: string | null;
  relationship_status?: string | null;
  tags?: string[];
  created_at?: string;
}

export interface ExtractedFields {
  invoice_number?: string | null;
  customer_name?: string | null;
  amount_due?: number | null;
  currency?: string | null;
  due_date?: string | null;
  payment_terms?: string | null;
  [key: string]: unknown;
}

export interface Invoice {
  invoice_id: string;
  tenant_id: string;
  customer_id?: string | null;
  file_name: string;
  storage_key?: string | null;
  status: string;
  extracted_fields?: ExtractedFields | null;
  evidence_ids?: string[] | null;
  created_at?: string;
  updated_at?: string;
}

export interface Review {
  review_id: string;
  tenant_id: string;
  invoice_id: string;
  draft_message: string;
  risk_level: RiskLevel;
  guardrails_passed: boolean;
  evidence_ids: string[];
  status?: ReviewStatus;
  reviewer_comment?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AuthState {
  accessToken: string | null;
  user: UserProfile | null;
}

export interface ApiHealth {
  service: string;
  status: string;
  environment?: string;
}

export interface DashboardData {
  tenants: Tenant[];
  customers: Customer[];
  invoices: Invoice[];
  reviews: Review[];
}

export interface UploadResult {
  invoice?: Invoice;
  event_id?: string;
  event_type?: string;
  event_topic?: string;
}
