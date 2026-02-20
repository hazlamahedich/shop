"""Make storefront_token_encrypted nullable.

Revision ID: 024_shopify_nullable_storefront_token
Revises: 023_add_widget_config
Create Date: 2026-02-20

Storefront access tokens are no longer required since we use
tokenless Storefront API and direct checkout URLs.
"""

from alembic import op
import sqlalchemy as sa

revision = "024_nullable_storefront_tkn"
down_revision = "023_add_widget_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "shopify_integrations",
        "storefront_token_encrypted",
        existing_type=sa.String(length=500),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "shopify_integrations",
        "storefront_token_encrypted",
        existing_type=sa.String(length=500),
        nullable=False,
    )
