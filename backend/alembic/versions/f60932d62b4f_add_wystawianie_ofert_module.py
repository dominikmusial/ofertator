"""add_wystawianie_ofert_module

Revision ID: f60932d62b4f
Revises: e1bed5ae5f6b
Create Date: 2026-01-15 21:05:34.047715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f60932d62b4f'
down_revision: Union[str, None] = 'e1bed5ae5f6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Insert the missing wystawianie_ofert module
    op.execute("""
        INSERT INTO modules (name, display_name, route_pattern, description, is_core) 
        VALUES ('wystawianie_ofert', 'Wystawianie Ofert', '/create-offer', 'Wystawianie nowych ofert na Allegro', false)
        ON CONFLICT (name) DO NOTHING
    """)
    
    # Grant the new module only to admin and vsprint_employee users
    op.execute("""
        INSERT INTO user_module_permissions (user_id, module_id, granted, granted_by_admin_id)
        SELECT 
            u.id as user_id,
            m.id as module_id,
            true as granted,
            NULL as granted_by_admin_id
        FROM users u, modules m 
        WHERE m.name = 'wystawianie_ofert'
        AND u.role IN ('admin', 'vsprint_employee')
        AND NOT EXISTS (
            SELECT 1 FROM user_module_permissions ump 
            WHERE ump.user_id = u.id AND ump.module_id = m.id
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove permissions first, then the module
    op.execute("""
        DELETE FROM user_module_permissions 
        WHERE module_id IN (SELECT id FROM modules WHERE name = 'wystawianie_ofert')
    """)
    op.execute("DELETE FROM modules WHERE name = 'wystawianie_ofert'")
