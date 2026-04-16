"""
Allegro-specific AI prompts and instructions.

These prompts are tailored for the Polish Allegro marketplace and include
marketplace-specific requirements like character limits, language, and rules.
"""

# Allegro title optimization - Anthropic
ALLEGRO_TITLES_PROMPT_ANTHROPIC = """Jesteś Tytułomatem dla sprzedawców eCommerce na Allegro. 

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
   - Główne usprawnienia"""

# Allegro title optimization - Gemini
ALLEGRO_TITLES_PROMPT_GEMINI = """Jesteś Tytułomatem dla sprzedawców eCommerce na Allegro. 

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
   - Główne usprawnienia"""

# Allegro-specific output format instructions
# Used by title optimizer to enforce Allegro's API requirements
ALLEGRO_TITLE_OUTPUT_INSTRUCTIONS = """

KRYTYCZNE WYMAGANIE: Każdy zoptymalizowany tytuł MUSI mieć maksymalnie 75 znaków. 
To jest techniczny limit API Allegro. Tytuły dłuższe niż 75 znaków zostaną odrzucone.

Odpowiedz WYŁĄCZNIE w formacie JSON (bez dodatkowego tekstu):
[
  {{
    "offer_id": "ID_OFERTY",
    "optimized_title": "Zoptymalizowany tytuł produktu",
    "analysis": "Krótka analiza zmian (opcjonalnie)"
  }}
]

Input titles:
{titles_json}"""

# Allegro title validation rules
ALLEGRO_TITLE_MAX_LENGTH = 75
ALLEGRO_TITLE_DISALLOWED_PATTERNS = [
    r'[\U0001F600-\U0001F64F]',  # Emoticons
    r'[\U0001F300-\U0001F5FF]',  # Symbols & pictographs
    r'[\U0001F680-\U0001F6FF]',  # Transport & map
    r'[\U0001F1E0-\U0001F1FF]',  # Flags
]

# Default AI generation parameters for Allegro
ALLEGRO_AI_PARAMS = {
    "anthropic": {
        "temperature": 1.0,
        "max_output_tokens": 4000,
        "top_p": 1.0,
        "stop_sequences": [],
    },
    "gemini": {
        "temperature": 1.0,
        "max_output_tokens": 4000,
        "top_p": 1.0,
        "stop_sequences": [],
    }
}


def get_allegro_prompt(module: str, provider: str) -> str:
    """
    Get Allegro-specific prompt for a given module and AI provider.
    
    Args:
        module: Module name (e.g., 'titles', 'offer_editor')
        provider: AI provider ('anthropic' or 'google'/'gemini')
        
    Returns:
        Prompt string
        
    Raises:
        ValueError: If module/provider combination not found
    """
    # Normalize provider name
    provider_normalized = 'gemini' if provider in ['google', 'gemini'] else provider
    
    if module == 'titles':
        if provider_normalized == 'anthropic':
            return ALLEGRO_TITLES_PROMPT_ANTHROPIC
        elif provider_normalized == 'gemini':
            return ALLEGRO_TITLES_PROMPT_GEMINI
    
    raise ValueError(f"No Allegro prompt found for module='{module}' and provider='{provider}'")


def get_allegro_ai_params(provider: str) -> dict:
    """
    Get default AI generation parameters for Allegro.
    
    Args:
        provider: AI provider ('anthropic' or 'google'/'gemini')
        
    Returns:
        Dictionary with generation parameters
    """
    provider_normalized = 'gemini' if provider in ['google', 'gemini'] else provider
    return ALLEGRO_AI_PARAMS.get(provider_normalized, {})
