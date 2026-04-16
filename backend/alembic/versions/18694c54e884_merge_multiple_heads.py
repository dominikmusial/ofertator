"""merge_multiple_heads

Revision ID: 18694c54e884
Revises: 3a8f7e2c4d1b, 4b5c6d7e8f9a
Create Date: 2025-10-21 16:08:06.965393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18694c54e884'
down_revision: Union[str, None] = ('3a8f7e2c4d1b', '4b5c6d7e8f9a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
