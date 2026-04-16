"""merge_heads

Revision ID: f4932fcd0940
Revises: 2f984f8ae3ae, b3280dc94a9a
Create Date: 2025-10-29 00:17:29.197261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4932fcd0940'
down_revision: Union[str, None] = ('2f984f8ae3ae', 'b3280dc94a9a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
