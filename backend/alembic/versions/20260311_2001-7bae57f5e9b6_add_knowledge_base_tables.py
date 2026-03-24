"""add_knowledge_base_tables

Revision ID: 7bae57f5e9b6
Revises: 13daadbdc823
Create Date: 2026-03-11 20:01:30.540649

Story 8.3: Knowledge Base Models & Storage
- Creates knowledge_documents table for document metadata
- Creates document_chunks table for text chunks
- Note: Vector embedding column will be added in Story 8.4

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7bae57f5e9b6"
down_revision: str | None = "13daadbdc823"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_knowledge_documents_merchant_id", "knowledge_documents", ["merchant_id"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_id", "document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("ix_knowledge_documents_status", "knowledge_documents")
    op.drop_index("ix_knowledge_documents_merchant_id", "knowledge_documents")
    op.drop_table("knowledge_documents")
