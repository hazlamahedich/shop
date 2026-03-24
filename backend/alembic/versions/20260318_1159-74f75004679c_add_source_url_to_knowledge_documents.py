"""add_source_url_to_knowledge_documents

Revision ID: 74f75004679c
Revises:
Create Date: 2026-03-18 11:59:35.221870

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "74f75004679c"
down_revision: str | None = "widget_analytics_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_documents",
        sa.Column("source_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("knowledge_documents", "source_url")
