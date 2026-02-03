"""Alembic migration for Shopify integrations table.

Revision ID: 003_shopify_integrations
Revises: 002_facebook_integrations
Create Date: 2026-02-03

This migration creates the shopify_integrations table for storing
Shopify store connection details including encrypted Admin API
and Storefront API access tokens.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_shopify_integrations'
down_revision = '002_facebook_integrations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create shopify_integrations table."""

    # Create shopify_status enum type
    shopify_status_enum = postgresql.ENUM(
        'pending',
        'active',
        'error',
        name='shopify_status',
        create_type=True,
    )

    # Create shopify_integrations table
    op.create_table(
        'shopify_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('shop_domain', sa.String(length=255), nullable=False),
        sa.Column('shop_name', sa.String(length=255), nullable=False),
        sa.Column('storefront_token_encrypted', sa.String(length=500), nullable=False),
        sa.Column('admin_token_encrypted', sa.String(length=500), nullable=False),
        sa.Column('scopes', postgresql.JSONB(), nullable=False),
        sa.Column('status', shopify_status_enum, nullable=True, server_default='pending'),
        sa.Column('storefront_api_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('admin_api_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('webhook_subscribed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('webhook_topic_subscriptions', postgresql.JSONB(), nullable=True),
        sa.Column('last_webhook_at', sa.DateTime(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id'),
        sa.UniqueConstraint('shop_domain'),
    )
    op.create_index('ix_shopify_integrations_merchant_id', 'shopify_integrations', ['merchant_id'])
    op.create_index('ix_shopify_integrations_shop_domain', 'shopify_integrations', ['shop_domain'])


def downgrade() -> None:
    """Drop shopify_integrations table."""

    # Drop indexes
    op.drop_index('ix_shopify_integrations_shop_domain', table_name='shopify_integrations')
    op.drop_index('ix_shopify_integrations_merchant_id', table_name='shopify_integrations')

    # Drop table
    op.drop_table('shopify_integrations')

    # Drop enum type
    shopify_status_enum = postgresql.ENUM(name='shopify_status')
    shopify_status_enum.drop(op.get_bind())
