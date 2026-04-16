from sqlalchemy.orm import Session
from typing import Union
from app.db.models import MarketplaceType
from .allegro.client import AllegroMarketplaceClient
from .decathlon.client import DecathlonMarketplaceClient
from .castorama.client import CastoramaMarketplaceClient
from .leroymerlin.client import LeroyMerlinMarketplaceClient
from .config import get_marketplace_config
from app.db.repositories import AccountRepository
import logging

logger = logging.getLogger(__name__)

# Type alias for all marketplace clients
MarketplaceClient = Union[
    AllegroMarketplaceClient,
    DecathlonMarketplaceClient,
    CastoramaMarketplaceClient,
    LeroyMerlinMarketplaceClient
]


class MarketplaceFactory:
    """
    Factory for creating marketplace provider instances.
    
    Uses Strategy Pattern via marketplace-specific config classes to handle
    initialization and token preparation without if/else chains.
    
    To add a new marketplace:
    1. Create provider client in marketplaces/<name>/client.py
    2. Create config class in config.py
    3. Register both in the _providers dict below
    """
    
    _providers = {
        MarketplaceType.allegro: {
            'class': AllegroMarketplaceClient,
            'config_key': 'allegro'
        },
        MarketplaceType.decathlon: {
            'class': DecathlonMarketplaceClient,
            'config_key': 'decathlon'
        },
        MarketplaceType.castorama: {
            'class': CastoramaMarketplaceClient,
            'config_key': 'castorama'
        },
        MarketplaceType.leroymerlin: {
            'class': LeroyMerlinMarketplaceClient,
            'config_key': 'leroymerlin'
        },
    }
    
    def get_provider(
        self, 
        marketplace_type: MarketplaceType, 
        access_token: str, 
        marketplace_specific_data: dict = None
    ) -> MarketplaceClient:
        """
        Create provider instance using marketplace-specific config.
        
        Args:
            marketplace_type: Type of marketplace (enum)
            access_token: Access token/API key
            marketplace_specific_data: Additional marketplace-specific data
            
        Returns:
            Configured marketplace provider instance
            
        Raises:
            ValueError: If marketplace type is not supported
        """
        provider_info = self._providers.get(marketplace_type)
        if not provider_info:
            raise ValueError(
                f"Unsupported marketplace: {marketplace_type}. "
                f"Available: {list(self._providers.keys())}"
            )
        
        # Get provider class and config
        provider_class = provider_info['class']
        config_key = provider_info['config_key']
        config = get_marketplace_config(config_key)
        
        # Use strategy pattern to create instance
        return config.create_provider_instance(
            provider_class, 
            access_token, 
            marketplace_specific_data or {}
        )
    
    def get_provider_for_account(self, db: Session, account_id: int) -> MarketplaceClient:
        """
        Get provider for account (fetches account from DB and creates provider).
        
        Args:
            db: Database session
            account_id: Account ID
            
        Returns:
            Configured marketplace provider instance
            
        Raises:
            ValueError: If account not found or marketplace type not supported
        """
        # Use AccountRepository instead of crud
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Get marketplace type (default to Allegro for backward compatibility)
        marketplace_type = account.marketplace_type or MarketplaceType.allegro
        
        # Get marketplace-specific data
        marketplace_specific_data = account.marketplace_specific_data or {}
        
        logger.info(f"Creating provider for account {account_id}: {marketplace_type}")
        
        # Get config for this marketplace
        provider_info = self._providers.get(marketplace_type)
        if not provider_info:
            raise ValueError(f"Unsupported marketplace: {marketplace_type}")
        
        config_key = provider_info['config_key']
        config = get_marketplace_config(config_key)
        
        # Use strategy pattern to prepare token (decrypt if needed)
        access_token = config.prepare_access_token(account.access_token)
        
        # Create and return provider
        return self.get_provider(marketplace_type, access_token, marketplace_specific_data)


# Singleton instance
factory = MarketplaceFactory()
