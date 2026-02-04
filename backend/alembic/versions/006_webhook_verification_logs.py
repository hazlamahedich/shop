"""Webhook Verification Logs table.

Revision ID: 006_webhook_verification_logs
Revises: 005_tutorials
Create Date: 2026-02-04

This migration creates the webhook_verification_logs table for tracking
webhook verification tests, including status checks, test webhooks,
and re-subscriptions for troubleshooting purposes.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_webhook_verification_logs'
down_revision = '005_tutorials'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create webhook_verification_logs table and add columns to integration tables."""

    # Create webhook_verification_logs table
    op.create_table(
        'webhook_verification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('facebook', 'shopify', name='verification_platform', create_type=False), nullable=False),
        sa.Column('test_type', sa.Enum('status_check', 'test_webhook', 'resubscribe', name='test_type', create_type=False), nullable=False),
        sa.Column('status', sa.Enum('pending', 'success', 'failed', name='verification_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('diagnostic_data', postgresql.JSONB(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_verification_logs_merchant_id', 'webhook_verification_logs', ['merchant_id'])
    op.create_index('ix_webhook_verification_logs_platform', 'webhook_verification_logs', ['platform'])

    # Add last_webhook_verified_at column to facebook_integrations
    op.add_column(
        'facebook_integrations',
        sa.Column('last_webhook_verified_at', sa.DateTime(), nullable=True)
    )

    # Add last_webhook_verified_at column to shopify_integrations
    op.add_column(
        'shopify_integrations',
        sa.Column('last_webhook_verified_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Drop webhook_verification_logs table and remove columns from integration tables."""

    # Drop indexes
    op.drop_index('ix_webhook_verification_logs_platform', table_name='webhook_verification_logs')
    op.drop_index('ix_webhook_verification_logs_merchant_id', table_name='webhook_verification_logs')

    # Drop webhook_verification_logs table
    op.drop_table('webhook_verification_logs')

    # Remove last_webhook_verified_at from shopify_integrations
    op.drop_column('shopify_integrations', 'last_webhook_verified_at')

    # Remove last_webhook_verified_at from facebook_integrations
    op.drop_column('facebook_integrations', 'last_webhook_verified_at')
