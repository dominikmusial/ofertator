"""merge_asystenciai_and_price_scheduler_branches

Revision ID: 1a1177e7cad1
Revises: 2f984f8ae3ae, b3280dc94a9a
Create Date: 2025-10-13 17:00:40.726418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a1177e7cad1'
down_revision: Union[str, None] = ('2f984f8ae3ae', 'b3280dc94a9a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
