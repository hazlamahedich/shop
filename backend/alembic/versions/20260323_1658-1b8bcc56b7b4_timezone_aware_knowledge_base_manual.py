"""timezone_aware_knowledge_base_manual

Revision ID: 1b8bcc56b7b4
Revises: 20260322_1218_faq_interaction_logs
Create Date: 2026-03-23 16:58:00.145113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b8bcc56b7b4'
down_revision: Union[str, None] = '20260322_1218_faq_interaction_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert knowledge_documents created_at and updated_at to timezone-aware
    op.alter_column('knowledge_documents', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               postgresql_using='created_at AT TIME ZONE \'UTC\'')
    op.alter_column('knowledge_documents', 'updated_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               postgresql_using='updated_at AT TIME ZONE \'UTC\'')
               
    # Convert document_chunks created_at to timezone-aware
    op.alter_column('document_chunks', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.DateTime(timezone=True),
               postgresql_using='created_at AT TIME ZONE \'UTC\'')


def downgrade() -> None:
    # Convert knowledge_documents back to naive timestamps
    op.alter_column('knowledge_documents', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               postgresql_using='created_at AT TIME ZONE \'UTC\'')
    op.alter_column('knowledge_documents', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               postgresql_using='updated_at AT TIME ZONE \'UTC\'')
               
    # Convert document_chunks back to naive timestamps
    op.alter_column('document_chunks', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               postgresql_using='created_at AT TIME ZONE \'UTC\'')
