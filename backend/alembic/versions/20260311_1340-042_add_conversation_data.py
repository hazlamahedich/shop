"""add_conversation_data

Revision ID: 042
Revises: 7bae57f5e9b6
Create Date: 2026-03-11 13:40:56.773273

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "042"
down_revision: str | None = "7bae57f5e9b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add conversation_data column to conversations table
    op.add_column(
        "conversations",
        sa.Column(
            "conversation_data",
            sa.dialects.postgresql.JSONB,
            nullable=True,
            comment="Encrypted conversation metadata (formerly metadata)",
        ),
    )


def downgrade() -> None:
    op.drop_column("conversations", "conversation_data")
