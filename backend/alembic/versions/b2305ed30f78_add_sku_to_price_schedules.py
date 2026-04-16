"""add_sku_to_price_schedules

Revision ID: b2305ed30f78
Revises: 7a0005089fbc
Create Date: 2025-11-04 22:00:54.765715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2305ed30f78'
down_revision: Union[str, None] = '7a0005089fbc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add SKU column to price_schedules table
    op.add_column('price_schedules', sa.Column('sku', sa.String(), nullable=True))

    # Add index for SKU column for faster lookups
    op.create_index(op.f('ix_price_schedules_sku'), 'price_schedules', ['sku'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index and column
    op.drop_index(op.f('ix_price_schedules_sku'), table_name='price_schedules')
    op.drop_column('price_schedules', 'sku')
