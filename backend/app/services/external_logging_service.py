"""
External logging service for sending operation logs to Google Sheets via webhook.
Only activates for users with admin or vsprint_employee roles.
Webhook URL is stored in database and cached in memory for performance.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import pytz

from app.db import models
from app.db.repositories import SystemConfigRepository

logger = logging.getLogger(__name__)

# Warsaw timezone (UTC+1/+2 depending on daylight saving time)
WARSAW_TZ = pytz.timezone('Europe/Warsaw')

# In-memory cache for webhook URL
_webhook_url_cache = {
    "url": None,
    "last_fetched": None,
    "cache_duration_seconds": 300  # 5 minutes
}


def get_webhook_url(db: Session, force_refresh: bool = False) -> str:
    """
    Get webhook URL with caching (5 min) and DB fallback on error.
    
    Args:
        db: Database session
        force_refresh: If True, bypass cache and fetch from DB
        
    Returns:
        Webhook URL or empty string if not configured
    """
    now = datetime.utcnow()
    cache = _webhook_url_cache
    
    # Check if cache is valid and not forcing refresh
    if (not force_refresh and 
        cache["url"] and 
        cache["last_fetched"] and 
        now - cache["last_fetched"] < timedelta(seconds=cache["cache_duration_seconds"])):
        return cache["url"]
    
    # Fetch from DB
    try:
        config = SystemConfigRepository.get(db, "external_logging_webhook_url")
        
        if config and config.config_value:
            # Update cache
            cache["url"] = config.config_value
            cache["last_fetched"] = now
            logger.debug(f"Fetched webhook URL from database: {config.config_value[:50]}...")
            return config.config_value
        
        # Fallback to empty string if not configured
        logger.warning("Webhook URL not configured in database")
        return ""
        
    except Exception as e:
        logger.error(f"Error fetching webhook URL from DB: {e}")
        # Return cached value if available, even if expired
        if cache["url"]:
            logger.warning(f"Using expired cached webhook URL due to DB error")
            return cache["url"]
        return ""


def is_admin_or_vsprint(user_id: int, db: Session) -> bool:
    """
    Check if user has admin or vsprint_employee role.
    
    Args:
        user_id: ID of the user to check
        db: Database session
        
    Returns:
        True if user is admin or vsprint_employee, False otherwise
    """
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
        
        return user.role in [models.UserRole.admin, models.UserRole.vsprint_employee]
    except Exception as e:
        logger.error(f"Error checking user role: {e}")
        return False


def _send_log_to_webhook(payload: Dict, db: Session) -> Dict:
    """
    Internal function to send logs to webhook with retry on error.
    
    Args:
        payload: Log data to send
        db: Database session
        
    Returns:
        Dictionary with 'success' (bool) and 'error' (str or None)
    """
    try:
        webhook_url = get_webhook_url(db)
        
        if not webhook_url:
            return {"success": False, "error": "Webhook URL not configured"}
        
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'text/plain;charset=utf-8'},
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return {"success": True, "error": None}
        
    except requests.exceptions.RequestException as e:
        # Retry with fresh URL from DB
        logger.warning(f"Webhook call failed, retrying with fresh URL: {e}")
        
        try:
            webhook_url = get_webhook_url(db, force_refresh=True)
            
            if not webhook_url:
                return {"success": False, "error": "Webhook URL not configured"}
            
            response = requests.post(
                webhook_url,
                headers={'Content-Type': 'text/plain;charset=utf-8'},
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            logger.info("Retry successful with fresh webhook URL")
            return {"success": True, "error": None}
            
        except Exception as retry_error:
            error_msg = f"Failed to send log after retry: {str(retry_error)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error sending log: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


def send_logs_batch(logs: List[Dict[str, any]], db: Session) -> Dict[str, any]:
    """
    Send multiple log entries to the external Google Sheets webhook.
    Uses batch format to avoid overwhelming the Apps Script.
    
    Args:
        logs: List of log dictionaries, each containing:
              date_pl, time_pl, kind, offer_id, value, value_before, account_name
        db: Database session
        
    Returns:
        Dictionary with 'success' (bool) and 'error' (str or None)
    """
    if not logs:
        return {"success": True, "error": None}
    
    try:
        payload = {"logs": logs}
        result = _send_log_to_webhook(payload, db)
        
        if result["success"]:
            logger.info(f"Successfully sent batch of {len(logs)} logs to external system")
        else:
            logger.error(f"Failed to send batch of {len(logs)} logs: {result['error']}")
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error sending batch logs: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


def create_log_entry(
    account_name: str,
    kind: str,
    offer_id: str,
    value: Optional[str] = None,
    value_before: Optional[str] = None
) -> Dict[str, any]:
    """
    Create a log entry dictionary with proper formatting.
    
    Args:
        account_name: Name of the account (nazwa_konta)
        kind: Type of operation
        offer_id: ID of the offer
        value: New value (or None/empty)
        value_before: Old value (or None/empty)
        
    Returns:
        Dictionary with all required fields for logging
    """
    now_pl = datetime.now(WARSAW_TZ)
    return {
        "date_pl": now_pl.strftime("%d.%m.%Y"),
        "time_pl": now_pl.strftime("%H:%M"),
        "kind": kind,
        "offer_id": offer_id,
        "value": value,
        "value_before": value_before,
        "account_name": account_name
    }


def clear_webhook_cache():
    """
    Clear the webhook URL cache.
    Useful for forcing a fresh fetch from database (e.g., after URL update).
    """
    _webhook_url_cache["url"] = None
    _webhook_url_cache["last_fetched"] = None
    logger.info("Webhook URL cache cleared")
