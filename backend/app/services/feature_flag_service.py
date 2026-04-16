"""Feature Flag Service - Centralized feature flag management."""
from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.db.repositories.system_config_repository import SystemConfigRepository
import logging

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """Service for checking feature flags stored in SystemConfig"""
    
    # Cache for feature flags to avoid DB queries on every request
    _cache: Dict[str, str] = {}
    _cache_enabled = False  # Can be enabled with Redis in production
    
    @staticmethod
    def _get_flag(db: Session, key: str, default: str = "true") -> bool:
        """Get feature flag value from database"""
        if FeatureFlagService._cache_enabled and key in FeatureFlagService._cache:
            value = FeatureFlagService._cache[key]
        else:
            try:
                config = SystemConfigRepository.get(db, key)
                value = config.config_value if config else default
            except Exception:
                value = default
            
            if FeatureFlagService._cache_enabled:
                FeatureFlagService._cache[key] = value
        
        return value.lower() in ("true", "1", "yes", "enabled")
    
    @staticmethod
    def is_marketplace_enabled(db: Session, marketplace: str) -> bool:
        """
        Check if a marketplace is enabled.
        
        Args:
            db: Database session
            marketplace: Marketplace name (e.g., 'allegro', 'decathlon')
            
        Returns:
            True if marketplace is enabled, False otherwise
        """
        key = f"feature.marketplace.{marketplace.lower()}.enabled"
        return FeatureFlagService._get_flag(db, key, default="true")
    
    @staticmethod
    def is_registration_enabled(db: Session) -> bool:
        """
        Check if public registration is enabled.
        
        Returns:
            True if registration is enabled, False otherwise
        """
        return FeatureFlagService._get_flag(db, "feature.auth.registration.enabled", default="true")
    
    @staticmethod
    def is_google_sso_enabled(db: Session) -> bool:
        """
        Check if Google SSO is enabled.
        
        Returns:
            True if Google SSO is enabled, False otherwise
        """
        return FeatureFlagService._get_flag(db, "feature.auth.google_sso.enabled", default="true")
    
    @staticmethod
    def is_ai_config_enabled(db: Session) -> bool:
        """
        Check if AI Configuration admin page is enabled.
        
        Returns:
            True if AI Config is enabled, False otherwise
        """
        return FeatureFlagService._get_flag(db, "feature.admin.ai_config.enabled", default="true")
    
    @staticmethod
    def is_team_analytics_enabled(db: Session) -> bool:
        """
        Check if Team Analytics page is enabled.
        
        Returns:
            True if Team Analytics is enabled, False otherwise
        """
        return FeatureFlagService._get_flag(db, "feature.admin.team_analytics.enabled", default="true")
    
    @staticmethod
    def is_ai_usage_enabled(db: Session) -> bool:
        """
        Check if AI Usage tracking module is enabled.
        
        Returns:
            True if AI Usage is enabled, False otherwise
        """
        return FeatureFlagService._get_flag(db, "feature.modules.ai_usage.enabled", default="true")
    
    @staticmethod
    def is_user_ai_config_enabled(db: Session) -> bool:
        """
        Check if user AI Configuration in profile is enabled.
        
        Returns:
            True if user AI Config is enabled, False otherwise
        """
        return FeatureFlagService._get_flag(db, "feature.user.ai_config.enabled", default="true")
    
    @staticmethod
    def get_all_feature_flags(db: Session) -> Dict[str, bool]:
        """
        Get all feature flags as a dictionary.
        
        Returns:
            Dictionary mapping feature flag keys to boolean values
        """
        flags = {
            "marketplace": {
                "allegro": FeatureFlagService.is_marketplace_enabled(db, "allegro"),
                "decathlon": FeatureFlagService.is_marketplace_enabled(db, "decathlon"),
                "castorama": FeatureFlagService.is_marketplace_enabled(db, "castorama"),
                "leroymerlin": FeatureFlagService.is_marketplace_enabled(db, "leroymerlin"),
            },
            "auth": {
                "registration": FeatureFlagService.is_registration_enabled(db),
                "google_sso": FeatureFlagService.is_google_sso_enabled(db),
            },
            "admin": {
                "ai_config": FeatureFlagService.is_ai_config_enabled(db),
                "team_analytics": FeatureFlagService.is_team_analytics_enabled(db),
            },
            "modules": {
                "ai_usage": FeatureFlagService.is_ai_usage_enabled(db),
            },
            "user": {
                "ai_config": FeatureFlagService.is_user_ai_config_enabled(db),
            }
        }
        
        return flags
    
    @staticmethod
    def clear_cache():
        """Clear the feature flag cache"""
        FeatureFlagService._cache.clear()
    
    @staticmethod
    def enable_cache():
        """Enable feature flag caching"""
        FeatureFlagService._cache_enabled = True
        logger.info("Feature flag caching enabled")
    
    @staticmethod
    def disable_cache():
        """Disable feature flag caching"""
        FeatureFlagService._cache_enabled = False
        FeatureFlagService._cache.clear()
        logger.info("Feature flag caching disabled")
