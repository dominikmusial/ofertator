"""merge feature flags and castorama migrations

Revision ID: 3872648c41d9
Revises: add_feature_flags, fa2b9330befc
Create Date: 2026-02-04 13:34:54.244060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3872648c41d9'
down_revision: Union[str, None] = ('add_feature_flags', 'fa2b9330befc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
