"""add_onboarding_mode_to_merchant

Revision ID: d518bbce67eb
Revises: 506c5de07ae8
Create Date: 2026-03-11 11:33:49.004890

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d518bbce67eb"
down_revision: str | None = "506c5de07ae8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "merchants",
        sa.Column(
            "onboarding_mode",
            sa.String(20),
            nullable=False,
            server_default="general",
        ),
    )
    op.create_index("ix_merchants_onboarding_mode", "merchants", ["onboarding_mode"])
    op.create_check_constraint(
        "chk_onboarding_mode",
        "merchants",
        "onboarding_mode IN ('general', 'ecommerce')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_onboarding_mode", "merchants", type_="check")
    op.drop_index("ix_merchants_onboarding_mode", table_name="merchants")
    op.drop_column("merchants", "onboarding_mode")
