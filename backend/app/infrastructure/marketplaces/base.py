from abc import ABC, abstractmethod
from typing import List, Optional, Dict, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.db import models

# Import the canonical MarketplaceType from models (single source of truth)
from app.db.models import MarketplaceType


class IMarketplaceProvider(ABC):
    """Minimal interface - only truly common operations"""
    
    def supports_token_refresh(self) -> bool:
        """Check if this marketplace supports token refresh (OAuth-based)"""
        return False
    
    def refresh_token_if_needed(self, db: 'Session', account: 'models.Account') -> bool:
        """
        Refresh token if needed for OAuth-based marketplaces.
        
        Args:
            db: Database session
            account: Account model instance
            
        Returns:
            bool: True if token was refreshed, False otherwise
            
        Raises:
            Exception: If token refresh fails
        """
        return False
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token (legacy method for backward compatibility).
        Only implemented by OAuth-based marketplaces.
        """
        pass
    
    @abstractmethod
    def create_offer(self, offer_data: dict) -> dict:
        """Create new offer"""
        pass
    
    @abstractmethod
    def get_offer(self, offer_id: str) -> dict:
        """Get single offer details"""
        pass
    
    @abstractmethod
    def update_offer(self, offer_id: str, updates: dict) -> dict:
        """Update offer"""
        pass
    
    @abstractmethod
    def list_offers(self, filters: dict) -> List[dict]:
        """List offers with filters"""
        pass
    
    @abstractmethod
    def upload_image(self, image_bytes: bytes, filename: str) -> str:
        """Upload image, return URL"""
        pass
    
    @abstractmethod
    def get_categories(self, parent_id: Optional[str] = None) -> List[dict]:
        """Get categories"""
        pass
    
    @abstractmethod
    def get_marketplace_type(self) -> MarketplaceType:
        """Return marketplace type"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> dict:
        """Return marketplace capabilities"""
        pass
    
    @abstractmethod
    def normalize_error(self, error: Exception) -> str:
        """
        Convert API-specific exception to a user-friendly error message.
        Returns a string ready to be displayed to the user.
        """
        pass
