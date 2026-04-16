"""Decathlon products API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import models
from app.db.session import get_db
from app.db.repositories import AccountRepository
from app.core.auth import get_current_user
from app.infrastructure.marketplaces.factory import factory

router = APIRouter()


@router.get("/hierarchies")
def get_hierarchies(
    account_id: int,
    hierarchy_code: Optional[str] = None,
    max_level: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get category hierarchies (H11)
    
    Query Parameters:
        - account_id: Decathlon account ID (required)
        - hierarchy_code: Specific category code to retrieve
        - max_level: Number of child levels to retrieve
    """
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account or account.marketplace_type != models.MarketplaceType.decathlon:
        raise HTTPException(status_code=404, detail="Decathlon account not found")
    
    try:
        provider = factory.get_provider_for_account(db, account_id)
        hierarchies = provider.get_hierarchies(
            hierarchy_code=hierarchy_code,
            max_level=max_level
        )
        
        return {"hierarchies": hierarchies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products")
def get_products(
    account_id: int,
    product_references: str = Query(..., description="Format: TYPE|ID,TYPE|ID,..."),
    locale: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get products by references (P31)
    
    Query Parameters:
        - account_id: Decathlon account ID (required)
        - product_references: Product IDs with types, e.g., "EAN|1234567890,UPC|0987654321"
        - locale: Optional locale for translations (e.g., "fr_FR")
    """
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account or account.marketplace_type != models.MarketplaceType.decathlon:
        raise HTTPException(status_code=404, detail="Decathlon account not found")
    
    try:
        provider = factory.get_provider_for_account(db, account_id)
        return provider.get_products(
            product_references=product_references,
            locale=locale
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attributes")
def get_product_attributes(
    account_id: int,
    hierarchy_code: Optional[str] = None,
    max_level: Optional[int] = None,
    with_roles: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get product attribute configuration (PM11)
    
    Query Parameters:
        - account_id: Decathlon account ID (required)
        - hierarchy_code: Category code to get attributes for
        - max_level: Number of child category levels
        - with_roles: Return only attributes with roles
    """
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account or account.marketplace_type != models.MarketplaceType.decathlon:
        raise HTTPException(status_code=404, detail="Decathlon account not found")
    
    try:
        provider = factory.get_provider_for_account(db, account_id)
        return provider.get_product_attributes(
            hierarchy_code=hierarchy_code,
            max_level=max_level,
            with_roles=with_roles
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
