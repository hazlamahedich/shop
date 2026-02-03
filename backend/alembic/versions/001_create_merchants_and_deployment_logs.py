"""Create merchants and deployment_logs tables.

Revision ID: 001_create_merchants
Revises:
Create Date: 2026-02-03

This migration creates the core merchant and deployment log tables
for tracking bot deployments to cloud platforms.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_merchants'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create merchants, prerequisite_checklists, and deployment_logs tables."""
    # Create merchant_status enum type (it will be created implicitly)
    merchant_status_enum = postgresql.ENUM(
        'pending',
        'active',
        'failed',
        name='merchant_status',
        create_type=True,
    )

    # Create merchants table
    op.create_table(
        'merchants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_key', sa.String(length=50), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('status', merchant_status_enum, nullable=True),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('secret_key_hash', sa.String(length=100), nullable=True),
        sa.Column('deployed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_key'),
    )
    op.create_index('ix_merchants_merchant_key', 'merchants', ['merchant_key'])

    # Create prerequisite_checklists table
    op.create_table(
        'prerequisite_checklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('has_cloud_account', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_facebook_account', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_shopify_access', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_llm_provider_choice', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create deployment_logs table
    op.create_table(
        'deployment_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deployment_id', sa.String(length=36), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(length=10), nullable=False),
        sa.Column('step', sa.String(length=50), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deployment_logs_deployment_id', 'deployment_logs', ['deployment_id'])
    op.create_index('ix_deployment_logs_timestamp', 'deployment_logs', ['timestamp'])


def downgrade() -> None:
    """Drop merchants, prerequisite_checklists, and deployment_logs tables."""
    # Drop deployment_logs table
    op.drop_index('ix_deployment_logs_timestamp', table_name='deployment_logs')
    op.drop_index('ix_deployment_logs_deployment_id', table_name='deployment_logs')
    op.drop_table('deployment_logs')

    # Drop prerequisite_checklists table
    op.drop_table('prerequisite_checklists')

    # Drop merchants table
    op.drop_index('ix_merchants_merchant_key', table_name='merchants')
    op.drop_table('merchants')

    # Drop merchant_status enum type
    merchant_status_enum = postgresql.ENUM(
        name='merchant_status',
    )
    merchant_status_enum.drop(op.get_bind())
