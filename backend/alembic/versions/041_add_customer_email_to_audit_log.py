"""Add customer_email to deletion_audit_log

Revision ID: 041
Revises: 040
Create Date: 2026-03-08

Story 6-6: GDPR Deletion Processing
- Add customer_email column for queuing confirmation emails
- This column was missing from migration 040
"""

from alembic import op
import sqlalchemy as sa

revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "customer_email",
            sa.String(255),
            nullable=True,
            comment="Queued email address for confirmation email (deleted after sending)",
        ),
    )


def downgrade() -> None:
    op.drop_column("deletion_audit_log", "customer_email")
