"""add_marketplace_type_to_accounts

Revision ID: 3dd0feec84e9
Revises: f60932d62b4f
Create Date: 2026-01-21 13:27:08.569815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3dd0feec84e9'
down_revision: Union[str, None] = 'f60932d62b4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type
    marketplace_type_enum = postgresql.ENUM('allegro', 'amazon', 'emag', 'kaufland', name='marketplacetype')
    marketplace_type_enum.create(op.get_bind())
    
    # Add marketplace_type column (default to 'allegro')
    op.add_column('accounts', 
        sa.Column('marketplace_type', 
                  sa.Enum('allegro', 'amazon', 'emag', 'kaufland', name='marketplacetype'),
                  nullable=False, 
                  server_default='allegro'))
    
    # Add marketplace_specific_data column
    op.add_column('accounts',
        sa.Column('marketplace_specific_data', sa.JSON(), nullable=True))
    
    # Create index
    op.create_index('ix_accounts_marketplace_type', 'accounts', ['marketplace_type'])
    
    # Rename table (with backward-compatible VIEW)
    op.rename_table('user_allegro_accounts', 'user_marketplace_accounts')
    
    # Create VIEW for backward compatibility
    op.execute("""
        CREATE VIEW user_allegro_accounts AS 
        SELECT * FROM user_marketplace_accounts
    """)
    
    # Update module name
    op.execute("""
        UPDATE modules 
        SET name = 'konta_marketplace', display_name = 'Konta' 
        WHERE name = 'konta_allegro'
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove VIEW
    op.execute("DROP VIEW IF EXISTS user_allegro_accounts")
    
    # Revert table rename
    op.rename_table('user_marketplace_accounts', 'user_allegro_accounts')
    
    # Revert module name
    op.execute("""
        UPDATE modules 
        SET name = 'konta_allegro', display_name = 'Konta Allegro' 
        WHERE name = 'konta_marketplace'
    """)
    
    # Drop columns
    op.drop_index('ix_accounts_marketplace_type', table_name='accounts')
    op.drop_column('accounts', 'marketplace_specific_data')
    op.drop_column('accounts', 'marketplace_type')
    
    # Drop enum
    op.execute("DROP TYPE marketplacetype")
