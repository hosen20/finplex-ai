import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  approveReview,
  checkHealth,
  createTenantUser,
  listCustomers,
  listInvoices,
  listPendingReviews,
  listUsers,
  login,
  rejectReview,
  uploadInvoice,
} from "./api/client";
import type { ApiSession } from "./api/client";
import type { Customer, Invoice, Review, User } from "./types";
import { asMoney, formatDate, normalizeStatus, riskClass } from "./utils";

const USER_ROLES = ["tenant_admin", "manager", "reviewer", "auditor"];

function App() {
  const [session, setSession] = useState<ApiSession | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [activePage, setActivePage] = useState("overview");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(false);

  const token = session?.accessToken || "";
  const tenantId = session?.user.tenant_id || "";
  const canManageUsers = session?.user.role === "tenant_admin";

  const metrics = useMemo(() => {
    const highRisk = reviews.filter((review) =>
      review.risk_level.toLowerCase().includes("high"),
    ).length;
    const overdueInvoices = invoices.filter((invoice) =>
      invoice.payment_status.toLowerCase().includes("overdue"),
    ).length;

    return {
      customers: customers.length,
      invoices: invoices.length,
      pendingReviews: reviews.length,
      highRisk,
      overdueInvoices,
    };
  }, [customers, invoices, reviews]);

  async function loadWorkspace(currentSession = session) {
    if (!currentSession) {
      return;
    }

    const currentToken = currentSession.accessToken;
    const currentTenantId = currentSession.user.tenant_id;

    const [customerList, invoiceList, reviewList] = await Promise.all([
      listCustomers(currentToken, currentTenantId),
      listInvoices(currentToken, currentTenantId),
      listPendingReviews(currentToken, currentTenantId),
    ]);

    setCustomers(customerList);
    setInvoices(invoiceList);
    setReviews(reviewList);

    if (currentSession.user.role === "tenant_admin") {
      const tenantUsers = await listUsers(currentToken, currentTenantId);
      setUsers(tenantUsers);
    } else {
      setUsers([]);
    }

    if (!selectedCustomerId && customerList.length > 0) {
      setSelectedCustomerId(customerList[0].customer_id);
    }
  }

  useEffect(() => {
    checkHealth().then(setApiHealthy).catch(() => setApiHealthy(false));
  }, []);

  useEffect(() => {
    if (!session) {
      return;
    }

    const intervalId = window.setInterval(() => {
      loadWorkspace(session).catch(() => undefined);
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [session]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setActionMessage("");
    setIsLoading(true);

    try {
      const nextSession = await login(email.trim(), password);
      setSession(nextSession);
      await loadWorkspace(nextSession);
      setActivePage("overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!session || !selectedFile || !selectedCustomerId) {
      setError("Choose an invoice image and customer before uploading.");
      return;
    }

    setError("");
    setUploadMessage("Uploading invoice and starting AI processing...");
    setIsLoading(true);

    try {
      const response = await uploadInvoice(
        session.accessToken,
        session.user.tenant_id,
        selectedFile,
        selectedCustomerId,
      );
      await loadWorkspace(session);
      setSelectedFile(null);
      setUploadMessage(
        `Uploaded ${response.invoice.file_name}. The AI review will appear when processing finishes.`,
      );
      setActivePage("reviews");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setUploadMessage("");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleApprove(review: Review) {
    setError("");
    setActionMessage("");
    setIsLoading(true);

    try {
      await approveReview(
        token,
        review.review_id,
        "Approved by the human reviewer after checking the evidence.",
      );
      await loadWorkspace();
      setActionMessage("Review approved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not approve review.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleReject(review: Review) {
    setError("");
    setActionMessage("");
    setIsLoading(true);

    try {
      await rejectReview(
        token,
        review.review_id,
        "Rejected by the human reviewer because the draft needs revision.",
      );
      await loadWorkspace();
      setActionMessage("Review rejected successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reject review.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateUser(input: UserFormState) {
    if (!session) {
      return;
    }

    setError("");
    setActionMessage("");
    setIsLoading(true);

    try {
      await createTenantUser(session.accessToken, {
        tenantId: session.user.tenant_id,
        email: input.email.trim(),
        fullName: input.fullName.trim(),
        password: input.password,
        role: input.role,
      });
      await loadWorkspace(session);
      setActionMessage("User created successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create user.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleSignOut() {
    setSession(null);
    setPassword("");
    setCustomers([]);
    setInvoices([]);
    setReviews([]);
    setUsers([]);
    setSelectedCustomerId("");
    setActionMessage("");
    setError("");
  }

  if (!session) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div>
            <span className="eyebrow">Finplex AI</span>
            <h1>Invoice intelligence for finance teams</h1>
            <p>
              Sign in with the account created by your Finplex platform admin or
              tenant admin. Finplex AI connects invoice uploads, ERP records, CRM
              history, risk scoring, evidence retrieval, guardrails, and human
              approval in one local-first product.
            </p>
          </div>

          <form onSubmit={handleLogin} className="stack">
            <label>
              Email
              <input
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@company.com"
                type="email"
              />
            </label>
            <label>
              Password
              <input
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                type="password"
              />
            </label>
            {error ? <div className="notice danger">{error}</div> : null}
            <button disabled={isLoading} type="submit">
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="access-note">
            <strong>No public signup</strong>
            <span>
              New companies are created in the Streamlit Platform Admin console.
              Tenant admins then create finance managers, reviewers, and auditors.
            </span>
          </div>
        </section>
      </main>
    );
  }

  const navigationItems = [
    ["overview", "Overview"],
    ["upload", "Upload Invoices"],
    ["reviews", "Human Review"],
    ["invoices", "Invoices"],
    ["customers", "Customers"],
    ...(canManageUsers ? [["users", "Users & Roles"]] : []),
    ["evidence", "Evidence"],
  ];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <span className="logo-mark">F</span>
          <h2>Finplex AI</h2>
          <p>Tenant workspace</p>
        </div>

        <nav>
          {navigationItems.map(([key, label]) => (
            <button
              className={activePage === key ? "active" : ""}
              key={key}
              onClick={() => setActivePage(key)}
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <section className="content-shell">
        <header className="topbar">
          <div>
            <span className="eyebrow">Tenant: {tenantId}</span>
            <h1>{pageTitle(activePage)}</h1>
          </div>
          <div className="user-card">
            <span>{session.user.full_name}</span>
            <small>{session.user.email}</small>
            <small>{normalizeStatus(session.user.role)}</small>
            <button type="button" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        </header>

        <div className="status-row">
          <span className={apiHealthy ? "pill success" : "pill danger"}>
            API {apiHealthy ? "connected" : "not reachable"}
          </span>
          <button
            className="secondary"
            disabled={isLoading}
            onClick={() => loadWorkspace()}
            type="button"
          >
            Refresh data
          </button>
        </div>

        {error ? <div className="notice danger">{error}</div> : null}
        {actionMessage ? <div className="notice success">{actionMessage}</div> : null}

        {activePage === "overview" ? (
          <Overview metrics={metrics} invoices={invoices} reviews={reviews} />
        ) : null}

        {activePage === "upload" ? (
          <UploadPanel
            customers={customers}
            selectedCustomerId={selectedCustomerId}
            selectedFile={selectedFile}
            uploadMessage={uploadMessage}
            onCustomerChange={setSelectedCustomerId}
            onFileChange={setSelectedFile}
            onSubmit={handleUpload}
          />
        ) : null}

        {activePage === "reviews" ? (
          <ReviewPanel
            reviews={reviews}
            invoices={invoices}
            isLoading={isLoading}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        ) : null}

        {activePage === "invoices" ? (
          <InvoicePanel invoices={invoices} customers={customers} />
        ) : null}

        {activePage === "customers" ? (
          <CustomerPanel customers={customers} invoices={invoices} />
        ) : null}

        {activePage === "users" && canManageUsers ? (
          <UserManagementPanel
            users={users}
            isLoading={isLoading}
            onCreateUser={handleCreateUser}
          />
        ) : null}

        {activePage === "evidence" ? <EvidencePanel reviews={reviews} /> : null}
      </section>
    </main>
  );
}

function pageTitle(page: string): string {
  const titles: Record<string, string> = {
    overview: "Workspace overview",
    upload: "Upload invoice images",
    reviews: "Human review queue",
    invoices: "Invoice processing status",
    customers: "Customer intelligence",
    users: "Users and roles",
    evidence: "Evidence and citations",
  };

  return titles[page] || "Finplex AI";
}

function Overview({
  metrics,
  invoices,
  reviews,
}: {
  metrics: Record<string, number>;
  invoices: Invoice[];
  reviews: Review[];
}) {
  return (
    <section className="stack">
      <div className="metric-grid">
        <Metric label="Customers" value={metrics.customers} />
        <Metric label="Invoices" value={metrics.invoices} />
        <Metric label="Pending reviews" value={metrics.pendingReviews} />
        <Metric label="High-risk reviews" value={metrics.highRisk} />
        <Metric label="Overdue invoices" value={metrics.overdueInvoices} />
      </div>

      <div className="card two-column">
        <div>
          <h3>Product workflow</h3>
          <ol className="timeline">
            <li>Upload invoice images or PDFs from the tenant workspace.</li>
            <li>Finplex AI extracts invoice fields and links ERP/CRM evidence.</li>
            <li>Risk scoring, RAG citations, and guardrails prepare a draft.</li>
            <li>A human reviewer approves, rejects, or revises the result.</li>
          </ol>
        </div>
        <div>
          <h3>Current workspace</h3>
          <p>{invoices.length} invoices have entered the tenant pipeline.</p>
          <p>{reviews.length} reviews are waiting for a human decision.</p>
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function UploadPanel({
  customers,
  selectedCustomerId,
  selectedFile,
  uploadMessage,
  onCustomerChange,
  onFileChange,
  onSubmit,
}: {
  customers: Customer[];
  selectedCustomerId: string;
  selectedFile: File | null;
  uploadMessage: string;
  onCustomerChange: (value: string) => void;
  onFileChange: (value: File | null) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <section className="card stack">
      <div>
        <h3>Invoice upload</h3>
        <p>
          Upload a PNG or JPG invoice image. The backend stores the file,
          publishes an event, and the AI pipeline creates a review with evidence
          and guardrails status.
        </p>
      </div>

      <div className="info-panel">
        <strong>Dataset-ready upload</strong>
        <span>
          Use invoice images from the local dataset folder or upload a new tenant
          invoice. Each upload is scoped to the signed-in user's tenant.
        </span>
      </div>

      <form className="upload-form" onSubmit={onSubmit}>
        <label>
          Customer
          <select
            value={selectedCustomerId}
            onChange={(event) => onCustomerChange(event.target.value)}
          >
            <option value="">Choose customer</option>
            {customers.map((customer) => (
              <option key={customer.customer_id} value={customer.customer_id}>
                {customer.company_name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Invoice image
          <input
            accept="image/png,image/jpeg,.png,.jpg,.jpeg"
            onChange={(event) => onFileChange(event.target.files?.[0] || null)}
            type="file"
          />
        </label>

        <button disabled={!selectedFile || !selectedCustomerId} type="submit">
          Upload and process invoice
        </button>
      </form>

      {uploadMessage ? <div className="notice info">{uploadMessage}</div> : null}
    </section>
  );
}

function ReviewPanel({
  reviews,
  invoices,
  isLoading,
  onApprove,
  onReject,
}: {
  reviews: Review[];
  invoices: Invoice[];
  isLoading: boolean;
  onApprove: (review: Review) => void;
  onReject: (review: Review) => void;
}) {
  if (reviews.length === 0) {
    return (
      <section className="empty-card">
        <h3>No pending reviews</h3>
        <p>Upload an invoice image and wait for the AI worker to process it.</p>
      </section>
    );
  }

  return (
    <section className="review-grid">
      {reviews.map((review) => {
        const invoice = invoices.find((item) => item.invoice_id === review.invoice_id);

        return (
          <article className="review-card" key={review.review_id}>
            <div className="review-heading">
              <div>
                <span className="eyebrow">{invoice?.file_name || review.invoice_id}</span>
                <h3>{review.review_id}</h3>
              </div>
              <span className={`pill ${riskClass(review.risk_level)}`}>
                {normalizeStatus(review.risk_level)} risk
              </span>
            </div>

            <p className="draft-message">{review.draft_message}</p>

            <div className="review-meta">
              <span className={review.guardrails_passed ? "pill success" : "pill danger"}>
                Guardrails {review.guardrails_passed ? "passed" : "blocked"}
              </span>
              <span className="pill neutral">{normalizeStatus(review.status)}</span>
            </div>

            <div className="evidence-list">
              {review.evidence_ids.map((evidenceId) => (
                <span key={evidenceId}>{evidenceId}</span>
              ))}
            </div>

            <div className="review-actions">
              <button disabled={isLoading} onClick={() => onApprove(review)} type="button">
                Approve
              </button>
              <button
                className="danger-button"
                disabled={isLoading}
                onClick={() => onReject(review)}
                type="button"
              >
                Reject
              </button>
            </div>
          </article>
        );
      })}
    </section>
  );
}

function InvoicePanel({
  invoices,
  customers,
}: {
  invoices: Invoice[];
  customers: Customer[];
}) {
  return (
    <section className="card stack">
      <h3>Invoices</h3>
      <div className="table-like">
        {invoices.map((invoice) => {
          const customer = customers.find(
            (item) => item.customer_id === invoice.customer_id,
          );

          return (
            <div className="table-row" key={invoice.invoice_id}>
              <div>
                <strong>{invoice.file_name}</strong>
                <small>{customer?.company_name || invoice.customer_id || "No customer"}</small>
              </div>
              <span className="pill neutral">{normalizeStatus(invoice.status)}</span>
              <span className="pill warning">{normalizeStatus(invoice.payment_status)}</span>
              <span>{asMoney(invoice.extracted_fields?.amount_due)}</span>
              <small>{formatDate(invoice.created_at)}</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function CustomerPanel({
  customers,
  invoices,
}: {
  customers: Customer[];
  invoices: Invoice[];
}) {
  return (
    <section className="customer-grid">
      {customers.map((customer) => {
        const customerInvoices = invoices.filter(
          (invoice) => invoice.customer_id === customer.customer_id,
        );

        return (
          <article className="card stack" key={customer.customer_id}>
            <div>
              <span className="eyebrow">{customer.relationship_status}</span>
              <h3>{customer.company_name}</h3>
              <p>{customer.contact_name} · {customer.contact_email}</p>
            </div>
            <div className="customer-facts">
              <span>{customerInvoices.length} invoices</span>
              <span>{normalizeStatus(customer.preferred_contact_channel)}</span>
            </div>
            <div className="evidence-list">
              {customer.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
          </article>
        );
      })}
    </section>
  );
}

type UserFormState = {
  email: string;
  fullName: string;
  password: string;
  role: string;
};

function UserManagementPanel({
  users,
  isLoading,
  onCreateUser,
}: {
  users: User[];
  isLoading: boolean;
  onCreateUser: (input: UserFormState) => Promise<void>;
}) {
  const [form, setForm] = useState<UserFormState>({
    email: "",
    fullName: "",
    password: "",
    role: "reviewer",
  });

  async function submitUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCreateUser(form);
    setForm({ email: "", fullName: "", password: "", role: "reviewer" });
  }

  return (
    <section className="stack">
      <div className="card stack">
        <div>
          <h3>Create tenant user</h3>
          <p>
            Tenant admins can create finance managers, reviewers, and auditors
            for their own company. Platform tenant creation stays in Streamlit.
          </p>
        </div>

        <form className="user-form" onSubmit={submitUser}>
          <label>
            Full name
            <input
              value={form.fullName}
              onChange={(event) => setForm({ ...form, fullName: event.target.value })}
              placeholder="Jane Finance"
              required
              type="text"
            />
          </label>
          <label>
            Email
            <input
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="jane@company.com"
              required
              type="email"
            />
          </label>
          <label>
            Role
            <select
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value })}
            >
              {USER_ROLES.map((role) => (
                <option key={role} value={role}>
                  {normalizeStatus(role)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Temporary password
            <input
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              minLength={8}
              required
              type="password"
            />
          </label>
          <button disabled={isLoading} type="submit">
            Create user
          </button>
        </form>
      </div>

      <div className="card stack">
        <h3>Tenant users</h3>
        <div className="table-like">
          {users.map((user) => (
            <div className="table-row users-row" key={user.user_id}>
              <div>
                <strong>{user.full_name}</strong>
                <small>{user.email}</small>
              </div>
              <span className="pill neutral">{normalizeStatus(user.role)}</span>
              <span className={user.is_active ? "pill success" : "pill danger"}>
                {user.is_active ? "Active" : "Inactive"}
              </span>
              <small>{formatDate(user.created_at)}</small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EvidencePanel({ reviews }: { reviews: Review[] }) {
  const evidenceIds = Array.from(
    new Set(reviews.flatMap((review) => review.evidence_ids)),
  );

  return (
    <section className="card stack">
      <h3>Evidence IDs used in pending reviews</h3>
      <p>
        These are the citation IDs used by the AI draft and human review flow.
        Each evidence item belongs to the signed-in user's tenant workspace.
      </p>
      <div className="evidence-list large">
        {evidenceIds.length > 0 ? (
          evidenceIds.map((evidenceId) => <span key={evidenceId}>{evidenceId}</span>)
        ) : (
          <span>No evidence yet. Upload an invoice first.</span>
        )}
      </div>
    </section>
  );
}

export default App;
