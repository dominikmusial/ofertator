"""
Allegro OAuth authentication - Device Code Flow.
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any
import logging
import os
from pathlib import Path

from dotenv import dotenv_values

logger = logging.getLogger(__name__)

ALLEGRO_API_URL = "https://api.allegro.pl"
ALLEGRO_AUTH_URL = "https://allegro.pl"

def _clean_credential(value: str) -> str:
    v = (value or "").strip()
    if len(v) >= 2 and v[0] == "`" and v[-1] == "`":
        v = v[1:-1].strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1].strip()
    if len(v) >= 2 and v[0] == "'" and v[-1] == "'":
        v = v[1:-1].strip()
    return v

def _get_credentials() -> tuple[str, str]:
    client_id = _clean_credential(os.getenv("ALLEGRO_CLIENT_ID"))
    client_secret = _clean_credential(os.getenv("ALLEGRO_CLIENT_SECRET"))
    if client_id and client_secret and client_id != "DUMMY" and client_secret != "DUMMY":
        return client_id, client_secret

    env_values = dotenv_values(Path(__file__).resolve().parents[5] / ".env")
    client_id = _clean_credential(str(env_values.get("ALLEGRO_CLIENT_ID") or ""))
    client_secret = _clean_credential(str(env_values.get("ALLEGRO_CLIENT_SECRET") or ""))
    return client_id, client_secret


def start_device_flow():
    """
    Initiates the device flow authentication with Allegro API.
    """
    client_id, client_secret = _get_credentials()
    url = f"{ALLEGRO_AUTH_URL}/auth/oauth/device"
    auth = HTTPBasicAuth(client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'client_id': client_id}

    response = requests.post(url, auth=auth, headers=headers, data=data)
    response.raise_for_status()
    return response.json()


def get_token_from_device_code(device_code: str):
    """
    Polls Allegro API to get the access token using the device code.
    """
    client_id, client_secret = _get_credentials()
    url = f"{ALLEGRO_AUTH_URL}/auth/oauth/token"
    auth = HTTPBasicAuth(client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
        'device_code': device_code
    }

    response = requests.post(url, auth=auth, headers=headers, data=data)
    # Don't raise for status here, as we expect errors until the user authorizes
    return response.json()


def refresh_allegro_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refreshes the Allegro API token.
    Raises HTTPError with specific status codes:
    - 400 with 'invalid_grant' error: refresh token expired/invalid
    - Other errors: general API failures
    """
    client_id, client_secret = _get_credentials()
    auth = HTTPBasicAuth(client_id, client_secret)
    data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = f"{ALLEGRO_AUTH_URL}/auth/oauth/token"
    
    response = requests.post(url, auth=auth, data=data, headers=headers)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Allegro Token Refresh Error: {response.status_code} - {response.text}")
        
        # Check if it's an invalid_grant error (expired/invalid refresh token)
        if response.status_code == 400:
            try:
                error_data = response.json()
                if error_data.get('error') == 'invalid_grant':
                    logger.warning(f"Refresh token expired or invalid: {error_data.get('error_description')}")
            except:
                pass
        
        raise e
        
    return response.json()


def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    Gets user information from Allegro API.
    """
    url = f"{ALLEGRO_API_URL}/me"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
