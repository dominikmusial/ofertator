"""fix_admin_notification_emails_foreign_key

Revision ID: 341d3fcd2fd4
Revises: 7d538c3e5cf0
Create Date: 2025-09-17 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '341d3fcd2fd4'
down_revision: Union[str, None] = '7d538c3e5cf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix foreign key constraints to allow user deletion."""
    
    # Fix admin_notification_emails table
    # Make created_by_admin_id column nullable
    op.alter_column('admin_notification_emails', 'created_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=True)
    
    # Drop and recreate foreign key constraint with SET NULL on delete
    op.drop_constraint('admin_notification_emails_created_by_admin_id_fkey', 'admin_notification_emails', type_='foreignkey')
    op.create_foreign_key(
        'admin_notification_emails_created_by_admin_id_fkey',
        'admin_notification_emails', 'users',
        ['created_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Fix user_module_permissions table - granted_by_admin_id should also be nullable and SET NULL
    # (it's already nullable in the model, just need to fix the constraint)
    op.drop_constraint('user_module_permissions_granted_by_admin_id_fkey', 'user_module_permissions', type_='foreignkey')
    op.create_foreign_key(
        'user_module_permissions_granted_by_admin_id_fkey',
        'user_module_permissions', 'users',
        ['granted_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Revert foreign key constraints back to original (no action on delete)."""
    
    # Revert user_module_permissions
    op.drop_constraint('user_module_permissions_granted_by_admin_id_fkey', 'user_module_permissions', type_='foreignkey')
    op.create_foreign_key(
        'user_module_permissions_granted_by_admin_id_fkey',
        'user_module_permissions', 'users',
        ['granted_by_admin_id'], ['id']
    )
    
    # Revert admin_notification_emails
    op.drop_constraint('admin_notification_emails_created_by_admin_id_fkey', 'admin_notification_emails', type_='foreignkey')
    op.create_foreign_key(
        'admin_notification_emails_created_by_admin_id_fkey',
        'admin_notification_emails', 'users',
        ['created_by_admin_id'], ['id']
    )
    
    # Revert column back to NOT NULL
    op.alter_column('admin_notification_emails', 'created_by_admin_id',
                   existing_type=sa.Integer(),
                   nullable=False)