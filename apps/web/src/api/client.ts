import type {
  ApiHealth,
  Customer,
  Invoice,
  Review,
  Tenant,
  UploadResult,
  UserProfile
} from "../types";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || DEFAULT_API_BASE_URL;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return "Please check the highlighted form fields.";
    }
  } catch {
    // ignore JSON parsing errors and use status text below
  }

  return response.statusText || "Request failed";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers = new Headers(options.headers);
  const isFormData = options.body instanceof FormData;

  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => request<ApiHealth>("/health"),

  login: async (email: string, password: string) => {
    return request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },

  me: (token: string) => request<UserProfile>("/auth/me", {}, token),

  listTenants: () => request<Tenant[]>("/tenants"),

  createTenant: (payload: {
    name: string;
    erp_provider: string;
    crm_provider: string;
    actor_user_id: string;
  }) =>
    request<Tenant>("/tenants", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  bootstrapAdmin: (payload: {
    tenant_id: string;
    email: string;
    full_name: string;
    password: string;
  }) =>
    request<UserProfile>("/auth/bootstrap-admin", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  listCustomers: (tenantId: string, token: string) =>
    request<Customer[]>(`/customers?tenant_id=${encodeURIComponent(tenantId)}`, {}, token),

  listInvoices: (tenantId: string, token: string) =>
    request<Invoice[]>(`/invoices?tenant_id=${encodeURIComponent(tenantId)}`, {}, token),

  listPendingReviews: (tenantId: string, token: string) =>
    request<Review[]>(`/reviews/pending?tenant_id=${encodeURIComponent(tenantId)}`, {}, token),

  uploadInvoice: (
    payload: { tenantId: string; customerId?: string; file: File },
    token: string
  ) => {
    const form = new FormData();
    form.append("tenant_id", payload.tenantId);
    if (payload.customerId) {
      form.append("customer_id", payload.customerId);
    }
    form.append("file", payload.file);

    return request<UploadResult>(
      "/invoices/upload",
      {
        method: "POST",
        body: form
      },
      token
    );
  },

  approveReview: (reviewId: string, comment: string, token: string) =>
    request<Review>(
      `/reviews/${encodeURIComponent(reviewId)}/approve`,
      {
        method: "POST",
        body: JSON.stringify({ comment })
      },
      token
    ),

  rejectReview: (reviewId: string, comment: string, token: string) =>
    request<Review>(
      `/reviews/${encodeURIComponent(reviewId)}/reject`,
      {
        method: "POST",
        body: JSON.stringify({ comment })
      },
      token
    ),

  requestChanges: (reviewId: string, comment: string, token: string) =>
    request<Review>(
      `/reviews/${encodeURIComponent(reviewId)}/request-changes`,
      {
        method: "POST",
        body: JSON.stringify({ comment })
      },
      token
    )
};
