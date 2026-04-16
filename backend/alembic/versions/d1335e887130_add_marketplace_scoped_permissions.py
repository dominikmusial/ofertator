"""add_marketplace_scoped_permissions

Revision ID: d1335e887130
Revises: b1ebfc1978a4
Create Date: 2026-01-23 09:54:54.126075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1335e887130'
down_revision: Union[str, None] = 'b1ebfc1978a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add marketplace-scoped permissions."""
    
    # Step 1: Rename existing modules to allegro-prefixed versions
    # This automatically updates all foreign key references (user_module_permissions, module_dependencies)
    module_renames = [
        ('edytor_ofert', 'allegro_edytor_ofert', 'Edytor Ofert - Allegro', '/allegro/offer-editor'),
        ('wystawianie_ofert', 'allegro_wystawianie_ofert', 'Wystawianie Ofert - Allegro', '/allegro/create-offer'),
        ('kopiowanie_ofert', 'allegro_kopiowanie_ofert', 'Kopiowanie Ofert - Allegro', '/allegro/copy-offers'),
        ('promocje', 'allegro_promocje', 'Promocje - Allegro', '/allegro/promotions'),
        ('price_scheduler', 'allegro_harmonogram_cen', 'Harmonogram Cen - Allegro', '/allegro/price-scheduler'),
        ('tytuly', 'allegro_tytuly', 'Tytuły - Allegro', '/allegro/titles'),
        ('miniatury', 'allegro_miniatury', 'Miniatury - Allegro', '/allegro/thumbnails'),
        ('podmiana_zdjec', 'allegro_podmiana_zdjec', 'Podmiana Zdjęć - Allegro', '/allegro/replace-images'),
        ('wylaczanie_ofert', 'allegro_wylaczanie_ofert', 'Wyłączanie Ofert - Allegro', '/allegro/disable-offers'),
        ('zdjecia_na_banerach', 'allegro_zdjecia_na_banerach', 'Zdjęcia na Banerach - Allegro', '/allegro/banner-images'),
        ('karty_produktowe', 'allegro_karty_produktowe', 'Karty Produktowe - Allegro', '/allegro/product-cards'),
        ('dodawanie_grafik', 'allegro_dodawanie_grafik', 'Dodawanie Grafik - Allegro', '/allegro/images'),
        ('zapisane_zdjecia', 'allegro_zapisane_zdjecia', 'Zapisane Zdjęcia - Allegro', '/allegro/saved-images'),
    ]
    
    for old_name, new_name, new_display, new_route in module_renames:
        op.execute(f"""
            UPDATE modules 
            SET name = '{new_name}',
                display_name = '{new_display}',
                route_pattern = '{new_route}'
            WHERE name = '{old_name}'
        """)
    
    # Step 2: Create new Decathlon-specific modules
    op.execute("""
        INSERT INTO modules (name, display_name, route_pattern, description, is_core)
        VALUES 
        ('decathlon_edytor_ofert', 'Edytor Ofert - Decathlon', '/decathlon/offer-editor', 
         'Edycja ofert na platformie Decathlon/Mirakl', false),
        ('decathlon_wystawianie_ofert', 'Wystawianie Ofert - Decathlon', '/decathlon/create-offer', 
         'Wystawianie nowych ofert na Decathlon', false)
    """)
    
    # Step 3: Update module dependencies to use new names
    # Dependencies are automatically updated via foreign keys, but we need to update the logic if any hardcoded
    
    # Step 4: Note - user_module_permissions are automatically updated via foreign key cascade
    # Users who had 'edytor_ofert' now have 'allegro_edytor_ofert' permission


def downgrade() -> None:
    """Downgrade schema - revert to feature-scoped permissions."""
    
    # Step 1: Remove Decathlon modules
    op.execute("""
        DELETE FROM modules 
        WHERE name IN ('decathlon_edytor_ofert', 'decathlon_wystawianie_ofert')
    """)
    
    # Step 2: Revert Allegro module renames back to generic names
    module_reverts = [
        ('allegro_edytor_ofert', 'edytor_ofert', 'Edytor Ofert', '/offer-editor'),
        ('allegro_wystawianie_ofert', 'wystawianie_ofert', 'Wystawianie Ofert', '/create-offer'),
        ('allegro_kopiowanie_ofert', 'kopiowanie_ofert', 'Kopiowanie Ofert', '/copy-offers'),
        ('allegro_promocje', 'promocje', 'Promocje', '/promotions'),
        ('allegro_harmonogram_cen', 'price_scheduler', 'Harmonogram Cen', '/price-scheduler'),
        ('allegro_tytuly', 'tytuly', 'Tytuły', '/titles'),
        ('allegro_miniatury', 'miniatury', 'Miniatury', '/thumbnails'),
        ('allegro_podmiana_zdjec', 'podmiana_zdjec', 'Podmiana Zdjęć', '/replace-images'),
        ('allegro_wylaczanie_ofert', 'wylaczanie_ofert', 'Wyłączanie Ofert', '/disable-offers'),
        ('allegro_zdjecia_na_banerach', 'zdjecia_na_banerach', 'Zdjęcia na Banerach', '/banner-images'),
        ('allegro_karty_produktowe', 'karty_produktowe', 'Karty Produktowe', '/product-cards'),
        ('allegro_dodawanie_grafik', 'dodawanie_grafik', 'Dodawanie Grafik', '/images'),
        ('allegro_zapisane_zdjecia', 'zapisane_zdjecia', 'Zapisane Zdjęcia', '/saved-images'),
    ]
    
    for new_name, old_name, old_display, old_route in module_reverts:
        op.execute(f"""
            UPDATE modules 
            SET name = '{old_name}',
                display_name = '{old_display}',
                route_pattern = '{old_route}'
            WHERE name = '{new_name}'
        """)
