"""
Token cost calculation service for AI providers.
Handles dynamic pricing fetching and cost calculations.
"""

import asyncio
import aiohttp
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import re
import json

logger = logging.getLogger(__name__)

class TokenCostService:
    """Service for calculating AI token costs using dynamic pricing"""
    
    # Cache pricing data to avoid excessive API calls
    _pricing_cache = {}
    _cache_expiry = {}
    CACHE_DURATION_HOURS = 24
    
    # Fallback pricing (updated manually as last resort)
    FALLBACK_PRICING = {
        'anthropic': {
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
            'claude-3-5-sonnet-20240620': {'input': 0.003, 'output': 0.015},
            'claude-3-5-haiku-20241022': {'input': 0.001, 'output': 0.005},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
        },
        'google': {
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
            'gemini-1.5-flash': {'input': 0.000075, 'output': 0.0003},
            'gemini-1.5-flash-8b': {'input': 0.0000375, 'output': 0.00015},
            'gemini-2.0-flash': {'input': 0.000075, 'output': 0.0003},
            'gemini-2.5-pro': {'input': 0.00125, 'output': 0.005},
            'gemini-2.5-flash': {'input': 0.000075, 'output': 0.0003},
        }
    }
    
    @classmethod
    async def get_anthropic_pricing(cls) -> Dict[str, Dict[str, float]]:
        """Fetch current Anthropic pricing from their website/API"""
        cache_key = 'anthropic_pricing'
        
        # Check cache first
        if cls._is_cache_valid(cache_key):
            return cls._pricing_cache[cache_key]
        
        try:
            # Try to scrape pricing from Anthropic's pricing page
            async with aiohttp.ClientSession() as session:
                async with session.get('https://docs.anthropic.com/en/docs/about-claude/pricing') as response:
                    if response.status == 200:
                        text = await response.text()
                        pricing = cls._parse_anthropic_pricing(text)
                        if pricing:
                            cls._pricing_cache[cache_key] = pricing
                            cls._cache_expiry[cache_key] = datetime.now() + timedelta(hours=cls.CACHE_DURATION_HOURS)
                            logger.info("Successfully fetched Anthropic pricing")
                            return pricing
        except Exception as e:
            logger.warning(f"Failed to fetch Anthropic pricing: {e}")
        
        # Fallback to cached or default pricing
        pricing = cls.FALLBACK_PRICING['anthropic']
        logger.info("Using fallback Anthropic pricing")
        return pricing
    
    @classmethod
    async def get_google_pricing(cls) -> Dict[str, Dict[str, float]]:
        """Fetch current Google Gemini pricing from their website/API"""
        cache_key = 'google_pricing'
        
        # Check cache first
        if cls._is_cache_valid(cache_key):
            return cls._pricing_cache[cache_key]
        
        try:
            # Try to scrape pricing from Google's pricing page
            async with aiohttp.ClientSession() as session:
                async with session.get('https://ai.google.dev/pricing') as response:
                    if response.status == 200:
                        text = await response.text()
                        pricing = cls._parse_google_pricing(text)
                        if pricing:
                            cls._pricing_cache[cache_key] = pricing
                            cls._cache_expiry[cache_key] = datetime.now() + timedelta(hours=cls.CACHE_DURATION_HOURS)
                            logger.info("Successfully fetched Google pricing")
                            return pricing
        except Exception as e:
            logger.warning(f"Failed to fetch Google pricing: {e}")
        
        # Fallback to cached or default pricing
        pricing = cls.FALLBACK_PRICING['google']
        logger.info("Using fallback Google pricing")
        return pricing
    
    @classmethod
    def _parse_anthropic_pricing(cls, html_text: str) -> Optional[Dict[str, Dict[str, float]]]:
        """Parse Anthropic pricing from their website HTML"""
        try:
            # This is a simplified parser - in production, you'd want more robust parsing
            # Look for pricing patterns in the HTML
            pricing = {}
            
            # Example patterns to look for:
            # "$3.00 per million input tokens"
            # "$15.00 per million output tokens"
            
            # For now, return None to use fallback
            return None
        except Exception as e:
            logger.error(f"Error parsing Anthropic pricing: {e}")
            return None
    
    @classmethod
    def _parse_google_pricing(cls, html_text: str) -> Optional[Dict[str, Dict[str, float]]]:
        """Parse Google pricing from their website HTML"""
        try:
            # This is a simplified parser - in production, you'd want more robust parsing
            # Look for pricing patterns in the HTML
            pricing = {}
            
            # Example patterns to look for:
            # "$0.075 per million input tokens"
            # "$0.30 per million output tokens"
            
            # For now, return None to use fallback
            return None
        except Exception as e:
            logger.error(f"Error parsing Google pricing: {e}")
            return None
    
    @classmethod
    def _is_cache_valid(cls, cache_key: str) -> bool:
        """Check if cached pricing is still valid"""
        if cache_key not in cls._pricing_cache or cache_key not in cls._cache_expiry:
            return False
        return datetime.now() < cls._cache_expiry[cache_key]
    
    @classmethod
    async def calculate_cost(
        cls,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, str]:
        """
        Calculate cost for given token usage.
        Returns costs as strings for precise decimal handling.
        """
        try:
            # Get current pricing
            if provider == 'anthropic':
                pricing = await cls.get_anthropic_pricing()
            elif provider == 'google':
                pricing = await cls.get_google_pricing()
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Get model pricing
            if model not in pricing:
                logger.warning(f"Model {model} not found in pricing, using closest match")
                # Try to find a similar model or use a default
                model = cls._find_similar_model(model, pricing)
            
            model_pricing = pricing.get(model)
            if not model_pricing:
                raise ValueError(f"No pricing found for model: {model}")
            
            # Calculate costs using Decimal for precision
            input_rate = Decimal(str(model_pricing['input']))
            output_rate = Decimal(str(model_pricing['output']))
            
            # Rates are per million tokens
            million = Decimal('1000000')
            
            input_cost = (Decimal(str(input_tokens)) / million * input_rate).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
            output_cost = (Decimal(str(output_tokens)) / million * output_rate).quantize(
                Decimal('0.000001'), rounding=ROUND_HALF_UP
            )
            total_cost = input_cost + output_cost
            
            return {
                'input_cost_usd': str(input_cost),
                'output_cost_usd': str(output_cost),
                'total_cost_usd': str(total_cost),
                'pricing_version': f"{provider}_{datetime.now().strftime('%Y%m%d')}"
            }
            
        except Exception as e:
            logger.error(f"Error calculating cost: {e}")
            # Return zero costs on error
            return {
                'input_cost_usd': '0.000000',
                'output_cost_usd': '0.000000',
                'total_cost_usd': '0.000000',
                'pricing_version': f"error_{datetime.now().strftime('%Y%m%d')}"
            }
    
    @classmethod
    def _find_similar_model(cls, model: str, pricing: Dict[str, Dict[str, float]]) -> str:
        """Find a similar model in pricing if exact match not found"""
        model_lower = model.lower()
        
        # Try to match by model family
        for available_model in pricing.keys():
            available_lower = available_model.lower()
            
            # Check for common patterns
            if 'claude-3.5-sonnet' in model_lower and 'claude-3.5-sonnet' in available_lower:
                return available_model
            elif 'claude-3.5-haiku' in model_lower and 'claude-3.5-haiku' in available_lower:
                return available_model
            elif 'gemini-1.5-pro' in model_lower and 'gemini-1.5-pro' in available_lower:
                return available_model
            elif 'gemini-1.5-flash' in model_lower and 'gemini-1.5-flash' in available_lower:
                return available_model
        
        # If no match found, return the first available model
        return list(pricing.keys())[0] if pricing else model
    
    @classmethod
    async def get_current_pricing_summary(cls) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Get current pricing for all providers and models"""
        anthropic_pricing = await cls.get_anthropic_pricing()
        google_pricing = await cls.get_google_pricing()
        
        return {
            'anthropic': anthropic_pricing,
            'google': google_pricing,
            'last_updated': datetime.now().isoformat(),
            'cache_status': {
                'anthropic': cls._is_cache_valid('anthropic_pricing'),
                'google': cls._is_cache_valid('google_pricing')
            }
        }
