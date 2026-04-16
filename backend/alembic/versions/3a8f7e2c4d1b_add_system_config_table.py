"""add system_config table

Revision ID: 3a8f7e2c4d1b
Revises: 1a1177e7cad1
Create Date: 2025-10-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '3a8f7e2c4d1b'
down_revision = '1a1177e7cad1'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection to inspect existing tables and indexes
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create system_config table only if it doesn't exist
    if 'system_config' not in existing_tables:
        op.create_table(
            'system_config',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('config_key', sa.String(), nullable=False),
            sa.Column('config_value', sa.Text(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('config_key')
        )
        
        # Create indexes only if table was just created
        op.create_index(op.f('ix_system_config_id'), 'system_config', ['id'], unique=False)
        op.create_index(op.f('ix_system_config_config_key'), 'system_config', ['config_key'], unique=True)
        
        # Seed initial webhook URL only if table was just created
        op.execute("""
            INSERT INTO system_config (config_key, config_value, description, updated_at) 
            VALUES (
                'external_logging_webhook_url',
                'https://script.google.com/macros/s/AKfycbyJWoGjMENnRWv7Bqb859D-qeETsO1x3rc-aDpitWYHK4fM0XPwuXncv4zC86IVQTby/exec',
                'Google Apps Script webhook URL for external logging',
                NOW()
            )
        """)
    else:
        # If table exists, check if indexes exist and create them if needed
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('system_config')]
        
        if 'ix_system_config_id' not in existing_indexes:
            op.create_index(op.f('ix_system_config_id'), 'system_config', ['id'], unique=False)
        
        if 'ix_system_config_config_key' not in existing_indexes:
            op.create_index(op.f('ix_system_config_config_key'), 'system_config', ['config_key'], unique=True)
        
        # Check if initial data exists and insert if needed
        result = conn.execute(sa.text("SELECT COUNT(*) FROM system_config WHERE config_key = 'external_logging_webhook_url'"))
        count = result.scalar()
        
        if count == 0:
            op.execute("""
                INSERT INTO system_config (config_key, config_value, description, updated_at) 
                VALUES (
                    'external_logging_webhook_url',
                    'https://script.google.com/macros/s/AKfycbyJWoGjMENnRWv7Bqb859D-qeETsO1x3rc-aDpitWYHK4fM0XPwuXncv4zC86IVQTby/exec',
                    'Google Apps Script webhook URL for external logging',
                    NOW()
                )
            """)


def downgrade():
    # Get connection to inspect existing tables and indexes
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Only proceed if table exists
    if 'system_config' in existing_tables:
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('system_config')]
        
        # Drop indexes if they exist
        if 'ix_system_config_config_key' in existing_indexes:
            op.drop_index(op.f('ix_system_config_config_key'), table_name='system_config')
        
        if 'ix_system_config_id' in existing_indexes:
            op.drop_index(op.f('ix_system_config_id'), table_name='system_config')
        
        # Drop table
        op.drop_table('system_config')

