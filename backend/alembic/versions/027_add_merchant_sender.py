"""add merchant to message_sender enum

Revision ID: add_merchant_sender
Revises: 026_add_consents_table
Create Date: 2026-02-22

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "add_merchant_sender"
down_revision = "026_add_consents_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'merchant' value to message_sender enum
    # PostgreSQL requires altering the enum type directly
    op.execute("""
        ALTER TYPE message_sender ADD VALUE IF NOT EXISTS 'merchant';
    """)


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # We would need to recreate the enum, but for safety we'll skip downgrade
    # In production, this would be handled by recreating the enum type
    pass
