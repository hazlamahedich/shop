"""Integration tests for Story 6-4: Data Tier Migration (037).

Tests verify:
- DataTier ENUM type exists with correct values
- data_tier column added to conversations, messages, orders tables
- Composite indexes created for retention queries
- Default values set correctly
- Backfill completed for existing records
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestDataTierMigration:
    """Test suite for migration 037_add_data_tier_columns.py."""

    async def test_datatier_enum_exists(self, db_session: AsyncSession) -> None:
        """Test that DataTier ENUM type exists with correct values."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT enumlabel
                    FROM pg_enum
                    JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
                    WHERE pg_type.typname = 'datatier'
                    ORDER BY enumsortorder;
                    """
                )
            )
            enum_values = [row[0] for row in result.fetchall()]

            assert "voluntary" in enum_values, "DataTier ENUM missing 'voluntary' value"
            assert "operational" in enum_values, "DataTier ENUM missing 'operational' value"
            assert "anonymized" in enum_values, "DataTier ENUM missing 'anonymized' value"
            assert len(enum_values) == 3, f"Expected 3 enum values, got {len(enum_values)}"

    async def test_conversations_has_data_tier_column(self, db_session: AsyncSession) -> None:
        """Test that conversations table has data_tier column with default VOLUNTARY."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'conversations'
                      AND column_name = 'data_tier';
                    """
                )
            )
            row = result.fetchone()

            assert row is not None, "conversations.data_tier column not found"
            assert row[1] == "USER-DEFINED", f"Expected ENUM type, got {row[1]}"
            assert "voluntary" in (row[2] or ""), f"Expected default 'voluntary', got {row[2]}"

    async def test_messages_has_data_tier_column(self, db_session: AsyncSession) -> None:
        """Test that messages table has data_tier column with default VOLUNTARY."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'messages'
                      AND column_name = 'data_tier';
                    """
                )
            )
            row = result.fetchone()

            assert row is not None, "messages.data_tier column not found"
            assert row[1] == "USER-DEFINED", f"Expected ENUM type, got {row[1]}"
            assert "voluntary" in (row[2] or ""), f"Expected default 'voluntary', got {row[2]}"

    async def test_orders_has_data_tier_column(self, db_session: AsyncSession) -> None:
        """Test that orders table has data_tier column with default OPERATIONAL."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'orders'
                      AND column_name = 'data_tier';
                    """
                )
            )
            row = result.fetchone()

            assert row is not None, "orders.data_tier column not found"
            assert row[1] == "USER-DEFINED", f"Expected ENUM type, got {row[1]}"
            assert "operational" in (row[2] or ""), f"Expected default 'operational', got {row[2]}"

    async def test_conversations_composite_index_exists(self, db_session: AsyncSession) -> None:
        """Test that composite index (data_tier, created_at) exists on conversations."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'conversations'
                      AND indexname LIKE '%tier%created%';
                    """
                )
            )
            indexes = [row[0] for row in result.fetchall()]

            assert len(indexes) > 0, (
                "Composite index (data_tier, created_at) not found on conversations"
            )

    async def test_messages_composite_index_exists(self, db_session: AsyncSession) -> None:
        """Test that composite index (data_tier, created_at) exists on messages."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'messages'
                      AND indexname LIKE '%tier%created%';
                    """
                )
            )
            indexes = [row[0] for row in result.fetchall()]

            assert len(indexes) > 0, "Composite index (data_tier, created_at) not found on messages"

    async def test_orders_composite_index_exists(self, db_session: AsyncSession) -> None:
        """Test that composite index (data_tier, created_at) exists on orders."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'orders'
                      AND indexname LIKE '%tier%created%';
                    """
                )
            )
            indexes = [row[0] for row in result.fetchall()]

            assert len(indexes) > 0, "Composite index (data_tier, created_at) not found on orders"

    async def test_existing_conversations_backfilled(self, db_session: AsyncSession) -> None:
        """Test that existing conversation records have data_tier set to VOLUNTARY."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM conversations
                    WHERE data_tier IS NULL;
                    """
                )
            )
            null_count = result.scalar()

            assert null_count == 0, (
                f"Found {null_count} conversations with NULL data_tier (backfill incomplete)"
            )

    async def test_existing_messages_backfilled(self, db_session: AsyncSession) -> None:
        """Test that existing message records have data_tier set to VOLUNTARY."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM messages
                    WHERE data_tier IS NULL;
                    """
                )
            )
            null_count = result.scalar()

            assert null_count == 0, (
                f"Found {null_count} messages with NULL data_tier (backfill incomplete)"
            )

    async def test_existing_orders_backfilled(self, db_session: AsyncSession) -> None:
        """Test that existing order records have data_tier set to OPERATIONAL."""
        async with db_session as session:
            result = await session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM orders
                    WHERE data_tier IS NULL;
                    """
                )
            )
            null_count = result.scalar()

            assert null_count == 0, (
                f"Found {null_count} orders with NULL data_tier (backfill incomplete)"
            )

    async def test_migration_rollback_works(self, db_session: AsyncSession) -> None:
        """Test that migration can be rolled back successfully.

        Note: This test should be run manually after testing rollback.
        Marked as skip for automated test runs.
        """
        pytest.skip("Manual rollback test - run with: alembic downgrade -1")
