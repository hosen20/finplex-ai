"""Add ERP, CRM, and RAG support tables.

Revision ID: 0002_demo_support_tables
Revises: 0001_init
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_demo_support_tables"
down_revision: str | None = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "erp_invoices",
        sa.Column("erp_invoice_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("invoice_number", sa.String(length=128), nullable=False),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("payment_status", sa.String(length=64), nullable=False),
        sa.Column("total_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.customer_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_erp_invoices_tenant_id", "erp_invoices", ["tenant_id"])
    op.create_index("ix_erp_invoices_customer_id", "erp_invoices", ["customer_id"])
    op.create_index(
        "ix_erp_invoices_invoice_number",
        "erp_invoices",
        ["invoice_number"],
    )

    op.create_table(
        "erp_payments",
        sa.Column("payment_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("erp_invoice_id", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("paid_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["erp_invoice_id"],
            ["erp_invoices.erp_invoice_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_erp_payments_tenant_id", "erp_payments", ["tenant_id"])
    op.create_index("ix_erp_payments_customer_id", "erp_payments", ["customer_id"])
    op.create_index(
        "ix_erp_payments_erp_invoice_id",
        "erp_payments",
        ["erp_invoice_id"],
    )

    op.create_table(
        "crm_notes",
        sa.Column("note_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("author_user_id", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.customer_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_crm_notes_tenant_id", "crm_notes", ["tenant_id"])
    op.create_index("ix_crm_notes_customer_id", "crm_notes", ["customer_id"])

    op.create_table(
        "crm_disputes",
        sa.Column("dispute_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("invoice_number", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.customer_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_crm_disputes_tenant_id", "crm_disputes", ["tenant_id"])
    op.create_index("ix_crm_disputes_customer_id", "crm_disputes", ["customer_id"])

    op.create_table(
        "rag_documents",
        sa.Column("document_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.tenant_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_rag_documents_tenant_id", "rag_documents", ["tenant_id"])

    op.create_table(
        "rag_chunks",
        sa.Column("chunk_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["rag_documents.document_id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_rag_chunks_tenant_id", "rag_chunks", ["tenant_id"])
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_table("rag_chunks")
    op.drop_table("rag_documents")
    op.drop_table("crm_disputes")
    op.drop_table("crm_notes")
    op.drop_table("erp_payments")
    op.drop_table("erp_invoices")
