from app.domain.enums import InvoiceStatus, PaymentStatus, TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.repositories.invoice_repository import InvoiceRepository
from app.infrastructure.db.repositories.tenant_repository import TenantRepository
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_tenant_repository_adds_and_gets_tenant() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = TenantRepository(session)
        repository.add(
            TenantModel(
                tenant_id="tenant_acme",
                name="Acme",
                status=TenantStatus.ACTIVE,
                erp_provider="local",
                crm_provider="local",
            )
        )
        session.commit()

        tenant = repository.get("tenant_acme")

        assert tenant is not None
        assert tenant.name == "Acme"


def test_invoice_repository_lists_invoices_by_tenant() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
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
                user_id="user_001",
                tenant_id="tenant_acme",
                email="admin@acme.com",
                full_name="Admin User",
                hashed_password="not-real",
                role=UserRole.TENANT_ADMIN,
                is_active=True,
            )
        )
        session.add(
            InvoiceModel(
                invoice_id="inv_001",
                tenant_id="tenant_acme",
                uploaded_by_user_id="user_001",
                file_name="invoice.pdf",
                storage_key="tenant_acme/invoices/invoice.pdf",
                status=InvoiceStatus.UPLOADED,
                payment_status=PaymentStatus.UNPAID,
                evidence_ids=[],
            )
        )
        session.commit()

        repository = InvoiceRepository(session)
        invoices = repository.list_by_tenant("tenant_acme")

        assert len(invoices) == 1
        assert invoices[0].invoice_id == "inv_001"