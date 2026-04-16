"""Add key_source to ai_token_usage

Revision ID: g1h2i3j4k5l6
Revises: b2305ed30f78
Create Date: 2025-02-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, None] = 'b2305ed30f78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add key_source column to track company vs user API keys"""
    # Create enum type for key_source
    op.execute("CREATE TYPE keysource AS ENUM ('user_custom', 'company_default')")
    
    # Add key_source column
    op.add_column('ai_token_usage', sa.Column('key_source', sa.Enum('user_custom', 'company_default', name='keysource'), nullable=True))
    
    # Create index for filtering
    op.create_index(op.f('ix_ai_token_usage_key_source'), 'ai_token_usage', ['key_source'], unique=False)


def downgrade() -> None:
    """Remove key_source column"""
    op.drop_index(op.f('ix_ai_token_usage_key_source'), table_name='ai_token_usage')
    op.drop_column('ai_token_usage', 'key_source')
    op.execute("DROP TYPE keysource")

