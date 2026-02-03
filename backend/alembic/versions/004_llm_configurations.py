"""LLM Configuration tables.

Revision ID: 004_llm_configurations
Revises: 003_shopify_integrations
Create Date: 2026-02-03

This migration creates the llm_configurations and llm_conversation_costs
tables for storing LLM provider settings and tracking per-conversation costs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_llm_configurations'
down_revision = '003_shopify_integrations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create llm_configurations and llm_conversation_costs tables."""

    # Create llm_provider enum type
    llm_provider_enum = postgresql.ENUM(
        'ollama',
        'openai',
        'anthropic',
        'gemini',
        'glm',
        name='llm_provider',
        create_type=True,
    )

    # Create llm_status enum type
    llm_status_enum = postgresql.ENUM(
        'pending',
        'active',
        'error',
        name='llm_status',
        create_type=True,
    )

    # Create llm_configurations table
    op.create_table(
        'llm_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('provider', llm_provider_enum, nullable=False),
        sa.Column('ollama_url', sa.String(length=500), nullable=True),
        sa.Column('ollama_model', sa.String(length=100), nullable=True),
        sa.Column('api_key_encrypted', sa.String(length=500), nullable=True),
        sa.Column('cloud_model', sa.String(length=100), nullable=True),
        sa.Column('backup_provider', sa.String(length=50), nullable=True),
        sa.Column('backup_api_key_encrypted', sa.String(length=500), nullable=True),
        sa.Column('status', llm_status_enum, nullable=False, server_default='pending'),
        sa.Column('configured_at', sa.DateTime(), nullable=False),
        sa.Column('last_test_at', sa.DateTime(), nullable=True),
        sa.Column('test_result', postgresql.JSONB(), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id'),
    )
    op.create_index('ix_llm_configurations_merchant_id', 'llm_configurations', ['merchant_id'])
    op.create_index('ix_llm_configurations_provider', 'llm_configurations', ['provider'])
    op.create_index('ix_llm_configurations_status', 'llm_configurations', ['status'])

    # Create llm_conversation_costs table for granular cost tracking
    op.create_table(
        'llm_conversation_costs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('input_cost_usd', sa.Float(), nullable=False),
        sa.Column('output_cost_usd', sa.Float(), nullable=False),
        sa.Column('total_cost_usd', sa.Float(), nullable=False),
        sa.Column('request_timestamp', sa.DateTime(), nullable=False),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_llm_conversation_costs_conversation_id',
        'llm_conversation_costs',
        ['conversation_id']
    )
    op.create_index(
        'ix_llm_conversation_costs_merchant_id',
        'llm_conversation_costs',
        ['merchant_id']
    )
    op.create_index(
        'ix_llm_conversation_costs_provider',
        'llm_conversation_costs',
        ['provider']
    )
    op.create_index(
        'ix_llm_conversation_costs_request_timestamp',
        'llm_conversation_costs',
        ['request_timestamp']
    )


def downgrade() -> None:
    """Drop llm_conversation_costs and llm_configurations tables."""

    # Drop indexes for llm_conversation_costs
    op.drop_index('ix_llm_conversation_costs_request_timestamp', table_name='llm_conversation_costs')
    op.drop_index('ix_llm_conversation_costs_provider', table_name='llm_conversation_costs')
    op.drop_index('ix_llm_conversation_costs_merchant_id', table_name='llm_conversation_costs')
    op.drop_index('ix_llm_conversation_costs_conversation_id', table_name='llm_conversation_costs')

    # Drop llm_conversation_costs table
    op.drop_table('llm_conversation_costs')

    # Drop indexes for llm_configurations
    op.drop_index('ix_llm_configurations_status', table_name='llm_configurations')
    op.drop_index('ix_llm_configurations_provider', table_name='llm_configurations')
    op.drop_index('ix_llm_configurations_merchant_id', table_name='llm_configurations')

    # Drop llm_configurations table
    op.drop_table('llm_configurations')

    # Drop enum types
    llm_status_enum = postgresql.ENUM(name='llm_status')
    llm_status_enum.drop(op.get_bind())

    llm_provider_enum = postgresql.ENUM(name='llm_provider')
    llm_provider_enum.drop(op.get_bind())
