from app.infrastructure.marketplaces.base import IMarketplaceProvider, MarketplaceType
from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
from . import auth, api
from . import price_operations
from . import offer_operations
from . import template_processor
import logging

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.db import models

logger = logging.getLogger(__name__)


class AllegroMarketplaceClient(IMarketplaceProvider):
    """
    Allegro marketplace client implementation.
    
    Implements protocols: TokenRefreshProvider, OffersProvider, 
    CategoriesProvider, ImageUploadProvider, MarketplaceIdentity
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    # ===== Interface Methods (required by IMarketplaceProvider) =====
    
    def supports_token_refresh(self) -> bool:
        """Allegro uses OAuth with token refresh"""
        return True
    
    def refresh_token_if_needed(self, db: 'Session', account: 'models.Account') -> bool:
        """
        Refresh Allegro OAuth token if it's expiring soon.
        
        Args:
            db: Database session
            account: Account model instance
            
        Returns:
            bool: True if token was refreshed, False if refresh not needed
            
        Raises:
            Exception: If token refresh fails or refresh token is invalid
        """
        # Check if we need to refresh (expires within 5 minutes)
        should_refresh = account.token_expires_at <= datetime.utcnow() + timedelta(minutes=5)
        
        if not should_refresh:
            return False
        
        try:
            # Refresh the token
            new_token_data = auth.refresh_allegro_token(account.refresh_token)
            
            # Update account with new tokens
            account.access_token = new_token_data['access_token']
            account.refresh_token = new_token_data['refresh_token']
            account.token_expires_at = datetime.utcnow() + timedelta(seconds=new_token_data['expires_in'])
            account.refresh_token_expires_at = datetime.utcnow() + timedelta(days=90)
            account.last_token_refresh = datetime.utcnow()
            account.needs_reauth = False
            
            db.commit()
            db.refresh(account)
            
            logger.info(f"Successfully refreshed token for Allegro account {account.id} ({account.nazwa_konta})")
            return True
            
        except Exception as e:
            # Check if it's an invalid/expired refresh token error
            error_str = str(e).lower()
            if 'invalid' in error_str or 'expired' in error_str or 'invalid_grant' in error_str:
                # Mark account as needing re-authentication
                account.needs_reauth = True
                db.commit()
                
                logger.error(
                    f"Refresh token expired for Allegro account {account.id} ({account.nazwa_konta}). "
                    f"Re-authentication required."
                )
                
                raise Exception(
                    f"Konto Allegro '{account.nazwa_konta}' wymaga ponownej autoryzacji. "
                    f"Token dostępowy wygasł lub został unieważniony. "
                    f"Przejdź do zakładki 'Konta' i połącz konto ponownie."
                )
            else:
                logger.error(f"Failed to refresh token for account {account.id}: {e}")
                raise Exception(f"Nie udało się odświeżyć tokenu Allegro: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token (legacy method for backward compatibility)"""
        return auth.refresh_allegro_token(refresh_token)
    
    def create_offer(self, offer_data: dict) -> dict:
        """Create new offer"""
        return api.create_product_offer(self.access_token, offer_data)
    
    def get_offer(self, offer_id: str) -> dict:
        """Get offer details"""
        return api.get_offer_details(self.access_token, offer_id)
    
    def update_offer(self, offer_id: str, updates: dict) -> dict:
        """Update offer"""
        return api.update_offer(self.access_token, offer_id, updates)
    
    def list_offers(self, filters: dict) -> List[dict]:
        """List offers with filters"""
        return api.list_offers(
            self.access_token,
            status=filters.get('status'),
            search=filters.get('search'),
            limit=filters.get('limit', 50),
            offset=filters.get('offset', 0),
            price_from=filters.get('price_from'),
            price_to=filters.get('price_to'),
            category_id=filters.get('category_id'),
            offer_ids=filters.get('offer_ids')
        )
    
    def upload_image(self, image_bytes: bytes, filename: str) -> str:
        """Upload image, return URL"""
        return api.upload_image(self.access_token, image_bytes)
    
    def get_categories(self, parent_id: Optional[str] = None) -> List[dict]:
        """Get categories"""
        return api.get_categories(self.access_token, parent_id)
    
    def get_marketplace_type(self) -> MarketplaceType:
        return MarketplaceType.allegro
    
    def get_capabilities(self) -> dict:
        return {
            'bundle_promotions': True,
            'warranty_policies': True,
            'smart_category': False,
            'max_images': 16,
            'supports_price_scheduling': True,
            'supports_template_processing': True,
            'supports_bulk_operations': True,
            'html_allowed_tags': ['h1', 'h2', 'p', 'ul', 'ol', 'li', 'b']
        }
    
    def normalize_error(self, error: Exception) -> str:
        """Convert API-specific exception to a user-friendly error message"""
        from .error_handler import parse_allegro_api_error
        
        # If it's an HTTP error (requests), parse it
        if hasattr(error, 'response'):
            # In update_offer_task, we sometimes pass offer_id for better messages
            # Here we just parse generic API errors
            return parse_allegro_api_error(error)
            
        return str(error)
    
    # ===== Allegro-specific methods (not in interface) =====
    
    def update_offer_title(self, offer_id: str, title: str) -> dict:
        """Update offer title (Allegro-specific)"""
        return api.update_offer_title(self.access_token, offer_id, title)
    
    def update_offer_status(self, offer_id: str, status: str) -> dict:
        """
        Update offer status (Allegro-specific).
        Status can be 'ACTIVE' or 'ENDED'.
        """
        return offer_operations.update_offer_status(self.access_token, offer_id, status)
    
    def bulk_edit_offers(self, offer_ids: List[str], actions: dict) -> str:
        """
        Bulk edit offers (Allegro-specific bulk commands).
        Returns command_id for tracking.
        """
        return offer_operations.bulk_edit_offers(self.access_token, offer_ids, actions)
    
    def update_offer_attachments(self, offer_id: str, update_data: dict) -> bool:
        """Update offer attachments (Allegro-specific)"""
        return offer_operations.update_offer_attachments(self.access_token, offer_id, update_data)
    
    # Price operations (Allegro-specific)
    
    def get_offer_price(self, offer_id: str) -> str:
        """Get current offer price (Allegro-specific)"""
        return price_operations.get_offer_price(self.access_token, offer_id)
    
    def update_offer_price(self, offer_id: str, new_price: str) -> bool:
        """Update offer price (Allegro-specific)"""
        return price_operations.update_offer_price(self.access_token, offer_id, new_price)
    
    def fetch_active_offers(self, limit: int = 1000) -> list:
        """Fetch all active offers (Allegro-specific)"""
        return price_operations.fetch_active_offers(self.access_token, limit)
    
    # Template processing (Allegro-specific)
    
    def process_template_sections_for_offer(
        self,
        template_sections: list,
        offer_details: dict,
        template_prompt: Optional[str] = None,
        image_mapping: Optional[Dict[str, str]] = None,
        user_id: Optional[int] = None,
        frame_scale: int = None,
        account_name: str = None,
        account_id: int = None,
        processing_mode: str = "Oryginalny",
        auto_fill_images: bool = True,
        save_processed_images: bool = False
    ) -> tuple[list, dict]:
        """
        Process template sections with AI content generation (Allegro-specific).
        
        Returns:
            tuple: (processed_sections, image_replacements)
        """
        return template_processor.process_template_sections_for_offer(
            template_sections,
            offer_details,
            template_prompt,
            image_mapping,
            user_id,
            frame_scale,
            account_name,
            account_id,
            processing_mode,
            auto_fill_images,
            save_processed_images
        )
    
    # Placeholder methods for future Allegro-specific features
    
    def create_bundle_promotion(self, bundle_data: dict) -> dict:
        """Create bundle promotion (Allegro-specific, not yet implemented)"""
        raise NotImplementedError("Bundle promotions not yet implemented")
    
    def get_warranty_policies(self) -> List[dict]:
        """Get warranty policies (Allegro-specific, not yet implemented)"""
        raise NotImplementedError("Warranty policies not yet implemented")
