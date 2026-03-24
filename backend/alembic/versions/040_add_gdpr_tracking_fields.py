"""Add GDPR tracking fields to deletion_audit_log

Revision ID: 040
Revises: 039
Create Date: 2026-03-06

Story 6-6: GDPR Deletion Processing
- Add customer_id for GDPR-level tracking
- Add request_type enum (manual, gdpr_formal, ccpa_request)
- Add request_timestamp for when GDPR request was received
- Add processing_deadline for 30-day compliance window
- Add completion_date for when GDPR deletion was actually completed
- Add confirmation_email_sent flag
- Add email_sent_at timestamp
- Add compliance index on (processing_deadline, completion_date)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for deletion_request_type
    request_type_enum = postgresql.ENUM(
        "manual", "gdpr_formal", "ccpa_request", name="deletion_request_type", create_type=False
    )

    # Create the enum type if it doesn't exist
    op.execute(
        "CREATE TYPE deletion_request_type AS ENUM ('manual', 'gdpr_formal', 'ccpa_request')"
    )

    # Add customer_id column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "customer_id",
            sa.String(100),
            nullable=True,
            comment="Customer ID for GDPR-level tracking (optional)",
        ),
    )

    # Add index on customer_id
    op.create_index(
        "ix_deletion_audit_log_customer_id", "deletion_audit_log", ["customer_id"], unique=False
    )

    # Add request_type column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "request_type",
            request_type_enum,
            nullable=True,
            default="manual",
            comment="Type of GDPR/CCPA deletion request",
        ),
    )

    # Add request_timestamp column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "request_timestamp",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When GDPR request was received",
        ),
    )

    # Add processing_deadline column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "processing_deadline",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="30-day deadline from request",
        ),
    )

    # Add completion_date column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "completion_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When GDPR deletion was actually completed",
        ),
    )

    # Add confirmation_email_sent column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "confirmation_email_sent",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether confirmation email was sent",
        ),
    )

    # Add email_sent_at column
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "email_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When confirmation email was sent",
        ),
    )

    # Add compliance index for GDPR monitoring
    op.create_index(
        "ix_deletion_audit_log_gdpr_compliance",
        "deletion_audit_log",
        ["processing_deadline", "completion_date"],
        unique=False,
    )


def downgrade() -> None:
    # Drop compliance index
    op.drop_index("ix_deletion_audit_log_gdpr_compliance", table_name="deletion_audit_log")

    # Drop email_sent_at column
    op.drop_column("deletion_audit_log", "email_sent_at")

    # Drop confirmation_email_sent column
    op.drop_column("deletion_audit_log", "confirmation_email_sent")

    # Drop completion_date column
    op.drop_column("deletion_audit_log", "completion_date")

    # Drop processing_deadline column
    op.drop_column("deletion_audit_log", "processing_deadline")

    # Drop request_timestamp column
    op.drop_column("deletion_audit_log", "request_timestamp")

    # Drop request_type column
    op.drop_column("deletion_audit_log", "request_type")

    # Drop customer_id index
    op.drop_index("ix_deletion_audit_log_customer_id", table_name="deletion_audit_log")

    # Drop customer_id column
    op.drop_column("deletion_audit_log", "customer_id")

    # Drop enum type
    op.execute("DROP TYPE deletion_request_type")
