"""Mirakl API error handling - Single Responsibility Principle"""
import logging
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)


class MiraklAPIError(Exception):
    """Base exception for Mirakl API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class MiraklRateLimitError(MiraklAPIError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: str):
        super().__init__(f"Przekroczono limit zapytań. Spróbuj ponownie za {retry_after} sekund")
        self.retry_after = retry_after


class MiraklErrorHandler:
    """Handles Mirakl API error responses - SRP"""
    
    ERROR_MESSAGES = {
        400: "Nieprawidłowe parametry lub niewłaściwe użycie API",
        401: "Brak autoryzacji - sprawdź klucz API",
        403: "Brak dostępu do zasobu",
        404: "Nie znaleziono zasobu",
        405: "Metoda HTTP niedozwolona",
        406: "Nieakceptowalny format odpowiedzi",
        410: "Zasób został trwale usunięty",
        415: "Nieobsługiwany typ zawartości",
        429: "Przekroczono limit zapytań",
        500: "Wewnętrzny błąd serwera"
    }
    
    def handle_response(self, response: requests.Response) -> None:
        """
        Check response and raise appropriate exception if error
        
        Args:
            response: HTTP response object
            
        Raises:
            MiraklAPIError: For API errors
            MiraklRateLimitError: For rate limit errors
        """
        if 200 <= response.status_code < 300:
            return
        
        error_msg = self._get_error_message(response.status_code)
        
        logger.error(f"Mirakl API Error {response.status_code}: {error_msg}")
        
        # Try to extract detailed error info
        error_data = self._extract_error_data(response)
        if error_data:
            logger.error(f"Error details: {error_data}")
        
        # Handle rate limiting specifically
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After', '60')
            raise MiraklRateLimitError(retry_after)
        
        raise MiraklAPIError(
            message=error_msg,
            status_code=response.status_code,
            response_data=error_data
        )
    
    def _get_error_message(self, status_code: int) -> str:
        """Get human-readable error message for status code"""
        return self.ERROR_MESSAGES.get(
            status_code,
            f"Nieznany błąd HTTP {status_code}"
        )
    
    def _extract_error_data(self, response: requests.Response) -> Optional[Dict]:
        """Extract error details from response body"""
        try:
            return response.json()
        except:
            text = response.text[:500] if response.text else ""
            return {"raw_response": text} if text else None
