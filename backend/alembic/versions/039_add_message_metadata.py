"""Add message_metadata column to messages table

Revision ID: 039
Revises: 038_add_retention_audit_fields
Create Date: 2026-03-05

Story 6-5: 30-Day Retention Enforcement
Task: Add message_metadata column for storing additional message context

This column was defined in the Message model but missing from the initial migration.
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = '039'
down_revision = '038'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add message_metadata column to messages table
    op.add_column(
        'messages',
        sa.Column(
            'message_metadata',
            postgresql.JSONB,
            nullable=True,
            comment='Additional message context and metadata (encrypted for sensitive data)',
        ),
    )


def downgrade() -> None:
    op.drop_column('messages', 'message_metadata')
