"""Marketplace Configuration Strategy Pattern

This module provides marketplace-specific configuration classes that handle
initialization and token preparation logic for different marketplace providers.

Each marketplace has its own config class that knows how to:
1. Create provider instances with correct parameters
2. Prepare access tokens (decrypt, validate, etc.)

This pattern allows adding new marketplaces without modifying the factory.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from .base import IMarketplaceProvider
import logging

logger = logging.getLogger(__name__)


class MarketplaceConfig(ABC):
    """Base class for marketplace-specific configuration"""
    
    @abstractmethod
    def create_provider_instance(
        self, 
        provider_class: type, 
        access_token: str, 
        marketplace_data: Dict[str, Any]
    ) -> IMarketplaceProvider:
        """
        Create provider instance with marketplace-specific initialization.
        
        Args:
            provider_class: Provider class to instantiate
            access_token: Access token/API key (already prepared)
            marketplace_data: Marketplace-specific data from database
            
        Returns:
            Configured provider instance
        """
        pass
    
    @abstractmethod
    def prepare_access_token(self, raw_token: str) -> str:
        """
        Prepare access token (decrypt if needed, validate, etc.).
        
        Args:
            raw_token: Raw token from database
            
        Returns:
            Prepared token ready for use
        """
        pass


class AllegroConfig(MarketplaceConfig):
    """Configuration for Allegro marketplace"""
    
    def create_provider_instance(
        self, 
        provider_class: type, 
        access_token: str, 
        marketplace_data: Dict[str, Any]
    ) -> IMarketplaceProvider:
        """
        Create Allegro provider instance.
        Allegro only needs access_token (OAuth).
        """
        return provider_class(access_token)
    
    def prepare_access_token(self, raw_token: str) -> str:
        """
        Allegro uses OAuth tokens - no decryption needed.
        Tokens are stored as-is in database.
        """
        return raw_token


class DecathlonConfig(MarketplaceConfig):
    """Configuration for Decathlon (Mirakl) marketplace"""
    
    def __init__(self):
        # Lazy import to avoid circular dependencies
        from app.services.encryption_service import encryption_service
        self.encryption_service = encryption_service
    
    def create_provider_instance(
        self, 
        provider_class: type, 
        access_token: str, 
        marketplace_data: Dict[str, Any]
    ) -> IMarketplaceProvider:
        """
        Create Decathlon provider instance.
        Decathlon requires shop_id in addition to API key.
        """
        shop_id = marketplace_data.get('shop_id')
        if not shop_id:
            logger.warning("No shop_id found in marketplace_data for Decathlon account")
        
        return provider_class(access_token, shop_id)
    
    def prepare_access_token(self, raw_token: str) -> str:
        """
        Decathlon uses encrypted API keys.
        Decrypt before use, with fallback for backward compatibility.
        """
        try:
            decrypted_token = self.encryption_service.decrypt_api_key(raw_token)
            logger.debug("Successfully decrypted Decathlon API key")
            return decrypted_token
        except Exception as e:
            logger.warning(
                f"Failed to decrypt Decathlon API key: {e}. "
                f"Using raw token (backward compatibility)"
            )
            # Fallback for backward compatibility (if token wasn't encrypted)
            return raw_token


# Marketplace configuration registry
# Add new marketplace configs here when implementing new marketplaces
MARKETPLACE_CONFIGS = {
    'allegro': AllegroConfig(),
    'decathlon': DecathlonConfig(),
}


def get_marketplace_config(marketplace_type_str: str) -> MarketplaceConfig:
    """
    Get marketplace configuration by marketplace type string.
    
    Args:
        marketplace_type_str: Marketplace type as string (e.g., 'allegro', 'decathlon')
        
    Returns:
        Marketplace configuration instance
        
    Raises:
        ValueError: If marketplace type is not supported
    """
    config = MARKETPLACE_CONFIGS.get(marketplace_type_str.lower())
    if not config:
        raise ValueError(
            f"Unsupported marketplace: {marketplace_type_str}. "
            f"Available: {list(MARKETPLACE_CONFIGS.keys())}"
        )
    return config
