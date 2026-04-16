"""
Marketplace-agnostic token management utilities.

This module provides token refresh functionality that delegates to
marketplace-specific providers. Each provider handles its own auth mechanism.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db import models
from app.infrastructure.marketplaces.factory import factory
import logging

logger = logging.getLogger(__name__)


def get_valid_token_with_reauth_handling(
    db: Session, 
    account_id: int, 
    force_refresh: bool = False
) -> str:
    """
    Get a valid access token for an account, refreshing if needed.
    FOR API ENDPOINTS - raises HTTPException.
    
    Delegates to the marketplace provider for token refresh logic.
    
    Args:
        db: Database session
        account_id: Account ID to get token for
        force_refresh: Force refresh even if token is not expired
    
    Returns:
        Valid access token string
    
    Raises:
        HTTPException: 
            - 404 if account not found
            - 401 if refresh token expired (with needs_reauth=True in detail)
            - 503 for other token refresh failures
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get provider for this account
    provider = factory.get_provider_for_account(db, account_id)
    
    # Check if this marketplace supports token refresh
    if not provider.supports_token_refresh():
        # For non-OAuth marketplaces (e.g., API key), just return the token
        return account.access_token
    
    # Attempt token refresh if needed
    try:
        if force_refresh:
            # Force refresh
            provider.refresh_token_if_needed(db, account)
        else:
            # Let provider decide if refresh is needed
            provider.refresh_token_if_needed(db, account)
        
        # Refresh account object after potential DB updates
        db.refresh(account)
        return account.access_token
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's a re-auth required error
        if 'wymaga ponownej autoryzacji' in error_msg or account.needs_reauth:
            marketplace_name = account.marketplace_type.value if account.marketplace_type else 'marketplace'
            raise HTTPException(
                status_code=401,
                detail={
                    "message": f"Konto '{account.nazwa_konta}' ({marketplace_name}) wymaga ponownej autoryzacji.",
                    "needs_reauth": True,
                    "account_id": account.id,
                    "account_name": account.nazwa_konta
                }
            )
        else:
            logger.error(f"Token refresh failed for account {account_id}: {e}")
            raise HTTPException(status_code=503, detail=f"Nie udało się odświeżyć tokenu: {error_msg}")


def get_valid_token_for_task(
    db: Session,
    account_id: int,
    force_refresh: bool = False
) -> str:
    """
    Get a valid access token for an account, refreshing if needed.
    FOR BACKGROUND TASKS - raises regular Exception (not HTTPException).
    
    Delegates to the marketplace provider for token refresh logic.
    
    Args:
        db: Database session
        account_id: Account ID to get token for
        force_refresh: Force refresh even if token is not expired
    
    Returns:
        Valid access token string
    
    Raises:
        Exception: 
            - If account not found
            - If refresh token expired (with user-friendly message)
            - For other token refresh failures
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise Exception("Account not found")
    
    # Get provider for this account
    provider = factory.get_provider_for_account(db, account_id)
    
    # Check if this marketplace supports token refresh
    if not provider.supports_token_refresh():
        # For non-OAuth marketplaces (e.g., API key), just return the token
        return account.access_token
    
    # Attempt token refresh if needed
    try:
        if force_refresh:
            provider.refresh_token_if_needed(db, account)
        else:
            provider.refresh_token_if_needed(db, account)
        
        # Refresh account object after potential DB updates
        db.refresh(account)
        return account.access_token
        
    except Exception as e:
        # Re-raise with user-friendly error message
        raise


def refresh_account_token_if_needed(
    db: Session,
    account: models.Account,
    for_api: bool = False
) -> str:
    """
    Refresh account token if needed, using an existing account object.
    Useful when you already have the account loaded.
    
    Delegates to the marketplace provider for token refresh logic.
    
    Args:
        db: Database session
        account: Account model instance (already loaded)
        for_api: If True, raises HTTPException; if False, raises Exception
    
    Returns:
        Valid access token string
    
    Raises:
        HTTPException or Exception depending on for_api parameter
    """
    # Get provider for this account
    from app.infrastructure.marketplaces.factory import factory
    provider = factory.get_provider_by_type(db, account.marketplace_type)
    
    # Check if this marketplace supports token refresh
    if not provider.supports_token_refresh():
        # For non-OAuth marketplaces (e.g., API key), just return the token
        return account.access_token
    
    # Attempt token refresh if needed
    try:
        provider.refresh_token_if_needed(db, account)
        
        # Refresh account object after potential DB updates
        db.refresh(account)
        return account.access_token
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's a re-auth required error
        if 'wymaga ponownej autoryzacji' in error_msg or account.needs_reauth:
            marketplace_name = account.marketplace_type.value if account.marketplace_type else 'marketplace'
            
            if for_api:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": f"Konto '{account.nazwa_konta}' ({marketplace_name}) wymaga ponownej autoryzacji.",
                        "needs_reauth": True,
                        "account_id": account.id,
                        "account_name": account.nazwa_konta
                    }
                )
            else:
                raise Exception(
                    f"Konto '{account.nazwa_konta}' ({marketplace_name}) wymaga ponownej autoryzacji. "
                    f"Przejdź do zakładki 'Konta' i połącz konto ponownie."
                )
        else:
            logger.error(f"Token refresh failed for account {account.id}: {e}")
            
            if for_api:
                raise HTTPException(status_code=503, detail=f"Nie udało się odświeżyć tokenu: {error_msg}")
            else:
                raise Exception(f"Nie udało się odświeżyć tokenu: {error_msg}")
