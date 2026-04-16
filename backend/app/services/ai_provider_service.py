"""
Service for managing AI providers and testing API keys.
"""

import logging
from typing import Dict, List, Optional, Tuple
from app.db.models import AIProvider, AnthropicModel, GeminiModel
import anthropic
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIProviderService:
    """Service for managing AI providers and validating API keys"""
    
    @staticmethod
    def get_available_models() -> Dict[str, List[Dict[str, str]]]:
        """Get all available models organized by provider"""
        return {
            "anthropic": [
                {"id": model.value, "name": AIProviderService._get_model_display_name(model.value, "anthropic")}
                for model in AnthropicModel
            ],
            "google": [
                {"id": model.value, "name": AIProviderService._get_model_display_name(model.value, "google")}
                for model in GeminiModel
            ]
        }
    
    @staticmethod
    def _get_model_display_name(model_id: str, provider: str) -> str:
        """Get human-readable display name for model"""
        display_names = {
            # Claude 4.5 Models
            "claude-sonnet-4-5-20250929": "Claude 4.5 Sonnet",

            # Claude 4.1 Models
            "claude-opus-4-1-20250805": "Claude 4.1 Opus",

            # Claude 4 Models
            "claude-opus-4-20250514": "Claude 4 Opus (Najnowszy - Najlepszy)",
            "claude-sonnet-4-20250514": "Claude 4 Sonnet (Najnowszy - Szybki)",
            
            # Claude 3.7 Models  
            "claude-3-7-sonnet-20250219": "Claude 3.7 Sonnet",
            
            # Claude 3.5 Models
            "claude-3-5-haiku-20241022": "Claude 3.5 Haiku (Szybki)",
            
            # Gemini 2.5 Models
            "gemini-2.5-pro": "Gemini 2.5 Pro (Najlepszy)",
            "gemini-2.5-flash": "Gemini 2.5 Flash (Szybki)",
            "gemini-2.5-flash-lite-preview-06-17": "Gemini 2.5 Flash Lite",
            
            # Gemini 2.0 Models
            "gemini-2.0-flash": "Gemini 2.0 Flash",
            "gemini-2.0-flash-lite": "Gemini 2.0 Flash Lite",
        }
        return display_names.get(model_id, model_id)
    
    @staticmethod
    def get_default_model() -> Tuple[str, str]:
        """Get the default AI provider and model"""
        return ("anthropic", "claude-3-7-sonnet-20250219")
    
    @staticmethod
    async def test_anthropic_api_key(api_key: str, model: str = "claude-3-7-sonnet-20250219") -> Tuple[bool, Optional[str]]:
        """Test Anthropic API key with a simple request"""
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            # Simple test message
            response = client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            
            if response and response.content:
                logger.info(f"Anthropic API key validated successfully for model {model}")
                return True, None
            else:
                return False, "Nieoczekiwana odpowiedź z API Anthropic"
                
        except anthropic.AuthenticationError:
            return False, "Nieprawidłowy klucz API Anthropic"
        except anthropic.PermissionDeniedError:
            return False, "Brak uprawnień do tego modelu"
        except anthropic.NotFoundError:
            return False, "Model nie istnieje lub nie jest dostępny"
        except anthropic.RateLimitError:
            return False, "Przekroczono limit żądań API"
        except anthropic.BadRequestError as e:
            return False, f"Błędne żądanie: {str(e)}"
        except Exception as e:
            logger.error(f"Error testing Anthropic API key: {e}")
            return False, f"Błąd testowania klucza API: {str(e)}"
    
    @staticmethod
    async def test_google_api_key(api_key: str, model: str = "gemini-1.5-flash") -> Tuple[bool, Optional[str]]:
        """Test Google API key with a simple request"""
        try:
            genai.configure(api_key=api_key)
            
            # Create the model
            model_instance = genai.GenerativeModel(model)
            
            # Use a more robust test request that works better with Gemini 2.5 models
            test_prompt = "Respond with: OK"
            generation_config = {
                'max_output_tokens': 50,
                'temperature': 0.1,
            }
            
            # For Gemini 2.5 models, add safety settings to avoid potential blocking
            safety_settings = None
            if "2.5" in model:
                import google.generativeai.types as genai_types
                safety_settings = [
                    {
                        "category": genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": genai_types.HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": genai_types.HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": genai_types.HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": genai_types.HarmBlockThreshold.BLOCK_NONE,
                    },
                ]
            
            # Make the request
            response = model_instance.generate_content(
                test_prompt, 
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response has content
            if response and hasattr(response, 'text') and response.text:
                logger.info(f"Google API key validated successfully for model {model}")
                return True, None
            elif response and hasattr(response, 'candidates') and response.candidates:
                # Check if there's a finish_reason that indicates success but no text
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    # If it finished due to length/stop token, that's actually success
                    if candidate.finish_reason in [1, 2]:  # STOP or MAX_TOKENS
                        logger.info(f"Google API key validated successfully for model {model} (finish_reason: {candidate.finish_reason})")
                        return True, None
                    else:
                        return False, f"Model zabezpieczenia zablokowały odpowiedź (finish_reason: {candidate.finish_reason})"
                else:
                    return False, "Nieoczekiwana odpowiedź z API Google - brak finish_reason"
            else:
                return False, "Nieoczekiwana odpowiedź z API Google - brak treści"
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "api key not valid" in error_msg or "invalid api key" in error_msg:
                return False, "Nieprawidłowy klucz API Google"
            elif "permission denied" in error_msg:
                return False, "Brak uprawnień do tego modelu"
            elif "not found" in error_msg:
                return False, "Model nie istnieje lub nie jest dostępny"
            elif "quota exceeded" in error_msg or "rate limit" in error_msg:
                return False, "Przekroczono limit żądań API"
            elif "finish_reason" in error_msg and "2" in error_msg:
                # Special handling for Gemini 2.5 models with finish_reason issues
                logger.info(f"Google API key validated (Gemini 2.5 model with expected finish_reason behavior): {model}")
                return True, None
            else:
                logger.error(f"Error testing Google API key: {e}")
                return False, f"Błąd testowania klucza API: {str(e)}"
    
    @staticmethod
    async def test_api_key(provider: str, api_key: str, model: str) -> Tuple[bool, Optional[str]]:
        """Test API key for specified provider and model"""
        if provider == "anthropic":
            return await AIProviderService.test_anthropic_api_key(api_key, model)
        elif provider == "google":
            return await AIProviderService.test_google_api_key(api_key, model)
        else:
            return False, f"Nieobsługiwany provider: {provider}"
    
    @staticmethod
    def get_user_ai_client(user_config, fallback_to_default: bool = True, user_role=None, registration_source=None):
        """Get AI client for user based on their configuration"""
        if user_config and user_config.is_active:
            # User has custom configuration
            try:
                from app.services.encryption_service import encryption_service
                decrypted_key = encryption_service.decrypt_api_key(user_config.encrypted_api_key)
                
                if user_config.ai_provider == AIProvider.anthropic:
                    return anthropic.Anthropic(api_key=decrypted_key), user_config.model_name
                elif user_config.ai_provider == AIProvider.google:
                    genai.configure(api_key=decrypted_key)
                    return genai.GenerativeModel(user_config.model_name), user_config.model_name
                    
            except Exception as e:
                logger.error(f"Error creating user AI client: {e}")
                if not fallback_to_default:
                    raise
        
        # Fallback to default configuration based on user type
        if fallback_to_default:
            from app.db.models import UserRole, RegistrationSource
            
            # Asystenci AI users get Gemini fallback (regardless of role)
            if registration_source == RegistrationSource.asystenciai and settings.GEMINI_API_KEY:
                try:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    return genai.GenerativeModel("gemini-2.0-flash"), "gemini-2.0-flash"
                except Exception as e:
                    logger.error(f"Error creating Gemini fallback client: {e}")
            
            # Regular external users get Gemini fallback
            if settings.GEMINI_API_KEY and user_role == UserRole.user:
                try:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    return genai.GenerativeModel("gemini-2.0-flash"), "gemini-2.0-flash"
                except Exception as e:
                    logger.error(f"Error creating Gemini fallback client for external user: {e}")
            
            # vSprint employees and admins get Anthropic fallback (only if NOT asystenciai)
            if settings.ANTHROPIC_API_KEY:
                if user_role and user_role in [UserRole.vsprint_employee, UserRole.admin]:
                    default_provider, default_model = AIProviderService.get_default_model()
                    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY), default_model
                elif user_role is None:
                    # Fallback for backward compatibility when no role provided
                    default_provider, default_model = AIProviderService.get_default_model()
                    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY), default_model
        
        return None, None

# Global instance
ai_provider_service = AIProviderService() 