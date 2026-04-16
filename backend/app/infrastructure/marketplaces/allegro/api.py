"""
Allegro API client functions.

All direct API calls to Allegro endpoints.
"""
from __future__ import annotations
import requests
import uuid
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

ALLEGRO_API_URL = "https://api.allegro.pl"


def _get_auth_headers(access_token: str, content_type: str = 'application/vnd.allegro.public.v1+json', language: str = None) -> Dict[str, str]:
    """Build authorization headers for Allegro API"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': content_type,
        'Idempotency-Key': str(uuid.uuid4())
    }
    if language:
        headers['Accept-Language'] = language
    return headers


def get_offer_details(access_token: str, offer_id: str) -> dict:
    """Get offer details from Allegro API"""
    url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_product_offer(access_token: str, offer_payload: dict, language: str = None) -> dict:
    """Create new product offer on Allegro"""
    headers = _get_auth_headers(access_token, language=language)
    url = f"{ALLEGRO_API_URL}/sale/product-offers"
    
    response = requests.post(url, headers=headers, json=offer_payload)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Allegro API Error: {response.status_code} - {response.text}")
        raise e
        
    return response.json()


def update_offer(access_token: str, offer_id: str, updates: dict) -> dict:
    """Update offer using PATCH"""
    url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
    headers = _get_auth_headers(access_token)
    
    response = requests.patch(url, headers=headers, json=updates)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Allegro API Update Error: {response.status_code} - {response.text}")
        raise e
        
    return response.json()


def update_offer_title(access_token: str, offer_id: str, title: str):
    """
    Updates the title of a specific offer using PATCH.
    """
    logger.info(f"update_offer_title called with offer_id='{offer_id}', title='{title}'")
    url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }
    payload = {'name': title}
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def list_offers(access_token: str, status: Optional[str] = None, search: Optional[str] = None, limit: int = 50, offset: int = 0, 
                price_from: Optional[float] = None, price_to: Optional[float] = None, category_id: Optional[str] = None, 
                offer_ids: Optional[list] = None):
    """Returns seller offers list simplified."""
    url = f"{ALLEGRO_API_URL}/sale/offers"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
    }
    params = {
        'limit': limit,
        'offset': offset,
    }
    if status:
        params['publication.status'] = status
    if search:
        params['name'] = search
    if price_from is not None:
        params['sellingMode.price.amount.gte'] = str(price_from)
    if price_to is not None:
        params['sellingMode.price.amount.lte'] = str(price_to)
    if category_id:
        params['category.id'] = category_id
    if offer_ids:
        # For offer IDs, we might need to use a different approach as Allegro API might not support filtering by multiple IDs in sale/offers
        # For now, we'll include this parameter but it might not work as expected
        params['offer.id'] = ','.join(offer_ids)
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def upload_image(access_token: str, image_bytes: bytes) -> str:
    """Upload image to Allegro"""
    headers = _get_auth_headers(access_token, content_type='image/jpeg')
    url = "https://upload.allegro.pl/sale/images"
    
    response = requests.post(url, headers=headers, data=image_bytes)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Allegro API Image Upload Error: {response.status_code} - {response.text}")
        raise e
    
    return response.json()["location"]


def get_categories(access_token: str, parent_id: Optional[str] = None) -> list:
    """
    Get Allegro categories, optionally filtered by parent category.
    
    Args:
        access_token: Allegro API access token
        parent_id: Optional parent category ID to get subcategories
        
    Returns:
        JSON response with categories list from Allegro API
    """
    url = f"{ALLEGRO_API_URL}/sale/categories"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Accept-Language': 'pl-PL',  # Get Polish category names
    }
    params = {}
    if parent_id:
        params['parent.id'] = parent_id
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
