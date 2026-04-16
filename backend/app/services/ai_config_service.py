"""
AI Configuration Service - loads AI prompts and parameters from SystemConfig
"""

import logging
import json
from typing import Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
from app.db.repositories import SystemConfigRepository

logger = logging.getLogger(__name__)


class AIConfigService:
    """Service for managing AI configuration from database"""
    
    @staticmethod
    def get_config_for_module(db: Session, module: str, provider: str) -> Dict[str, Any]:
        """
        Load AI config from SystemConfig for specific module+provider.
        
        Args:
            db: Database session
            module: Module name ('titles' or 'offer_editor')
            provider: Provider name ('anthropic' or 'google')
            
        Returns:
            Dictionary with all configuration parameters
        """
        # Normalize provider name: 'google' -> 'gemini' for database keys
        db_provider = 'gemini' if provider == 'google' else provider
        prefix = f"ai.{module}.{db_provider}."
        configs = SystemConfigRepository.get_ai_configs_by_prefix(db, prefix)
        
        result = {}
        for config in configs:
            # Extract parameter name from key (e.g., 'ai.titles.anthropic.temperature' -> 'temperature')
            param_name = config.config_key[len(prefix):]
            
            # Parse value based on parameter type
            value = config.config_value
            
            # Handle stop_sequences as JSON array
            if param_name == 'stop_sequences':
                try:
                    result[param_name] = json.loads(value) if value else []
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse stop_sequences for {config.config_key}: {value}")
                    result[param_name] = []
            # Handle numeric values
            elif param_name in ['temperature', 'top_p']:
                try:
                    result[param_name] = float(value) if value else None
                except (ValueError, TypeError):
                    logger.warning(f"Failed to parse float for {config.config_key}: {value}")
                    result[param_name] = None
            elif param_name in ['max_output_tokens', 'top_k']:
                try:
                    result[param_name] = int(value) if value else None
                except (ValueError, TypeError):
                    logger.warning(f"Failed to parse int for {config.config_key}: {value}")
                    result[param_name] = None
            # Handle string values (prompts)
            else:
                result[param_name] = value
        
        return result
    
    @staticmethod
    def get_prompt_for_titles(db: Session, provider: str, marketplace_type: str) -> str:
        """
        Get prompt for Titles module with marketplace context.
        
        Args:
            db: Database session
            provider: Provider name ('anthropic' or 'google')
            marketplace_type: Marketplace type (e.g., 'allegro', 'decathlon') - REQUIRED
            
        Returns:
            Prompt string
            
        Raises:
            ValueError: If no prompt configured for the marketplace/provider combination
        """
        # Normalize provider name: 'google' -> 'gemini' for database keys
        db_provider = 'gemini' if provider == 'google' else provider
        
        # First try marketplace-specific prompt
        config_key = f"ai.titles.{marketplace_type}.{db_provider}.prompt"
        config = SystemConfigRepository.get(db, config_key)
        
        if config:
            return config.config_value
        
        # Fallback to default marketplace-agnostic prompt
        default_key = f"ai.titles.default.{db_provider}.prompt"
        default_config = SystemConfigRepository.get(db, default_key)
        
        if default_config:
            logger.info(f"Using default prompt for {marketplace_type}/{provider}")
            return default_config.config_value
        
        # Backward compatibility: try old key format (without marketplace prefix)
        legacy_key = f"ai.titles.{db_provider}.prompt"
        legacy_config = SystemConfigRepository.get(db, legacy_key)
        
        if legacy_config:
            logger.warning(f"Using legacy prompt key '{legacy_key}'. Consider migrating to '{config_key}' or '{default_key}'")
            return legacy_config.config_value
        
        # No prompt found in database
        logger.error(f"No AI prompt configured for {marketplace_type}/{provider}. Please configure in database.")
        raise ValueError(
            f"No AI prompt configured for marketplace '{marketplace_type}' and provider '{provider}'. "
            f"Please add configuration to SystemConfig table with key '{config_key}', '{default_key}', or legacy key '{legacy_key}'"
        )
    
    @staticmethod
    def get_generation_params(db: Session, module: str, provider: str) -> Dict[str, Any]:
        """
        Get API generation parameters (temperature, max_tokens, etc.).
        
        Args:
            db: Database session
            module: Module name ('titles' or 'offer_editor')
            provider: Provider name ('anthropic' or 'google')
            
        Returns:
            Dictionary with generation parameters
        """
        # get_config_for_module already handles provider normalization
        config = AIConfigService.get_config_for_module(db, module, provider)
        
        # Extract only generation parameters (not prompts)
        params = {}
        
        if 'temperature' in config and config['temperature'] is not None:
            params['temperature'] = config['temperature']
        
        if 'max_output_tokens' in config and config['max_output_tokens'] is not None:
            params['max_output_tokens'] = config['max_output_tokens']
        
        if 'top_p' in config and config['top_p'] is not None:
            params['top_p'] = config['top_p']
        
        if 'top_k' in config and config['top_k'] is not None:
            params['top_k'] = config['top_k']
        
        if 'stop_sequences' in config and config['stop_sequences']:
            params['stop_sequences'] = config['stop_sequences']
        
        return params


# Global instance
ai_config_service = AIConfigService()

