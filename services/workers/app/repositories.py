from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

metadata = MetaData()

invoices_table = Table(
    "invoices",
    metadata,
    Column("invoice_id", String(64), primary_key=True),
    Column("tenant_id", String(64), nullable=False),
    Column("uploaded_by_user_id", String(64), nullable=False),
    Column("customer_id", String(64), nullable=True),
    Column("file_name", String(255), nullable=False),
    Column("storage_key", String(512), nullable=False),
    Column("status", String(64), nullable=False),
    Column("payment_status", String(64), nullable=False),
    Column("extracted_fields", JSON, nullable=True),
    Column("evidence_ids", JSON, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

reviews_table = Table(
    "reviews",
    metadata,
    Column("review_id", String(64), primary_key=True),
    Column("tenant_id", String(64), nullable=False),
    Column("invoice_id", String(64), nullable=False),
    Column("draft_message", Text, nullable=False),
    Column("risk_level", String(64), nullable=False),
    Column("guardrails_passed", Boolean, nullable=False),
    Column("evidence_ids", JSON, nullable=False),
    Column("status", String(64), nullable=False),
    Column("reviewer_user_id", String(64), nullable=True),
    Column("reviewer_comment", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

audit_events_table = Table(
    "audit_events",
    metadata,
    Column("audit_event_id", String(64), primary_key=True),
    Column("tenant_id", String(64), nullable=False),
    Column("action", String(64), nullable=False),
    Column("actor_user_id", String(64), nullable=True),
    Column("entity_type", String(128), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("trace_id", String(128), nullable=False),
    Column("metadata", JSON, key="metadata_json", nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class InvoiceProcessingRepository:
    """Database writes needed by the asynchronous invoice worker."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_invoice(self, invoice_id: str) -> dict[str, Any] | None:
        statement = select(invoices_table).where(
            invoices_table.c.invoice_id == invoice_id
        )
        row = self.session.execute(statement).mappings().first()
        return dict(row) if row is not None else None

    def update_invoice_processing(
        self,
        *,
        invoice_id: str,
        status: str,
        extracted_fields: dict[str, Any] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> None:
        values: dict[str, Any] = {
            "status": status,
            "updated_at": utc_now(),
        }

        if extracted_fields is not None:
            values["extracted_fields"] = extracted_fields

        if evidence_ids is not None:
            values["evidence_ids"] = evidence_ids

        statement = (
            update(invoices_table)
            .where(invoices_table.c.invoice_id == invoice_id)
            .values(**values)
        )
        self.session.execute(statement)

    def create_review(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        draft_message: str,
        risk_level: str,
        guardrails_passed: bool,
        evidence_ids: list[str],
    ) -> str:
        review_id = f"review_{uuid4().hex}"
        now = utc_now()

        statement = insert(reviews_table).values(
            review_id=review_id,
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            draft_message=draft_message,
            risk_level=risk_level,
            guardrails_passed=guardrails_passed,
            evidence_ids=evidence_ids,
            status="pending",
            reviewer_user_id=None,
            reviewer_comment=None,
            created_at=now,
            updated_at=None,
        )
        self.session.execute(statement)
        return review_id

    def record_audit(
        self,
        *,
        tenant_id: str,
        action: str,
        actor_user_id: str | None,
        entity_type: str,
        entity_id: str,
        trace_id: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> None:
        statement = insert(audit_events_table).values(
            audit_event_id=f"audit_{uuid4().hex}",
            tenant_id=tenant_id,
            action=action,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            trace_id=trace_id,
            metadata_json=metadata_json or {},
            created_at=utc_now(),
            updated_at=None,
        )
        self.session.execute(statement)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()