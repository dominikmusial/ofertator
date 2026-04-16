"""fix_price_change_logs_cascade

Revision ID: b3280dc94a9a
Revises: dc7bc207998a
Create Date: 2025-10-09 13:03:46.144064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3280dc94a9a'
down_revision: Union[str, None] = 'dc7bc207998a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CASCADE to price_change_logs foreign key constraint."""
    # Drop the old foreign key constraint
    op.drop_constraint('price_change_logs_schedule_id_fkey', 'price_change_logs', type_='foreignkey')

    # Create new foreign key constraint with ON DELETE CASCADE
    op.create_foreign_key(
        'price_change_logs_schedule_id_fkey',
        'price_change_logs', 'price_schedules',
        ['schedule_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove CASCADE from price_change_logs foreign key constraint."""
    # Drop the constraint with CASCADE
    op.drop_constraint('price_change_logs_schedule_id_fkey', 'price_change_logs', type_='foreignkey')

    # Recreate without CASCADE (original state)
    op.create_foreign_key(
        'price_change_logs_schedule_id_fkey',
        'price_change_logs', 'price_schedules',
        ['schedule_id'], ['id']
    )
