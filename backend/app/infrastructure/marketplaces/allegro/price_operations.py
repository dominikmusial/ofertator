"""
Allegro-specific price operations.

Price management is currently Allegro-specific feature.
Other marketplaces may not support price updates via API.
"""
import requests
import uuid
import logging
from typing import Dict, Any

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


def get_offer_price(access_token: str, offer_id: str) -> str:
    """
    Fetch current price of an offer from Allegro API.
    Returns price as string "XX.XX"
    """
    url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
    headers = _get_auth_headers(access_token)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        price = data.get('sellingMode', {}).get('price', {}).get('amount', '0.00')
        logger.info(f"Fetched price for offer {offer_id}: {price} PLN")
        return price
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch price for offer {offer_id}: {e}")
        raise


def update_offer_price(access_token: str, offer_id: str, new_price: str) -> bool:
    """
    Update offer price using PATCH method.
    new_price: String format "XX.XX"
    Returns: True if successful
    """
    payload = {
        "sellingMode": {
            "price": {
                "amount": new_price,
                "currency": "PLN"
            }
        }
    }

    try:
        # Use PATCH to update offer
        url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
        headers = _get_auth_headers(access_token)
        
        response = requests.patch(url, headers=headers, json=payload)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Allegro API PATCH Error for offer {offer_id}: {response.status_code} - {response.text}")
            raise e

        logger.info(f"Successfully updated price for offer {offer_id} to {new_price} PLN")
        return True
    except Exception as e:
        logger.error(f"Failed to update price for offer {offer_id}: {e}")
        return False


def fetch_active_offers(access_token: str, limit: int = 1000) -> list:
    """
    Fetch all active offers for an account.
    Returns list of offers with id, name, price
    """
    url = f"{ALLEGRO_API_URL}/sale/offers"
    headers = _get_auth_headers(access_token)

    params = {
        'publication.status': 'ACTIVE',
        'limit': limit
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        offers = []

        for offer in data.get('offers', []):
            offers.append({
                'id': offer['id'],
                'name': offer['name'],
                'price': offer.get('sellingMode', {}).get('price', {}).get('amount', '0.00'),
                'category': offer.get('category', {}).get('id')
            })

        logger.info(f"Fetched {len(offers)} active offers")
        return offers
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch active offers: {e}")
        raise
