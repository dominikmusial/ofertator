"""Decathlon (Mirakl) authentication module"""
import logging
from typing import Dict, Any
from .api import MiraklAPIClient

logger = logging.getLogger(__name__)


def validate_credentials(api_key: str, shop_id: str) -> Dict[str, Any]:
    """
    Validate Decathlon/Mirakl API credentials
    Uses A01 endpoint to verify access
    
    Args:
        api_key: Mirakl API key
        shop_id: Shop ID (must be valid integer string)
        
    Returns:
        Dictionary with account information
        
    Raises:
        Exception if validation fails
    """
    try:
        # Convert shop_id to int (OpenAPI spec requires integer)
        shop_id_int = int(shop_id)
        
        # Create client and test connection
        client = MiraklAPIClient(api_key, shop_id_int)
        shop_info = client.get_account()
        
        logger.info(f"Validated Mirakl credentials for shop: {shop_info.name}")
        
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
        
    except ValueError:
        logger.error(f"Invalid shop_id format: {shop_id}")
        raise Exception(f"Invalid shop_id format. Must be a number, got: {shop_id}")
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        raise Exception(f"Invalid API key or shop ID: {str(e)}")


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
