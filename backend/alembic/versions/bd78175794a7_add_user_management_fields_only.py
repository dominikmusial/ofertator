"""add_user_management_fields_only

Revision ID: bd78175794a7
Revises: 1cf67a6ef659
Create Date: 2025-09-16 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd78175794a7'
down_revision: Union[str, None] = '1cf67a6ef659'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user management fields to users table."""
    
    # Add user management columns to the users table
    op.add_column('users', sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deactivated_by_admin_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('deactivation_reason', sa.Text(), nullable=True))
    
    # Add foreign key constraint for deactivated_by_admin_id
    op.create_foreign_key('fk_users_deactivated_by_admin', 'users', 'users', ['deactivated_by_admin_id'], ['id'])


def downgrade() -> None:
    """Remove user management fields from users table."""
    
    # Drop foreign key constraint first
    op.drop_constraint('fk_users_deactivated_by_admin', 'users', type_='foreignkey')
    
    # Drop the columns
    op.drop_column('users', 'deactivation_reason')
    op.drop_column('users', 'deactivated_by_admin_id')
    op.drop_column('users', 'deactivated_at')