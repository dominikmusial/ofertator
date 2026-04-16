"""Mirakl API client - configurable for any Mirakl marketplace"""
import logging
from typing import Optional, List, Dict, Any
from .http_client import IHttpClient, RequestsHttpClient
from .error_handler import MiraklErrorHandler
from .types import (
    HttpMethod,
    MiraklShopInfo,
    MiraklHierarchy,
    MiraklOffer,
    MiraklOrder,
    MiraklImportResponse,
    OrderStateCode
)

logger = logging.getLogger(__name__)


class MiraklAPIClient:
    """
    Clean Mirakl API client following SOLID principles
    Configurable base_url allows reuse across multiple Mirakl marketplaces
    """
    
    def __init__(
        self,
        api_key: str,
        shop_id: Optional[int],
        base_url: str,
        http_client: Optional[IHttpClient] = None
    ):
        self.api_key = api_key
        self.shop_id = shop_id
        self.base_url = base_url.rstrip('/')  # Remove trailing slash if present
        
        # Dependency injection - can swap HTTP client (DIP)
        if http_client is None:
            error_handler = MiraklErrorHandler()
            http_client = RequestsHttpClient(error_handler)
        
        self._http = http_client
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with API key"""
        return {
            'Authorization': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _add_shop_id(self, params: Optional[Dict] = None) -> Dict:
        """Add shop_id to request params (only if shop_id is set)"""
        if params is None:
            params = {}
        # Only add shop_id if it's not None - Mirakl uses default shop when omitted
        if self.shop_id is not None:
            params['shop_id'] = self.shop_id
        return params
    
    # ============ Account Operations (A01) ============
    
    def get_account(self) -> MiraklShopInfo:
        """
        Get shop information - A01
        Endpoint: GET /api/account
        """
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/account",
            headers=self._build_headers(),
            params=self._add_shop_id()
        )
        
        return MiraklShopInfo.from_api_response(response.data)
    
    # ============ Hierarchies/Categories (H11) ============
    
    def get_hierarchies(
        self,
        hierarchy_code: Optional[str] = None,
        max_level: Optional[int] = None
    ) -> List[MiraklHierarchy]:
        """
        Get category hierarchies - H11
        Endpoint: GET /api/hierarchies
        
        Args:
            hierarchy_code: Specific hierarchy to retrieve
            max_level: Number of child levels to retrieve
        """
        params = self._add_shop_id()
        
        if hierarchy_code:
            params['hierarchy'] = hierarchy_code
        if max_level is not None:
            params['max_level'] = max_level
        
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/hierarchies",
            headers=self._build_headers(),
            params=params
        )
        
        # Response contains hierarchies array
        hierarchies_data = response.data.get('hierarchies', [])
        return [MiraklHierarchy.from_api_response(h) for h in hierarchies_data]
    
    # ============ Product Operations (P31, PM11) ============
    
    def get_products(
        self,
        product_references: str,
        locale: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get products by references - P31
        Endpoint: GET /api/products
        
        Args:
            product_references: Format "TYPE|ID,TYPE|ID,..." 
                               e.g., "EAN|1234567890,UPC|9876543210"
            locale: Optional locale for translations
            
        Returns:
            Dict with 'products' array and 'total_count'
        """
        params = self._add_shop_id({'product_references': product_references})
        if locale:
            params['locale'] = locale
        
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/products",
            headers=self._build_headers(),
            params=params
        )
        
        return response.data
    
    def get_product_attributes(
        self,
        hierarchy_code: Optional[str] = None,
        max_level: Optional[int] = None,
        with_roles: bool = False
    ) -> Dict[str, Any]:
        """
        Get product attribute configuration - PM11
        Endpoint: GET /api/products/attributes
        
        Args:
            hierarchy_code: Category code to get attributes for
            max_level: Number of child category levels
            with_roles: Return only attributes with roles
            
        Returns:
            Dict with 'attributes' array
        """
        params = self._add_shop_id()
        
        if hierarchy_code:
            params['hierarchy'] = hierarchy_code
        if max_level is not None:
            params['max_level'] = max_level
        if with_roles:
            params['with_roles'] = 'true'
        
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/products/attributes",
            headers=self._build_headers(),
            params=params
        )
        
        return response.data
    
    # ============ Offer Operations (OF21, OF22, OF24, OF04) ============
    
    def list_offers(
        self,
        offer_state_codes: Optional[str] = None,
        sku: Optional[str] = None,
        max_results: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List offers - OF21
        Endpoint: GET /api/offers
        
        Returns dict with 'offers' array and 'total_count'
        """
        params = self._add_shop_id({
            'max': max_results,
            'offset': offset
        })
        
        if offer_state_codes:
            params['offer_state_codes'] = offer_state_codes
        if sku:
            params['sku'] = sku
        
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/offers",
            headers=self._build_headers(),
            params=params
        )
        
        return response.data
    
    def get_offer(self, offer_id: int) -> Dict[str, Any]:
        """
        Get single offer details - OF22
        Endpoint: GET /api/offers/{offer}
        
        Note: offer parameter is integer, not string
        """
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/offers/{offer_id}",
            headers=self._build_headers(),
            params=self._add_shop_id()
        )
        
        return response.data
    
    def create_or_update_offers(self, offers: List[Dict[str, Any]]) -> MiraklImportResponse:
        """
        Create, update, or delete offers (async operation) - OF24
        Endpoint: POST /api/offers
        
        Returns import_id to track operation status
        Must send all offer fields; unsent fields are reset to default
        
        Args:
            offers: List of offer data dicts
            
        Returns:
            MiraklImportResponse with import_id for tracking
        """
        payload = {"offers": offers}
        
        response = self._http.request(
            method=HttpMethod.POST,
            url=f"{self.base_url}/offers",
            headers=self._build_headers(),
            params=self._add_shop_id(),
            json_data=payload
        )
        
        return MiraklImportResponse.from_api_response(response.data)
    
    def update_offers(self, offers: List[Dict[str, Any]]) -> MiraklImportResponse:
        """
        Update offers field by field (async operation) - OF04
        Endpoint: PUT /api/offers
        
        Returns import_id to track operation status
        Only specified fields are updated; unspecified fields remain unchanged
        
        Args:
            offers: List of offer updates
            
        Returns:
            MiraklImportResponse with import_id for tracking
        """
        payload = {"offers": offers}
        
        response = self._http.request(
            method=HttpMethod.PUT,
            url=f"{self.base_url}/offers",
            headers=self._build_headers(),
            params=self._add_shop_id(),
            json_data=payload
        )
        
        return MiraklImportResponse.from_api_response(response.data)
    
    def import_offers(self, offers: List[Dict[str, Any]]) -> MiraklImportResponse:
        """
        Import offers (async operation) - OF01
        Endpoint: POST /api/offers/imports
        
        Returns import_id to track operation status
        
        Args:
            offers: List of offers to import
            
        Returns:
            MiraklImportResponse with import_id for tracking
        """
        payload = {"offers": offers}
        
        response = self._http.request(
            method=HttpMethod.POST,
            url=f"{self.base_url}/offers/imports",
            headers=self._build_headers(),
            params=self._add_shop_id(),
            json_data=payload
        )
        
        return MiraklImportResponse.from_api_response(response.data)
    
    # ============ Order Operations (OR11) ============
    
    def get_orders(
        self,
        start_date: str,
        end_date: str,
        order_state_codes: Optional[str] = None,
        max_results: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get orders - OR11
        Endpoint: GET /api/orders
        
        Args:
            start_date: ISO 8601 date-time format
            end_date: ISO 8601 date-time format
            order_state_codes: Comma-separated state codes
            max_results: Maximum results per page (default 100)
            offset: Offset for pagination
            
        Returns:
            Dict with 'orders' array and 'total_count'
        """
        if not order_state_codes:
            order_state_codes = "SHIPPING,SHIPPED,TO_COLLECT,RECEIVED,CLOSED,REFUSED"
        
        params = self._add_shop_id({
            'start_date': start_date,
            'end_date': end_date,
            'order_state_codes': order_state_codes,
            'max': max_results,
            'offset': offset
        })
        
        response = self._http.request(
            method=HttpMethod.GET,
            url=f"{self.base_url}/orders",
            headers=self._build_headers(),
            params=params
        )
        
        return response.data
    
    def get_all_orders_paginated(
        self,
        start_date: str,
        end_date: str,
        order_state_codes: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all orders with automatic pagination
        
        Args:
            start_date: ISO 8601 date-time format
            end_date: ISO 8601 date-time format
            order_state_codes: Comma-separated state codes
            
        Returns:
            List of all orders
        """
        all_orders = []
        offset = 0
        max_results = 100
        
        logger.info(f"Fetching orders from {start_date} to {end_date}")
        
        while True:
            data = self.get_orders(
                start_date=start_date,
                end_date=end_date,
                order_state_codes=order_state_codes,
                max_results=max_results,
                offset=offset
            )
            
            orders = data.get('orders', [])
            total_count = data.get('total_count', 0)
            
            all_orders.extend(orders)
            logger.info(f"Fetched {len(orders)} orders (total: {len(all_orders)}/{total_count})")
            
            if len(orders) < max_results or len(all_orders) >= total_count:
                break
            
            offset += max_results
        
        return all_orders
