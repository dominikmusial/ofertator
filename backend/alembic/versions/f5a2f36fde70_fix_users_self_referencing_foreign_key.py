"""fix_users_self_referencing_foreign_key

Revision ID: f5a2f36fde70
Revises: 341d3fcd2fd4
Create Date: 2025-09-17 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a2f36fde70'
down_revision: Union[str, None] = '341d3fcd2fd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix self-referencing foreign key constraint in users table to allow user deletion."""
    
    # Drop and recreate the self-referencing foreign key constraint with SET NULL on delete
    # This constraint is from deactivated_by_admin_id back to users.id
    op.drop_constraint('fk_users_deactivated_by_admin', 'users', type_='foreignkey')
    op.create_foreign_key(
        'fk_users_deactivated_by_admin',
        'users', 'users',
        ['deactivated_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Revert self-referencing foreign key constraint back to original (no action on delete)."""
    
    # Revert users self-referencing constraint
    op.drop_constraint('fk_users_deactivated_by_admin', 'users', type_='foreignkey')
    op.create_foreign_key(
        'fk_users_deactivated_by_admin',
        'users', 'users',
        ['deactivated_by_admin_id'], ['id']
    )