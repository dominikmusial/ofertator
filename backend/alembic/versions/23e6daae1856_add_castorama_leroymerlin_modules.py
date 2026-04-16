"""add_castorama_leroymerlin_modules

Revision ID: 23e6daae1856
Revises: d1335e887130
Create Date: 2026-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23e6daae1856'
down_revision: Union[str, None] = 'd1335e887130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Castorama and Leroy Merlin marketplace modules."""
    
    # Add Castorama modules
    op.execute("""
        INSERT INTO modules (name, display_name, route_pattern, description, is_core)
        VALUES 
        ('castorama_edytor_ofert', 'Edytor Ofert - Castorama', '/castorama/offer-editor', 
         'Edycja ofert na platformie Castorama/Mirakl', false),
        ('castorama_wystawianie_ofert', 'Wystawianie Ofert - Castorama', '/castorama/create-offer', 
         'Wystawianie nowych ofert na Castorama', false)
    """)
    
    # Add Leroy Merlin modules
    op.execute("""
        INSERT INTO modules (name, display_name, route_pattern, description, is_core)
        VALUES 
        ('leroymerlin_edytor_ofert', 'Edytor Ofert - Leroy Merlin', '/leroymerlin/offer-editor', 
         'Edycja ofert na platformie Leroy Merlin/Mirakl', false),
        ('leroymerlin_wystawianie_ofert', 'Wystawianie Ofert - Leroy Merlin', '/leroymerlin/create-offer', 
         'Wystawianie nowych ofert na Leroy Merlin', false)
    """)
    
    # Auto-grant new modules to existing users (maintain current functionality)
    # This ensures users who already have marketplace permissions get the new modules
    # Use NULL for granted_by_admin_id instead of hardcoding user ID 1
    op.execute("""
        INSERT INTO user_module_permissions (user_id, module_id, granted, granted_by_admin_id)
        SELECT 
            u.id as user_id,
            m.id as module_id,
            true as granted,
            NULL as granted_by_admin_id
        FROM users u 
        CROSS JOIN modules m 
        WHERE m.name IN (
            'castorama_edytor_ofert', 
            'castorama_wystawianie_ofert',
            'leroymerlin_edytor_ofert',
            'leroymerlin_wystawianie_ofert'
        )
        AND u.id IS NOT NULL
        ON CONFLICT (user_id, module_id) DO NOTHING
    """)


def downgrade() -> None:
    """Remove Castorama and Leroy Merlin marketplace modules."""
    
    # Remove user permissions first (foreign key constraint)
    op.execute("""
        DELETE FROM user_module_permissions 
        WHERE module_id IN (
            SELECT id FROM modules 
            WHERE name IN (
                'castorama_edytor_ofert', 
                'castorama_wystawianie_ofert',
                'leroymerlin_edytor_ofert',
                'leroymerlin_wystawianie_ofert'
            )
        )
    """)
    
    # Remove modules
    op.execute("""
        DELETE FROM modules 
        WHERE name IN (
            'castorama_edytor_ofert', 
            'castorama_wystawianie_ofert',
            'leroymerlin_edytor_ofert',
            'leroymerlin_wystawianie_ofert'
        )
    """)
