import type { Customer, Invoice, Review, UploadResponse, User } from "../types";

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || DEFAULT_API_BASE_URL;

export const DEMO_TENANT_ID =
  import.meta.env.VITE_DEMO_TENANT_ID || "tenant_demo_clinic";

export type ApiSession = {
  accessToken: string;
  user: User;
};

class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function friendlyError(status: number, detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return "Please check the highlighted fields and try again.";
  }

  if (status === 401) {
    return "Login failed. Please check the email and password.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "The requested item was not found.";
  }

  if (status >= 500) {
    return "The server had a problem. Please check the API terminal logs.";
  }

  return "The request could not be completed. Please try again.";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof data === "object" && data !== null ? data.detail : data;
    throw new ApiError(friendlyError(response.status, detail));
  }

  return data as T;
}

export async function login(email: string, password: string): Promise<ApiSession> {
  const token = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  const user = await request<User>("/auth/me", {}, token.access_token);

  return {
    accessToken: token.access_token,
    user,
  };
}

export async function listCustomers(token: string): Promise<Customer[]> {
  return request<Customer[]>(
    `/customers?tenant_id=${encodeURIComponent(DEMO_TENANT_ID)}`,
    {},
    token,
  );
}

export async function listInvoices(token: string): Promise<Invoice[]> {
  return request<Invoice[]>(
    `/invoices?tenant_id=${encodeURIComponent(DEMO_TENANT_ID)}`,
    {},
    token,
  );
}

export async function listPendingReviews(token: string): Promise<Review[]> {
  return request<Review[]>(
    `/reviews/pending?tenant_id=${encodeURIComponent(DEMO_TENANT_ID)}`,
    {},
    token,
  );
}

export async function uploadInvoice(
  token: string,
  file: File,
  customerId: string,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("tenant_id", DEMO_TENANT_ID);
  formData.append("customer_id", customerId);
  formData.append("file", file);

  return request<UploadResponse>(
    "/invoices/upload",
    {
      method: "POST",
      body: formData,
    },
    token,
  );
}

export async function approveReview(
  token: string,
  reviewId: string,
  comment: string,
): Promise<Review> {
  return request<Review>(
    `/reviews/${reviewId}/approve`,
    {
      method: "POST",
      body: JSON.stringify({ comment }),
    },
    token,
  );
}

export async function rejectReview(
  token: string,
  reviewId: string,
  comment: string,
): Promise<Review> {
  return request<Review>(
    `/reviews/${reviewId}/reject`,
    {
      method: "POST",
      body: JSON.stringify({ comment }),
    },
    token,
  );
}

export async function checkHealth(): Promise<boolean> {
  try {
    const health = await request<{ status: string }>("/health");
    return health.status === "ok";
  } catch {
    return false;
  }
}
