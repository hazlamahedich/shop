"""add widget_config to merchants

Revision ID: 023_add_widget_config
Revises: 022_add_shopify_order_fields
Create Date: 2026-02-17

Story 5-1: Backend Widget API
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "023_add_widget_config"
down_revision = "022_add_shopify_order_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add widget_config JSONB column to merchants table."""
    op.add_column(
        "merchants",
        sa.Column(
            "widget_config",
            JSONB,
            nullable=True,
            server_default=sa.text("""
                '{
                    "enabled": true,
                    "bot_name": "Shopping Assistant",
                    "welcome_message": "Hi! How can I help you today?",
                    "theme": {
                        "primary_color": "#6366f1",
                        "background_color": "#ffffff",
                        "text_color": "#1f2937",
                        "position": "bottom-right",
                        "border_radius": 16
                    },
                    "allowed_domains": []
                }'::jsonb
            """),
        ),
    )


def downgrade() -> None:
    """Remove widget_config column from merchants table."""
    op.drop_column("merchants", "widget_config")
