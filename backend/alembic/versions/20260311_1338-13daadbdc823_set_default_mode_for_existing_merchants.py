"""set_default_mode_for_existing_merchants

Revision ID: 13daadbdc823
Revises: d518bbce67eb
Create Date: 2026-03-11 13:38:39.384506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13daadbdc823'
down_revision: Union[str, None] = 'd518bbce67eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set default mode for existing merchants.
    
    Story 8.2: Set onboarding_mode to 'ecommerce' for existing merchants.
    
    Rationale:
    - Existing merchants have been through the onboarding flow
    - They likely have Shopify connections (backward compatible)
    - New merchants default to 'general' via model default
    - ONLY update NULL values to preserve explicitly set modes
    """
    op.execute(
        """
        UPDATE merchants 
        SET onboarding_mode = 'ecommerce' 
        WHERE onboarding_mode IS NULL;
        """
    )


def downgrade() -> None:
    """Revert mode changes.
    
    Story 8.2: Reset onboarding_mode to NULL for affected merchants.
    """
    op.execute(
        """
        UPDATE merchants 
        SET onboarding_mode = NULL 
        WHERE onboarding_mode = 'ecommerce';
        """
    )
