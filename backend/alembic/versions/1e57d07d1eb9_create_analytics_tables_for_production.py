"""Create analytics tables for production

Revision ID: 1e57d07d1eb9
Revises: 11aca05ac1c3
Create Date: 2025-08-27 12:49:18.016093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e57d07d1eb9'
down_revision: Union[str, None] = '11aca05ac1c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tables already created in previous migration (11aca05ac1c3)
    # This migration is a no-op to maintain compatibility
    pass

    # Original code commented out to avoid duplicate table creation
    # op.create_table('ai_usage_daily_stats',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('user_id', sa.Integer(), nullable=False),
    # sa.Column('date', sa.String(), nullable=False),
    # sa.Column('total_requests', sa.Integer(), nullable=True),
    # sa.Column('total_input_tokens', sa.Integer(), nullable=True),
    # sa.Column('total_output_tokens', sa.Integer(), nullable=True),
    # sa.Column('total_cost_usd', sa.String(), nullable=True),
    # sa.Column('operations_breakdown', sa.JSON(), nullable=True),
    # sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    # sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    # sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    # sa.PrimaryKeyConstraint('id'),
    # sa.UniqueConstraint('user_id', 'date', name='uq_user_daily_stats')
    # )
    # op.create_index(op.f('ix_ai_usage_daily_stats_date'), 'ai_usage_daily_stats', ['date'], unique=False)
    # op.create_index(op.f('ix_ai_usage_daily_stats_id'), 'ai_usage_daily_stats', ['id'], unique=False)

    # Tables already created by migration 11aca05ac1c3
    # All table creation code commented out to prevent duplicates


def downgrade() -> None:
    """Downgrade schema."""
    # No-op downgrade since this migration doesn't create anything
    pass
