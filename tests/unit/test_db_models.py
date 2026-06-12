from app.domain.enums import InvoiceStatus, PaymentStatus, TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_database_models_can_create_and_query_records() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        tenant = TenantModel(
            tenant_id="tenant_acme",
            name="Acme",
            status=TenantStatus.ACTIVE,
            erp_provider="local",
            crm_provider="local",
        )
        user = UserModel(
            user_id="user_001",
            tenant_id="tenant_acme",
            email="admin@acme.com",
            full_name="Admin User",
            hashed_password="not-real",
            role=UserRole.TENANT_ADMIN,
            is_active=True,
        )
        invoice = InvoiceModel(
            invoice_id="inv_001",
            tenant_id="tenant_acme",
            uploaded_by_user_id="user_001",
            file_name="invoice.pdf",
            storage_key="tenant_acme/invoices/invoice.pdf",
            status=InvoiceStatus.UPLOADED,
            payment_status=PaymentStatus.UNPAID,
            evidence_ids=[],
        )

        session.add_all([tenant, user, invoice])
        session.commit()

        result = session.scalar(
            select(InvoiceModel).where(InvoiceModel.invoice_id == "inv_001")
        )

        assert result is not None
        assert result.tenant_id == "tenant_acme"
        assert result.status == InvoiceStatus.UPLOADED