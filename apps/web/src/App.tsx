import { useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { api, apiBaseUrl, ApiError } from "./api/client";
import { demoDashboardData, demoTenant } from "./data/demoData";
import type {
  ApiHealth,
  AuthState,
  Customer,
  DashboardData,
  Invoice,
  Review,
  Tenant,
  UserProfile
} from "./types";
import { clampPercentage, formatCurrency, formatDate, humanize, riskLabel } from "./utils/format";

const TOKEN_KEY = "finplex_access_token";
const USER_KEY = "finplex_user";
const TENANT_KEY = "finplex_selected_tenant";

type View = "overview" | "upload" | "invoices" | "reviews" | "evidence" | "customers" | "settings";
type NoticeKind = "success" | "warning" | "error" | "info";

interface Notice {
  kind: NoticeKind;
  message: string;
}

function loadAuth(): AuthState {
  const accessToken = localStorage.getItem(TOKEN_KEY);
  const userRaw = localStorage.getItem(USER_KEY);

  if (!accessToken || !userRaw) {
    return { accessToken: null, user: null };
  }

  try {
    return { accessToken, user: JSON.parse(userRaw) as UserProfile };
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    return { accessToken: null, user: null };
  }
}

function App() {
  const [auth, setAuth] = useState<AuthState>(() => loadAuth());
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [data, setData] = useState<DashboardData>(demoDashboardData);
  const [selectedTenantId, setSelectedTenantId] = useState<string>(
    () => localStorage.getItem(TENANT_KEY) || demoTenant.tenant_id
  );
  const [view, setView] = useState<View>("overview");
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);
  const [usingSampleData, setUsingSampleData] = useState(true);

  const selectedTenant = useMemo(() => {
    return data.tenants.find((tenant) => tenant.tenant_id === selectedTenantId) || data.tenants[0];
  }, [data.tenants, selectedTenantId]);

  const filteredInvoices = useMemo(() => {
    return data.invoices.filter((invoice) => invoice.tenant_id === selectedTenant?.tenant_id);
  }, [data.invoices, selectedTenant]);

  const filteredReviews = useMemo(() => {
    return data.reviews.filter((review) => review.tenant_id === selectedTenant?.tenant_id);
  }, [data.reviews, selectedTenant]);

  const filteredCustomers = useMemo(() => {
    return data.customers.filter((customer) => customer.tenant_id === selectedTenant?.tenant_id);
  }, [data.customers, selectedTenant]);

  const metrics = useMemo(() => {
    const totalAmount = filteredInvoices.reduce((sum, invoice) => {
      const amount = invoice.extracted_fields?.amount_due;
      return sum + (typeof amount === "number" ? amount : 0);
    }, 0);
    const pendingReviews = filteredReviews.filter((review) => (review.status || "pending") === "pending").length;
    const highRiskReviews = filteredReviews.filter((review) => ["high", "critical"].includes(String(review.risk_level))).length;
    const guardrailsPassed = filteredReviews.filter((review) => review.guardrails_passed).length;
    const guardrailsRate = filteredReviews.length ? (guardrailsPassed / filteredReviews.length) * 100 : 100;

    return {
      totalAmount,
      pendingReviews,
      highRiskReviews,
      guardrailsRate: clampPercentage(guardrailsRate),
      evidenceCount: new Set(filteredReviews.flatMap((review) => review.evidence_ids)).size
    };
  }, [filteredInvoices, filteredReviews]);

  useEffect(() => {
    void checkHealth();
  }, []);

  useEffect(() => {
    if (auth.accessToken) {
      void refreshData(auth.accessToken);
    }
  }, [auth.accessToken]);

  function showNotice(kind: NoticeKind, message: string) {
    setNotice({ kind, message });
    window.setTimeout(() => setNotice(null), 5200);
  }

  async function checkHealth() {
    try {
      const response = await api.health();
      setHealth(response);
    } catch {
      setHealth(null);
    }
  }

  async function refreshData(
    token = auth.accessToken,
    preferredTenantId?: string
  ) {
    setLoading(true);
    try {
      const tenants = await api.listTenants();
      const tenantId = preferredTenantId || selectedTenantId || auth.user?.tenant_id || tenants[0]?.tenant_id || demoTenant.tenant_id;
      const [customers, invoices, reviews] = token
        ? await Promise.all([
            api.listCustomers(tenantId, token),
            api.listInvoices(tenantId, token),
            api.listPendingReviews(tenantId, token)
          ])
        : [[], [], []];

      setData({
        tenants: tenants.length ? tenants : demoDashboardData.tenants,
        customers: customers.length ? customers : demoDashboardData.customers,
        invoices: invoices.length ? invoices : demoDashboardData.invoices,
        reviews: reviews.length ? reviews : demoDashboardData.reviews
      });
      setSelectedTenantId(tenantId);
      localStorage.setItem(TENANT_KEY, tenantId);
      setUsingSampleData(!(customers.length || invoices.length || reviews.length));
    } catch (error) {
      setData(demoDashboardData);
      setUsingSampleData(true);
      showNotice("warning", friendlyError(error, "Live API data is not available, so the dashboard is showing a polished sample workspace."));
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(email: string, password: string) {
    setLoading(true);
    try {
      const tokenResponse = await api.login(email, password);
      const accessToken = tokenResponse.access_token;
      const user = await api.me(accessToken);

      localStorage.setItem(TOKEN_KEY, accessToken);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      localStorage.setItem(TENANT_KEY, user.tenant_id);

      setAuth({ accessToken, user });
      setSelectedTenantId(user.tenant_id);
      setUsingSampleData(false);
      showNotice("success", `Welcome back, ${user.full_name}.`);
      await refreshData(accessToken, user.tenant_id);
    } catch (error) {
      showNotice("error", friendlyError(error, "Sign in failed. Please check the email and password."));
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setAuth({ accessToken: null, user: null });
    setData(demoDashboardData);
    setUsingSampleData(true);
    setSelectedTenantId(demoTenant.tenant_id);
    showNotice("info", "You are signed out. The sample workspace is still available for review.");
  }

  async function handleUpload(file: File, customerId?: string) {
    if (!auth.accessToken || !selectedTenant) {
      showNotice("warning", "Please sign in before uploading invoices.");
      return;
    }

    setLoading(true);
    try {
      await api.uploadInvoice(
        {
          tenantId: selectedTenant.tenant_id,
          customerId,
          file
        },
        auth.accessToken
      );
      showNotice("success", "Invoice uploaded. The worker pipeline can now extract fields, retrieve evidence, run guardrails, and create a review.");
      await refreshData(auth.accessToken);
      setView("invoices");
    } catch (error) {
      showNotice("error", friendlyError(error, "Invoice upload failed."));
    } finally {
      setLoading(false);
    }
  }

  async function handleReviewAction(reviewId: string, action: "approve" | "reject" | "changes", comment: string) {
    if (!auth.accessToken) {
      showNotice("warning", "Please sign in before reviewing drafts.");
      return;
    }

    setLoading(true);
    try {
      if (action === "approve") {
        await api.approveReview(reviewId, comment, auth.accessToken);
        showNotice("success", "Draft approved for the next step.");
      } else if (action === "reject") {
        await api.rejectReview(reviewId, comment, auth.accessToken);
        showNotice("success", "Draft rejected and recorded.");
      } else {
        await api.requestChanges(reviewId, comment, auth.accessToken);
        showNotice("success", "Change request sent back to the workflow.");
      }
      await refreshData(auth.accessToken);
    } catch (error) {
      showNotice("error", friendlyError(error, "Review action failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        currentView={view}
        setView={setView}
        selectedTenant={selectedTenant}
        health={health}
        usingSampleData={usingSampleData}
      />

      <main className="main-panel">
        <Topbar
          user={auth.user}
          tenants={data.tenants}
          selectedTenantId={selectedTenant?.tenant_id || selectedTenantId}
          onTenantChange={(tenantId) => {
            setSelectedTenantId(tenantId);
            localStorage.setItem(TENANT_KEY, tenantId);
          }}
          onRefresh={() => void refreshData()}
          onLogout={handleLogout}
          loading={loading}
        />

        {notice && <NoticeBanner notice={notice} />}

        {!auth.accessToken && (
          <LoginPanel
            onLogin={(email, password) => void handleLogin(email, password)}
            loading={loading}
          />
        )}

        {view === "overview" && (
          <Overview
            metrics={metrics}
            invoices={filteredInvoices}
            reviews={filteredReviews}
            customers={filteredCustomers}
            usingSampleData={usingSampleData}
          />
        )}
        {view === "upload" && (
          <UploadPanel
            customers={filteredCustomers}
            loading={loading}
            onUpload={(file, customerId) => void handleUpload(file, customerId)}
          />
        )}
        {view === "invoices" && <InvoicesPanel invoices={filteredInvoices} />}
        {view === "reviews" && (
          <ReviewsPanel reviews={filteredReviews} onAction={handleReviewAction} />
        )}
        {view === "evidence" && <EvidencePanel reviews={filteredReviews} invoices={filteredInvoices} />}
        {view === "customers" && <CustomersPanel customers={filteredCustomers} />}
        {view === "settings" && <SettingsPanel health={health} apiBaseUrl={apiBaseUrl} />}
      </main>
    </div>
  );
}

function Sidebar({
  currentView,
  setView,
  selectedTenant,
  health,
  usingSampleData
}: {
  currentView: View;
  setView: (view: View) => void;
  selectedTenant?: Tenant;
  health: ApiHealth | null;
  usingSampleData: boolean;
}) {
  const items: { view: View; label: string; icon: string }[] = [
    { view: "overview", label: "Overview", icon: "◆" },
    { view: "upload", label: "Upload", icon: "↑" },
    { view: "invoices", label: "Invoices", icon: "□" },
    { view: "reviews", label: "Reviews", icon: "✓" },
    { view: "evidence", label: "Evidence", icon: "◎" },
    { view: "customers", label: "Customers", icon: "◌" },
    { view: "settings", label: "Settings", icon: "⚙" }
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">F</div>
        <div>
          <strong>Finplex AI</strong>
          <span>Invoice intelligence</span>
        </div>
      </div>

      <div className="workspace-card">
        <span className="eyebrow">Workspace</span>
        <strong>{selectedTenant?.name || "No workspace"}</strong>
        <small>{selectedTenant?.erp_provider || "ERP"} · {selectedTenant?.crm_provider || "CRM"}</small>
      </div>

      <nav className="nav-list" aria-label="Dashboard navigation">
        {items.map((item) => (
          <button
            className={item.view === currentView ? "nav-item active" : "nav-item"}
            key={item.view}
            onClick={() => setView(item.view)}
          >
            <span>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <StatusPill label="API" value={health?.status || "offline"} tone={health?.status === "ok" ? "good" : "muted"} />
        {usingSampleData && <StatusPill label="Data" value="sample" tone="warn" />}
      </div>
    </aside>
  );
}

function Topbar({
  user,
  tenants,
  selectedTenantId,
  onTenantChange,
  onRefresh,
  onLogout,
  loading
}: {
  user: UserProfile | null;
  tenants: Tenant[];
  selectedTenantId: string;
  onTenantChange: (tenantId: string) => void;
  onRefresh: () => void;
  onLogout: () => void;
  loading: boolean;
}) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">Command center</span>
        <h1>Accounts Receivable AI Dashboard</h1>
      </div>
      <div className="topbar-actions">
        <select value={selectedTenantId} onChange={(event) => onTenantChange(event.target.value)}>
          {tenants.map((tenant) => (
            <option value={tenant.tenant_id} key={tenant.tenant_id}>{tenant.name}</option>
          ))}
        </select>
        <button className="button ghost" onClick={onRefresh} disabled={loading}>{loading ? "Loading" : "Refresh"}</button>
        {user ? (
          <div className="user-chip">
            <span>{user.full_name}</span>
            <small>{humanize(user.role)}</small>
            <button onClick={onLogout}>Sign out</button>
          </div>
        ) : (
          <span className="muted-text">Preview mode</span>
        )}
      </div>
    </header>
  );
}

function LoginPanel({ onLogin, loading }: { onLogin: (email: string, password: string) => void; loading: boolean }) {
  const [email, setEmail] = useState("manager@example.com");
  const [password, setPassword] = useState("password123");

  function submit(event: FormEvent) {
    event.preventDefault();
    onLogin(email, password);
  }

  return (
    <section className="login-panel">
      <div>
        <span className="eyebrow">Secure access</span>
        <h2>Sign in to work with live invoices</h2>
        <p>
          The dashboard can be reviewed in sample mode, but upload, approve, and reject actions require a live backend token.
        </p>
      </div>
      <form className="login-form" onSubmit={submit}>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
        </label>
        <label>
          Password
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
        </label>
        <button className="button primary" disabled={loading}>{loading ? "Signing in" : "Sign in"}</button>
      </form>
    </section>
  );
}

function Overview({
  metrics,
  invoices,
  reviews,
  customers,
  usingSampleData
}: {
  metrics: { totalAmount: number; pendingReviews: number; highRiskReviews: number; guardrailsRate: number; evidenceCount: number };
  invoices: Invoice[];
  reviews: Review[];
  customers: Customer[];
  usingSampleData: boolean;
}) {
  return (
    <section className="page-stack">
      <div className="hero-card">
        <div>
          <span className="eyebrow">Responsible automation</span>
          <h2>Invoice follow-up decisions, evidence, and approvals in one clear workspace.</h2>
          <p>
            Finplex AI helps teams move from invoice upload to AI-assisted review without exposing technical JSON or raw model output to business users.
          </p>
        </div>
        <div className="hero-metrics">
          <strong>{metrics.guardrailsRate}%</strong>
          <span>Guardrails pass rate</span>
        </div>
      </div>

      {usingSampleData && (
        <div className="soft-alert">
          You are viewing a polished sample workspace. Sign in and refresh to use live backend data.
        </div>
      )}

      <div className="metric-grid">
        <MetricCard title="Open invoice value" value={formatCurrency(metrics.totalAmount)} detail="Across the selected workspace" />
        <MetricCard title="Pending reviews" value={String(metrics.pendingReviews)} detail="Drafts waiting for human approval" />
        <MetricCard title="High risk drafts" value={String(metrics.highRiskReviews)} detail="Needs careful review before sending" />
        <MetricCard title="Evidence links" value={String(metrics.evidenceCount)} detail="Traceable citation IDs available" />
      </div>

      <div className="two-column">
        <Panel title="Recent invoices" subtitle="Human-readable status from the processing workflow.">
          <InvoiceList invoices={invoices.slice(0, 4)} compact />
        </Panel>
        <Panel title="Review queue" subtitle="Drafts are never sent without approval.">
          <ReviewList reviews={reviews.slice(0, 3)} />
        </Panel>
      </div>

      <Panel title="Customer context" subtitle="CRM and relationship context for non-technical users.">
        <div className="customer-strip">
          {customers.map((customer) => (
            <article key={customer.customer_id} className="customer-card">
              <strong>{customer.company_name}</strong>
              <span>{customer.contact_name || "No contact"}</span>
              <small>{humanize(customer.relationship_status)}</small>
            </article>
          ))}
        </div>
      </Panel>
    </section>
  );
}

function UploadPanel({
  customers,
  loading,
  onUpload
}: {
  customers: Customer[];
  loading: boolean;
  onUpload: (file: File, customerId?: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [customerId, setCustomerId] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    if (file) {
      onUpload(file, customerId || undefined);
    }
  }

  return (
    <section className="page-stack">
      <Panel title="Upload invoice" subtitle="The backend stores the file, publishes a Kafka event, then the worker runs extraction, risk scoring, Hybrid RAG, guardrails, and review creation.">
        <form className="upload-box" onSubmit={submit}>
          <label className="drop-zone">
            <input type="file" accept=".pdf,.png,.jpg,.jpeg,.txt" onChange={(event) => setFile(event.target.files?.[0] || null)} />
            <span>{file ? file.name : "Choose an invoice file"}</span>
            <small>PDF, PNG, JPG, or TXT for local demo testing</small>
          </label>
          <label>
            Optional customer link
            <select value={customerId} onChange={(event) => setCustomerId(event.target.value)}>
              <option value="">Let AI/customer matching decide</option>
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>{customer.company_name}</option>
              ))}
            </select>
          </label>
          <button className="button primary" disabled={!file || loading}>{loading ? "Uploading" : "Upload and process"}</button>
        </form>
      </Panel>
    </section>
  );
}

function InvoicesPanel({ invoices }: { invoices: Invoice[] }) {
  return (
    <section className="page-stack">
      <Panel title="Invoices" subtitle="Clear invoice status for finance users and demo reviewers.">
        <InvoiceList invoices={invoices} />
      </Panel>
    </section>
  );
}

function ReviewsPanel({ reviews, onAction }: { reviews: Review[]; onAction: (reviewId: string, action: "approve" | "reject" | "changes", comment: string) => void }) {
  return (
    <section className="page-stack">
      <Panel title="Human review queue" subtitle="Approve, reject, or request changes without viewing raw JSON.">
        <div className="review-grid">
          {reviews.map((review) => (
            <ReviewCard key={review.review_id} review={review} onAction={onAction} />
          ))}
        </div>
      </Panel>
    </section>
  );
}

function EvidencePanel({ reviews, invoices }: { reviews: Review[]; invoices: Invoice[] }) {
  const evidenceIds = Array.from(new Set([...reviews.flatMap((review) => review.evidence_ids), ...invoices.flatMap((invoice) => invoice.evidence_ids || [])]));

  return (
    <section className="page-stack">
      <Panel title="Evidence center" subtitle="Traceable citation IDs used by Hybrid RAG, draft generation, and guardrails.">
        <div className="evidence-grid">
          {evidenceIds.map((id, index) => (
            <article className="evidence-card" key={id}>
              <span className="evidence-icon">EV</span>
              <div>
                <strong>{id}</strong>
                <p>{evidenceDescription(index)}</p>
              </div>
            </article>
          ))}
        </div>
      </Panel>
    </section>
  );
}

function CustomersPanel({ customers }: { customers: Customer[] }) {
  return (
    <section className="page-stack">
      <Panel title="Customers" subtitle="CRM-friendly view of customers connected to invoices and review decisions.">
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Contact</th>
                <th>Email</th>
                <th>Status</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((customer) => (
                <tr key={customer.customer_id}>
                  <td>{customer.company_name}</td>
                  <td>{customer.contact_name || "—"}</td>
                  <td>{customer.contact_email || "—"}</td>
                  <td><StatusPill label="" value={humanize(customer.relationship_status)} tone="muted" /></td>
                  <td>{customer.tags?.join(", ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </section>
  );
}

function SettingsPanel({ health, apiBaseUrl }: { health: ApiHealth | null; apiBaseUrl: string }) {
  return (
    <section className="page-stack">
      <Panel title="Settings" subtitle="Non-technical status summary for the local demo environment.">
        <div className="settings-grid">
          <SettingRow label="API base URL" value={apiBaseUrl} />
          <SettingRow label="API status" value={health?.status || "offline"} />
          <SettingRow label="Environment" value={health?.environment || "local"} />
          <SettingRow label="UI mode" value="Professional dashboard" />
          <SettingRow label="Raw JSON in UI" value="Hidden" />
        </div>
      </Panel>
    </section>
  );
}

function InvoiceList({ invoices, compact = false }: { invoices: Invoice[]; compact?: boolean }) {
  if (!invoices.length) {
    return <EmptyState title="No invoices yet" message="Upload an invoice to start the AI workflow." />;
  }

  return (
    <div className="invoice-list">
      {invoices.map((invoice) => {
        const fields = invoice.extracted_fields || {};
        return (
          <article className="invoice-row" key={invoice.invoice_id}>
            <div>
              <strong>{fields.invoice_number || invoice.file_name}</strong>
              <span>{fields.customer_name || "Customer not extracted yet"}</span>
            </div>
            {!compact && <span>{formatDate(fields.due_date as string | undefined)}</span>}
            <span>{formatCurrency(fields.amount_due as number | undefined, (fields.currency as string | undefined) || "USD")}</span>
            <StatusPill label="" value={humanize(invoice.status)} tone={invoice.status === "review_pending" ? "warn" : invoice.status === "failed" ? "bad" : "muted"} />
          </article>
        );
      })}
    </div>
  );
}

function ReviewList({ reviews }: { reviews: Review[] }) {
  if (!reviews.length) {
    return <EmptyState title="No reviews waiting" message="When AI drafts are ready, they will appear here." />;
  }

  return (
    <div className="compact-review-list">
      {reviews.map((review) => (
        <div className="compact-review" key={review.review_id}>
          <RiskBadge level={review.risk_level} />
          <div>
            <strong>{review.invoice_id}</strong>
            <span>{review.guardrails_passed ? "Guardrails passed" : "Needs rewrite"}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function ReviewCard({ review, onAction }: { review: Review; onAction: (reviewId: string, action: "approve" | "reject" | "changes", comment: string) => void }) {
  const [comment, setComment] = useState("Reviewed by manager.");

  return (
    <article className="review-card">
      <div className="review-card-header">
        <div>
          <span className="eyebrow">Invoice</span>
          <h3>{review.invoice_id}</h3>
        </div>
        <RiskBadge level={review.risk_level} />
      </div>
      <div className="guardrail-line">
        <StatusPill label="Guardrails" value={review.guardrails_passed ? "passed" : "blocked"} tone={review.guardrails_passed ? "good" : "bad"} />
        <StatusPill label="Evidence" value={`${review.evidence_ids.length} citations`} tone="muted" />
      </div>
      <div className="draft-preview">
        {review.draft_message.split("\n").filter(Boolean).map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
      <div className="evidence-tags">
        {review.evidence_ids.map((id) => <span key={id}>{id}</span>)}
      </div>
      <label className="comment-box">
        Review note
        <textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={3} />
      </label>
      <div className="review-actions">
        <button className="button primary" onClick={() => onAction(review.review_id, "approve", comment)}>Approve</button>
        <button className="button ghost" onClick={() => onAction(review.review_id, "changes", comment)}>Request changes</button>
        <button className="button danger" onClick={() => onAction(review.review_id, "reject", comment)}>Reject</button>
      </div>
    </article>
  );
}

function MetricCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <article className="metric-card">
      <span>{title}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function Panel({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="panel-card">
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function NoticeBanner({ notice }: { notice: Notice }) {
  return <div className={`notice ${notice.kind}`}>{notice.message}</div>;
}

function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}

function StatusPill({ label, value, tone }: { label: string; value: string; tone: "good" | "warn" | "bad" | "muted" }) {
  return <span className={`status-pill ${tone}`}>{label ? `${label}: ` : ""}{value}</span>;
}

function RiskBadge({ level }: { level: string }) {
  const normalized = String(level).toLowerCase();
  const tone = normalized === "high" || normalized === "critical" ? "bad" : normalized === "medium" ? "warn" : "good";
  return <span className={`risk-badge ${tone}`}>{riskLabel(level)} risk</span>;
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="setting-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function evidenceDescription(index: number) {
  const descriptions = [
    "Invoice evidence extracted from the uploaded document.",
    "ERP/payment evidence used to explain late-payment risk.",
    "CRM context used to detect dispute or support signals.",
    "Policy evidence used by guardrails and human review.",
    "Hybrid RAG citation available for dashboard explanation."
  ];

  return descriptions[index % descriptions.length];
}

function friendlyError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message || fallback;
  }
  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
}

export default App;
