"""ensure_accounts_nazwa_konta_non_unique

Revision ID: 834919fd61e6
Revises: 1e57d07d1eb9
Create Date: 2025-09-05 09:21:54.097092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '834919fd61e6'
down_revision: Union[str, None] = '1e57d07d1eb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
