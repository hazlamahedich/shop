"""Add store_provider column to merchants

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

Revision ID: 016
Revises: 015_add_use_custom_greeting
Create Date: 2026-02-13

Changes:
1. Add store_provider VARCHAR(20) column to merchants table
2. Default value 'none' (no store connected)
3. Create index for common query pattern
4. Migrate existing Shopify merchants to 'shopify' value
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016_add_store_provider'
down_revision = '015_add_use_custom_greeting'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add store_provider column and migrate existing Shopify merchants."""
    # Add the column with default 'none' and NOT NULL constraint
    op.add_column(
        'merchants',
        sa.Column(
            'store_provider',
            sa.String(20),
            nullable=False,
            server_default='none',
        ),
    )

    # Create index for the store_provider column
    op.create_index(
        'idx_merchants_store_provider',
        'merchants',
        ['store_provider'],
    )

    # Migrate existing merchants with Shopify integrations to 'shopify'
    # This uses a subquery to find merchants that have a corresponding
    # record in the shopify_integrations table
    op.execute("""
        UPDATE merchants
        SET store_provider = 'shopify'
        WHERE id IN (
            SELECT merchant_id FROM shopify_integrations
        )
    """)


def downgrade() -> None:
    """Remove store_provider column."""
    op.drop_index('idx_merchants_store_provider', 'merchants')
    op.drop_column('merchants', 'store_provider')
