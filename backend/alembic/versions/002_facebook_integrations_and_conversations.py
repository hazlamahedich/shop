"""Create Facebook integrations, conversations, and messages tables.

Revision ID: 002_facebook_integrations
Revises: 001_create_merchants
Create Date: 2026-02-03

This migration creates tables for Facebook Page integration,
conversation tracking, and message storage.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_facebook_integrations'
down_revision = '001_create_merchants'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create facebook_integrations, conversations, and messages tables."""

    # Create facebook_status enum type
    facebook_status_enum = postgresql.ENUM(
        'pending',
        'active',
        'error',
        name='facebook_status',
        create_type=True,
    )

    # Create conversation_status enum type
    conversation_status_enum = postgresql.ENUM(
        'active',
        'handoff',
        'closed',
        name='conversation_status',
        create_type=True,
    )

    # Create message_sender enum type
    message_sender_enum = postgresql.ENUM(
        'customer',
        'bot',
        name='message_sender',
        create_type=True,
    )

    # Create message_type enum type
    message_type_enum = postgresql.ENUM(
        'text',
        'attachment',
        'postback',
        name='message_type',
        create_type=True,
    )

    # Create facebook_integrations table
    op.create_table(
        'facebook_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.String(length=50), nullable=False),
        sa.Column('page_name', sa.String(length=255), nullable=False),
        sa.Column('page_picture_url', sa.String(length=500), nullable=True),
        sa.Column('access_token_encrypted', sa.String(length=500), nullable=False),
        sa.Column('scopes', postgresql.JSONB(), nullable=False),
        sa.Column('status', facebook_status_enum, nullable=True),
        sa.Column('webhook_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('last_webhook_at', sa.DateTime(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id'),
    )
    op.create_index('ix_facebook_integrations_merchant_id', 'facebook_integrations', ['merchant_id'])
    op.create_index('ix_facebook_integrations_page_id', 'facebook_integrations', ['page_id'])

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('platform_sender_id', sa.String(length=100), nullable=False),
        sa.Column('status', conversation_status_enum, nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_merchant_id', 'conversations', ['merchant_id'])
    op.create_index('ix_conversations_platform_sender_id', 'conversations', ['platform_sender_id'])
    # Composite index for webhook deduplication
    op.create_index(
        'ix_conversations_platform_sender_created',
        'conversations',
        ['platform', 'platform_sender_id', 'created_at']
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender', message_sender_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', message_type_enum, nullable=False, server_default='text'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    """Drop facebook_integrations, conversations, and messages tables."""

    # Drop messages table
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')

    # Drop conversations table
    op.drop_index('ix_conversations_platform_sender_created', table_name='conversations')
    op.drop_index('ix_conversations_platform_sender_id', table_name='conversations')
    op.drop_index('ix_conversations_merchant_id', table_name='conversations')
    op.drop_table('conversations')

    # Drop facebook_integrations table
    op.drop_index('ix_facebook_integrations_page_id', table_name='facebook_integrations')
    op.drop_index('ix_facebook_integrations_merchant_id', table_name='facebook_integrations')
    op.drop_table('facebook_integrations')

    # Drop enum types
    message_type_enum = postgresql.ENUM(name='message_type')
    message_type_enum.drop(op.get_bind())

    message_sender_enum = postgresql.ENUM(name='message_sender')
    message_sender_enum.drop(op.get_bind())

    conversation_status_enum = postgresql.ENUM(name='conversation_status')
    conversation_status_enum.drop(op.get_bind())

    facebook_status_enum = postgresql.ENUM(name='facebook_status')
    facebook_status_enum.drop(op.get_bind())
