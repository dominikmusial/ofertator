"""
Allegro-specific offer operations.

Includes status updates, bulk edits, and attachment management.
These operations use Allegro-specific API patterns.
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


def update_offer_status(access_token: str, offer_id: str, status: str):
    """Update offer status.

    Allegro API allows:
    • End offer → publication.status = "ENDED"
    • Activate again → publication.action = "ACTIVATE"
    """
    # First, validate that the offer exists by trying to fetch its details
    # This will raise HTTPError (404) if the offer doesn't exist
    try:
        url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.allegro.public.v1+json',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # Re-raise the error with the same status code for consistent error handling
        raise e
    
    url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "Content-Type": "application/vnd.allegro.public.v1+json",
    }

    if status == "ENDED":
        payload = {"publication": {"status": "ENDED"}}
    elif status == "ACTIVE":
        cmd_id = str(uuid.uuid4())
        url = f"{ALLEGRO_API_URL}/sale/offer-publication-commands/{cmd_id}"
        payload = {
            "publication": {"action": "ACTIVATE"},
            "offerCriteria": [{"type": "CONTAINS_OFFERS", "offers": [{"id": offer_id}]}]
        }
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    else:
        raise ValueError("Unsupported status value")

    # ENDED branch uses PATCH payload
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def bulk_edit_offers(access_token: str, offer_ids: list, actions: dict) -> str:
    """
    Bulk edit offers using Allegro bulk commands.
    Returns command_id for tracking.
    
    This is Allegro-specific - uses Allegro's bulk command API.
    """
    cmd_id = str(uuid.uuid4())
    url = f"{ALLEGRO_API_URL}/sale/offer-modification-commands/{cmd_id}"
    headers = _get_auth_headers(access_token)
    
    payload = {
        "modification": actions,
        "offerCriteria": [{
            "type": "CONTAINS_OFFERS",
            "offers": [{"id": offer_id} for offer_id in offer_ids]
        }]
    }
    
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    
    logger.info(f"Bulk edit command {cmd_id} created for {len(offer_ids)} offers")
    return cmd_id


def update_offer_attachments(access_token: str, offer_id: str, update_data: dict) -> bool:
    """
    Update offer attachments using PATCH method
    """
    try:
        headers = _get_auth_headers(access_token)
        url = f"{ALLEGRO_API_URL}/sale/product-offers/{offer_id}"
        
        response = requests.patch(url, headers=headers, json=update_data)
        
        if response.status_code == 200:
            logger.info(f"Successfully updated attachments for offer {offer_id}")
            return True
        else:
            logger.error(f"Failed to update attachments for offer {offer_id}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request error updating attachments for offer {offer_id}: {e}")
        return False
