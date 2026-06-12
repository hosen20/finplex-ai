from app.application.services.customer_service import CustomerService
from app.application.services.invoice_service import InvoiceService
from app.application.services.review_service import ReviewService
from app.domain.enums import RiskLevel, TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def seed_tenant_and_user(session: Session) -> None:
    session.add(
        TenantModel(
            tenant_id="tenant_acme",
            name="Acme",
            status=TenantStatus.ACTIVE,
            erp_provider="local",
            crm_provider="local",
        )
    )
    session.add(
        UserModel(
            user_id="user_admin",
            tenant_id="tenant_acme",
            email="admin@acme.com",
            full_name="Admin User",
            hashed_password="not-real",
            role=UserRole.TENANT_ADMIN,
            is_active=True,
        )
    )
    session.commit()


def test_customer_and_invoice_services_create_records() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_tenant_and_user(session)

        customer = CustomerService(session).create_customer(
            tenant_id="tenant_acme",
            actor_user_id="user_admin",
            company_name="Acme Customer",
            contact_name="Rana",
            contact_email="rana@example.com",
            tags=["late_payer"],
        )

        invoice = InvoiceService(session).create_invoice_metadata(
            tenant_id="tenant_acme",
            actor_user_id="user_admin",
            customer_id=customer.customer_id,
            file_name="invoice.pdf",
            storage_key="tenant_acme/invoices/invoice.pdf",
        )

        assert customer.customer_id.startswith("cust_")
        assert invoice.invoice_id.startswith("inv_")
        assert invoice.customer_id == customer.customer_id


def test_review_service_approves_review_with_evidence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_tenant_and_user(session)

        invoice = InvoiceService(session).create_invoice_metadata(
            tenant_id="tenant_acme",
            actor_user_id="user_admin",
            file_name="invoice.pdf",
            storage_key="tenant_acme/invoices/invoice.pdf",
        )

        review = ReviewService(session).create_review(
            tenant_id="tenant_acme",
            invoice_id=invoice.invoice_id,
            draft_message="Please review the overdue invoice.",
            risk_level=RiskLevel.MEDIUM,
            guardrails_passed=True,
            evidence_ids=["ev_001"],
        )

        approved = ReviewService(session).approve_review(
            review_id=review.review_id,
            actor_user_id="user_admin",
            comment="Approved.",
        )

        assert approved.reviewer_user_id == "user_admin"
        assert approved.reviewer_comment == "Approved."