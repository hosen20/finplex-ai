from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "services" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.database import SessionLocal  # noqa: E402
from app.domain.enums import (  # noqa: E402
    AuditAction,
    PaymentStatus,
    TenantStatus,
    UserRole,
)
from app.infrastructure.db.models.audit_model import AuditEventModel  # noqa: E402
from app.infrastructure.db.models.crm_model import (  # noqa: E402
    CRMDisputeModel,
    CRMNoteModel,
)
from app.infrastructure.db.models.customer_model import CustomerModel  # noqa: E402
from app.infrastructure.db.models.erp_model import (  # noqa: E402
    ERPInvoiceModel,
    ERPPaymentModel,
)
from app.infrastructure.db.models.invoice_model import InvoiceModel  # noqa: E402
from app.infrastructure.db.models.rag_model import (  # noqa: E402
    RagChunkModel,
    RagDocumentModel,
)
from app.infrastructure.db.models.review_model import ReviewModel  # noqa: E402
from app.infrastructure.db.models.tenant_model import TenantModel  # noqa: E402
from app.infrastructure.db.models.user_model import UserModel  # noqa: E402
from app.security import hash_password  # noqa: E402

TENANT_ID = "tenant_demo_clinic"
TENANT_NAME = "Finplex Demo Clinic Group"
ADMIN_USER_ID = "user_demo_admin"
MANAGER_USER_ID = "user_demo_manager"
ADMIN_EMAIL = "clinadmin@example.com"
MANAGER_EMAIL = "manager@example.com"
DEMO_PASSWORD = "FinplexDemo123!"

CUSTOMERS = [
    {
        "customer_id": "cust_demo_accept",
        "company_name": "Aurora Medical Supplies",
        "contact_name": "Maya Haddad",
        "contact_email": "maya.haddad@aurora-demo.example",
        "relationship_status": "watchlist",
        "tags": ["manual-upload-demo", "accept-path", "slow-payer"],
    },
    {
        "customer_id": "cust_demo_reject",
        "company_name": "Northstar Diagnostics Lab",
        "contact_name": "Karim Saleh",
        "contact_email": "karim.saleh@northstar-demo.example",
        "relationship_status": "disputed",
        "tags": ["manual-upload-demo", "reject-path", "open-dispute"],
    },
]

ERP_INVOICES = [
    {
        "erp_invoice_id": "erp_manual_accept_001",
        "customer_id": "cust_demo_accept",
        "invoice_number": "NEW-00001",
        "amount_due": Decimal("12450.00"),
        "currency": "USD",
        "due_date": date.today() - timedelta(days=18),
        "payment_status": PaymentStatus.OVERDUE,
        "total_paid": Decimal("0.00"),
        "payment_terms_days": 30,
    },
    {
        "erp_invoice_id": "erp_manual_reject_002",
        "customer_id": "cust_demo_reject",
        "invoice_number": "NEW-00002",
        "amount_due": Decimal("7380.00"),
        "currency": "USD",
        "due_date": date.today() - timedelta(days=12),
        "payment_status": PaymentStatus.DISPUTED,
        "total_paid": Decimal("0.00"),
        "payment_terms_days": 30,
    },
]

CRM_NOTES = [
    {
        "note_id": "crm_manual_accept_note_001",
        "customer_id": "cust_demo_accept",
        "body": (
            "Customer is late but usually cooperative. Use a respectful "
            "follow-up and include invoice details. This is suitable for "
            "approval if the draft remains factual and polite."
        ),
    },
    {
        "note_id": "crm_manual_reject_note_002",
        "customer_id": "cust_demo_reject",
        "body": (
            "Customer has an open dispute and requested no pressure language. "
            "A human reviewer should reject or request changes if the draft "
            "does not clearly acknowledge the dispute."
        ),
    },
]

CRM_DISPUTES = [
    {
        "dispute_id": "crm_manual_reject_dispute_002",
        "customer_id": "cust_demo_reject",
        "invoice_number": "NEW-00002",
        "reason": (
            "Open dispute about diagnostic equipment line-item pricing. "
            "Follow-up must acknowledge the dispute and offer clarification."
        ),
        "is_open": True,
    },
]

