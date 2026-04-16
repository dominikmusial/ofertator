"""Backup Repository - Handles offer backup operations."""
from sqlalchemy.orm import Session
from typing import Optional
from app.db import models, schemas


class BackupRepository:
    """Repository for offer backup operations"""
    
    @staticmethod
    def create(db: Session, backup: schemas.OfferBackupCreate) -> models.OfferBackup:
        db_backup = models.OfferBackup(**backup.model_dump())
        db.add(db_backup)
        db.commit()
        db.refresh(db_backup)
        return db_backup
    
    @staticmethod
    def get_latest(db: Session, offer_id: str, account_id: int) -> Optional[models.OfferBackup]:
        return db.query(models.OfferBackup).filter(
            models.OfferBackup.offer_id == offer_id,
            models.OfferBackup.account_id == account_id
        ).order_by(models.OfferBackup.created_at.desc()).first()
