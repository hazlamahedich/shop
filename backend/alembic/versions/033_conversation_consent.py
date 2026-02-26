"""add_conversation_consent_fields

Revision ID: 033_consent_conversation
Revises: 032_add_disputes_table
Create Date: 2026-02-25 12:00:00.000000

Story 6-1: Opt-In Consent Flow

Adds fields to consents table for conversation data consent:
- source_channel: Track where consent was collected (messenger, widget, preview)
- consent_message_shown: Track if consent prompt was shown to user
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "033_consent_conversation"
down_revision: Union[str, None] = "032_add_disputes_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "consents",
        sa.Column(
            "source_channel",
            sa.String(20),
            nullable=True,
        ),
    )
    op.add_column(
        "consents",
        sa.Column(
            "consent_message_shown",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("consents", "consent_message_shown")
    op.drop_column("consents", "source_channel")
