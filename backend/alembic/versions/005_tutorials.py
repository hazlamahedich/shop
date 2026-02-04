"""Interactive Tutorial table.

Revision ID: 005_tutorials
Revises: 004_llm_configurations
Create Date: 2026-02-04

This migration creates the tutorials table for tracking merchant
tutorial progress through the interactive onboarding flow.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_tutorials'
down_revision = '004_llm_configurations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tutorials table."""

    # Create tutorials table
    op.create_table(
        'tutorials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('completed_steps', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('skipped', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tutorial_version', sa.String(length=10), nullable=False, server_default='1.0'),
        sa.Column('steps_total', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id'),
    )
    op.create_index('ix_tutorials_merchant_id', 'tutorials', ['merchant_id'])


def downgrade() -> None:
    """Drop tutorials table."""

    # Drop indexes
    op.drop_index('ix_tutorials_merchant_id', table_name='tutorials')

    # Drop tutorials table
    op.drop_table('tutorials')
