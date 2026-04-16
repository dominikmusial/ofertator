"""Account Repository - Handles all marketplace account-related database operations."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timedelta
from app.db import models, schemas


class AccountRepository:
    """Repository for marketplace account-related database operations"""
    
    # ============ Basic Account CRUD ============
    
    @staticmethod
    def get_by_id(db: Session, account_id: int) -> Optional[models.Account]:
        """Get account by ID"""
        return db.query(models.Account).filter(models.Account.id == account_id).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.Account]:
        """Get all accounts with pagination"""
        return db.query(models.Account).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, account: schemas.AccountCreate, user_id: int) -> models.Account:
        """Create a new account and associate it with the user"""
        # Create the account
        db_account = models.Account(**account.model_dump())
        db.add(db_account)
        db.flush()  # Get the account ID without committing
        
        # Create user-account relationship
        AccountRepository.create_user_account_relationship(db, user_id, db_account.id, is_owner=True)
        
        db.commit()
        db.refresh(db_account)
        return db_account
    
    @staticmethod
    def update_token(db: Session, account_id: int, token_data: dict) -> Optional[models.Account]:
        """Update account tokens"""
        db_account = AccountRepository.get_by_id(db, account_id)
        if db_account:
            db_account.access_token = token_data['access_token']
            db_account.refresh_token = token_data['refresh_token']
            db_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            db_account.refresh_token_expires_at = datetime.utcnow() + timedelta(days=90)
            db_account.last_token_refresh = datetime.utcnow()
            db_account.needs_reauth = False
            db_account.updated_at = func.now()
            db.commit()
        return db_account
    
    @staticmethod
    def delete(db: Session, account_id: int) -> Optional[models.Account]:
        """
        Delete account only if no other users are associated with it.
        If other users are associated, this function should not be called directly.
        Use delete_user_account_relationship instead.
        """
        db_account = AccountRepository.get_by_id(db, account_id)
        if db_account:
            # Check if there are any user associations left
            remaining_associations = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == account_id
            ).count()
            
            if remaining_associations > 0:
                raise ValueError(f"Cannot delete account {account_id}: still has {remaining_associations} user associations")
            
            # Delete related data first to satisfy FK constraints
            db.query(models.Template).filter(models.Template.account_id == account_id).delete(synchronize_session=False)
            db.query(models.OfferBackup).filter(models.OfferBackup.account_id == account_id).delete(synchronize_session=False)
            db.query(models.AccountImage).filter(models.AccountImage.account_id == account_id).delete(synchronize_session=False)
            db.query(models.AITokenUsage).filter(models.AITokenUsage.account_id == account_id).delete(synchronize_session=False)
            db.query(models.UserActivityLog).filter(models.UserActivityLog.account_id == account_id).delete(synchronize_session=False)
            db.delete(db_account)
            db.commit()
        return db_account
    
    @staticmethod
    def force_delete(db: Session, account_id: int, owner_id: int) -> bool:
        """
        Force delete an account and all its associations.
        Can only be called by the account owner.
        """
        try:
            # Verify ownership
            owner_relation = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.user_id == owner_id,
                models.UserMarketplaceAccount.account_id == account_id,
                models.UserMarketplaceAccount.is_owner == True
            ).first()
            
            if not owner_relation:
                return False  # Not the owner
            
            # Get the account
            db_account = AccountRepository.get_by_id(db, account_id)
            if not db_account:
                return False  # Account doesn't exist
                
            # Delete all user-account relationships
            db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == account_id
            ).delete(synchronize_session=False)
            
            # Delete related templates and backups
            db.query(models.Template).filter(models.Template.account_id == account_id).delete(synchronize_session=False)
            db.query(models.OfferBackup).filter(models.OfferBackup.account_id == account_id).delete(synchronize_session=False)
            
            # Delete account images
            db.query(models.AccountImage).filter(models.AccountImage.account_id == account_id).delete(synchronize_session=False)
            
            # Delete AI token usage records
            db.query(models.AITokenUsage).filter(models.AITokenUsage.account_id == account_id).delete(synchronize_session=False)
            
            # Delete user activity logs
            db.query(models.UserActivityLog).filter(models.UserActivityLog.account_id == account_id).delete(synchronize_session=False)
            
            # Delete the account itself
            db.delete(db_account)
            db.commit()
            return True
            
        except Exception:
            db.rollback()
            return False
    
    # ============ User-Account Relationships ============
    
    @staticmethod
    def create_user_account_relationship(db: Session, user_id: int, account_id: int, is_owner: bool = True) -> models.UserMarketplaceAccount:
        """Create user-account relationship"""
        db_relation = models.UserMarketplaceAccount(
            user_id=user_id,
            account_id=account_id,
            is_owner=is_owner
        )
        db.add(db_relation)
        db.commit()
        db.refresh(db_relation)
        return db_relation
    
    @staticmethod
    def get_user_account_relationship(db: Session, user_id: int, account_id: int) -> Optional[models.UserMarketplaceAccount]:
        """Get user-account relationship if exists"""
        return db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == user_id,
            models.UserMarketplaceAccount.account_id == account_id
        ).first()
    
    @staticmethod
    def delete_user_account_relationship(db: Session, user_id: int, account_id: int) -> bool:
        """
        Delete user-account relationship. If user was the last one associated with the account,
        delete the account itself.
        """
        try:
            # Get the relationship
            user_account_relation = AccountRepository.get_user_account_relationship(db, user_id, account_id)
            
            if not user_account_relation:
                return False
            
            # Delete the relationship
            db.delete(user_account_relation)
            db.flush()  # Flush to get the deletion without committing
            
            # Check if there are any other users associated with this account
            remaining_associations = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == account_id
            ).count()
            
            if remaining_associations == 0:
                # No other users associated, delete the account itself
                db_account = AccountRepository.get_by_id(db, account_id)
                if db_account:
                    # Delete related templates and backups first
                    db.query(models.Template).filter(models.Template.account_id == account_id).delete(synchronize_session=False)
                    db.query(models.OfferBackup).filter(models.OfferBackup.account_id == account_id).delete(synchronize_session=False)
                    
                    # Delete account images
                    db.query(models.AccountImage).filter(models.AccountImage.account_id == account_id).delete(synchronize_session=False)
                    
                    # Delete AI token usage records
                    db.query(models.AITokenUsage).filter(models.AITokenUsage.account_id == account_id).delete(synchronize_session=False)
                    
                    # Delete user activity logs
                    db.query(models.UserActivityLog).filter(models.UserActivityLog.account_id == account_id).delete(synchronize_session=False)
                    
                    db.delete(db_account)
            
            db.commit()
            return True
            
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def get_user_accounts(db: Session, user: models.User) -> List[models.Account]:
        """Get accounts accessible to user based on role and sharing"""
        from app.core.security import get_user_accounts_query
        return get_user_accounts_query(db, user).all()
    
    @staticmethod
    def can_user_access_account(db: Session, user: models.User, account_id: int) -> bool:
        """Check if user can access an account (directly or through vSprint sharing)"""
        # Check direct access
        user_account = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == user.id,
            models.UserMarketplaceAccount.account_id == account_id
        ).first()
        
        if user_account:
            return True
        
        # For vSprint employees/admins, check if account is shared with vSprint
        if user.role in [models.UserRole.vsprint_employee, models.UserRole.admin]:
            shared_account = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == account_id,
                models.UserMarketplaceAccount.shared_with_vsprint == True
            ).join(models.User).filter(
                models.User.role.in_([models.UserRole.vsprint_employee, models.UserRole.admin])
            ).first()
            
            return shared_account is not None
        
        return False
    
    @staticmethod
    def share_with_vsprint(db: Session, user_id: int, account_id: int) -> bool:
        """Allow vsprint employees to share their accounts with team"""
        relation = AccountRepository.get_user_account_relationship(db, user_id, account_id)
        
        if relation:
            relation.shared_with_vsprint = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_logo(db: Session, account_id: int) -> Optional[models.AccountImage]:
        """Get the logo image for an account"""
        return db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id,
            models.AccountImage.is_logo == True
        ).first()
