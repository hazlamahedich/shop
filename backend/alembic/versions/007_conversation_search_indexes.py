"""Search and filter optimization indexes for conversations.

Revision ID: 007_conversation_search_indexes
Revises: 006_webhook_verification_logs
Create Date: 2026-02-07

This migration adds indexes to optimize search and filter queries for conversations.
Adds GIN index with pg_trgm for message content search and ensures other indexes exist.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_conversation_search_indexes'
down_revision = '006_webhook_verification_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add search and filter optimization indexes."""

    # Enable pg_trgm extension for trigram-based text search
    # This enables efficient LIKE/ILIKE queries on text columns
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # Add GIN index for message content search (for bot messages which are plaintext)
    # This significantly improves ILIKE searches on message content
    # Note: Customer messages are encrypted, so this primarily helps with bot message search
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_messages_content_gin '
        'ON messages USING GIN (content gin_trgm_ops) '
        'WHERE sender = \'bot\''
    )

    # Verify/create indexes on conversations table for filtering
    # Most of these should already exist, but we ensure they're created

    # Index on merchant_id (should exist from initial migration)
    op.create_index(
        'ix_conversations_merchant_id',
        'conversations',
        ['merchant_id'],
        unique=False,
        if_not_exists=True
    )

    # Index on status for filtering
    op.create_index(
        'ix_conversations_status',
        'conversations',
        ['status'],
        unique=False,
        if_not_exists=True
    )

    # Index on created_at for date range filtering
    op.create_index(
        'ix_conversations_created_at',
        'conversations',
        ['created_at'],
        unique=False,
        if_not_exists=True
    )

    # Index on updated_at (should exist, but ensure it's there)
    op.create_index(
        'ix_conversations_updated_at',
        'conversations',
        ['updated_at'],
        unique=False,
        if_not_exists=True
    )

    # Index on platform_sender_id for customer ID search
    # This enables efficient ILIKE searches on customer IDs
    op.create_index(
        'ix_conversations_platform_sender_id',
        'conversations',
        ['platform_sender_id'],
        unique=False,
        if_not_exists=True
    )


def downgrade() -> None:
    """Remove search and filter optimization indexes."""

    # Drop GIN index on message content
    op.execute('DROP INDEX IF EXISTS ix_messages_content_gin')

    # Drop indexes on conversations
    op.drop_index('ix_conversations_platform_sender_id', table_name='conversations')
    op.drop_index('ix_conversations_updated_at', table_name='conversations')
    op.drop_index('ix_conversations_created_at', table_name='conversations')
    op.drop_index('ix_conversations_status', table_name='conversations')
    # Note: We don't drop merchant_id index as it's a foreign key

    # Note: We don't drop the pg_trgm extension as other migrations might use it
    # To properly remove it: DROP EXTENSION pg_trgm; (but only if no other dependencies)
