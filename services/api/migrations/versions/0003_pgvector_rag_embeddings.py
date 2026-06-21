"""Add pgvector-backed embeddings for RAG chunks.

Revision ID: 0003_pgvector_rag_embeddings
Revises: 0002_demo_support_tables
Create Date: 2026-06-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_pgvector_rag_embeddings"
down_revision: str | None = "0002_demo_support_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


VECTOR_DIMENSIONS = 8


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"""
        ALTER TABLE rag_chunks
        ADD COLUMN IF NOT EXISTS embedding_vector vector({VECTOR_DIMENSIONS})
        """
    )
    op.execute(
        """
        UPDATE rag_chunks
        SET embedding_vector = (
            '[' || (
                SELECT string_agg(value::text, ',')
                FROM json_array_elements_text(embedding) AS value
            ) || ']'
        )::vector
        WHERE embedding_vector IS NULL
          AND embedding IS NOT NULL
          AND json_typeof(embedding) = 'array'
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rag_chunks_embedding_vector
        ON rag_chunks
        USING ivfflat (embedding_vector vector_cosine_ops)
        WITH (lists = 16)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rag_chunks_embedding_vector")
    op.execute("ALTER TABLE rag_chunks DROP COLUMN IF EXISTS embedding_vector")
