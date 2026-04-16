"""fix_archive_foreign_key_constraints

Revision ID: 7d538c3e5cf0
Revises: e8b329d4a71c
Create Date: 2025-09-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d538c3e5cf0'
down_revision: Union[str, None] = 'e8b329d4a71c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix foreign key constraints in archive tables to allow user deletion."""
    
    # First, make deleted_by_admin_id columns nullable
    op.alter_column('ai_token_usage_archive', 'deleted_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=True)
    
    op.alter_column('ai_usage_daily_stats_archive', 'deleted_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=True)
    
    op.alter_column('user_activity_logs_archive', 'deleted_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=True)
    
    # Drop and recreate foreign key constraints with SET NULL on delete
    # for ai_token_usage_archive table
    op.drop_constraint('ai_token_usage_archive_deleted_by_admin_id_fkey', 'ai_token_usage_archive', type_='foreignkey')
    op.create_foreign_key(
        'ai_token_usage_archive_deleted_by_admin_id_fkey',
        'ai_token_usage_archive', 'users',
        ['deleted_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # for ai_usage_daily_stats_archive table  
    op.drop_constraint('ai_usage_daily_stats_archive_deleted_by_admin_id_fkey', 'ai_usage_daily_stats_archive', type_='foreignkey')
    op.create_foreign_key(
        'ai_usage_daily_stats_archive_deleted_by_admin_id_fkey',
        'ai_usage_daily_stats_archive', 'users',
        ['deleted_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # for user_activity_logs_archive table
    op.drop_constraint('user_activity_logs_archive_deleted_by_admin_id_fkey', 'user_activity_logs_archive', type_='foreignkey')
    op.create_foreign_key(
        'user_activity_logs_archive_deleted_by_admin_id_fkey',
        'user_activity_logs_archive', 'users',
        ['deleted_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Revert foreign key constraints back to original (no action on delete)."""
    
    # Revert ai_token_usage_archive
    op.drop_constraint('ai_token_usage_archive_deleted_by_admin_id_fkey', 'ai_token_usage_archive', type_='foreignkey')
    op.create_foreign_key(
        'ai_token_usage_archive_deleted_by_admin_id_fkey',
        'ai_token_usage_archive', 'users',
        ['deleted_by_admin_id'], ['id']
    )
    
    # Revert ai_usage_daily_stats_archive
    op.drop_constraint('ai_usage_daily_stats_archive_deleted_by_admin_id_fkey', 'ai_usage_daily_stats_archive', type_='foreignkey')
    op.create_foreign_key(
        'ai_usage_daily_stats_archive_deleted_by_admin_id_fkey',
        'ai_usage_daily_stats_archive', 'users',
        ['deleted_by_admin_id'], ['id']
    )
    
    # Revert user_activity_logs_archive
    op.drop_constraint('user_activity_logs_archive_deleted_by_admin_id_fkey', 'user_activity_logs_archive', type_='foreignkey')
    op.create_foreign_key(
        'user_activity_logs_archive_deleted_by_admin_id_fkey',
        'user_activity_logs_archive', 'users',
        ['deleted_by_admin_id'], ['id']
    )
    
    # Revert columns back to NOT NULL
    op.alter_column('ai_token_usage_archive', 'deleted_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=False)
    
    op.alter_column('ai_usage_daily_stats_archive', 'deleted_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=False)
    
    op.alter_column('user_activity_logs_archive', 'deleted_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=False)