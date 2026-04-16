"""Leroy Merlin (Mirakl) marketplace provider implementation"""
from typing import List, Optional, Dict
from app.db.models import MarketplaceType
from app.infrastructure.marketplaces.mirakl import MiraklAPIClient, auth as mirakl_auth
from .config import LEROYMERLIN_CONFIG
import logging

logger = logging.getLogger(__name__)


class LeroyMerlinMarketplaceClient:
    """
    Leroy Merlin marketplace client using shared Mirakl infrastructure.
    
    Implements protocols: OffersProvider, CategoriesProvider, 
    ImageUploadProvider, MarketplaceIdentity
    
    Note: Does NOT implement TokenRefreshProvider - Mirakl uses static API keys.
    """
    
    def __init__(self, api_key: str, shop_id: Optional[str] = None):
        self.api_key = api_key
        self._config = LEROYMERLIN_CONFIG
        
        # Convert shop_id to int (Mirakl API requires integer)
        if shop_id:
            try:
                self.shop_id = int(shop_id)
            except ValueError:
                logger.error(f"Invalid shop_id: {shop_id}")
                raise ValueError(f"shop_id must be a valid integer, got: {shop_id}")
        else:
            # If no shop_id provided, will be fetched from API
            self.shop_id = 0
        
        # Compose Mirakl API client with Leroy Merlin config
        self._api_client = MiraklAPIClient(
            api_key=self.api_key,
            shop_id=self.shop_id,
            base_url=self._config.base_url
        )
        logger.info(f"Initialized LeroyMerlinMarketplaceClient with shop_id: {self.shop_id}")
    
    # ===== Core Methods =====
    
    def create_offer(self, offer_data: dict) -> dict:
        """
        Create new offer on Leroy Merlin/Mirakl
        
        Note: Mirakl uses async import pattern
        Returns import_id for tracking status
        """
        result = self._api_client.create_or_update_offers([offer_data])
        return {
            'import_id': result.import_id,
            'status': 'pending',
            'message': 'Offer creation queued. Track status with import_id'
        }
    
    def get_offer(self, offer_id: str) -> dict:
        """
        Get offer details from Leroy Merlin/Mirakl
        
        Args:
            offer_id: Offer ID (will be converted to int)
        """
        try:
            offer_id_int = int(offer_id)
        except ValueError:
            raise ValueError(f"offer_id must be a valid integer, got: {offer_id}")
        
        return self._api_client.get_offer(offer_id_int)
    
    def update_offer(self, offer_id: str, updates: dict) -> dict:
        """
        Update existing offer on Leroy Merlin/Mirakl
        
        Note: Mirakl uses async import pattern
        Updates must include offer_id in the updates dict
        """
        # Ensure offer_id is in updates
        try:
            offer_id_int = int(offer_id)
        except ValueError:
            raise ValueError(f"offer_id must be a valid integer, got: {offer_id}")
        
        updates['offer_id'] = offer_id_int
        
        result = self._api_client.update_offers([updates])
        return {
            'import_id': result.import_id,
            'status': 'pending',
            'message': 'Offer update queued. Track status with import_id'
        }
    
    def list_offers(self, filters: dict) -> List[dict]:
        """
        List offers with optional filters
        
        Args:
            filters: Dict with optional keys:
                - offer_state_codes: str
                - sku: str
                - max: int (default 100)
                - offset: int (default 0)
        """
        data = self._api_client.list_offers(
            offer_state_codes=filters.get('offer_state_codes'),
            sku=filters.get('sku'),
            max_results=filters.get('max', 100),
            offset=filters.get('offset', 0)
        )
        
        return data.get('offers', [])
    
    def upload_image(self, image_bytes: bytes, filename: str) -> str:
        """
        Upload image to Leroy Merlin/Mirakl
        
        Note: Mirakl doesn't have a direct image upload API
        Images must be hosted externally and referenced by URL
        """
        raise NotImplementedError(
            "Mirakl marketplaces don't support direct image upload. "
            "Host images externally (e.g., MinIO, CDN) and use image URLs in offer data."
        )
    
    def get_categories(self, parent_id: Optional[str] = None) -> List[dict]:
        """
        Get categories from Leroy Merlin/Mirakl
        
        Args:
            parent_id: Hierarchy code to filter by (optional)
        """
        hierarchies = self._api_client.get_hierarchies(
            hierarchy_code=parent_id
        )
        
        # Convert to dict format for compatibility
        return [
            {
                'code': h.code,
                'label': h.label,
                'type': h.type,
                'children': h.children if h.children else []
            }
            for h in hierarchies
        ]
    
    def get_hierarchies(self, hierarchy_code: Optional[str] = None, max_level: Optional[int] = None) -> List[dict]:
        """
        Get product hierarchies (H11 API)
        
        Args:
            hierarchy_code: Specific category code to retrieve
            max_level: Number of child levels to retrieve
        """
        hierarchies = self._api_client.get_hierarchies(
            hierarchy_code=hierarchy_code,
            max_level=max_level
        )
        
        return [
            {
                'code': h.code,
                'label': h.label,
                'type': h.type,
                'children': h.children
            }
            for h in hierarchies
        ]
    
    def get_products(self, product_references: str, locale: Optional[str] = None) -> dict:
        """
        Get products by references (P31 API)
        
        Args:
            product_references: Product IDs with types, e.g., "EAN|1234567890,UPC|0987654321"
            locale: Optional locale for translations (e.g., "fr_FR")
        """
        return self._api_client.get_products(
            product_references=product_references,
            locale=locale
        )
    
    def get_product_attributes(
        self,
        hierarchy_code: Optional[str] = None,
        max_level: Optional[int] = None,
        with_roles: bool = False
    ) -> dict:
        """
        Get product attribute configuration (PM11 API)
        
        Args:
            hierarchy_code: Category code to get attributes for
            max_level: Number of child category levels
            with_roles: Return only attributes with roles
        """
        return self._api_client.get_product_attributes(
            hierarchy_code=hierarchy_code,
            max_level=max_level,
            with_roles=with_roles
        )
    
    def get_marketplace_type(self) -> MarketplaceType:
        """Return marketplace type"""
        return MarketplaceType.leroymerlin
    
    def get_capabilities(self) -> dict:
        """Return Leroy Merlin/Mirakl capabilities"""
        return {
            'bundle_promotions': False,
            'warranty_policies': False,
            'smart_category': False,
            'max_images': 10,
            'supports_sections': False,  # Mirakl doesn't use Allegro-style sections
            'auth_type': 'api_key',
            'async_operations': True,  # Mirakl uses async import pattern
            'supports_hierarchies': True
        }
    
    def normalize_error(self, error: Exception) -> str:
        """Convert API-specific exception to a user-friendly error message"""
        # TODO: Implement Mirakl-specific error parsing when needed
        return str(error)

    
    # Leroy Merlin-specific methods (not in interface) - can be added if needed
    
    def get_orders(
        self,
        start_date: str,
        end_date: str,
        order_state_codes: Optional[str] = None
    ) -> List[Dict]:
        """
        Leroy Merlin-specific: Get orders for reporting
        This is not part of the core IMarketplaceProvider interface
        
        Args:
            start_date: ISO 8601 format (e.g., "2024-01-01T00:00:00Z")
            end_date: ISO 8601 format
            order_state_codes: Comma-separated state codes (optional)
            
        Returns:
            List of orders with automatic pagination
        """
        return self._api_client.get_all_orders_paginated(
            start_date=start_date,
            end_date=end_date,
            order_state_codes=order_state_codes
        )
    
    def get_shop_info(self) -> Dict:
        """
        Get current shop information
        
        Returns:
            Dict with shop details
        """
        shop_info = self._api_client.get_account()
        return {
            'id': shop_info.id,
            'name': shop_info.name,
            'currency': shop_info.currency_iso_code,
            'is_professional': shop_info.is_professional,
            'description': shop_info.description
        }
