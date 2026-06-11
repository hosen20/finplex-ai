import pytest
from app.domain.entities.invoice import Invoice
from app.domain.entities.review import Review
from app.domain.entities.tenant import Tenant
from app.domain.entities.user import User
from app.domain.enums import RiskLevel, UserRole
from app.domain.exceptions import CrossTenantAccessError, PermissionDeniedError
from app.domain.policies.invoice_policy import InvoicePolicy
from app.domain.policies.review_policy import ReviewPolicy
from app.domain.policies.tenant_policy import TenantPolicy


def test_tenant_policy_blocks_cross_tenant_access() -> None:
    actor = User(
        user_id="user_001",
        tenant_id="tenant_acme",
        email="admin@acme.com",
        full_name="Admin",
        role=UserRole.TENANT_ADMIN,
    )

    with pytest.raises(CrossTenantAccessError):
        TenantPolicy.ensure_same_tenant(actor, "tenant_other")


def test_tenant_admin_can_manage_own_tenant() -> None:
    actor = User(
        user_id="user_001",
        tenant_id="tenant_acme",
        email="admin@acme.com",
        full_name="Admin",
        role=UserRole.TENANT_ADMIN,
    )

    TenantPolicy.ensure_can_manage_tenant(actor, "tenant_acme")


def test_reviewer_can_review_own_tenant_review() -> None:
    actor = User(
        user_id="reviewer_001",
        tenant_id="tenant_acme",
        email="reviewer@acme.com",
        full_name="Reviewer",
        role=UserRole.REVIEWER,
    )
    review = Review(
        review_id="review_001",
        tenant_id="tenant_acme",
        invoice_id="inv_001",
        draft_message="Draft message",
        risk_level=RiskLevel.LOW,
        guardrails_passed=True,
        evidence_ids=["ev_001"],
    )

    ReviewPolicy.ensure_can_review(actor, review)


def test_auditor_cannot_approve_or_reject_review() -> None:
    actor = User(
        user_id="auditor_001",
        tenant_id="tenant_acme",
        email="auditor@acme.com",
        full_name="Auditor",
        role=UserRole.AUDITOR,
    )
    review = Review(
        review_id="review_001",
        tenant_id="tenant_acme",
        invoice_id="inv_001",
        draft_message="Draft message",
        risk_level=RiskLevel.LOW,
        guardrails_passed=True,
        evidence_ids=["ev_001"],
    )

    with pytest.raises(PermissionDeniedError):
        ReviewPolicy.ensure_can_review(actor, review)


def test_invoice_policy_allows_active_user_to_upload_to_own_tenant() -> None:
    tenant = Tenant(tenant_id="tenant_acme", name="Acme")
    actor = User(
        user_id="user_001",
        tenant_id="tenant_acme",
        email="user@acme.com",
        full_name="User",
        role=UserRole.MANAGER,
    )

    InvoicePolicy.ensure_can_upload(actor, tenant)


def test_invoice_policy_blocks_cross_tenant_invoice_view() -> None:
    actor = User(
        user_id="user_001",
        tenant_id="tenant_acme",
        email="user@acme.com",
        full_name="User",
        role=UserRole.MANAGER,
    )
    invoice = Invoice(
        invoice_id="inv_001",
        tenant_id="tenant_other",
        uploaded_by_user_id="user_999",
        file_name="invoice.pdf",
        storage_key="tenant_other/invoices/invoice.pdf",
    )

    with pytest.raises(CrossTenantAccessError):
        InvoicePolicy.ensure_can_view(actor, invoice)