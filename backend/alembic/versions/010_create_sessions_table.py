"""Create sessions table.

Revision ID: 010_create_sessions_table
Revises: 009_merchant_auth_fields
Create Date: 2026-02-09

Story 1.8: Merchant Dashboard Authentication
AC 2, AC 6: Create sessions table for JWT revocation support.
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010_create_sessions_table"
down_revision: str | None = "009_merchant_auth_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create sessions table with indexes."""
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), default=False, nullable=False),
    )

    # Create indexes
    op.create_index("ix_sessions_merchant_id", "sessions", ["merchant_id"])
    op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"])
    op.create_index("ix_sessions_merchant_revoked", "sessions", ["merchant_id", "revoked"])
    op.create_index("ix_sessions_expires", "sessions", ["expires_at"])


def downgrade() -> None:
    """Drop sessions table and indexes."""
    # Drop indexes first
    op.drop_index("ix_sessions_expires", table_name="sessions")
    op.drop_index("ix_sessions_merchant_revoked", table_name="sessions")
    op.drop_index("ix_sessions_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_merchant_id", table_name="sessions")

    # Drop table
    op.drop_table("sessions")
