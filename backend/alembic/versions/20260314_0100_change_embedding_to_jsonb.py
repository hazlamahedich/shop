"""Change embedding column to JSONB for flexible dimensions

Revision ID: embedding_jsonb
Revises: add_embedding_provider
Create Date: 2026-03-14

Story 8-11: LLM Embedding Provider Integration & Re-embedding
- Changes document_chunks.embedding from Vector(1536) to JSONB
- Adds embedding_dimension column for runtime vector casting
- Enables support for 768d (Gemini/Ollama) and 1536d (OpenAI)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "embedding_jsonb"
down_revision: str | None = "add_embedding_provider"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Step 1: Add embedding_dimension column
    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding_dimension",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Step 2: Add temporary JSONB column for migration
    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding_jsonb",
            JSONB,
            nullable=True,
        ),
    )

    # Step 3: Migrate existing Vector(1536) data to JSONB
    # Vector cannot be cast directly to JSONB, so we:
    # 1. Cast vector to text (produces "[0.1, 0.2, ...]" format)
    # 2. Parse text as JSON array
    # Note: This assumes existing embeddings are 1536-dimensional (OpenAI)
    op.execute("""
        UPDATE document_chunks
        SET embedding_jsonb = (embedding::text)::jsonb,
            embedding_dimension = 1536
        WHERE embedding IS NOT NULL
    """)

    # Step 4: Drop the old vector column
    op.drop_column("document_chunks", "embedding")

    # Step 5: Rename temp column to embedding
    op.alter_column("document_chunks", "embedding_jsonb", new_column_name="embedding")


def downgrade() -> None:
    # Note: Downgrade will lose non-1536 dimensional embeddings!
    # Only 1536d embeddings can be restored (others will be lost)

    # Step 1: Create temporary vector column
    op.execute("""
        ALTER TABLE document_chunks
        ADD COLUMN embedding_vector vector(1536)
    """)

    # Step 2: Migrate JSONB back to vector (only 1536d embeddings)
    op.execute("""
        UPDATE document_chunks
        SET embedding_vector = (embedding::text)::vector
        WHERE embedding IS NOT NULL
          AND jsonb_array_length(embedding) = 1536
    """)

    # Step 3: Drop JSONB column and dimension column
    op.drop_column("document_chunks", "embedding")
    op.drop_column("document_chunks", "embedding_dimension")

    # Step 4: Rename vector column back to embedding
    op.alter_column("document_chunks", "embedding_vector", new_column_name="embedding")
