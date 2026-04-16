"""AI Config Repository - Handles AI configuration operations."""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db import models
from app.services.encryption_service import encryption_service


class AIConfigRepository:
    """Repository for AI configuration operations"""
    
    @staticmethod
    def get_user_config(db: Session, user_id: int) -> Optional[models.UserAIConfig]:
        return db.query(models.UserAIConfig).filter(models.UserAIConfig.user_id == user_id).first()
    
    @staticmethod
    def create(db: Session, user_id: int, provider: str, model_name: str, api_key: str, is_active: bool = True) -> models.UserAIConfig:
        existing_config = AIConfigRepository.get_user_config(db, user_id)
        if existing_config:
            db.delete(existing_config)
            db.flush()
        
        encrypted_key = encryption_service.encrypt_api_key(api_key)
        
        db_config = models.UserAIConfig(
            user_id=user_id,
            ai_provider=models.AIProvider(provider),
            model_name=model_name,
            encrypted_api_key=encrypted_key,
            is_active=is_active,
            last_validated_at=datetime.utcnow()
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config
    
    @staticmethod
    def update(db: Session, user_id: int, provider: str = None, model_name: str = None, api_key: str = None, is_active: bool = None) -> Optional[models.UserAIConfig]:
        config = AIConfigRepository.get_user_config(db, user_id)
        if not config:
            return None
        
        if provider is not None:
            config.ai_provider = models.AIProvider(provider)
        if model_name is not None:
            config.model_name = model_name
        if api_key is not None:
            config.encrypted_api_key = encryption_service.encrypt_api_key(api_key)
            config.last_validated_at = datetime.utcnow()
        if is_active is not None:
            config.is_active = is_active
        
        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        config = AIConfigRepository.get_user_config(db, user_id)
        if config:
            db.delete(config)
            db.commit()
            return True
        return False
    
    @staticmethod
    def deactivate(db: Session, user_id: int) -> bool:
        """Deactivate user AI config"""
        config = AIConfigRepository.get_user_config(db, user_id)
        if config:
            config.is_active = False
            db.commit()
            return True
        return False
    
    @staticmethod
    def activate(db: Session, user_id: int) -> bool:
        """Activate user AI config"""
        config = AIConfigRepository.get_user_config(db, user_id)
        if config:
            config.is_active = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_validation(db: Session, user_id: int, is_valid: bool) -> bool:
        """Update validation status"""
        config = AIConfigRepository.get_user_config(db, user_id)
        if config:
            config.is_valid = is_valid
            config.last_validated_at = datetime.utcnow()
            db.commit()
            return True
        return False
