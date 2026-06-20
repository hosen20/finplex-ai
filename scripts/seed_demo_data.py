from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "services" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.domain.enums import (  # noqa: E402
    AuditAction,
    InvoiceStatus,
    PaymentStatus,
    ReviewStatus,
    RiskLevel,
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
DEMO_PASSWORD = "FinplexDemo123!"
ADMIN_USER_ID = "user_demo_admin"
MANAGER_USER_ID = "user_demo_manager"
ADMIN_EMAIL = "clinadmin@example.com"
MANAGER_EMAIL = "manager@example.com"

DEMO_CUSTOMERS = [
    {
        "customer_id": "cust_demo_aurora",
        "company_name": "Aurora Medical Supplies",
        "contact_name": "Maya Haddad",
        "contact_email": "maya.haddad@aurora-demo.example",
        "relationship_status": "at_risk",
        "tags": ["high-risk", "open-dispute", "priority-account"],
    },
    {
        "customer_id": "cust_demo_cedar",
        "company_name": "Cedar Retail Group",
        "contact_name": "Omar Nasser",
        "contact_email": "omar.nasser@cedar-demo.example",
        "relationship_status": "watchlist",
        "tags": ["medium-risk", "slow-payer"],
    },
    {
        "customer_id": "cust_demo_blueharbor",
        "company_name": "Blue Harbor Logistics",
        "contact_name": "Lina Farah",
        "contact_email": "lina.farah@blueharbor-demo.example",
        "relationship_status": "healthy",
        "tags": ["low-risk", "long-term-customer"],
    },
]

DEMO_INVOICES = [
    {
        "invoice_id": "inv_demo_high_001",
        "customer_id": "cust_demo_aurora",
        "erp_invoice_id": "erp_inv_demo_high_001",
        "file_name": "NEW-00001.png",
        "invoice_number": "NEW-00001",
        "amount_due": Decimal("12450.00"),
        "currency": "USD",
        "due_date": date.today() - timedelta(days=21),
        "payment_status": PaymentStatus.OVERDUE,
        "status": InvoiceStatus.REVIEW_PENDING,
        "risk_level": RiskLevel.HIGH,
        "risk_score": 0.87,
        "guardrails_passed": True,
    },
    {
        "invoice_id": "inv_demo_medium_001",
        "customer_id": "cust_demo_cedar",
        "erp_invoice_id": "erp_inv_demo_medium_001",
        "file_name": "NEW-00002.png",
        "invoice_number": "NEW-00002",
        "amount_due": Decimal("4720.50"),
        "currency": "USD",
        "due_date": date.today() - timedelta(days=6),
        "payment_status": PaymentStatus.PARTIALLY_PAID,
        "status": InvoiceStatus.REVIEW_PENDING,
        "risk_level": RiskLevel.MEDIUM,
        "risk_score": 0.56,
        "guardrails_passed": True,
    },
    {
        "invoice_id": "inv_demo_low_001",
        "customer_id": "cust_demo_blueharbor",
        "erp_invoice_id": "erp_inv_demo_low_001",
        "file_name": "NEW-00003.png",
        "invoice_number": "NEW-00003",
        "amount_due": Decimal("1890.00"),
        "currency": "USD",
        "due_date": date.today() + timedelta(days=9),
        "payment_status": PaymentStatus.UNPAID,
        "status": InvoiceStatus.SCORED,
        "risk_level": RiskLevel.LOW,
        "risk_score": 0.18,
        "guardrails_passed": True,
    },
]


class DemoSeedError(RuntimeError):
    """Raised when the local demo seed cannot be prepared."""


def main() -> None:
    with SessionLocal() as session:
        reset_demo_data(session)
        session.commit()

        seed_tenant(session)
        session.commit()

        seed_users(session)
        session.commit()

        seed_customers(session)
        session.commit()

        seed_erp_and_crm(session)
        session.commit()

        seed_invoice_storage_files()

        seed_invoices(session)
        session.commit()

        seed_rag_documents(session)
        session.commit()

        seed_reviews(session)
        session.commit()

        seed_audit_events(session)
        session.commit()

    print_success_summary()


def reset_demo_data(session) -> None:
    print("Resetting previous Finplex demo data...")
    session.query(ReviewModel).filter(
        ReviewModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(AuditEventModel).filter(
        AuditEventModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(RagChunkModel).filter(
        RagChunkModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(RagDocumentModel).filter(
        RagDocumentModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(CRMDisputeModel).filter(
        CRMDisputeModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(CRMNoteModel).filter(
        CRMNoteModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(ERPPaymentModel).filter(
        ERPPaymentModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(ERPInvoiceModel).filter(
        ERPInvoiceModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(InvoiceModel).filter(
        InvoiceModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(CustomerModel).filter(
        CustomerModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.query(UserModel).filter(
        UserModel.email.in_([ADMIN_EMAIL, MANAGER_EMAIL]),
    ).delete(synchronize_session=False)
    session.query(TenantModel).filter(
        TenantModel.tenant_id == TENANT_ID,
    ).delete(synchronize_session=False)
    session.flush()


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
    for customer in DEMO_CUSTOMERS:
        session.add(
            CustomerModel(
                tenant_id=TENANT_ID,
                preferred_contact_channel="email",
                **customer,
            )
        )


def seed_erp_and_crm(session) -> None:
    for invoice in DEMO_INVOICES:
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
                total_paid=paid_amount_for(invoice),
                payment_terms_days=30,
            )
        )

    session.flush()

    session.add(
        ERPPaymentModel(
            payment_id="pay_demo_cedar_partial_001",
            tenant_id=TENANT_ID,
            customer_id="cust_demo_cedar",
            erp_invoice_id="erp_inv_demo_medium_001",
            amount=Decimal("1500.00"),
            currency="USD",
            paid_at=date.today() - timedelta(days=3),
        )
    )

    session.add_all(
        [
            CRMNoteModel(
                note_id="crm_note_demo_aurora_001",
                tenant_id=TENANT_ID,
                customer_id="cust_demo_aurora",
                author_user_id=MANAGER_USER_ID,
                body=(
                    "Customer mentioned a pricing discrepancy and requested "
                    "supporting evidence before payment. Use a respectful "
                    "tone and avoid pressure language."
                ),
            ),
            CRMNoteModel(
                note_id="crm_note_demo_cedar_001",
                tenant_id=TENANT_ID,
                customer_id="cust_demo_cedar",
                author_user_id=MANAGER_USER_ID,
                body=(
                    "Customer paid part of the balance and usually responds "
                    "within three business days."
                ),
            ),
            CRMDisputeModel(
                dispute_id="crm_dispute_demo_aurora_001",
                tenant_id=TENANT_ID,
                customer_id="cust_demo_aurora",
                invoice_number="NEW-00001",
                reason=(
                    "Open dispute about invoice line-item pricing. Follow-up "
                    "should acknowledge the dispute and offer clarification."
                ),
                is_open=True,
            ),
        ]
    )


def paid_amount_for(invoice: dict) -> Decimal:
    if invoice["payment_status"] == PaymentStatus.PARTIALLY_PAID:
        return Decimal("1500.00")
    if invoice["payment_status"] == PaymentStatus.PAID:
        return invoice["amount_due"]
    return Decimal("0.00")


def seed_invoice_storage_files() -> None:
    source_dir = ROOT_DIR / "data" / "demo_invoices" / "new_uploaded_invoices"
    if not source_dir.exists():
        raise DemoSeedError(f"Demo invoice folder does not exist: {source_dir}")

    for invoice in DEMO_INVOICES:
        source_file = source_dir / invoice["file_name"]
        if not source_file.exists():
            raise DemoSeedError(f"Missing demo invoice image: {source_file}")

        destination = (
            settings.local_storage_dir
            / TENANT_ID
            / "invoices"
            / invoice["invoice_id"]
            / invoice["file_name"]
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_file, destination)


def seed_invoices(session) -> None:
    for invoice in DEMO_INVOICES:
        session.add(
            InvoiceModel(
                invoice_id=invoice["invoice_id"],
                tenant_id=TENANT_ID,
                uploaded_by_user_id=ADMIN_USER_ID,
                customer_id=invoice["customer_id"],
                file_name=invoice["file_name"],
                storage_key=storage_key_for(invoice),
                status=invoice["status"].name,
                payment_status=invoice["payment_status"].name,
                extracted_fields=extracted_fields_for(invoice),
                evidence_ids=evidence_ids_for(invoice),
            )
        )


def storage_key_for(invoice: dict) -> str:
    return f"{TENANT_ID}/invoices/{invoice['invoice_id']}/{invoice['file_name']}"


def extracted_fields_for(invoice: dict) -> dict[str, object]:
    return {
        "invoice_number": invoice["invoice_number"],
        "customer_id": invoice["customer_id"],
        "amount_due": str(invoice["amount_due"]),
        "currency": invoice["currency"],
        "due_date": invoice["due_date"].isoformat(),
        "risk_score": invoice["risk_score"],
        "risk_level": invoice["risk_level"].value,
        "extraction_confidence": 0.94,
        "demo_source": "seed_demo_data.py",
    }


def evidence_ids_for(invoice: dict) -> list[str]:
    return [
        f"ev_invoice_{invoice['invoice_number'].lower()}",
        f"ev_erp_{invoice['invoice_number'].lower()}",
        f"ev_crm_{invoice['customer_id']}",
        "ev_policy_respectful_followup",
    ]


def seed_rag_documents(session) -> None:
    documents = [
        {
            "document_id": "rag_doc_demo_policy_001",
            "title": "Responsible Collection Follow-Up Policy",
            "source_type": "regulation",
            "storage_key": "regulations/demo/responsible_followup_policy.md",
            "chunks": [
                (
                    "ev_policy_respectful_followup",
                    "Debt-collection follow-ups must be respectful, factual, "
                    "non-threatening, and should offer a path to clarify "
                    "disputes or payment questions.",
                ),
            ],
        },
        {
            "document_id": "rag_doc_demo_erp_001",
            "title": "ERP Invoice and Payment Evidence",
            "source_type": "erp",
            "storage_key": "data/seed/historical_erp_invoices.csv",
            "chunks": [
                (
                    "ev_erp_new-00001",
                    "ERP shows invoice NEW-00001 for Aurora Medical Supplies "
                    "has an open balance of 12450.00 USD and is overdue.",
                ),
                (
                    "ev_erp_new-00002",
                    "ERP shows invoice NEW-00002 for Cedar Retail Group is "
                    "partially paid with 1500.00 USD already received.",
                ),
            ],
        },
        {
            "document_id": "rag_doc_demo_crm_001",
            "title": "CRM Customer History Evidence",
            "source_type": "crm",
            "storage_key": "data/seed/crm_customers.csv",
            "chunks": [
                (
                    "ev_crm_cust_demo_aurora",
                    "CRM shows Aurora Medical Supplies has an open dispute "
                    "about pricing and prefers a clarification-first follow-up.",
                ),
                (
                    "ev_crm_cust_demo_cedar",
                    "CRM shows Cedar Retail Group made a partial payment and "
                    "usually responds within three business days.",
                ),
            ],
        },
    ]

    for document in documents:
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


def seed_reviews(session) -> None:
    for invoice in DEMO_INVOICES[:2]:
        session.add(
            ReviewModel(
                review_id=f"review_{invoice['invoice_number'].lower()}",
                tenant_id=TENANT_ID,
                invoice_id=invoice["invoice_id"],
                draft_message=draft_message_for(invoice),
                risk_level=invoice["risk_level"].name,
                guardrails_passed=invoice["guardrails_passed"],
                evidence_ids=evidence_ids_for(invoice),
                status=ReviewStatus.PENDING.name,
            )
        )


def draft_message_for(invoice: dict) -> str:
    customer = customer_name_for(invoice["customer_id"])
    amount = f"{invoice['amount_due']} {invoice['currency']}"
    invoice_number = invoice["invoice_number"]

    if invoice["risk_level"] == RiskLevel.HIGH:
        return (
            f"Hello, I hope you are well. I am following up on invoice "
            f"{invoice_number} for {amount}. Our records show that the "
            f"balance is still open, and I also see there may be a pricing "
            f"question. We are happy to clarify the invoice details or share "
            f"supporting information before the next payment step."
        )

    return (
        f"Hello, I am following up on invoice {invoice_number} for "
        f"{customer}. Our records show that part of the balance has been "
        f"received, and we would appreciate an update on the remaining "
        f"payment timeline."
    )


def customer_name_for(customer_id: str) -> str:
    for customer in DEMO_CUSTOMERS:
        if customer["customer_id"] == customer_id:
            return customer["company_name"]
    return customer_id


def seed_audit_events(session) -> None:
    now = datetime.now(UTC)
    audit_events = [
        (
            "audit_demo_tenant_created",
            AuditAction.TENANT_CREATED,
            ADMIN_USER_ID,
            "tenant",
            TENANT_ID,
            {"name": TENANT_NAME},
        ),
        (
            "audit_demo_invoice_uploaded",
            AuditAction.INVOICE_UPLOADED,
            ADMIN_USER_ID,
            "invoice",
            "inv_demo_high_001",
            {"file_name": "NEW-00001.png"},
        ),
        (
            "audit_demo_invoice_processed",
            AuditAction.INVOICE_PROCESSED,
            None,
            "invoice",
            "inv_demo_high_001",
            {"risk_level": "high", "risk_score": 0.87},
        ),
        (
            "audit_demo_guardrails_checked",
            AuditAction.GUARDRAILS_CHECKED,
            None,
            "review",
            "review_new-00001",
            {"passed": True, "policy": "responsible_collection"},
        ),
        (
            "audit_demo_draft_created",
            AuditAction.DRAFT_CREATED,
            None,
            "review",
            "review_new-00001",
            {"citations": evidence_ids_for(DEMO_INVOICES[0])},
        ),
    ]

    for index, event in enumerate(audit_events):
        event_id, action, actor_user_id, entity_type, entity_id, metadata = event
        model = AuditEventModel(
            audit_event_id=event_id,
            tenant_id=TENANT_ID,
            action=action.name,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            trace_id=f"trace_demo_{index + 1:03d}",
            metadata_json=metadata,
        )
        model.created_at = now + timedelta(seconds=index)
        session.add(model)


def print_success_summary() -> None:
    summary = {
        "tenant_id": TENANT_ID,
        "tenant_name": TENANT_NAME,
        "admin_email": ADMIN_EMAIL,
        "manager_email": MANAGER_EMAIL,
        "password": DEMO_PASSWORD,
        "seeded_customers": len(DEMO_CUSTOMERS),
        "seeded_invoices": len(DEMO_INVOICES),
        "pending_reviews": 2,
    }
    print("\nFinplex demo data is ready.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
