"""add_password_reset_tokens

Revision ID: 032_add_password_reset_tokens
Revises: 746061b0e712
Create Date: 2026-04-03 12:10:00.000000

Password Reset Flow - Add password_reset_tokens table.

This migration creates the password_reset_tokens table to support
password reset functionality. Tokens are valid for 1 hour and can
only be used once.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '032_add_password_reset_tokens'
down_revision: Union[str, None] = '746061b0e712'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create password_reset_tokens table."""

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['merchant_id'],
            ['merchants.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )

    # Create indexes for efficient lookups
    op.create_index(
        'ix_password_reset_tokens_merchant_id',
        'password_reset_tokens',
        ['merchant_id'],
    )
    op.create_index(
        'ix_password_reset_tokens_merchant_token',
        'password_reset_tokens',
        ['merchant_id', 'token'],
    )


def downgrade() -> None:
    """Drop password_reset_tokens table."""

    op.drop_index('ix_password_reset_tokens_merchant_token', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_merchant_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
