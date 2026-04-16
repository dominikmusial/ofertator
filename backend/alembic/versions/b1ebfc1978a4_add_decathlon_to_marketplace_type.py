"""add_decathlon_to_marketplace_type

Revision ID: b1ebfc1978a4
Revises: 3dd0feec84e9
Create Date: 2026-01-22 10:46:01.344028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'b1ebfc1978a4'
down_revision: Union[str, None] = '3dd0feec84e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'decathlon' to MarketplaceType enum."""
    # Check if we're using PostgreSQL or SQLite
    conn = op.get_bind()
    
    if conn.dialect.name == 'postgresql':
        # PostgreSQL: Add new value to existing enum type
        op.execute("ALTER TYPE marketplacetype ADD VALUE IF NOT EXISTS 'decathlon'")
    else:
        # SQLite: Enums are stored as strings, no action needed
        # The model definition already includes 'decathlon', so SQLite will accept it
        pass


def downgrade() -> None:
    """Remove 'decathlon' from MarketplaceType enum."""
    # Note: Both PostgreSQL and SQLite don't need downgrade for enum changes
    # PostgreSQL: Cannot remove enum values directly
    # SQLite: Stores enums as strings, no action needed
    pass
