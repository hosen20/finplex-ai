import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  DEMO_TENANT_ID,
  approveReview,
  checkHealth,
  listCustomers,
  listInvoices,
  listPendingReviews,
  login,
  rejectReview,
  uploadInvoice,
} from "./api/client";
import type { ApiSession } from "./api/client";
import type { Customer, Invoice, Review } from "./types";
import { asMoney, formatDate, normalizeStatus, riskClass } from "./utils";

const ADMIN_EMAIL = "clinadmin@example.com";
const MANAGER_EMAIL = "manager@example.com";
const DEMO_PASSWORD = "FinplexDemo123!";

function App() {
  const [session, setSession] = useState<ApiSession | null>(null);
  const [email, setEmail] = useState(ADMIN_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [activePage, setActivePage] = useState("overview");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("cust_demo_accept");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(false);

  const token = session?.accessToken || "";

  const metrics = useMemo(() => {
    const highRisk = reviews.filter((review) =>
      review.risk_level.toLowerCase().includes("high"),
    ).length;

    return {
      customers: customers.length,
      invoices: invoices.length,
      pendingReviews: reviews.length,
      highRisk,
    };
  }, [customers, invoices, reviews]);

  async function loadWorkspace(currentToken = token) {
    if (!currentToken) {
      return;
    }

    const [customerList, invoiceList, reviewList] = await Promise.all([
      listCustomers(currentToken),
      listInvoices(currentToken),
      listPendingReviews(currentToken),
    ]);

    setCustomers(customerList);
    setInvoices(invoiceList);
    setReviews(reviewList);

    if (!selectedCustomerId && customerList.length > 0) {
      setSelectedCustomerId(customerList[0].customer_id);
    }
  }

  useEffect(() => {
    checkHealth().then(setApiHealthy).catch(() => setApiHealthy(false));
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }

    const intervalId = window.setInterval(() => {
      loadWorkspace(token).catch(() => undefined);
    }, 3000);

    return () => window.clearInterval(intervalId);
  }, [token]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setActionMessage("");
    setIsLoading(true);

    try {
      const nextSession = await login(email, password);
      setSession(nextSession);
      await loadWorkspace(nextSession.accessToken);
      setActivePage("overview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token || !selectedFile || !selectedCustomerId) {
      setError("Choose an invoice image and customer before uploading.");
      return;
    }

    setError("");
    setUploadMessage("Uploading invoice and starting AI processing...");
    setIsLoading(true);

    try {
      const response = await uploadInvoice(
        token,
        selectedFile,
        selectedCustomerId,
      );
      await loadWorkspace(token);
      setSelectedFile(null);
      setUploadMessage(
        `Uploaded ${response.invoice.file_name}. The worker will create a review shortly.`,
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
        "Approved during manual upload demo.",
      );
      await loadWorkspace(token);
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
        "Rejected by human reviewer because this account needs a revised tone.",
      );
      await loadWorkspace(token);
      setActionMessage("Review rejected successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reject review.");
    } finally {
      setIsLoading(false);
    }
  }

  if (!session) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div>
            <span className="eyebrow">Finplex AI Demo</span>
            <h1>Invoice intelligence for responsible collections</h1>
            <p>
              Sign in and run the full manual upload demo: invoice image,
              OCR extraction, risk scoring, evidence retrieval, guardrails, and
              human approval.
            </p>
          </div>

          <form onSubmit={handleLogin} className="stack">
            <label>
              Email
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
              />
            </label>
            <label>
              Password
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
              />
            </label>
            {error ? <div className="notice danger">{error}</div> : null}
            <button disabled={isLoading} type="submit">
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="demo-accounts">
            <strong>Demo accounts</strong>
            <button type="button" onClick={() => setEmail(ADMIN_EMAIL)}>
              Admin
            </button>
            <button type="button" onClick={() => setEmail(MANAGER_EMAIL)}>
              Manager
            </button>
            <span>Password: {DEMO_PASSWORD}</span>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <span className="logo-mark">F</span>
          <h2>Finplex AI</h2>
          <p>Manual Upload Demo</p>
        </div>

        <nav>
          {[
            ["overview", "Overview"],
            ["upload", "Upload Invoices"],
            ["reviews", "Human Review"],
            ["invoices", "Invoices"],
            ["evidence", "Evidence"],
          ].map(([key, label]) => (
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
            <span className="eyebrow">Tenant: {DEMO_TENANT_ID}</span>
            <h1>{pageTitle(activePage)}</h1>
          </div>
          <div className="user-card">
            <span>{session.user.full_name}</span>
            <small>{session.user.email}</small>
            <button type="button" onClick={() => setSession(null)}>
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

        {activePage === "evidence" ? <EvidencePanel reviews={reviews} /> : null}
      </section>
    </main>
  );
}

function pageTitle(page: string): string {
  const titles: Record<string, string> = {
    overview: "Demo overview",
    upload: "Upload invoice images",
    reviews: "Human review queue",
    invoices: "Invoice processing status",
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
      </div>

      <div className="card two-column">
        <div>
          <h3>Final demo story</h3>
          <ol className="timeline">
            <li>Upload NEW-00001.png and approve the generated review.</li>
            <li>Upload NEW-00002.png and reject the generated review.</li>
            <li>Show evidence IDs, risk labels, and guardrails status.</li>
          </ol>
        </div>
        <div>
          <h3>Current workspace</h3>
          <p>{invoices.length} invoices have entered the system.</p>
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
        <h3>Manual invoice upload</h3>
        <p>
          Upload the PNG invoice image. Finplex will store it, publish the
          Kafka event, process it through the worker, and create a human review.
        </p>
      </div>

      <div className="demo-files">
        <div>
          <strong>Approval path</strong>
          <span>data/demo_invoices/manual_upload_images/NEW-00001.png</span>
          <small>Recommended customer: Aurora Medical Supplies</small>
        </div>
        <div>
          <strong>Rejection path</strong>
          <span>data/demo_invoices/manual_upload_images/NEW-00002.png</span>
          <small>Recommended customer: Northstar Diagnostics Lab</small>
        </div>
      </div>

      <form className="upload-form" onSubmit={onSubmit}>
        <label>
          Customer
          <select
            value={selectedCustomerId}
            onChange={(event) => onCustomerChange(event.target.value)}
          >
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
        <h3>No pending reviews yet</h3>
        <p>Upload an invoice image and wait a few seconds for the worker.</p>
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
              <span>{asMoney(invoice.extracted_fields?.amount_due)}</span>
              <small>{formatDate(invoice.created_at)}</small>
            </div>
          );
        })}
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
        The UI keeps them readable and does not expose raw backend JSON.
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
