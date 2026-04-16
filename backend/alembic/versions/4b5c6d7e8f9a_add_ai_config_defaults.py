"""add ai config defaults

Revision ID: 4b5c6d7e8f9a
Revises: 3a8f7e2c4d1b
Create Date: 2025-01-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b5c6d7e8f9a'
down_revision = 'e8b329d4a71c'
branch_labels = None
depends_on = None


def upgrade():
    # Create system_config table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR NOT NULL UNIQUE,
            config_value TEXT NOT NULL,
            description VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by_user_id INTEGER,
            FOREIGN KEY (updated_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_system_config_id ON system_config (id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_system_config_config_key ON system_config (config_key)")
    
    # Insert default AI configurations for Titles module + Anthropic
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description, updated_at)
        VALUES 
        (
            'ai.titles.anthropic.prompt',
            'Jesteś Tytułomatem dla sprzedawców eCommerce (Allegro-first). 

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
            'Prompt for Titles optimization - Anthropic',
            CURRENT_TIMESTAMP
        ),
        ('ai.titles.anthropic.temperature', '1.0', 'Temperature for Anthropic (0.0-1.0)', CURRENT_TIMESTAMP),
        ('ai.titles.anthropic.max_output_tokens', '4000', 'Max output tokens for Titles', CURRENT_TIMESTAMP),
        ('ai.titles.anthropic.top_p', '1.0', 'Top P sampling', CURRENT_TIMESTAMP),
        ('ai.titles.anthropic.top_k', '', 'Top K sampling (empty = not set)', CURRENT_TIMESTAMP),
        ('ai.titles.anthropic.stop_sequences', '[]', 'Stop sequences as JSON array', CURRENT_TIMESTAMP)
        ON CONFLICT (config_key) DO NOTHING
    """)
    
    # Insert default AI configurations for Titles module + Gemini
    op.execute("""
        INSERT INTO system_config (config_key, config_value, description, updated_at)
        VALUES 
        (
            'ai.titles.gemini.prompt',
            'Jesteś Tytułomatem dla sprzedawców eCommerce (Allegro-first). 

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
            'Prompt for Titles optimization - Gemini',
            CURRENT_TIMESTAMP
        ),
        ('ai.titles.gemini.temperature', '1.0', 'Temperature for Gemini (0.0-2.0)', CURRENT_TIMESTAMP),
        ('ai.titles.gemini.max_output_tokens', '4000', 'Max output tokens for Titles', CURRENT_TIMESTAMP),
        ('ai.titles.gemini.top_p', '1.0', 'Top P sampling', CURRENT_TIMESTAMP),
        ('ai.titles.gemini.top_k', '', 'Top K sampling (empty = not set)', CURRENT_TIMESTAMP),
        ('ai.titles.gemini.stop_sequences', '[]', 'Stop sequences as JSON array', CURRENT_TIMESTAMP)
        ON CONFLICT (config_key) DO NOTHING
    """)
    


def downgrade():
    # Remove all AI configuration entries
    op.execute("""
        DELETE FROM system_config 
        WHERE config_key LIKE 'ai.%'
    """)

