"""add token reauth tracking

Adds fields to track Allegro refresh token expiration and re-authentication needs.

Migration Strategy:
- Optimistic approach: assumes all existing accounts have fresh tokens
- Sets refresh_token_expires_at = NOW() + 90 days for all existing accounts
- Avoids false alarms (red badges) for accounts that are actively used (~1 API call/day)
- System automatically detects truly expired tokens on first API operation
- User sees "Wymaga ponownej autoryzacji" only when token actually fails

Revision ID: a1b2c3d4e5f6
Revises: f9245e312a60
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f9245e312a60'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add token expiry tracking and re-authentication fields to accounts table."""
    
    # Check if columns exist before adding them (idempotent migration)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('accounts')]
    
    # Add new columns only if they don't exist
    if 'refresh_token_expires_at' not in columns:
        op.add_column('accounts', sa.Column('refresh_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    
    if 'needs_reauth' not in columns:
        op.add_column('accounts', sa.Column('needs_reauth', sa.Boolean(), server_default='false', nullable=False))
    
    if 'last_token_refresh' not in columns:
        op.add_column('accounts', sa.Column('last_token_refresh', sa.DateTime(timezone=True), nullable=True))
    
    # Create index for needs_reauth to speed up queries (only if it doesn't exist)
    indexes = [idx['name'] for idx in inspector.get_indexes('accounts')]
    if 'ix_accounts_needs_reauth' not in indexes:
        op.create_index('ix_accounts_needs_reauth', 'accounts', ['needs_reauth'])
    
    # Populate refresh_token_expires_at for existing accounts
    # Optimistic approach: assume all tokens are fresh (valid for 90 days from NOW)
    # This avoids false alarms for accounts that are actively used
    # System will automatically detect truly expired tokens on first API call
    connection.execute(sa.text("""
        UPDATE accounts 
        SET refresh_token_expires_at = NOW() + INTERVAL '90 days',
            last_token_refresh = NOW(),
            needs_reauth = false
        WHERE refresh_token_expires_at IS NULL
    """))


def downgrade() -> None:
    """Remove token expiry tracking fields."""
    # Check what exists before dropping (idempotent downgrade)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    indexes = [idx['name'] for idx in inspector.get_indexes('accounts')]
    if 'ix_accounts_needs_reauth' in indexes:
        op.drop_index('ix_accounts_needs_reauth', table_name='accounts')
    
    columns = [col['name'] for col in inspector.get_columns('accounts')]
    if 'last_token_refresh' in columns:
        op.drop_column('accounts', 'last_token_refresh')
    if 'needs_reauth' in columns:
        op.drop_column('accounts', 'needs_reauth')
    if 'refresh_token_expires_at' in columns:
        op.drop_column('accounts', 'refresh_token_expires_at')


