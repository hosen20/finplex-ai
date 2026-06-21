from enum import Enum


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"


class InvoiceStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    SCORED = "scored"
    DRAFTED = "drafted"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceSource(str, Enum):
    INVOICE = "invoice"
    ERP = "erp"
    CRM = "crm"
    RAG = "rag"
    GUARDRAILS = "guardrails"


class AuditAction(str, Enum):
    TENANT_CREATED = "tenant_created"
    TENANT_SUSPENDED = "tenant_suspended"
    TENANT_REACTIVATED = "tenant_reactivated"
    USER_CREATED = "user_created"
    INVOICE_UPLOADED = "invoice_uploaded"
    INVOICE_PROCESSED = "invoice_processed"
    DRAFT_CREATED = "draft_created"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_REJECTED = "draft_rejected"
    GUARDRAILS_CHECKED = "guardrails_checked"
