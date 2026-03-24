"""add pgvector extension and fix embedding column

Revision ID: 5a26926258cb
Revises: 7bae57f5e9b6
Create Date: 2026-03-11 21:58:30.819996

Story 8.3 Code Review Fix:
- Enable pgvector extension for vector similarity search
- Alter embedding column from TEXT to VECTOR(1536)
- Create IVFFlat index for vector similarity search

This fixes CRITICAL issue #1 from code review:
- Original migration used TEXT instead of VECTOR type
- Missing pgvector extension prevented Story 8.4 RAG functionality

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5a26926258cb"
down_revision: str | None = "042"  # Depend on latest head
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Alter embedding column from TEXT to VECTOR(1536)
    # Note: This assumes the column is empty (new installation)
    # For production with existing data, use:
    #   ALTER TABLE document_chunks ALTER COLUMN embedding TYPE VECTOR(1536) USING NULL;
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE VECTOR(1536) USING NULL;")

    # Create IVFFlat index for vector similarity search
    # lists=100 is suitable for up to 100K vectors
    # For larger datasets, increase lists proportionally
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100);"
    )


def downgrade() -> None:
    # Drop vector index
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding;")

    # Revert embedding column to TEXT
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE TEXT USING NULL;")

    # Note: We don't drop the pgvector extension as it may be used by other features
    # To completely remove: DROP EXTENSION IF EXISTS vector CASCADE;
