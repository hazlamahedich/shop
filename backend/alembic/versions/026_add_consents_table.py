"""add_consents_table

Revision ID: 026_add_consents_table
Revises: 025_add_is_test_to_orders
Create Date: 2026-02-21 12:00:00.000000

Story 5-10 Task 18: Consent Management Middleware

Adds consents table for tracking user consent for GDPR compliance.
Consent is required before cart operations (add to cart, checkout).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "026_add_consents_table"
down_revision: Union[str, None] = "025_add_is_test_to_orders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_consents_session_id",
        "consents",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_consents_merchant_id",
        "consents",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_consents_session_type",
        "consents",
        ["session_id", "consent_type"],
        unique=False,
    )
    op.create_index(
        "ix_consents_merchant_type",
        "consents",
        ["merchant_id", "consent_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_consents_merchant_type", table_name="consents")
    op.drop_index("ix_consents_session_type", table_name="consents")
    op.drop_index("ix_consents_merchant_id", table_name="consents")
    op.drop_index("ix_consents_session_id", table_name="consents")
    op.drop_table("consents")
