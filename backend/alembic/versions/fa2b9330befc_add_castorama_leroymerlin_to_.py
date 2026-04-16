"""add_castorama_leroymerlin_to_marketplace_type

Revision ID: fa2b9330befc
Revises: 23e6daae1856
Create Date: 2026-01-29 11:46:56.273447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa2b9330befc'
down_revision: Union[str, None] = '23e6daae1856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'castorama' and 'leroymerlin' to MarketplaceType enum."""
    # Check if we're using PostgreSQL or SQLite
    conn = op.get_bind()
    
    if conn.dialect.name == 'postgresql':
        # PostgreSQL: Add new values to existing enum type
        op.execute("ALTER TYPE marketplacetype ADD VALUE IF NOT EXISTS 'castorama'")
        op.execute("ALTER TYPE marketplacetype ADD VALUE IF NOT EXISTS 'leroymerlin'")
    else:
        # SQLite: Enums are stored as strings, no action needed
        # The model definition already includes these values, so SQLite will accept them
        pass


def downgrade() -> None:
    """Remove 'castorama' and 'leroymerlin' from MarketplaceType enum."""
    # Note: Both PostgreSQL and SQLite don't need downgrade for enum changes
    # PostgreSQL: Cannot remove enum values directly (would require complex migration)
    # SQLite: Stores enums as strings, no action needed
    pass
