"""add response_type column to llm_conversation_costs

Revision ID: a1b2c3d4e5f7
Revises: add response_type column to llm_conversation_costs table
for tracking RAG vs non-RAG responses in Story 10-9 AC5.

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "a1b2c3d4e5f7"
down_revision = "243f8387c787"
branch_labels = None
depends_on = None
branch_labels = None
depends_on = None


def upgrade():
    # Add response_type column to llm_conversation_costs table
    # Values: 'rag', 'general', 'unknown'
    # Default: 'unknown' for existing rows
    op.add_column(
        "llm_conversation_costs",
        "response_type",
        sa.String(20),
        nullable=True,
        server_default="unknown",
    )

    # Create index for efficient querying by response_type
    op.create_index(
        "idx_llm_costs_response_type",
        "llm_conversation_costs",
        ["merchant_id", "response_type", "request_timestamp"],
    )


def downgrade():
    # Drop index first
    op.drop_index(
        "idx_llm_costs_response_type",
        table_name="llm_conversation_costs",
    )

    # Drop column
    op.drop_column("llm_conversation_costs", "response_type")
