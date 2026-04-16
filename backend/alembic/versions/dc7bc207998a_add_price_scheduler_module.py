"""add_price_scheduler_module

Revision ID: dc7bc207998a
Revises: 5a7926f01d3d
Create Date: 2025-10-09 12:21:24.428891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc7bc207998a'
down_revision: Union[str, None] = '5a7926f01d3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add price_scheduler module to modules table."""
    # Insert the price_scheduler module
    op.execute("""
        INSERT INTO modules (name, display_name, description, route_pattern, is_core)
        VALUES (
            'price_scheduler',
            'Harmonogram Cen',
            'Automatyczne zarządzanie cenami ofert według harmonogramu tygodniowego',
            '/price-scheduler',
            false
        )
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove price_scheduler module from modules table."""
    op.execute("""
        DELETE FROM modules WHERE name = 'price_scheduler';
    """)
