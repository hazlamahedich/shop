"""add_embedding_provider_fields

Revision ID: add_embedding_provider
Revises: 5a26926258cb
Create Date: 2026-03-14

Story 8-11: LLM Embedding Provider Integration & Re-embedding
- Adds embedding_provider, embedding_model, embedding_dimension to merchants
- Adds re_embedding_status, re_embedding_progress, embedding_version to knowledge_documents
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "add_embedding_provider"
down_revision: str | None = "5a26926258cb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "merchants",
        sa.Column(
            "embedding_provider",
            sa.String(20),
            nullable=False,
            server_default="openai",
        ),
    )
    op.add_column(
        "merchants",
        sa.Column(
            "embedding_model",
            sa.String(50),
            nullable=False,
            server_default="text-embedding-3-small",
        ),
    )
    op.add_column(
        "merchants",
        sa.Column(
            "embedding_dimension",
            sa.Integer(),
            nullable=False,
            server_default="1536",
        ),
    )

    op.add_column(
        "knowledge_documents",
        sa.Column(
            "re_embedding_status",
            sa.String(20),
            nullable=True,
            server_default="none",
        ),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column(
            "re_embedding_progress",
            sa.Integer(),
            nullable=True,
            server_default="0",
        ),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column(
            "embedding_version",
            sa.String(100),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("knowledge_documents", "embedding_version")
    op.drop_column("knowledge_documents", "re_embedding_progress")
    op.drop_column("knowledge_documents", "re_embedding_status")
    op.drop_column("merchants", "embedding_dimension")
    op.drop_column("merchants", "embedding_model")
    op.drop_column("merchants", "embedding_provider")
