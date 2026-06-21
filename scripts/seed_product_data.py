#!/usr/bin/env python3
# ruff: noqa: E402, I001
"""Seed Finplex AI with reproducible local product data.

The seed data is privacy-safe and local. It combines the prepared IBM-style
customer/payment CSVs, generated invoice images, local ERP/CRM records, policy
references, RAG documents, review records, and audit events.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select

ROOT_DIR = Path(__file__).resolve().parents[1]
API_SERVICE_DIR = ROOT_DIR / "services" / "api"

if str(API_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_DIR))

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

DEFAULT_PASSWORD = "TenantAdmin123!"
CEDAR_TENANT_ID = "tenant_cedar_finance"
ORION_TENANT_ID = "tenant_orion_medical"
SEED_TENANT_IDS = (CEDAR_TENANT_ID, ORION_TENANT_ID)


@dataclass(frozen=True)
class TenantSeed:
    tenant_id: str
    name: str
    erp_provider: str
    crm_provider: str
    row_offset: int


TENANTS = (
    TenantSeed(
        tenant_id=CEDAR_TENANT_ID,
        name="Cedar Finance Group",
        erp_provider="local_erp_dataset",
        crm_provider="local_crm_dataset",
        row_offset=0,
    ),
    TenantSeed(
        tenant_id=ORION_TENANT_ID,
        name="Orion Medical Billing",
        erp_provider="local_erp_dataset",
        crm_provider="local_crm_dataset",
        row_offset=18,
    ),
)

USER_BLUEPRINTS = (
    ("tenant_admin", UserRole.TENANT_ADMIN, "Tenant Administrator"),
    ("manager", UserRole.MANAGER, "Finance Manager"),
    ("reviewer", UserRole.REVIEWER, "Invoice Reviewer"),
    ("auditor", UserRole.AUDITOR, "Audit Analyst"),
)


class SeedError(RuntimeError):
    """Raised when local seed data cannot be loaded."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed Finplex AI with realistic local product data."
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        help="Password assigned to seeded tenant users.",
    )
    parser.add_argument(
        "--max-customers-per-tenant",
        type=int,
        default=12,
        help="Number of customers imported per tenant from the prepared dataset.",
    )
    parser.add_argument(
        "--max-history-invoices-per-tenant",
        type=int,
        default=80,
        help="Number of historical ERP invoices imported per tenant.",
    )
    parser.add_argument(
        "--max-uploaded-invoices-per-tenant",
        type=int,
        default=6,
        help="Number of invoice-image records imported per tenant.",
    )
    parser.add_argument(
        "--reset-product-tenants",
        action="store_true",
        help="Delete and recreate only the seeded product tenants.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SeedError(f"Required seed file was not found: {path}")

    with path.open(newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def decimal_from(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def int_from(value: str, default: int = 0) -> int:
    if value == "":
        return default
    return int(float(value))


def float_from(value: str, default: float = 0.0) -> float:
    if value == "":
        return default
    return float(value)


def bool_from_dataset(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def tenant_domain(tenant: TenantSeed) -> str:
    if tenant.tenant_id == CEDAR_TENANT_ID:
        return "cedarfinance.com"
    return "orionmedical.com"


def seeded_email(prefix: str, tenant: TenantSeed) -> str:
    return f"{prefix}@{tenant_domain(tenant)}"


def contact_email(customer_id: str, tenant: TenantSeed) -> str:
    safe_customer = customer_id.replace("cust_", "").replace("-", "").lower()
    return f"ar-{safe_customer}@customers.{tenant_domain(tenant)}"


def relationship_status(row: dict[str, str]) -> str:
    late_count = int_from(row["previous_late_payments"])
    dispute_count = int_from(row["disputed_invoice_count"])
    negative_score = float_from(row["crm_negative_signal_score"])

    if late_count >= 8 or dispute_count >= 5 or negative_score >= 0.75:
        return "at_risk"
    if late_count >= 3 or dispute_count >= 2 or negative_score >= 0.45:
        return "watchlist"
    return "healthy"


def risk_level_for_customer(row: dict[str, str]) -> RiskLevel:
    late_count = int_from(row.get("previous_late_payments", "0"))
    dispute_count = int_from(row.get("disputed_invoice_count", "0"))
    negative_score = float_from(row.get("crm_negative_signal_score", "0"))

    if late_count >= 8 or dispute_count >= 5 or negative_score >= 0.75:
        return RiskLevel.HIGH
    if late_count >= 3 or dispute_count >= 2 or negative_score >= 0.45:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def deterministic_embedding(text: str, dimensions: int = 8) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [round(digest[index] / 255, 6) for index in range(dimensions)]


def chunk_text(text: str, max_chars: int = 650) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if not paragraph:
            continue
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        current = paragraph[:max_chars]

    if current:
        chunks.append(current)

    return chunks or [text[:max_chars]]


def reset_seeded_product_tenants(session: Any) -> None:
    tenant_ids = list(SEED_TENANT_IDS)

    for model in (
        AuditEventModel,
        ReviewModel,
        InvoiceModel,
        ERPPaymentModel,
        CRMDisputeModel,
        CRMNoteModel,
        RagChunkModel,
        RagDocumentModel,
        ERPInvoiceModel,
        CustomerModel,
        UserModel,
        TenantModel,
    ):
        session.execute(delete(model).where(model.tenant_id.in_(tenant_ids)))

    session.commit()


def upsert_tenant(session: Any, tenant: TenantSeed) -> TenantModel:
    existing = session.get(TenantModel, tenant.tenant_id)
    if existing is None:
        existing = TenantModel(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            status=TenantStatus.ACTIVE,
            erp_provider=tenant.erp_provider,
            crm_provider=tenant.crm_provider,
        )
        session.add(existing)
    else:
        existing.name = tenant.name
        existing.status = TenantStatus.ACTIVE
        existing.erp_provider = tenant.erp_provider
        existing.crm_provider = tenant.crm_provider

    return existing


def upsert_user(
    session: Any,
    *,
    tenant_id: str,
    user_id: str,
    email: str,
    full_name: str,
    password: str,
    role: UserRole,
) -> UserModel:
    existing_by_email = session.scalar(
        select(UserModel).where(UserModel.email == email)
    )
    user = existing_by_email or session.get(UserModel, user_id)

    if user is None:
        user = UserModel(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
    else:
        user.tenant_id = tenant_id
        user.email = email
        user.full_name = full_name
        user.hashed_password = hash_password(password)
        user.role = role
        user.is_active = True

    return user


def seed_users(session: Any, tenant: TenantSeed, password: str) -> dict[str, UserModel]:
    users: dict[str, UserModel] = {}
    tenant_slug = tenant.tenant_id.replace("tenant_", "")

    for prefix, role, title in USER_BLUEPRINTS:
        full_name = f"{tenant.name} {title}"
        user = upsert_user(
            session,
            tenant_id=tenant.tenant_id,
            user_id=f"user_{tenant_slug}_{prefix}",
            email=seeded_email(prefix, tenant),
            full_name=full_name,
            password=password,
            role=role,
        )
        users[prefix] = user

    return users


def select_window(
    rows: list[dict[str, str]],
    *,
    offset: int,
    limit: int,
) -> list[dict[str, str]]:
    return rows[offset : offset + limit]


def seed_customers(
    session: Any,
    tenant: TenantSeed,
    customer_rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    customer_lookup: dict[str, dict[str, str]] = {}

    for row in customer_rows:
        customer_id = row["finplex_customer_id"]
        if customer_id in customer_lookup:
            continue

        customer_lookup[customer_id] = row
        tags = [
            "source:ibm_customer_payment_dataset",
            f"country:{row['country_code']}",
            f"relationship:{relationship_status(row)}",
        ]

        session.merge(
            CustomerModel(
                customer_id=customer_id,
                tenant_id=tenant.tenant_id,
                company_name=row["customer_name"],
                contact_name=f"Finance Contact {row['external_customer_id']}",
                contact_email=contact_email(customer_id, tenant),
                preferred_contact_channel="email",
                relationship_status=relationship_status(row),
                tags=tags,
            )
        )

    return customer_lookup


def seed_customer_notes(
    session: Any,
    *,
    tenant: TenantSeed,
    customer_lookup: dict[str, dict[str, str]],
    author_user_id: str,
) -> None:
    for index, (customer_id, row) in enumerate(customer_lookup.items(), start=1):
        body = (
            f"Customer intelligence summary for {row['customer_name']}: "
            f"{row['historical_invoice_count']} historical invoices, "
            f"{row['previous_late_payments']} previous late payments, "
            f"{row['disputed_invoice_count']} disputed invoices, "
            f"on-time payment rate {row['on_time_payment_rate']}, and CRM negative "
            f"signal score {row['crm_negative_signal_score']}."
        )
        session.merge(
            CRMNoteModel(
                note_id=f"note_{tenant.tenant_id}_{index:03d}",
                tenant_id=tenant.tenant_id,
                customer_id=customer_id,
                author_user_id=author_user_id,
                body=body,
            )
        )


def seed_historical_erp(
    session: Any,
    *,
    tenant: TenantSeed,
    invoice_rows: list[dict[str, str]],
    payment_rows: list[dict[str, str]],
    customer_lookup: dict[str, dict[str, str]],
    max_invoices: int,
) -> None:
    selected_invoices = [
        row for row in invoice_rows if row["finplex_customer_id"] in customer_lookup
    ][:max_invoices]
    known_invoice_ids = {row["historical_invoice_id"] for row in selected_invoices}

    for row in selected_invoices:
        is_disputed = bool_from_dataset(row.get("is_disputed", "0"))
        payment_status = PaymentStatus.DISPUTED if is_disputed else PaymentStatus.PAID
        amount_due = decimal_from(row["amount_due"])

        session.merge(
            ERPInvoiceModel(
                erp_invoice_id=row["historical_invoice_id"],
                tenant_id=tenant.tenant_id,
                customer_id=row["finplex_customer_id"],
                invoice_number=row["invoice_number"],
                amount_due=amount_due,
                currency=row.get("currency", "USD") or "USD",
                due_date=parse_date(row["due_date"]),
                payment_status=payment_status,
                total_paid=amount_due,
                payment_terms_days=int_from(row["payment_terms_days"], 30),
            )
        )

    for row in payment_rows:
        historical_invoice_id = row["historical_invoice_id"]
        if historical_invoice_id not in known_invoice_ids:
            continue

        invoice_row = next(
            item
            for item in selected_invoices
            if item["historical_invoice_id"] == historical_invoice_id
        )
        session.merge(
            ERPPaymentModel(
                payment_id=f"pay_{historical_invoice_id}",
                tenant_id=tenant.tenant_id,
                customer_id=row["finplex_customer_id"],
                erp_invoice_id=historical_invoice_id,
                amount=decimal_from(invoice_row["amount_due"]),
                currency=invoice_row.get("currency", "USD") or "USD",
                paid_at=parse_date(row["settled_date"]),
            )
        )


def seed_disputes(
    session: Any,
    *,
    tenant: TenantSeed,
    invoice_rows: list[dict[str, str]],
    customer_lookup: dict[str, dict[str, str]],
) -> None:
    disputed_rows = [
        row
        for row in invoice_rows
        if row["finplex_customer_id"] in customer_lookup
        and bool_from_dataset(row.get("is_disputed", "0"))
    ][:24]

    for index, row in enumerate(disputed_rows, start=1):
        reason = (
            f"Historical dispute on invoice {row['invoice_number']}: customer "
            "requested clarification before payment. Future drafts must mention "
            "available evidence and avoid pressure language."
        )
        session.merge(
            CRMDisputeModel(
                dispute_id=f"disp_{tenant.tenant_id}_{index:03d}",
                tenant_id=tenant.tenant_id,
                customer_id=row["finplex_customer_id"],
                invoice_number=row["invoice_number"],
                reason=reason,
                is_open=False,
            )
        )


def seed_uploaded_invoices(
    session: Any,
    *,
    tenant: TenantSeed,
    uploaded_rows: list[dict[str, str]],
    customer_lookup: dict[str, dict[str, str]],
    uploaded_by_user_id: str,
    max_uploaded: int,
) -> None:
    selected_rows = [
        row for row in uploaded_rows if row["finplex_customer_id"] in customer_lookup
    ][:max_uploaded]

    for row in selected_rows:
        invoice_id = f"invoice_{tenant.tenant_id}_{row['new_invoice_id']}"
        erp_invoice_id = f"erp_{tenant.tenant_id}_{row['new_invoice_id']}"
        review_id = f"review_{tenant.tenant_id}_{row['new_invoice_id']}"
        customer_row = customer_lookup[row["finplex_customer_id"]]
        risk_level = risk_level_for_customer(customer_row)
        due_date = parse_date(row["due_date"])
        payment_status = (
            PaymentStatus.OVERDUE
            if due_date < date.today()
            else PaymentStatus.UNPAID
        )
        image_path = Path(row["image_path"]).name
        storage_key = f"data/demo_invoices/new_uploaded_invoices/{image_path}"

        session.merge(
            ERPInvoiceModel(
                erp_invoice_id=erp_invoice_id,
                tenant_id=tenant.tenant_id,
                customer_id=row["finplex_customer_id"],
                invoice_number=row["invoice_number"],
                amount_due=decimal_from(row["amount_due"]),
                currency=row.get("currency", "USD") or "USD",
                due_date=due_date,
                payment_status=payment_status,
                total_paid=Decimal("0.00"),
                payment_terms_days=int_from(row["payment_terms_days"], 30),
            )
        )

        session.merge(
            InvoiceModel(
                invoice_id=invoice_id,
                tenant_id=tenant.tenant_id,
                uploaded_by_user_id=uploaded_by_user_id,
                customer_id=row["finplex_customer_id"],
                file_name=image_path,
                storage_key=storage_key,
                status=InvoiceStatus.REVIEW_PENDING,
                payment_status=payment_status,
                extracted_fields={
                    "invoice_number": row["invoice_number"],
                    "customer_name": row["customer_name"],
                    "invoice_date": row["invoice_date"],
                    "due_date": row["due_date"],
                    "amount_due": row["amount_due"],
                    "currency": row.get("currency", "USD") or "USD",
                    "source": "generated_invoice_image_dataset",
                },
                evidence_ids=[
                    erp_invoice_id,
                    row["finplex_customer_id"],
                    f"rag_{tenant.tenant_id}_human_approval_policy_000",
                ],
            )
        )

        draft_message = (
            f"Hello {row['customer_name']}, our records show invoice "
            f"{row['invoice_number']} for {row['amount_due']} "
            f"{row.get('currency', 'USD') or 'USD'} is awaiting payment. "
            "Could you please confirm whether payment has been scheduled or if "
            "there is any documentation we should review?"
        )
        session.merge(
            ReviewModel(
                review_id=review_id,
                tenant_id=tenant.tenant_id,
                invoice_id=invoice_id,
                draft_message=draft_message,
                risk_level=risk_level,
                guardrails_passed=True,
                evidence_ids=[
                    erp_invoice_id,
                    row["finplex_customer_id"],
                    f"rag_{tenant.tenant_id}_human_approval_policy_000",
                ],
                status=ReviewStatus.PENDING,
                reviewer_user_id=None,
                reviewer_comment=None,
            )
        )

        session.merge(
            AuditEventModel(
                audit_event_id=f"audit_{tenant.tenant_id}_{row['new_invoice_id']}",
                tenant_id=tenant.tenant_id,
                action=AuditAction.DRAFT_CREATED,
                actor_user_id=uploaded_by_user_id,
                entity_type="review",
                entity_id=review_id,
                trace_id=f"seed-trace-{tenant.tenant_id}-{row['new_invoice_id']}",
                metadata_json={
                    "source": "seed_product_data.py",
                    "invoice_id": invoice_id,
                    "risk_level": risk_level.value,
                },
            )
        )


def policy_files() -> list[Path]:
    preferred = [
        ROOT_DIR / "regulations/debt_collection/human_approval_policy.md",
        ROOT_DIR / "regulations/debt_collection/communication_rules.md",
        ROOT_DIR / "regulations/debt_collection/prohibited_claims.md",
        ROOT_DIR / "regulations/privacy_security/tenant_isolation_policy.md",
        ROOT_DIR / "regulations/ai_governance/evidence_required_policy.md",
        ROOT_DIR / "regulations/ai_governance/hallucination_prevention_policy.md",
    ]
    return [path for path in preferred if path.exists()]


def seed_rag_documents(session: Any, tenant: TenantSeed) -> None:
    for path in policy_files():
        slug = path.stem
        document_id = f"ragdoc_{tenant.tenant_id}_{slug}"
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            text = (
                f"{path.stem.replace('_', ' ').title()} for {tenant.name}. "
                "Customer-facing financial follow-up must be respectful, "
                "evidence-based, tenant-scoped, and approved by a human reviewer."
            )

        session.merge(
            RagDocumentModel(
                document_id=document_id,
                tenant_id=tenant.tenant_id,
                title=path.stem.replace("_", " ").title(),
                source_type="policy_document",
                storage_key=str(path.relative_to(ROOT_DIR)),
            )
        )
        session.flush()

        for chunk_index, chunk in enumerate(chunk_text(text)):
            chunk_id = f"rag_{tenant.tenant_id}_{slug}_{chunk_index:03d}"
            embedding = deterministic_embedding(chunk)
            session.merge(
                RagChunkModel(
                    chunk_id=chunk_id,
                    tenant_id=tenant.tenant_id,
                    document_id=document_id,
                    content=chunk,
                    chunk_index=chunk_index,
                    embedding=embedding,
                    embedding_vector=embedding,
                )
            )


def seed_tenant(
    session: Any,
    *,
    tenant: TenantSeed,
    customer_rows: list[dict[str, str]],
    history_invoice_rows: list[dict[str, str]],
    payment_rows: list[dict[str, str]],
    uploaded_rows: list[dict[str, str]],
    password: str,
    max_customers: int,
    max_history_invoices: int,
    max_uploaded: int,
) -> dict[str, int]:
    upsert_tenant(session, tenant)
    users = seed_users(session, tenant, password)
    session.flush()

    customer_lookup = seed_customers(
        session,
        tenant,
        select_window(
            customer_rows,
            offset=tenant.row_offset,
            limit=max_customers,
        ),
    )
    session.flush()

    seed_customer_notes(
        session,
        tenant=tenant,
        customer_lookup=customer_lookup,
        author_user_id=users["manager"].user_id,
    )
    seed_historical_erp(
        session,
        tenant=tenant,
        invoice_rows=history_invoice_rows,
        payment_rows=payment_rows,
        customer_lookup=customer_lookup,
        max_invoices=max_history_invoices,
    )
    seed_disputes(
        session,
        tenant=tenant,
        invoice_rows=history_invoice_rows,
        customer_lookup=customer_lookup,
    )
    seed_rag_documents(session, tenant)
    seed_uploaded_invoices(
        session,
        tenant=tenant,
        uploaded_rows=uploaded_rows,
        customer_lookup=customer_lookup,
        uploaded_by_user_id=users["manager"].user_id,
        max_uploaded=max_uploaded,
    )

    return {
        "users": len(users),
        "customers": len(customer_lookup),
        "uploaded_invoices": min(max_uploaded, len(customer_lookup)),
    }


def main() -> None:
    args = parse_args()
    if len(args.password) < 8:
        raise SystemExit("Seed password must be at least 8 characters.")

    seed_dir = ROOT_DIR / "data" / "seed"
    customer_rows = read_csv(seed_dir / "crm_customers.csv")
    history_invoice_rows = read_csv(seed_dir / "historical_erp_invoices.csv")
    payment_rows = read_csv(seed_dir / "historical_erp_payments.csv")
    uploaded_rows = read_csv(seed_dir / "new_uploaded_invoice_ground_truth.csv")

    with SessionLocal() as session:
        if args.reset_product_tenants:
            reset_seeded_product_tenants(session)

        summaries = []
        for tenant in TENANTS:
            summary = seed_tenant(
                session,
                tenant=tenant,
                customer_rows=customer_rows,
                history_invoice_rows=history_invoice_rows,
                payment_rows=payment_rows,
                uploaded_rows=uploaded_rows,
                password=args.password,
                max_customers=args.max_customers_per_tenant,
                max_history_invoices=args.max_history_invoices_per_tenant,
                max_uploaded=args.max_uploaded_invoices_per_tenant,
            )
            summaries.append((tenant, summary))

        session.commit()

    print("Finplex local product data is ready.")
    print(f"Seeded at: {datetime.now(UTC).isoformat()}")
    print(f"Password for seeded tenant users: {args.password}")
    for tenant, summary in summaries:
        print(
            f"- {tenant.name} ({tenant.tenant_id}): "
            f"{summary['users']} users, {summary['customers']} customers, "
            f"{summary['uploaded_invoices']} review-ready invoices"
        )

    print("\nTenant user accounts:")
    for tenant in TENANTS:
        for prefix, _, _ in USER_BLUEPRINTS:
            print(f"- {seeded_email(prefix, tenant)}")


if __name__ == "__main__":
    main()
