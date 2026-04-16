"""System Config Repository - Handles system configuration operations."""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime
from app.db import models


class SystemConfigRepository:
    """Repository for system configuration operations"""
    
    @staticmethod
    def get(db: Session, config_key: str) -> Optional[models.SystemConfig]:
        return db.query(models.SystemConfig).filter(
            models.SystemConfig.config_key == config_key
        ).first()
    
    @staticmethod
    def update(db: Session, config_key: str, config_value: str, user_id: int, description: Optional[str] = None) -> models.SystemConfig:
        config = SystemConfigRepository.get(db, config_key)
        
        if config:
            config.config_value = config_value
            config.updated_by_user_id = user_id
            config.updated_at = datetime.utcnow()
            if description is not None:
                config.description = description
        else:
            config = models.SystemConfig(
                config_key=config_key,
                config_value=config_value,
                updated_by_user_id=user_id,
                description=description
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def get_ai_configs_by_prefix(db: Session, prefix: str) -> List[models.SystemConfig]:
        return db.query(models.SystemConfig).filter(
            models.SystemConfig.config_key.like(f"{prefix}%")
        ).all()
    
    @staticmethod
    def get_all_ai_configs(db: Session) -> Dict[str, str]:
        configs = db.query(models.SystemConfig).filter(
            models.SystemConfig.config_key.like("ai.%")
        ).all()
        
        return {config.config_key: config.config_value for config in configs}
    
    @staticmethod
    def upsert_ai_config(
        db: Session, 
        module: str, 
        marketplace: str, 
        provider: str, 
        param: str, 
        value: str, 
        user_id: int
    ) -> models.SystemConfig:
        """Upsert AI config for specific marketplace/provider/param"""
        config_key = f"ai.{module}.{marketplace}.{provider}.{param}"
        return SystemConfigRepository.update(db, config_key, value, user_id)
