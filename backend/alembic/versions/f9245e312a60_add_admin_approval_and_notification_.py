"""add_admin_approval_and_notification_system

Revision ID: f9245e312a60
Revises: 834919fd61e6
Create Date: 2025-09-11 13:42:44.961804

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9245e312a60'
down_revision: Union[str, None] = '834919fd61e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Add admin_approved column to users table
    op.add_column('users', sa.Column('admin_approved', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create admin_notification_emails table
    op.create_table('admin_notification_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_admin_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_admin_notification_emails_email', 'email'),
    )
    
    # Auto-approve all vsprint employees and admins (existing Google SSO users)
    op.execute("""
        UPDATE users 
        SET admin_approved = true 
        WHERE role IN ('vsprint_employee', 'admin') 
        OR email LIKE '%@vsprint.pl'
    """)


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop admin_notification_emails table
    op.drop_table('admin_notification_emails')
    
    # Drop admin_approved column from users table
    op.drop_column('users', 'admin_approved')
