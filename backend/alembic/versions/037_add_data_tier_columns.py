"""Add data_tier columns for GDPR/CCPA compliance.

Revision ID: 037_add_data_tier_columns
Revises: 036_add_data_export_audit_log
Create Date: 2026-03-05

Story 6-4: Data Tier Separation

Adds:
- DataTier ENUM type: 'voluntary', 'operational', 'anonymized'
- data_tier column to conversations table (default: VOLUNTARY)
- data_tier column to messages table (default: VOLUNTARY)
- data_tier column to orders table (default: OPERATIONAL)
- Composite indexes (data_tier, created_at) for retention queries
- Backfill existing records with appropriate tier values

Data Tier Definitions:
- VOLUNTARY: User preferences, conversation history (30-day retention, deletable)
- OPERATIONAL: Order references, business data (indefinite retention, exempt from deletion)
- ANONYMIZED: Aggregated analytics, no PII (indefinite retention, no privacy impact)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "037_data_tier_columns"
down_revision = "036_export_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add data tier columns and indexes for GDPR/CCPA compliance."""

    # Step 1: Create DataTier ENUM type
    data_tier_enum = sa.Enum(
        "voluntary",
        "operational",
        "anonymized",
        name="datatier",
    )
    data_tier_enum.create(op.get_bind(), checkfirst=True)

    # Step 2: Add data_tier to conversations table (default: VOLUNTARY)
    op.add_column(
        "conversations",
        sa.Column(
            "data_tier",
            sa.Enum(
                "voluntary",
                "operational",
                "anonymized",
                name="datatier",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # Step 3: Backfill existing conversations with VOLUNTARY tier
    op.execute(
        """
        UPDATE conversations
        SET data_tier = 'voluntary'
        WHERE data_tier IS NULL;
        """
    )

    # Step 4: Make data_tier NOT NULL with default
    op.alter_column(
        "conversations",
        "data_tier",
        nullable=False,
        server_default="voluntary",
    )

    # Step 5: Create composite index on conversations
    op.create_index(
        "ix_conversations_tier_created",
        "conversations",
        ["data_tier", "created_at"],
    )

    # Step 6: Add data_tier to messages table (default: VOLUNTARY)
    op.add_column(
        "messages",
        sa.Column(
            "data_tier",
            sa.Enum(
                "voluntary",
                "operational",
                "anonymized",
                name="datatier",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # Step 7: Backfill existing messages with VOLUNTARY tier
    op.execute(
        """
        UPDATE messages
        SET data_tier = 'voluntary'
        WHERE data_tier IS NULL;
        """
    )

    # Step 8: Make data_tier NOT NULL with default
    op.alter_column(
        "messages",
        "data_tier",
        nullable=False,
        server_default="voluntary",
    )

    # Step 9: Create composite index on messages
    op.create_index(
        "ix_messages_tier_created",
        "messages",
        ["data_tier", "created_at"],
    )

    # Step 10: Add data_tier to orders table (default: OPERATIONAL)
    op.add_column(
        "orders",
        sa.Column(
            "data_tier",
            sa.Enum(
                "voluntary",
                "operational",
                "anonymized",
                name="datatier",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # Step 11: Backfill existing orders with OPERATIONAL tier
    op.execute(
        """
        UPDATE orders
        SET data_tier = 'operational'
        WHERE data_tier IS NULL;
        """
    )

    # Step 12: Make data_tier NOT NULL with default
    op.alter_column(
        "orders",
        "data_tier",
        nullable=False,
        server_default="operational",
    )

    # Step 13: Create composite index on orders
    op.create_index(
        "ix_orders_tier_created",
        "orders",
        ["data_tier", "created_at"],
    )


def downgrade() -> None:
    """Remove data tier columns and indexes."""

    # Drop indexes
    op.drop_index("ix_orders_tier_created", table_name="orders")
    op.drop_index("ix_messages_tier_created", table_name="messages")
    op.drop_index("ix_conversations_tier_created", table_name="conversations")

    # Drop columns
    op.drop_column("orders", "data_tier")
    op.drop_column("messages", "data_tier")
    op.drop_column("conversations", "data_tier")

    # Drop ENUM type
    sa.Enum(name="datatier").drop(op.get_bind(), checkfirst=True)