RAG_DOCUMENTS = [
    {
        "document_id": "rag_manual_policy_001",
        "title": "Responsible Follow-Up Policy",
        "source_type": "regulation",
        "storage_key": "regulations/manual_demo/responsible_followup.md",
        "chunks": [
            (
                "ev_manual_policy_respectful_followup",
                "Follow-up messages must be respectful, factual, non-threatening, "
                "and must offer clarification when there is an open dispute.",
            )
        ],
    },
    {
        "document_id": "rag_manual_erp_001",
        "title": "Manual Upload Demo ERP Evidence",
        "source_type": "erp",
        "storage_key": "data/seed/manual_demo_erp_invoices.csv",
        "chunks": [
            (
                "ev_manual_erp_new_00001",
                "ERP shows invoice NEW-00001 for Aurora Medical Supplies is "
                "overdue with an open balance of 12450.00 USD.",
            ),
            (
                "ev_manual_erp_new_00002",
                "ERP shows invoice NEW-00002 for Northstar Diagnostics Lab is "
                "marked disputed with an open balance of 7380.00 USD.",
            ),
        ],
    },
    {
        "document_id": "rag_manual_crm_001",
        "title": "Manual Upload Demo CRM Evidence",
        "source_type": "crm",
        "storage_key": "data/seed/manual_demo_crm_context.csv",
        "chunks": [
            (
                "ev_manual_crm_accept_customer",
                "CRM shows Aurora Medical Supplies is cooperative and suitable "
                "for a polite factual follow-up.",
            ),
            (
                "ev_manual_crm_reject_customer",
                "CRM shows Northstar Diagnostics Lab has an open dispute and "
                "requires a clarification-first tone.",
            ),
        ],
    },
]


def main() -> None:
    with SessionLocal() as session:
        reset_manual_demo(session)
        session.commit()

        seed_tenant(session)
        session.commit()

        seed_users(session)
        session.commit()

        seed_customers(session)
        session.commit()

        seed_erp(session)
        session.commit()

        seed_crm(session)
        session.commit()

        seed_rag_documents(session)
        session.commit()

        seed_audit(session)
        session.commit()

    print_success_summary()


def reset_manual_demo(session) -> None:
    print("Resetting manual upload demo context...")
    session.query(ReviewModel).filter(ReviewModel.tenant_id == TENANT_ID).delete(
        synchronize_session=False
    )
    session.query(AuditEventModel).filter(
        AuditEventModel.tenant_id == TENANT_ID
    ).delete(synchronize_session=False)
    session.query(RagChunkModel).filter(RagChunkModel.tenant_id == TENANT_ID).delete(
        synchronize_session=False
    )
    session.query(RagDocumentModel).filter(
        RagDocumentModel.tenant_id == TENANT_ID
    ).delete(synchronize_session=False)
    session.query(CRMDisputeModel).filter(
        CRMDisputeModel.tenant_id == TENANT_ID
    ).delete(synchronize_session=False)
    session.query(CRMNoteModel).filter(CRMNoteModel.tenant_id == TENANT_ID).delete(
        synchronize_session=False
    )
    session.query(ERPPaymentModel).filter(
        ERPPaymentModel.tenant_id == TENANT_ID
    ).delete(synchronize_session=False)
    session.query(ERPInvoiceModel).filter(
        ERPInvoiceModel.tenant_id == TENANT_ID
    ).delete(synchronize_session=False)
    session.query(InvoiceModel).filter(InvoiceModel.tenant_id == TENANT_ID).delete(
        synchronize_session=False
    )
    session.query(CustomerModel).filter(CustomerModel.tenant_id == TENANT_ID).delete(
        synchronize_session=False
    )
    session.query(UserModel).filter(
        UserModel.email.in_([ADMIN_EMAIL, MANAGER_EMAIL])
    ).delete(synchronize_session=False)
    session.query(TenantModel).filter(TenantModel.tenant_id == TENANT_ID).delete(
        synchronize_session=False
    )


def seed_tenant(session) -> None:
    session.add(
        TenantModel(
            tenant_id=TENANT_ID,
            name=TENANT_NAME,
            status=TenantStatus.ACTIVE.name,
            erp_provider="local-demo",
            crm_provider="local-demo",
        )
    )


