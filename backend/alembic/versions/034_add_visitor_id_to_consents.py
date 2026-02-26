"""add_visitor_id_to_consents

Revision ID: 034_visitor_id_consent
Revises: 033_consent_conversation
Create Date: 2026-02-25 18:00:00.000000

Story 6-1: Opt-In Consent Flow Enhancement

Adds visitor_id column to consents table for privacy-friendly consent persistence.
Consent is now looked up by visitor_id (primary) or session_id (fallback).

This allows:
- Session data to clear on browser close (sessionStorage)
- Consent preferences to persist across sessions (localStorage visitor_id)
- Privacy-friendly approach: no session data persistence, only consent choice

Migration includes backfill of existing consent records.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "034_visitor_id_consent"
down_revision: Union[str, None] = "033_consent_conversation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "consents",
        sa.Column(
            "visitor_id",
            sa.String(100),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_consents_visitor_merchant",
        "consents",
        ["visitor_id", "merchant_id"],
    )

    op.execute(
        """
        UPDATE consents
        SET visitor_id = session_id
        WHERE visitor_id IS NULL
          AND consent_type = 'conversation';
        """
    )


def downgrade() -> None:
    op.drop_index("ix_consents_visitor_merchant", table_name="consents")
    op.drop_column("consents", "visitor_id")
