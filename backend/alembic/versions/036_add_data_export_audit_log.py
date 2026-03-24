"""add_data_export_audit_log

Revision ID: 036_export_audit
Revises: 035_deletion_audit
Create Date: 2026-03-04 00:00:00.000000

Story 6-3: Merchant CSV Export

Creates data_export_audit_log table for GDPR/CCPA compliance audit trail.
Tracks all merchant data exports with counts and timestamps.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "036_export_audit"
down_revision: str | None = "035_deletion_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_export_audit_log",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
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
            "conversations_exported",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "messages_exported",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "opted_out_excluded",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="Number of opted-out conversations excluded (GDPR compliance)",
        ),
        sa.Column(
            "file_size_bytes",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_data_export_audit_log_merchant_id",
        "data_export_audit_log",
        ["merchant_id"],
    )
    op.create_index(
        "ix_export_audit_merchant_requested",
        "data_export_audit_log",
        ["merchant_id", "requested_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_export_audit_merchant_requested", table_name="data_export_audit_log")
    op.drop_index("ix_data_export_audit_log_merchant_id", table_name="data_export_audit_log")
    op.drop_table("data_export_audit_log")
