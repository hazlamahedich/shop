"""add_deletion_audit_log

Revision ID: 035_deletion_audit
Revises: 034_add_visitor_id_to_consents
Create Date: 2026-02-26 00:00:00.000000

Story 6-2: Request Data Deletion

Creates deletion_audit_log table for GDPR/CCPA compliance audit trail.
Tracks all immediate "forget preferences" deletions with counts and timestamps.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "035_deletion_audit"
down_revision: Union[str, None] = "034_add_visitor_id_to_consents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deletion_audit_log",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "visitor_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "conversations_deleted",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "messages_deleted",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "redis_keys_cleared",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "failed_redis_keys",
            sa.Text(),
            nullable=True,
            comment="JSON array of Redis keys that failed to delete for retry",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_deletion_audit_log_session_id",
        "deletion_audit_log",
        ["session_id"],
    )
    op.create_index(
        "ix_deletion_audit_log_visitor_id",
        "deletion_audit_log",
        ["visitor_id"],
    )
    op.create_index(
        "ix_deletion_audit_log_merchant_id",
        "deletion_audit_log",
        ["merchant_id"],
    )
    op.create_index(
        "ix_deletion_audit_log_merchant_requested",
        "deletion_audit_log",
        ["merchant_id", "requested_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_deletion_audit_log_merchant_requested", table_name="deletion_audit_log")
    op.drop_index("ix_deletion_audit_log_merchant_id", table_name="deletion_audit_log")
    op.drop_index("ix_deletion_audit_log_visitor_id", table_name="deletion_audit_log")
    op.drop_index("ix_deletion_audit_log_session_id", table_name="deletion_audit_log")
    op.drop_table("deletion_audit_log")