def seed_users(session) -> None:
    password_hash = hash_password(DEMO_PASSWORD)
    session.add_all(
        [
            UserModel(
                user_id=ADMIN_USER_ID,
                tenant_id=TENANT_ID,
                email=ADMIN_EMAIL,
                full_name="Clinical Admin Demo",
                hashed_password=password_hash,
                role=UserRole.TENANT_ADMIN.name,
                is_active=True,
            ),
            UserModel(
                user_id=MANAGER_USER_ID,
                tenant_id=TENANT_ID,
                email=MANAGER_EMAIL,
                full_name="Operations Manager Demo",
                hashed_password=password_hash,
                role=UserRole.MANAGER.name,
                is_active=True,
            ),
        ]
    )


def seed_customers(session) -> None:
    for customer in CUSTOMERS:
        session.add(
            CustomerModel(
                tenant_id=TENANT_ID,
                preferred_contact_channel="email",
                **customer,
            )
        )


def seed_erp(session) -> None:
    for invoice in ERP_INVOICES:
        session.add(
            ERPInvoiceModel(
                erp_invoice_id=invoice["erp_invoice_id"],
                tenant_id=TENANT_ID,
                customer_id=invoice["customer_id"],
                invoice_number=invoice["invoice_number"],
                amount_due=invoice["amount_due"],
                currency=invoice["currency"],
                due_date=invoice["due_date"],
                payment_status=invoice["payment_status"].name,
                total_paid=invoice["total_paid"],
                payment_terms_days=invoice["payment_terms_days"],
            )
        )
    session.flush()

    session.add(
        ERPPaymentModel(
            payment_id="pay_manual_demo_none_001",
            tenant_id=TENANT_ID,
            customer_id="cust_demo_accept",
            erp_invoice_id="erp_manual_accept_001",
            amount=Decimal("0.00"),
            currency="USD",
            paid_at=date.today() - timedelta(days=1),
        )
    )


def seed_crm(session) -> None:
    for note in CRM_NOTES:
        session.add(
            CRMNoteModel(
                note_id=note["note_id"],
                tenant_id=TENANT_ID,
                customer_id=note["customer_id"],
                author_user_id=MANAGER_USER_ID,
                body=note["body"],
            )
        )

    for dispute in CRM_DISPUTES:
        session.add(
            CRMDisputeModel(
                dispute_id=dispute["dispute_id"],
                tenant_id=TENANT_ID,
                customer_id=dispute["customer_id"],
                invoice_number=dispute["invoice_number"],
                reason=dispute["reason"],
                is_open=dispute["is_open"],
            )
        )


def seed_rag_documents(session) -> None:
    for document in RAG_DOCUMENTS:
        session.add(
            RagDocumentModel(
                document_id=document["document_id"],
                tenant_id=TENANT_ID,
                title=document["title"],
                source_type=document["source_type"],
                storage_key=document["storage_key"],
            )
        )
        session.flush()

        for index, (chunk_id, content) in enumerate(document["chunks"]):
            session.add(
                RagChunkModel(
                    chunk_id=chunk_id,
                    tenant_id=TENANT_ID,
                    document_id=document["document_id"],
                    content=content,
                    chunk_index=index,
                    embedding={"demo": True, "source_type": document["source_type"]},
                )
            )


def seed_audit(session) -> None:
    session.add(
        AuditEventModel(
            audit_event_id="audit_manual_demo_context_seeded",
            tenant_id=TENANT_ID,
            action=AuditAction.TENANT_CREATED.name,
            actor_user_id=ADMIN_USER_ID,
            entity_type="tenant",
            entity_id=TENANT_ID,
            trace_id="trace_manual_demo_context_seeded",
            metadata_json={"demo_type": "manual_upload_e2e"},
        )
    )


def print_success_summary() -> None:
    summary = {
        "tenant_id": TENANT_ID,
        "tenant_name": TENANT_NAME,
        "admin_email": ADMIN_EMAIL,
        "manager_email": MANAGER_EMAIL,
        "password": DEMO_PASSWORD,
        "seeded_customers": len(CUSTOMERS),
        "seeded_erp_invoices": len(ERP_INVOICES),
        "seeded_reviews": 0,
        "upload_invoice_1": "data/demo_invoices/manual_upload_images/NEW-00001.png",
        "upload_invoice_2": "data/demo_invoices/manual_upload_images/NEW-00002.png",
    }
    print("\nManual upload demo context is ready.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
