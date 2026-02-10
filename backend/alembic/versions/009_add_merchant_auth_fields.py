"""Add merchant authentication fields.

Revision ID: 009_merchant_auth_fields
Revises: 008_conversation_llm_provider
Create Date: 2026-02-09

Story 1.8: Merchant Dashboard Authentication
AC 1, AC 4: Add email and password_hash to merchants table for authentication.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_merchant_auth_fields'
down_revision: Union[str, None] = '008_conversation_llm_provider'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add email and password_hash columns to merchants table."""
    # Add email column (nullable initially, will be populated)
    op.add_column(
        'merchants',
        sa.Column('email', sa.String(255), nullable=True)
    )

    # Add password_hash column (nullable initially)
    op.add_column(
        'merchants',
        sa.Column('password_hash', sa.String(255), nullable=True)
    )

    # Create unique index on email
    op.create_index(
        'ix_merchants_email',
        'merchants',
        ['email'],
        unique=True
    )


def downgrade() -> None:
    """Remove email and password_hash columns from merchants table."""
    # Drop index first
    op.drop_index('ix_merchants_email', table_name='merchants')

    # Drop columns
    op.drop_column('merchants', 'password_hash')
    op.drop_column('merchants', 'email')
