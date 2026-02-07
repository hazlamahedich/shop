"""Add LLM provider tracking to conversations.

Revision ID: 008_conversation_llm_provider
Revises: 007_conversation_search_indexes
Create Date: 2026-02-07

This migration adds the llm_provider column to the conversations table
to track which LLM provider was used for each conversation.
This enables accurate cost tracking per conversation when providers are switched.

Story: 3.4 - LLM Provider Switching
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_conversation_llm_provider'
down_revision = '007_conversation_search_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add llm_provider column and index to conversations table."""

    # Add llm_provider column to conversations table
    # This tracks which LLM provider (ollama, openai, anthropic, gemini, glm)
    # was used for each conversation for accurate cost tracking
    op.add_column(
        'conversations',
        sa.Column(
            'llm_provider',
            sa.String(50),
            nullable=True,
            comment='LLM provider used for this conversation (e.g., ollama, openai, anthropic)'
        )
    )

    # Create index on llm_provider for efficient queries
    # This supports filtering conversations by provider for cost analysis
    op.create_index(
        'ix_conversations_llm_provider',
        'conversations',
        ['llm_provider'],
        unique=False,
        if_not_exists=True
    )

    # Note: Existing conversations will have NULL llm_provider
    # New conversations will automatically have the provider set
    # based on the merchant's current provider configuration


def downgrade() -> None:
    """Remove llm_provider column and index from conversations table."""

    # Drop the index first
    op.drop_index('ix_conversations_llm_provider', table_name='conversations')

    # Drop the column
    op.drop_column('conversations', 'llm_provider')
