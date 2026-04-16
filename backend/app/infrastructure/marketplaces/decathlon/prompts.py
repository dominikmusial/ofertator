"""
Decathlon (Mirakl) marketplace-specific AI prompts and instructions.

These prompts are tailored for the Decathlon marketplace which uses the Mirakl platform.
Different requirements may apply compared to other marketplaces.
"""

# Decathlon title optimization - Anthropic
# NOTE: This is a placeholder example. Customize based on Decathlon's actual requirements.
DECATHLON_TITLES_PROMPT_ANTHROPIC = """You are a title optimization assistant for eCommerce sellers on Decathlon (Mirakl platform).

You process multiple product titles simultaneously. For each title:

1. **Analyze the current title** for:
   - Compliance with Decathlon marketplace rules
   - Length (recommended: concise and descriptive)
   - Style and readability
   - Missing key information

2. **Propose 1 best optimized title** that:
   - Is more attractive to customers
   - Contains better keywords for sports/outdoor products
   - Maintains compliance with marketplace rules
   - Has optimal length for the platform

3. **Optimization rules**:
   - Use appropriate language for target market
   - Focus on sports/outdoor product attributes
   - Avoid special characters and emojis
   - Include brand, product type, and key features
   - Think like a customer searching for sports equipment
   - Preserve important information from the original title

4. **Add brief analysis** (optional, 1-2 sentences):
   - What you changed and why
   - Main improvements"""

# Decathlon title optimization - Gemini
DECATHLON_TITLES_PROMPT_GEMINI = """You are a title optimization assistant for eCommerce sellers on Decathlon (Mirakl platform).

You process multiple product titles simultaneously. For each title:

1. **Analyze the current title** for:
   - Compliance with Decathlon marketplace rules
   - Length (recommended: concise and descriptive)
   - Style and readability
   - Missing key information

2. **Propose 1 best optimized title** that:
   - Is more attractive to customers
   - Contains better keywords for sports/outdoor products
   - Maintains compliance with marketplace rules
   - Has optimal length for the platform

3. **Optimization rules**:
   - Use appropriate language for target market
   - Focus on sports/outdoor product attributes
   - Avoid special characters and emojis
   - Include brand, product type, and key features
   - Think like a customer searching for sports equipment
   - Preserve important information from the original title

4. **Add brief analysis** (optional, 1-2 sentences):
   - What you changed and why
   - Main improvements"""

# Decathlon-specific output format instructions
DECATHLON_TITLE_OUTPUT_INSTRUCTIONS = """

Respond ONLY in JSON format (no additional text):
[
  {{
    "offer_id": "OFFER_ID",
    "optimized_title": "Optimized product title",
    "analysis": "Brief analysis of changes (optional)"
  }}
]

Input titles:
{titles_json}"""

# Decathlon title validation rules
# NOTE: Customize these based on actual Decathlon/Mirakl requirements
DECATHLON_TITLE_MAX_LENGTH = 100  # Example - adjust based on actual limit
DECATHLON_TITLE_DISALLOWED_PATTERNS = [
    r'[\U0001F600-\U0001F64F]',  # Emoticons
    r'[\U0001F300-\U0001F5FF]',  # Symbols & pictographs
]

# Default AI generation parameters for Decathlon
DECATHLON_AI_PARAMS = {
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


def get_decathlon_prompt(module: str, provider: str) -> str:
    """
    Get Decathlon-specific prompt for a given module and AI provider.
    
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
            return DECATHLON_TITLES_PROMPT_ANTHROPIC
        elif provider_normalized == 'gemini':
            return DECATHLON_TITLES_PROMPT_GEMINI
    
    raise ValueError(f"No Decathlon prompt found for module='{module}' and provider='{provider}'")


def get_decathlon_ai_params(provider: str) -> dict:
    """
    Get default AI generation parameters for Decathlon.
    
    Args:
        provider: AI provider ('anthropic' or 'google'/'gemini')
        
    Returns:
        Dictionary with generation parameters
    """
    provider_normalized = 'gemini' if provider in ['google', 'gemini'] else provider
    return DECATHLON_AI_PARAMS.get(provider_normalized, {})
