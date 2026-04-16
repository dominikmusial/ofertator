"""Mirakl authentication module - configurable for any Mirakl marketplace"""
import logging
from typing import Dict, Any, Optional
from .api_client import MiraklAPIClient

logger = logging.getLogger(__name__)


def validate_credentials(api_key: str, shop_id: Optional[str], base_url: str) -> Dict[str, Any]:
    """
    Validate Mirakl API credentials
    Uses A01 endpoint to verify access
    
    Args:
        api_key: Mirakl API key
        shop_id: Shop ID (optional - will auto-fetch from API if not provided)
        base_url: Mirakl API base URL for the marketplace
        
    Returns:
        Dictionary with account information
        
    Raises:
        Exception if validation fails
    """
    try:
        # Auto-fetch shop_id if not provided
        if not shop_id:
            # Call A01 without shop_id parameter to get default shop
            # Pass None to skip shop_id param - API will use default shop
            logger.info("shop_id not provided, auto-fetching from API")
            temp_client = MiraklAPIClient(api_key, None, base_url)
            shop_info = temp_client.get_account()
            shop_id_int = shop_info.id
            logger.info(f"Auto-fetched shop_id: {shop_id_int} ({shop_info.name})")
        else:
            # Convert shop_id to int (OpenAPI spec requires integer)
            try:
                shop_id_int = int(shop_id)
            except ValueError:
                logger.error(f"Invalid shop_id format: {shop_id}")
                raise Exception(f"Nieprawidłowy format Shop ID. Musi być liczbą, otrzymano: {shop_id}")
        
        # Create client with validated shop_id and get account info
        client = MiraklAPIClient(api_key, shop_id_int, base_url)
        shop_info = client.get_account()
        
        logger.info(f"Validated Mirakl credentials for shop: {shop_info.name} (ID: {shop_info.id})")
        
        return {
            'access_token': api_key,  # Mirakl uses API key as permanent token
            'refresh_token': None,  # No refresh mechanism for API keys
            'account_name': shop_info.name,
            'shop_id': str(shop_info.id),  # Return as string for consistency with storage
            'marketplace_specific_data': {
                'shop_id': str(shop_info.id),
                'shop_name': shop_info.name,
                'currency': shop_info.currency_iso_code,
                'is_professional': shop_info.is_professional
            }
        }
        
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        raise Exception(f"Nieprawidłowy klucz API lub Shop ID: {str(e)}")


def refresh_token(api_key: str) -> Dict[str, Any]:
    """
    Mirakl uses static API keys - no refresh needed
    
    Args:
        api_key: Current API key
        
    Returns:
        Same credentials (no actual refresh)
    """
    return {
        'access_token': api_key,
        'refresh_token': None
    }
