"""merge_key_source_migration

Revision ID: e1bed5ae5f6b
Revises: 18694c54e884, a1b2c3d4e5f6, g1h2i3j4k5l6
Create Date: 2025-11-05 14:25:46.317104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1bed5ae5f6b'
down_revision: Union[str, None] = ('18694c54e884', 'a1b2c3d4e5f6', 'g1h2i3j4k5l6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
