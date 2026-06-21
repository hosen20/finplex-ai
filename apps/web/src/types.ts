export type User = {
  user_id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
};

export type Customer = {
  customer_id: string;
  tenant_id: string;
  company_name: string;
  contact_name: string;
  contact_email: string;
  preferred_contact_channel: string;
  relationship_status: string;
  tags: string[];
  created_at: string;
  updated_at?: string | null;
};

export type Invoice = {
  invoice_id: string;
  tenant_id: string;
  uploaded_by_user_id: string;
  customer_id?: string | null;
  file_name: string;
  storage_key: string;
  status: string;
  payment_status: string;
  extracted_fields?: Record<string, unknown> | null;
  evidence_ids: string[];
  created_at: string;
  updated_at?: string | null;
};

export type Review = {
  review_id: string;
  tenant_id: string;
  invoice_id: string;
  draft_message: string;
  risk_level: string;
  guardrails_passed: boolean;
  evidence_ids: string[];
  status: string;
  reviewer_user_id?: string | null;
  reviewer_comment?: string | null;
  created_at: string;
  updated_at?: string | null;
};

export type UploadResponse = {
  invoice: Invoice;
  event_id: string;
  event_type: string;
  event_topic: string;
};
