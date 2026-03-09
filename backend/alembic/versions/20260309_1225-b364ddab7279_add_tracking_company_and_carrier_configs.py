"""add_tracking_company_and_carrier_configs

Revision ID: b364ddab7279
Revises: 041
Create Date: 2026-03-09 12:25:50.666792

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b364ddab7279"
down_revision: Union[str, None] = "041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tracking_company column to orders table
    op.add_column("orders", sa.Column("tracking_company", sa.String(100), nullable=True))

    # Create carrier_configs table
    op.create_table(
        "carrier_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("carrier_name", sa.String(100), nullable=False),
        sa.Column("tracking_url_template", sa.String(500), nullable=False),
        sa.Column("tracking_number_pattern", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_carrier_configs_merchant", "carrier_configs", ["merchant_id"])
    op.create_index(
        "ix_carrier_configs_merchant_active", "carrier_configs", ["merchant_id", "is_active"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_carrier_configs_merchant_active", table_name="carrier_configs")
    op.drop_index("ix_carrier_configs_merchant", table_name="carrier_configs")

    # Drop carrier_configs table
    op.drop_table("carrier_configs")

    # Drop tracking_company column from orders table
    op.drop_column("orders", "tracking_company")
