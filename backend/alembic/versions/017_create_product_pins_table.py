"""Create product_pins table.

Story 1.15: Product Highlight Pins

Revision ID: 017_create_product_pins_table
Create Date: 2026-02-12
Revises: 016_add_store_provider

Adds:
- product_pins table with merchant's pinned products
- Foreign key constraint to merchants table with CASCADE delete
- Indexes on merchant_id, product_id, and pinned_order
- Unique constraint on merchant_id + product_id (one pin per product)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "017_create_product_pins_table"
down_revision = "016_add_store_provider"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create product_pins table and related constraints."""
    # Create product_pins table
    op.create_table(
        "product_pins",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(255), nullable=False),
        sa.Column("product_title", sa.String(255), nullable=False),
        sa.Column("product_image_url", sa.String(500), nullable=True),
        sa.Column(
            "pinned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("pinned_order", sa.Integer(), nullable=False, server_default="0"),
    )

    # Create unique constraint on merchant_id + product_id (one pin per product)
    op.execute(
        "CREATE UNIQUE INDEX uq_product_pins_merchant_product ON product_pins (merchant_id, product_id)"
    )

    # Create index on merchant_id for efficient lookups
    op.create_index("ix_product_pins_merchant_id", "product_pins", ["merchant_id"])

    # Create index on product_id for quick existence checks
    op.create_index("ix_product_pins_product_id", "product_pins", ["product_id"])

    # Create index on pinned_order for ordered retrieval
    op.create_index("ix_product_pins_pinned_order", "product_pins", ["merchant_id", "pinned_order"])


def downgrade() -> None:
    """Remove product_pins table and related constraints."""
    # Drop indexes
    op.drop_index("ix_product_pins_pinned_order", table_name="product_pins")
    op.drop_index("ix_product_pins_product_id", table_name="product_pins")
    op.drop_index("ix_product_pins_merchant_id", table_name="product_pins")

    # Drop unique constraint
    op.execute("DROP INDEX IF EXISTS uq_product_pins_merchant_product")

    # Drop table
    op.drop_table("product_pins")
