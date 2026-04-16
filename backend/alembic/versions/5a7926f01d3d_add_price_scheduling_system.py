"""add_price_scheduling_system

Revision ID: 5a7926f01d3d
Revises: f5a2f36fde70
Create Date: 2025-10-09 11:23:47.899279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a7926f01d3d'
down_revision: Union[str, None] = 'f5a2f36fde70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create price_schedules table
    op.create_table(
        'price_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.String(), nullable=False),
        sa.Column('offer_name', sa.String(), nullable=True),
        sa.Column('original_price', sa.String(), nullable=False),
        sa.Column('scheduled_price', sa.String(), nullable=False),
        sa.Column('schedule_config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('current_price_state', sa.String(), nullable=True, server_default='original'),
        sa.Column('last_price_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_price_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_schedules_id'), 'price_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_price_schedules_offer_id'), 'price_schedules', ['offer_id'], unique=False)

    # Create price_change_logs table
    op.create_table(
        'price_change_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.String(), nullable=False),
        sa.Column('price_before', sa.String(), nullable=False),
        sa.Column('price_after', sa.String(), nullable=False),
        sa.Column('change_reason', sa.String(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('allegro_response', sa.JSON(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['schedule_id'], ['price_schedules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_change_logs_changed_at'), 'price_change_logs', ['changed_at'], unique=False)
    op.create_index(op.f('ix_price_change_logs_id'), 'price_change_logs', ['id'], unique=False)
    op.create_index(op.f('ix_price_change_logs_offer_id'), 'price_change_logs', ['offer_id'], unique=False)

    # Create price_snapshots table
    op.create_table(
        'price_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.String(), nullable=False),
        sa.Column('price', sa.String(), nullable=False),
        sa.Column('snapshot_reason', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_snapshots_created_at'), 'price_snapshots', ['created_at'], unique=False)
    op.create_index(op.f('ix_price_snapshots_id'), 'price_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_price_snapshots_offer_id'), 'price_snapshots', ['offer_id'], unique=False)
    op.create_index('idx_offer_snapshot', 'price_snapshots', ['offer_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_offer_snapshot', table_name='price_snapshots')
    op.drop_index(op.f('ix_price_snapshots_offer_id'), table_name='price_snapshots')
    op.drop_index(op.f('ix_price_snapshots_id'), table_name='price_snapshots')
    op.drop_index(op.f('ix_price_snapshots_created_at'), table_name='price_snapshots')
    op.drop_table('price_snapshots')

    op.drop_index(op.f('ix_price_change_logs_offer_id'), table_name='price_change_logs')
    op.drop_index(op.f('ix_price_change_logs_id'), table_name='price_change_logs')
    op.drop_index(op.f('ix_price_change_logs_changed_at'), table_name='price_change_logs')
    op.drop_table('price_change_logs')

    op.drop_index(op.f('ix_price_schedules_offer_id'), table_name='price_schedules')
    op.drop_index(op.f('ix_price_schedules_id'), table_name='price_schedules')
    op.drop_table('price_schedules')
