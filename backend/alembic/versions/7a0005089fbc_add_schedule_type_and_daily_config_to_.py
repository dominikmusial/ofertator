"""add_schedule_type_and_daily_config_to_price_schedules

Revision ID: 7a0005089fbc
Revises: f4932fcd0940
Create Date: 2025-10-29 00:17:41.072169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '7a0005089fbc'
down_revision: Union[str, None] = 'f4932fcd0940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Get connection to inspect existing columns
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('price_schedules')]
    
    # Add schedule_type column with default 'hourly' if it doesn't exist
    if 'schedule_type' not in existing_columns:
        op.add_column('price_schedules', sa.Column('schedule_type', sa.String(), nullable=False, server_default='hourly'))

    # Add daily_schedule_config column (JSON, nullable) if it doesn't exist
    if 'daily_schedule_config' not in existing_columns:
        op.add_column('price_schedules', sa.Column('daily_schedule_config', sa.JSON(), nullable=True))

    # Make schedule_config nullable (previously required, now optional based on type)
    op.alter_column('price_schedules', 'schedule_config', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Get connection to inspect existing columns
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('price_schedules')]
    
    # Remove added columns if they exist
    if 'daily_schedule_config' in existing_columns:
        op.drop_column('price_schedules', 'daily_schedule_config')
    if 'schedule_type' in existing_columns:
        op.drop_column('price_schedules', 'schedule_type')

    # Make schedule_config required again
    op.alter_column('price_schedules', 'schedule_config', nullable=False)
