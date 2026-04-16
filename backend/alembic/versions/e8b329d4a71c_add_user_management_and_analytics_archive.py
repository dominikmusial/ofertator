"""add_user_management_and_analytics_archive

Revision ID: e8b329d4a71c
Revises: 1cf67a6ef659
Create Date: 2025-09-16 22:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'e8b329d4a71c'
down_revision: Union[str, None] = 'bd78175794a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # User management fields already exist from model changes, skip adding them
    
    # Create AI token usage archive table
    op.create_table('ai_token_usage_archive',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('ai_provider', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('input_cost_usd', sa.String(), nullable=False),
        sa.Column('output_cost_usd', sa.String(), nullable=False),
        sa.Column('total_cost_usd', sa.String(), nullable=False),
        sa.Column('pricing_version', sa.String(), nullable=True),
        sa.Column('request_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('offer_id', sa.String(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('batch_id', sa.String(), nullable=True),
        sa.Column('deleted_user_display_name', sa.String(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('deleted_by_admin_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['deleted_by_admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_token_usage_archive_id'), 'ai_token_usage_archive', ['id'], unique=False)
    op.create_index(op.f('ix_ai_token_usage_archive_original_id'), 'ai_token_usage_archive', ['original_id'], unique=False)
    op.create_index(op.f('ix_ai_token_usage_archive_request_timestamp'), 'ai_token_usage_archive', ['request_timestamp'], unique=False)
    
    # Create AI usage daily stats archive table
    op.create_table('ai_usage_daily_stats_archive',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.String(), nullable=False),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('total_input_tokens', sa.Integer(), nullable=True),
        sa.Column('total_output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_cost_usd', sa.String(), nullable=True),
        sa.Column('operations_breakdown', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_user_display_name', sa.String(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('deleted_by_admin_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['deleted_by_admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_usage_daily_stats_archive_id'), 'ai_usage_daily_stats_archive', ['id'], unique=False)
    op.create_index(op.f('ix_ai_usage_daily_stats_archive_original_id'), 'ai_usage_daily_stats_archive', ['original_id'], unique=False)
    op.create_index(op.f('ix_ai_usage_daily_stats_archive_date'), 'ai_usage_daily_stats_archive', ['date'], unique=False)
    
    # Create user activity logs archive table
    op.create_table('user_activity_logs_archive',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('deleted_user_display_name', sa.String(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('deleted_by_admin_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['deleted_by_admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_activity_logs_archive_id'), 'user_activity_logs_archive', ['id'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_archive_original_id'), 'user_activity_logs_archive', ['original_id'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_archive_action_type'), 'user_activity_logs_archive', ['action_type'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_archive_timestamp'), 'user_activity_logs_archive', ['timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop archive tables
    op.drop_index(op.f('ix_user_activity_logs_archive_timestamp'), table_name='user_activity_logs_archive')
    op.drop_index(op.f('ix_user_activity_logs_archive_action_type'), table_name='user_activity_logs_archive')
    op.drop_index(op.f('ix_user_activity_logs_archive_original_id'), table_name='user_activity_logs_archive')
    op.drop_index(op.f('ix_user_activity_logs_archive_id'), table_name='user_activity_logs_archive')
    op.drop_table('user_activity_logs_archive')
    
    op.drop_index(op.f('ix_ai_usage_daily_stats_archive_date'), table_name='ai_usage_daily_stats_archive')
    op.drop_index(op.f('ix_ai_usage_daily_stats_archive_original_id'), table_name='ai_usage_daily_stats_archive')
    op.drop_index(op.f('ix_ai_usage_daily_stats_archive_id'), table_name='ai_usage_daily_stats_archive')
    op.drop_table('ai_usage_daily_stats_archive')
    
    op.drop_index(op.f('ix_ai_token_usage_archive_request_timestamp'), table_name='ai_token_usage_archive')
    op.drop_index(op.f('ix_ai_token_usage_archive_original_id'), table_name='ai_token_usage_archive')
    op.drop_index(op.f('ix_ai_token_usage_archive_id'), table_name='ai_token_usage_archive')
    op.drop_table('ai_token_usage_archive')
    
    # Note: User management fields are handled by model changes, not dropped here
