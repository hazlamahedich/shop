"""Add retention audit fields

Revision ID: 038
Revises: 037_add_data_tier_columns
Create Date: 2026-03-05

Story 6-5: 30-Day Retention Enforcement
Task 2.3: Add retention metadata to audit logs

Adds:
- retention_period_days: Retention period for automated deletions
- deletion_trigger: Manual vs automated deletion tracking
"""

import sqlalchemy as sa

from alembic import op

revision = "038"
down_revision = "037_data_tier_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "retention_period_days",
            sa.Integer(),
            nullable=True,
            comment="Retention period in days for automated deletions (null for manual)",
        ),
    )

    # Create enum type only if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE deletion_trigger AS ENUM ('manual', 'auto');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)

    op.add_column(
        "deletion_audit_log",
        sa.Column(
            "deletion_trigger",
            sa.Enum("manual", "auto", name="deletion_trigger", create_type=False),
            nullable=False,
            server_default="manual",
            comment="Whether deletion was manual (user-requested) or automated (retention policy)",
        ),
    )


def downgrade() -> None:
    op.drop_column("deletion_audit_log", "deletion_trigger")
    op.execute("DROP TYPE deletion_trigger")
    op.drop_column("deletion_audit_log", "retention_period_days")
