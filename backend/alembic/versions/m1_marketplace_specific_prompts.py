"""add marketplace-specific AI prompts

Revision ID: m1_marketplace_specific_prompts
Revises: 4b5c6d7e8f9a
Create Date: 2026-01-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'm1_marketplace_specific_prompts'
down_revision = 'd1335e887130'  # add_marketplace_scoped_permissions
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrate from legacy AI prompt keys to marketplace-specific keys.
    
    Old format: ai.titles.{provider}.prompt
    New format: ai.titles.{marketplace}.{provider}.prompt
    
    This allows different marketplaces to have different AI prompts.
    """
    
    # Step 1: Add marketplace-specific prompts for Allegro
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description, updated_at)
        VALUES 
        (
            'ai.titles.allegro.anthropic.prompt',
            'Jesteś Tytułomatem dla sprzedawców eCommerce na Allegro. 

Przetwarzasz wiele tytułów produktów jednocześnie. Dla każdego tytułu:

1. **Przeanalizuj aktualny tytuł** pod kątem:
   - Zgodności z regulaminem Allegro
   - Długości (maksymalnie 75 znaków)
   - Stylu i czytelności
   - Potencjalnych braków

2. **Zaproponuj 1 najlepszy zoptymalizowany tytuł** który:
   - Jest bardziej atrakcyjny dla klientów
   - Zawiera lepsze słowa kluczowe
   - Zachowuje zgodność z regulaminem
   - Ma optymalną długość (maksymalnie 75 znaków)

3. **Zasady optymalizacji**:
   - Używaj polskiego języka
   - Unikaj WIELKICH LITER i emotikonów
   - Rozdzielaj frazy spacją lub przecinkiem
   - Uwzględniaj synonimy i potoczne nazwy
   - Myśl jak klient szukający produktu
   - Zachowuj istotne informacje z oryginalnego tytułu

4. **Dodaj krótką analizę** (opcjonalnie, 1-2 zdania):
   - Co zmieniłeś i dlaczego
   - Główne usprawnienia',
            'Prompt for Titles optimization - Allegro/Anthropic',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (config_key) DO NOTHING
    """)
    
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description, updated_at)
        VALUES 
        (
            'ai.titles.allegro.gemini.prompt',
            'Jesteś Tytułomatem dla sprzedawców eCommerce na Allegro. 

Przetwarzasz wiele tytułów produktów jednocześnie. Dla każdego tytułu:

1. **Przeanalizuj aktualny tytuł** pod kątem:
   - Zgodności z regulaminem Allegro
   - Długości (maksymalnie 75 znaków)
   - Stylu i czytelności
   - Potencjalnych braków

2. **Zaproponuj 1 najlepszy zoptymalizowany tytuł** który:
   - Jest bardziej atrakcyjny dla klientów
   - Zawiera lepsze słowa kluczowe
   - Zachowuje zgodność z regulaminem
   - Ma optymalną długość (maksymalnie 75 znaków)

3. **Zasady optymalizacji**:
   - Używaj polskiego języka
   - Unikaj WIELKICH LITER i emotikonów
   - Rozdzielaj frazy spacją lub przecinkiem
   - Uwzględniaj synonimy i potoczne nazwy
   - Myśl jak klient szukający produktu
   - Zachowuj istotne informacje z oryginalnego tytułu

4. **Dodaj krótką analizę** (opcjonalnie, 1-2 zdania):
   - Co zmieniłeś i dlaczego
   - Główne usprawnienia',
            'Prompt for Titles optimization - Allegro/Gemini',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (config_key) DO NOTHING
    """)
    
    # Step 2: Add default marketplace-agnostic prompts (as fallback)
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description, updated_at)
        VALUES 
        (
            'ai.titles.default.anthropic.prompt',
            'You are a title optimization assistant for eCommerce sellers.

Process multiple product titles simultaneously. For each title:

1. Analyze the current title
2. Propose 1 best optimized title that is more attractive and keyword-rich
3. Add brief analysis of changes

Keep titles concise, clear, and marketplace-compliant.',
            'Default fallback prompt for Titles - Anthropic',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (config_key) DO NOTHING
    """)
    
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description, updated_at)
        VALUES 
        (
            'ai.titles.default.gemini.prompt',
            'You are a title optimization assistant for eCommerce sellers.

Process multiple product titles simultaneously. For each title:

1. Analyze the current title
2. Propose 1 best optimized title that is more attractive and keyword-rich
3. Add brief analysis of changes

Keep titles concise, clear, and marketplace-compliant.',
            'Default fallback prompt for Titles - Gemini',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (config_key) DO NOTHING
    """)
    
    # Step 3: Add note about legacy keys (don't delete them for backward compatibility)
    op.execute("""
        UPDATE system_config 
        SET description = description || ' [LEGACY - use marketplace-specific keys instead]'
        WHERE config_key IN ('ai.titles.anthropic.prompt', 'ai.titles.gemini.prompt')
        AND description NOT LIKE '%LEGACY%'
    """)


def downgrade():
    """Remove marketplace-specific prompts"""
    op.execute("""
        DELETE FROM system_config 
        WHERE config_key LIKE 'ai.titles.allegro.%'
        OR config_key LIKE 'ai.titles.default.%'
    """)
    
    # Remove legacy note
    op.execute("""
        UPDATE system_config 
        SET description = REPLACE(description, ' [LEGACY - use marketplace-specific keys instead]', '')
        WHERE config_key IN ('ai.titles.anthropic.prompt', 'ai.titles.gemini.prompt')
    """)
