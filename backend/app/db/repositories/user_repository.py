"""User Repository - Handles all user-related database operations."""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from app.db import models, schemas
from app.core.security import get_password_hash, verify_password, generate_verification_token, generate_reset_token


class UserRepository:
    """Repository for user-related database operations"""
    
    # ============ Basic User CRUD ============
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[models.User]:
        """Get user by ID"""
        return db.query(models.User).filter(models.User.id == user_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get user by email"""
        return db.query(models.User).filter(models.User.email == email).first()
    
    @staticmethod
    def get_by_google_id(db: Session, google_id: str) -> Optional[models.User]:
        """Get user by Google ID (SSO)"""
        return db.query(models.User).filter(models.User.google_id == google_id).first()
    
    @staticmethod
    def get_by_external_id(db: Session, external_user_id: str) -> Optional[models.User]:
        """Get user by external user ID from asystenciai"""
        return db.query(models.User).filter(
            models.User.external_user_id == external_user_id,
            models.User.registration_source == models.RegistrationSource.asystenciai
        ).first()
    
    @staticmethod
    def create(db: Session, user: schemas.UserCreate) -> models.User:
        """Create new user"""
        password_hash = get_password_hash(user.password) if user.password else None
        db_user = models.User(
            email=user.email,
            password_hash=password_hash,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role if hasattr(user, 'role') else models.UserRole.user
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def create_sso(db: Session, user: schemas.UserCreateSSO) -> models.User:
        """Create user via SSO"""
        db_user = models.User(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            google_id=user.google_id,
            role=user.role,
            is_verified=True,
            admin_approved=True,  # Auto-approve vsprint users
            company_domain='vsprint.pl'
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def create_asystenciai_user(db: Session, user_data: schemas.SetupTokenData, password: str) -> models.User:
        """Create a new user from asystenciai integration"""
        hashed_password = get_password_hash(password)
        
        db_user = models.User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=hashed_password,
            is_active=True,
            is_verified=True,  # Auto-verify for asystenciai users
            admin_approved=True,  # Auto-approve for asystenciai users
            role=models.UserRole.user,
            registration_source=models.RegistrationSource.asystenciai,
            external_user_id=str(user_data.asystenciai_user_id)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> bool:
        """Update user password"""
        db_user = UserRepository.get_by_id(db, user_id)
        if db_user:
            db_user.password_hash = get_password_hash(new_password)
            db.commit()
            return True
        return False
    
    @staticmethod
    def verify_email(db: Session, user_id: int) -> bool:
        """Mark user email as verified"""
        db_user = UserRepository.get_by_id(db, user_id)
        if db_user:
            db_user.is_verified = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_external_id(db: Session, user_id: int, external_user_id: str) -> bool:
        """Update user's external_user_id (for linking existing account)"""
        try:
            user = UserRepository.get_by_id(db, user_id)
            if not user:
                return False
            
            user.external_user_id = external_user_id
            user.registration_source = models.RegistrationSource.asystenciai
            
            db.commit()
            return True
            
        except Exception:
            db.rollback()
            return False
    
    # ============ Authentication ============
    
    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[models.User]:
        """Authenticate user with email and password"""
        user = UserRepository.get_by_email(db, email)
        if not user:
            return None
        if not user.password_hash:
            return None  # SSO user
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    # ============ Email Verification ============
    
    @staticmethod
    def create_email_verification(db: Session, user_id: int) -> models.EmailVerification:
        """Create email verification token"""
        token = generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Invalidate any existing email verification tokens for this user
        db.query(models.EmailVerification).filter(
            models.EmailVerification.user_id == user_id,
            models.EmailVerification.is_used == False
        ).update({"is_used": True})
        
        db_verification = models.EmailVerification(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(db_verification)
        db.commit()
        db.refresh(db_verification)
        return db_verification
    
    @staticmethod
    def get_valid_email_verification(db: Session, token: str) -> Optional[models.EmailVerification]:
        """Get valid (not expired, not used) email verification"""
        return db.query(models.EmailVerification).filter(
            models.EmailVerification.token == token,
            models.EmailVerification.expires_at > datetime.utcnow(),
            models.EmailVerification.is_used == False
        ).first()
    
    @staticmethod
    def mark_email_verification_used(db: Session, verification_id: int):
        """Mark email verification as used"""
        verification = db.query(models.EmailVerification).filter(
            models.EmailVerification.id == verification_id
        ).first()
        if verification:
            verification.is_used = True
            db.commit()
    
    # ============ Password Reset ============
    
    @staticmethod
    def create_password_reset(db: Session, user_id: int) -> models.PasswordReset:
        """Create password reset token"""
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Invalidate any existing password reset tokens for this user
        db.query(models.PasswordReset).filter(
            models.PasswordReset.user_id == user_id,
            models.PasswordReset.is_used == False
        ).update({"is_used": True})
        
        db_reset = models.PasswordReset(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(db_reset)
        db.commit()
        db.refresh(db_reset)
        return db_reset
    
    @staticmethod
    def get_valid_password_reset(db: Session, token: str) -> Optional[models.PasswordReset]:
        """Get valid (not expired, not used) password reset"""
        return db.query(models.PasswordReset).filter(
            models.PasswordReset.token == token,
            models.PasswordReset.expires_at > datetime.utcnow(),
            models.PasswordReset.is_used == False
        ).first()
    
    @staticmethod
    def mark_password_reset_used(db: Session, reset_id: int):
        """Mark password reset as used"""
        reset = db.query(models.PasswordReset).filter(
            models.PasswordReset.id == reset_id
        ).first()
        if reset:
            reset.is_used = True
            db.commit()
    
    # ============ Admin Operations ============
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list:
        """Get all users with pagination"""
        return db.query(models.User).offset(skip).limit(limit).all()
    
    @staticmethod
    def search(
        db: Session, 
        query: str = None, 
        role_filter: str = None, 
        approval_filter: str = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> list:
        """Search users with filters"""
        from sqlalchemy import or_
        
        filters = []
        
        # Text search in email, first_name, last_name
        if query:
            search_filter = or_(
                models.User.email.ilike(f"%{query}%"),
                models.User.first_name.ilike(f"%{query}%"),
                models.User.last_name.ilike(f"%{query}%")
            )
            filters.append(search_filter)
        
        # Role filter
        if role_filter and role_filter != "all":
            filters.append(models.User.role == models.UserRole(role_filter))
        
        # Approval status filter
        if approval_filter == "pending":
            filters.append(models.User.admin_approved == False)
            filters.append(models.User.is_active == True)
        elif approval_filter == "approved":
            filters.append(models.User.admin_approved == True)
        elif approval_filter == "inactive":
            filters.append(models.User.is_active == False)
        
        query_obj = db.query(models.User)
        if filters:
            query_obj = query_obj.filter(*filters)
        
        return query_obj.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_pending_approval(db: Session) -> list:
        """Get users awaiting admin approval"""
        return db.query(models.User).filter(
            models.User.admin_approved == False,
            models.User.is_verified == True,
            models.User.is_active == True,
            models.User.role == models.UserRole.user  # Only regular users need approval
        ).all()
    
    @staticmethod
    def approve(db: Session, user_id: int) -> bool:
        """Approve a user"""
        user = UserRepository.get_by_id(db, user_id)
        if user:
            user.admin_approved = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def reject(db: Session, user_id: int) -> bool:
        """Reject a user (deactivate)"""
        user = UserRepository.get_by_id(db, user_id)
        if user:
            user.is_active = False
            user.admin_approved = False
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_for_admin(db: Session, user_id: int):
        """Get user with full details for admin view"""
        return UserRepository.get_by_id(db, user_id)
    
    @staticmethod
    def delete_with_data(db: Session, user_id: int) -> bool:
        """Delete user and all associated data"""
        try:
            user = UserRepository.get_by_id(db, user_id)
            if not user:
                return False
            
            # Delete email verifications
            db.query(models.EmailVerification).filter(
                models.EmailVerification.user_id == user_id
            ).delete(synchronize_session=False)
            
            # Delete password resets
            db.query(models.PasswordReset).filter(
                models.PasswordReset.user_id == user_id
            ).delete(synchronize_session=False)
            
            # Delete AI config
            db.query(models.UserAIConfig).filter(
                models.UserAIConfig.user_id == user_id
            ).delete(synchronize_session=False)
            
            # Delete module permissions
            db.query(models.UserModulePermission).filter(
                models.UserModulePermission.user_id == user_id
            ).delete(synchronize_session=False)
            
            # Delete user-account relationships
            user_account_rels = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.user_id == user_id
            ).all()
            
            for rel in user_account_rels:
                db.delete(rel)
                
                # If this was the only user for the account, delete the account
                remaining = db.query(models.UserMarketplaceAccount).filter(
                    models.UserMarketplaceAccount.account_id == rel.account_id
                ).count()
                
                if remaining == 0:
                    account = db.query(models.Account).filter(
                        models.Account.id == rel.account_id
                    ).first()
                    if account:
                        # Delete account-related data
                        db.query(models.Template).filter(
                            models.Template.account_id == rel.account_id
                        ).delete(synchronize_session=False)
                        db.query(models.OfferBackup).filter(
                            models.OfferBackup.account_id == rel.account_id
                        ).delete(synchronize_session=False)
                        db.query(models.AccountImage).filter(
                            models.AccountImage.account_id == rel.account_id
                        ).delete(synchronize_session=False)
                        db.query(models.AITokenUsage).filter(
                            models.AITokenUsage.account_id == rel.account_id
                        ).delete(synchronize_session=False)
                        db.query(models.UserActivityLog).filter(
                            models.UserActivityLog.account_id == rel.account_id
                        ).delete(synchronize_session=False)
                        db.delete(account)
            
            # Delete templates owned by user
            db.query(models.Template).filter(
                models.Template.owner_id == user_id
            ).delete(synchronize_session=False)
            
            # Delete user sessions
            db.query(models.UserSession).filter(
                models.UserSession.user_id == user_id
            ).delete(synchronize_session=False)
            
            # Finally delete the user
            db.delete(user)
            db.commit()
            return True
            
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def delete_sessions(db: Session, user_id: int) -> bool:
        """Delete all user sessions"""
        try:
            db.query(models.UserSession).filter(
                models.UserSession.user_id == user_id
            ).delete(synchronize_session=False)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def create_default_admin(db: Session, email: str, password: str):
        """Create default admin if it doesn't exist"""
        existing_admin = UserRepository.get_by_email(db, email)
        if existing_admin:
            return existing_admin
        
        hashed_password = get_password_hash(password)
        admin = models.User(
            email=email,
            password_hash=hashed_password,
            first_name="Admin",
            last_name="User",
            role=models.UserRole.admin,
            is_verified=True,
            is_active=True,
            admin_approved=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
