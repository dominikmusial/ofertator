"""Leroy Merlin (Mirakl) API endpoints"""
from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import Optional
from app.core.auth import get_current_verified_user
from app.db.session import get_db
from app.db.models import User, Account, UserMarketplaceAccount, MarketplaceType, UserRole
from app.infrastructure.marketplaces.mirakl import auth as mirakl_auth
from app.infrastructure.marketplaces.leroymerlin.config import LEROYMERLIN_CONFIG
from app.services.encryption_service import encryption_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/authorize")
async def authorize_leroymerlin_account(
    api_key: str = Form(...),
    shop_id: Optional[str] = Form(None, description="Shop ID from Mirakl (optional - will auto-fetch if not provided)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Add Leroy Merlin account using API key authentication
    
    Args:
        api_key: Mirakl API key
        shop_id: Shop ID from Mirakl (optional - will auto-fetch from API if not provided)
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Success response with account_id
    """
    try:
        logger.info(f"Authorizing Leroy Merlin account for user {current_user.id}")
        
        # Normalize empty string to None
        if shop_id == "":
            shop_id = None
        
        # Validate API key with Mirakl
        result = mirakl_auth.validate_credentials(api_key, shop_id, LEROYMERLIN_CONFIG.base_url)
        
        logger.info(f"Leroy Merlin credentials validated: {result['account_name']}")
        
        # Create account
        # For Mirakl API keys: set far future expiry (10 years) since they don't expire like OAuth tokens
        far_future = datetime.utcnow() + timedelta(days=3650)
        
        # Extract marketplace_specific_data from validation result
        marketplace_data = result.get('marketplace_specific_data', {
            'shop_id': shop_id,
            'shop_name': result.get('shop_name', '')
        })
        
        account = Account(
            nazwa_konta=result['account_name'],
            access_token=encryption_service.encrypt_api_key(api_key),
            refresh_token='',  # Mirakl doesn't use refresh tokens, but column is NOT NULL
            token_expires_at=far_future,  # API keys don't expire like OAuth tokens
            marketplace_type=MarketplaceType.leroymerlin,
            marketplace_specific_data=marketplace_data
        )
        db.add(account)
        db.flush()  # Get account.id
        
        logger.info(f"Created Leroy Merlin account: {account.id}")
        
        # Link account to user
        user_account = UserMarketplaceAccount(
            user_id=current_user.id,
            account_id=account.id,
            is_owner=True
        )
        
        # Auto-share with vsprint team if user is vsprint employee
        if current_user.role in [UserRole.vsprint_employee, UserRole.admin]:
            user_account.shared_with_vsprint = True
            logger.info(f"Auto-sharing Leroy Merlin account {account.id} with vsprint team")
        
        db.add(user_account)
        
        db.commit()
        
        logger.info(f"Successfully added Leroy Merlin account {account.id} for user {current_user.id}")
        
        return {
            "status": "success",
            "account_id": account.id,
            "account_name": account.nazwa_konta
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to authorize Leroy Merlin account: {e}")
        raise HTTPException(status_code=400, detail=str(e))
