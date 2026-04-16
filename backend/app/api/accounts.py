from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import schemas, models
from app.db.repositories import AccountRepository
from app.db.session import get_db
from app.core.auth import get_current_verified_user
from app.core.security import verify_account_access
from app.db.models import User

router = APIRouter()

@router.get("/", response_model=List[schemas.AccountWithOwnership])
def read_accounts(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Retrieve user's accessible accounts"""
    accounts = AccountRepository.get_user_accounts(db, current_user)
    
    # Add ownership information
    result = []
    for account in accounts:
        user_account_relation = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == current_user.id,
            models.UserMarketplaceAccount.account_id == account.id
        ).first()
        
        account_data = schemas.AccountWithOwnership(
            **account.__dict__,
            is_owner=user_account_relation.is_owner if user_account_relation else False,
            shared_with_vsprint=user_account_relation.shared_with_vsprint if user_account_relation else False
        )
        result.append(account_data)
    
    return result

@router.get("/{account_id}", response_model=schemas.AccountWithOwnership)
def read_account(
    account_id: int, 
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get a specific account by ID"""
    # Verify access
    if not verify_account_access(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    db_account = AccountRepository.get_by_id(db, account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get ownership information
    user_account_relation = db.query(models.UserMarketplaceAccount).filter(
        models.UserMarketplaceAccount.user_id == current_user.id,
        models.UserMarketplaceAccount.account_id == account_id
    ).first()
    
    return schemas.AccountWithOwnership(
        **db_account.__dict__,
        is_owner=user_account_relation.is_owner if user_account_relation else False,
        shared_with_vsprint=user_account_relation.shared_with_vsprint if user_account_relation else False
    )

@router.delete("/{account_id}", response_model=schemas.MessageResponse)
def delete_account(
    account_id: int, 
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete account. If user is owner, completely remove the account and all relationships. 
    Otherwise, only remove user's association with the account."""
    
    # Verify user has access to this account
    if not verify_account_access(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    # Check if account exists
    db_account = AccountRepository.get_by_id(db, account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if user is the owner of the account
    user_account_relation = db.query(models.UserMarketplaceAccount).filter(
        models.UserMarketplaceAccount.user_id == current_user.id,
        models.UserMarketplaceAccount.account_id == account_id,
    ).first()
    
    if user_account_relation and user_account_relation.is_owner:
        # User is owner, force delete the account and all relationships
        success = AccountRepository.force_delete(db, account_id, current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete account")
        
        return {"message": "Account deleted completely"}
    else:
        # User is not owner, just delete their relationship with account
        success = AccountRepository.delete_user_account_relationship(db, current_user.id, account_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete account association")
        
        return {"message": "Account association deleted successfully"}

@router.post("/share", response_model=schemas.MessageResponse)
def share_account_with_team(
    sharing_data: schemas.AccountSharing,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Share/unshare account with vsprint team - only for vsprint employees who own the account"""
    if current_user.role.value not in ["admin", "vsprint_employee"]:
        raise HTTPException(
            status_code=403, 
            detail="Only vsprint employees can share accounts"
        )
    
    # Verify ownership
    user_account_relation = db.query(models.UserMarketplaceAccount).filter(
        models.UserMarketplaceAccount.user_id == current_user.id,
        models.UserMarketplaceAccount.account_id == sharing_data.account_id,
        models.UserMarketplaceAccount.is_owner == True
    ).first()
    
    if not user_account_relation:
        raise HTTPException(
            status_code=403, 
            detail="You must own the account to share it"
        )
    
    # Update sharing status
    if sharing_data.shared_with_vsprint:
        success = AccountRepository.share_with_vsprint(db, current_user.id, sharing_data.account_id)
        message = "Account shared with vsprint team"
    else:
        success = AccountRepository.unshare_with_vsprint(db, current_user.id, sharing_data.account_id)
        message = "Account no longer shared with vsprint team"
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update sharing status")
    
    return {"message": message} 