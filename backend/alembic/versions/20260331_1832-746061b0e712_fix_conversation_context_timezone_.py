"""fix_conversation_context_timezone_columns

Revision ID: 746061b0e712
Revises: xtrwpjgs
Create Date: 2026-03-31 18:32:00.000000

Story 11-1 Fix: Change datetime columns to TIMESTAMPTZ for timezone-aware datetimes.

The initial migration created TIMESTAMP WITHOUT TIME ZONE columns, but our
Python code uses timezone-aware datetimes (datetime.now(timezone.utc)).
This migration alters the columns to TIMESTAMP WITH TIME ZONE to fix the
"can't subtract offset-naive and offset-aware datetimes" error.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '746061b0e712'
down_revision: Union[str, None] = 'xtrwpjgs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Alter datetime columns to TIMESTAMPTZ."""

    # conversation_context table
    op.execute("ALTER TABLE conversation_context ALTER COLUMN last_summarized_at TYPE TIMESTAMPTZ USING last_summarized_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_context ALTER COLUMN expires_at TYPE TIMESTAMPTZ USING expires_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_context ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_context ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # conversation_turns table
    op.execute("ALTER TABLE conversation_turns ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Revert datetime columns to TIMESTAMP (no timezone)."""

    # conversation_context table
    op.execute("ALTER TABLE conversation_context ALTER COLUMN last_summarized_at TYPE TIMESTAMP USING last_summarized_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_context ALTER COLUMN expires_at TYPE TIMESTAMP USING expires_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_context ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_context ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'")

    # conversation_turns table
    op.execute("ALTER TABLE conversation_turns ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'")
