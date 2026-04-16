"""External Integration Repository - Handles external system integrations (asystenciai, etc.)"""
from sqlalchemy.orm import Session
from typing import Optional
from app.db import models, schemas
from app.core.security import get_password_hash


class ExternalIntegrationRepository:
    """Repository for external system integrations"""
    
    @staticmethod
    def get_user_by_external_id(db: Session, external_user_id: str) -> Optional[models.User]:
        """Get user by external user ID from asystenciai"""
        return db.query(models.User).filter(
            models.User.external_user_id == external_user_id,
            models.User.registration_source == models.RegistrationSource.asystenciai
        ).first()
    
    @staticmethod
    def create_asystencjai_user(db: Session, user_data: schemas.SetupTokenData, password: str) -> models.User:
        """Create a new user from asystencjai integration"""
        hashed_password = get_password_hash(password)
        
        db_user = models.User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=hashed_password,
            is_active=True,
            is_verified=True,  # Auto-verify for asystencjai users
            admin_approved=True,  # Auto-approve for asystencjai users
            role=models.UserRole.user,
            registration_source=models.RegistrationSource.asystenciai,
            external_user_id=str(user_data.asystenciai_user_id)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def grant_asystencjai_permissions(db: Session, user_id: int) -> bool:
        """Grant default asystencjai module permissions"""
        from app.db.repositories import PermissionRepository
        
        # Define asystenciai-specific modules
        asystencjai_modules = [
            "konta_marketplace",      # Access to marketplace accounts
            "wystawianie_ofert",       # Offer creation
            "allegro_harmonogram_cen", # Price scheduler
        ]
        
        try:
            for module_name in asystencjai_modules:
                # Use system admin ID (1) for automated grants
                PermissionRepository.grant_permission(db, user_id, module_name, granted_by_admin_id=1)
            
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def check_asystencjai_user_exists(db: Session, external_user_id: str, email: str) -> Optional[models.User]:
        """Check if asystencjai user exists by external ID or email"""
        # First try by external_user_id
        user = ExternalIntegrationRepository.get_user_by_external_id(db, external_user_id)
        if user:
            return user
        
        # Then try by email
        from app.db.repositories import UserRepository
        user = UserRepository.get_by_email(db, email)
        if user and user.registration_source == models.RegistrationSource.asystenciai:
            return user
        
        return None
    
    @staticmethod
    def update_external_id(db: Session, user_id: int, external_user_id: str) -> bool:
        """Update user's external_user_id (for linking existing account)"""
        try:
            from app.db.repositories import UserRepository
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
