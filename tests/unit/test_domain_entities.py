from datetime import date
from decimal import Decimal

import pytest
from app.domain.entities.erp_record import ERPInvoiceRecord
from app.domain.entities.invoice import Invoice, InvoiceExtractedFields
from app.domain.entities.review import Review
from app.domain.entities.tenant import Tenant
from app.domain.enums import InvoiceStatus, PaymentStatus, RiskLevel, TenantStatus
from app.domain.exceptions import (
    InvalidStateTransitionError,
    MissingEvidenceError,
    TenantSuspendedError,
)


def test_suspended_tenant_is_not_active() -> None:
    tenant = Tenant(
        tenant_id="tenant_acme",
        name="Acme",
        status=TenantStatus.SUSPENDED,
    )

    with pytest.raises(TenantSuspendedError):
        tenant.require_active()


def test_erp_invoice_outstanding_amount_and_overdue_days() -> None:
    record = ERPInvoiceRecord(
        erp_invoice_id="erp_inv_001",
        tenant_id="tenant_acme",
        customer_id="cust_001",
        invoice_number="INV-001",
        amount_due=Decimal("1000.00"),
        currency="USD",
        due_date=date(2026, 1, 10),
        payment_status=PaymentStatus.PARTIALLY_PAID,
        total_paid=Decimal("250.00"),
    )

    assert record.outstanding_amount == Decimal("750.00")
    assert record.days_overdue(date(2026, 1, 20)) == 10
    assert record.is_overdue(date(2026, 1, 20)) is True


def test_invoice_attach_extracted_fields_moves_status_to_extracted() -> None:
    invoice = Invoice(
        invoice_id="inv_001",
        tenant_id="tenant_acme",
        uploaded_by_user_id="user_001",
        file_name="invoice.pdf",
        storage_key="tenant_acme/invoices/invoice.pdf",
    )

    invoice.mark_processing()
    invoice.attach_extracted_fields(
        InvoiceExtractedFields(
            invoice_number="INV-001",
            customer_name="Acme Customer",
            amount_due=Decimal("500.00"),
            currency="USD",
            confidence=0.91,
        )
    )

    assert invoice.status == InvoiceStatus.EXTRACTED
    assert invoice.extracted_fields is not None
    assert invoice.extracted_fields.is_confident() is True


def test_review_cannot_be_approved_without_evidence() -> None:
    review = Review(
        review_id="review_001",
        tenant_id="tenant_acme",
        invoice_id="inv_001",
        draft_message="Please review the overdue invoice.",
        risk_level=RiskLevel.MEDIUM,
        guardrails_passed=True,
    )

    with pytest.raises(MissingEvidenceError):
        review.approve(reviewer_user_id="reviewer_001")


def test_review_cannot_be_approved_if_guardrails_failed() -> None:
    review = Review(
        review_id="review_001",
        tenant_id="tenant_acme",
        invoice_id="inv_001",
        draft_message="Bad draft.",
        risk_level=RiskLevel.HIGH,
        guardrails_passed=False,
        evidence_ids=["ev_001"],
    )

    with pytest.raises(InvalidStateTransitionError):
        review.approve(reviewer_user_id="reviewer_001")