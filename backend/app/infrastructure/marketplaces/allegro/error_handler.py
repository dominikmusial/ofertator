"""
Allegro API error handling and Polish error message generation.

Handles Allegro-specific error codes and provides user-friendly Polish error messages.
"""
import logging

logger = logging.getLogger(__name__)


def get_polish_error_message(response):
    """
    Parse Allegro API error response and return user-friendly Polish error message.
    """
    try:
        error_data = response.json()
        errors = error_data.get('errors', [])
        
        if not errors:
            return "Wystąpił nieoczekiwany błąd podczas kopiowania oferty."
        
        error = errors[0]
        error_code = error.get('code', '')
        error_message = error.get('message', '')
        user_message = error.get('userMessage', '')
        path = error.get('path', '')
        
        # Map common error codes to Polish messages
        error_translations = {
            'GallerySizeException': f'Przekroczono limit obrazów w galerii ({error.get("metadata", {}).get("gallerySizeLimit", "16")} maksymalnie). Usuń niektóre obrazy z oferty lub zmniejsz liczbę obrazów w szablonie.',
            'RequiredProductName': 'Brak wymaganej nazwy produktu. Sprawdź czy produkt w katalogu ma wszystkie wymagane dane.',
            'UnknownJSONProperty': f'Nieprawidłowa właściwość w żądaniu: {error.get("metadata", {}).get("unknownProperties", "")}',
            'InvalidParameterValue': 'Nieprawidłowa wartość parametru w ofercie.',
            'CategoryNotFound': 'Nie znaleziono kategorii produktu.',
            'ProductNotFound': 'Nie znaleziono produktu w katalogu.',
            'InsufficientPermissions': 'Brak uprawnień do wykonania tej operacji.',
            'InvalidShippingRate': 'Nieprawidłowa metoda dostawy.',
            'InvalidWarranty': 'Nieprawidłowa gwarancja.',
            'InvalidReturnPolicy': 'Nieprawidłowa polityka zwrotów.',
            'ImageSizeException': f'Rozmiar obrazu przekracza limit ({error.get("metadata", {}).get("maxSize", "nieznany")}). Zmniejsz rozmiar obrazu przed wysłaniem.',
            'ImageFormatException': f'Niepoprawny format obrazu. Obsługiwane formaty: {error.get("metadata", {}).get("supportedFormats", "JPG, PNG")}.',
            'ValidationException': f'Błąd walidacji: {user_message or error_message}',
            'AccessDeniedException': 'Brak dostępu do zasobu.'
        }
        
        if error_code in error_translations:
            return error_translations[error_code]
        
        if user_message and ('nie' in user_message.lower() or 'błąd' in user_message.lower()):
            return user_message
        
        if path:
            return f"Błąd w polu '{path}': {error_message}"
        
        return f"Błąd API Allegro: {error_message}"
        
    except Exception as parse_error:
        logger.error(f"Error parsing copy offer API error: {parse_error}")
        
        try:
            if hasattr(response, 'text'):
                response_text = response.text
                status_code = getattr(response, 'status_code', 'nieznany')
                
                try:
                    error_data = response.json()
                    if 'errors' in error_data and error_data['errors']:
                        first_error = error_data['errors'][0]
                        user_message = first_error.get('userMessage', '')
                        error_message = first_error.get('message', '')
                        
                        if user_message:
                            return f"Błąd kopiowania ({status_code}): {user_message}"
                        elif error_message:
                            return f"Błąd kopiowania ({status_code}): {error_message}"
                    
                    if len(response_text) > 300:
                        return f"Błąd kopiowania ({status_code}): {response_text[:300]}..."
                    else:
                        return f"Błąd kopiowania ({status_code}): {response_text}"
                        
                except (ValueError, KeyError):
                    if len(response_text) > 300:
                        return f"Błąd kopiowania ({status_code}): {response_text[:300]}..."
                    else:
                        return f"Błąd kopiowania ({status_code}): {response_text}"
        except Exception:
            pass
            
        return "Wystąpił błąd podczas kopiowania oferty. Sprawdź dane źródłowej oferty."


def parse_allegro_api_error(exception, offer_id=None):
    """
    Parse Allegro API error and return user-friendly Polish error message for offer updates.
    """
    try:
        if not hasattr(exception, 'response') or exception.response is None:
            return "Błąd połączenia z API Allegro"
        
        response = exception.response
        status_code = response.status_code
        response_text = response.text
        
        # HTTP status code specific messages
        if status_code == 403:
            return f"Brak dostępu do oferty {offer_id}. Sprawdź uprawnienia konta."
        elif status_code == 404:
            return f"Oferta {offer_id} nie istnieje lub została usunięta."
        elif status_code == 429:
            return "Przekroczono limit zapytań do API Allegro. Spróbuj ponownie za chwilę."
        
        # Try to extract specific error from response
        try:
            error_data = response.json()
            if 'errors' in error_data and error_data['errors']:
                first_error = error_data['errors'][0]
                error_code = first_error.get('code', '')
                error_message = first_error.get('message', '')
                user_message = first_error.get('userMessage', '')
                
                # Allegro-specific error codes
                error_translations = {
                    'OfferAccessDeniedException': 'Brak dostępu do oferty. Oferta może należeć do innego konta.',
                    'VALIDATION_ERROR': 'Błąd walidacji danych oferty.',
                    'GallerySizeException': 'Przekroczono limit obrazów w galerii.',
                    'ConstraintViolationException.DependencyValidator': 'Konflikt w parametrach oferty. Niektóre parametry są zależne od siebie.'
                }
                
                if error_code in error_translations:
                    return f"{error_translations[error_code]}: {user_message or error_message}"
                
                if user_message:
                    return user_message
                elif error_message:
                    return f"Błąd API: {error_message}"
        except (ValueError, KeyError):
            pass
        
        # Fallback to generic message with status code
        if len(response_text) > 200:
            return f"Błąd {status_code}: {response_text[:200]}..."
        else:
            return f"Błąd {status_code}: {response_text}"
            
    except Exception as e:
        logger.error(f"Error parsing Allegro API error: {e}")
        return f"Wystąpił błąd podczas aktualizacji oferty {offer_id or ''}"


def handle_parameter_validation_error(exception, offer_id, payload):
    """
    Handle parameter validation errors by attempting to update only description.
    According to Allegro API docs, if parameters have conflicts, we should update only what we need.
    """
    if not hasattr(exception, 'response') or not exception.response:
        return None
        
    try:
        response_text = exception.response.text
        
        # Check if it's a parameter dependency validation error
        if ('ConstraintViolationException.DependencyValidator' in response_text and 
            'parameters' in response_text):
            
            logger.info(f"Parameter validation conflict detected for offer {offer_id}")
            logger.info("Attempting to update only description without parameters")
            
            # Remove parameters from payload and try again with only description
            clean_payload = {}
            if 'description' in payload:
                clean_payload['description'] = payload['description']
            if 'images' in payload:
                clean_payload['images'] = payload['images']
                
            return clean_payload
            
    except Exception as e:
        logger.error(f"Error parsing parameter validation error: {e}")
        
    return None
