import requests
from typing import Dict, List, Any
import uuid

ALLEGRO_API_URL = "https://api.allegro.pl"

class PromotionServiceError(Exception):
    """Custom exception for promotion service errors."""
    pass

def _get_headers(access_token: str) -> Dict[str, str]:
    """Returns standard headers for Allegro API requests."""
    return {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }

def list_promotions(access_token: str, promotion_type: str = 'MULTIPACK', limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Fetches a list of promotions from the Allegro API."""
    url = f"{ALLEGRO_API_URL}/sale/loyalty/promotions"
    params = {'promotionType': promotion_type, 'limit': limit, 'offset': offset}
    try:
        response = requests.get(url, headers=_get_headers(access_token), params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise PromotionServiceError(f"Failed to fetch promotions: {e}")

def create_multipack_promotion(access_token: str, name: str, offer_ids: List[str], for_each_quantity: int, percentage: int) -> Dict[str, Any]:
    """Creates a new multipack promotion."""
    url = f"{ALLEGRO_API_URL}/sale/loyalty/promotions"
    command_id = str(uuid.uuid4())
    
    # Corrected payload structure based on bundles_service.py
    payload = {
        "name": name,
        "benefits": [{
            "specification": {
                "type": "UNIT_PERCENTAGE_DISCOUNT",
                "trigger": {
                    "forEachQuantity": str(for_each_quantity),
                    "discountedNumber": "1"
                },
                "configuration": {
                    "percentage": str(percentage)
                }
            }
        }],
        "offerCriteria": [{
            "offers": [{"id": offer_id} for offer_id in offer_ids],
            "type": "CONTAINS_OFFERS"
        }]
    }
    
    headers = _get_headers(access_token)
    headers['Idempotency-Key'] = command_id
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error_details = "No response from server."
        if e.response is not None:
            error_details = f"Status: {e.response.status_code}, Body: {e.response.text}"
        raise PromotionServiceError(f"Failed to create promotion: {error_details}")

def delete_promotion(access_token: str, promotion_id: str) -> None:
    """Deletes a promotion by its ID."""
    url = f"{ALLEGRO_API_URL}/sale/loyalty/promotions/{promotion_id}"
    try:
        response = requests.delete(url, headers=_get_headers(access_token))
        response.raise_for_status()
    except requests.RequestException as e:
        raise PromotionServiceError(f"Failed to delete promotion {promotion_id}: {e}") 