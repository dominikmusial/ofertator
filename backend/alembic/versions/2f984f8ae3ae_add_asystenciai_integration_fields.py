"""add_asystenciai_integration_fields

Revision ID: 2f984f8ae3ae
Revises: f5a2f36fde70
Create Date: 2025-10-09 13:47:45.042416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f984f8ae3ae'
down_revision: Union[str, None] = 'f5a2f36fde70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for registration source
    registration_source_enum = sa.Enum('web', 'asystenciai', name='registration_source')
    registration_source_enum.create(op.get_bind(), checkfirst=True)
    
    # Add new columns to users table
    op.add_column('users', sa.Column('registration_source', registration_source_enum, 
                                   nullable=False, server_default='web'))
    op.add_column('users', sa.Column('external_user_id', sa.String(255), nullable=True))
    
    # Add index for external_user_id for faster lookups
    op.create_index(op.f('ix_users_external_user_id'), 'users', ['external_user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index and columns
    op.drop_index(op.f('ix_users_external_user_id'), table_name='users')
    op.drop_column('users', 'external_user_id')
    op.drop_column('users', 'registration_source')
    
    # Drop enum type
    registration_source_enum = sa.Enum('web', 'asystenciai', name='registration_source')
    registration_source_enum.drop(op.get_bind(), checkfirst=True)
