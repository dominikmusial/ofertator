"""Admin Repository - Handles admin operations."""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Tuple
from app.db import models


class AdminRepository:
    """Repository for admin operations"""
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
        return db.query(models.User).offset(skip).limit(limit).all()
    
    @staticmethod
    def search_users(db: Session, page: int = 1, per_page: int = 25, search: str = None, role_filter: str = None, status_filter: str = None) -> Tuple[List[models.User], int]:
        from sqlalchemy import func
        query = db.query(models.User)
        
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(models.User.first_name).like(search_term),
                    func.lower(models.User.last_name).like(search_term),
                    func.lower(models.User.email).like(search_term)
                )
            )
        
        if role_filter and role_filter in ["user", "admin", "vsprint_employee"]:
            query = query.filter(models.User.role == getattr(models.UserRole, role_filter))
        
        if status_filter:
            if status_filter == "active":
                query = query.filter(models.User.is_active == True)
            elif status_filter == "inactive":
                query = query.filter(models.User.is_active == False)
            elif status_filter == "verified":
                query = query.filter(models.User.is_verified == True)
            elif status_filter == "unverified":
                query = query.filter(models.User.is_verified == False)
            elif status_filter == "approved":
                query = query.filter(models.User.admin_approved == True)
            elif status_filter == "unapproved":
                query = query.filter(models.User.admin_approved == False)
        
        total_count = query.count()
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        return users, total_count
    
    @staticmethod
    def get_pending_approval_users(db: Session) -> List[models.User]:
        return db.query(models.User).filter(
            and_(
                models.User.admin_approved == False,
                models.User.role == models.UserRole.user,
                models.User.is_verified == True
            )
        ).all()
    
    @staticmethod
    def approve_user(db: Session, user_id: int) -> bool:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
        
        user.admin_approved = True
        db.commit()
        return True
    
    @staticmethod
    def create_default_admin(db: Session, email: str, password: str) -> models.User:
        from app.db.repositories import UserRepository
        from app.db import schemas
        
        existing_admin = UserRepository.get_by_email(db, email)
        if existing_admin:
            return existing_admin
        
        admin_data = schemas.UserCreate(
            email=email,
            password=password,
            first_name="Admin",
            last_name="System"
        )
        admin_user = UserRepository.create(db, admin_data)
        admin_user.role = models.UserRole.admin
        admin_user.is_verified = True
        db.commit()
        return admin_user
    
    @staticmethod
    def get_notification_emails(db: Session) -> List[models.AdminNotificationEmail]:
        """Get all admin notification emails"""
        return db.query(models.AdminNotificationEmail).all()
    
    @staticmethod
    def create_notification_email(db: Session, email: str, admin_id: int) -> models.AdminNotificationEmail:
        """Create admin notification email"""
        existing = db.query(models.AdminNotificationEmail).filter(
            models.AdminNotificationEmail.email == email
        ).first()
        
        if existing:
            return existing
        
        notification_email = models.AdminNotificationEmail(
            email=email,
            added_by_admin_id=admin_id
        )
        db.add(notification_email)
        db.commit()
        db.refresh(notification_email)
        return notification_email
    
    @staticmethod
    def delete_notification_email(db: Session, email: str) -> bool:
        """Delete admin notification email"""
        notification = db.query(models.AdminNotificationEmail).filter(
            models.AdminNotificationEmail.email == email
        ).first()
        
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_notification_emails(db: Session, emails: List[str], admin_id: int) -> List[models.AdminNotificationEmail]:
        """Update entire list of admin notification emails (replace all)"""
        current_emails = db.query(models.AdminNotificationEmail).all()
        current_email_set = {e.email for e in current_emails}
        new_email_set = set(emails)
        
        # Delete emails no longer in list
        emails_to_delete = current_email_set - new_email_set
        for email in emails_to_delete:
            db.query(models.AdminNotificationEmail).filter(
                models.AdminNotificationEmail.email == email
            ).delete(synchronize_session=False)
        
        # Add new emails
        emails_to_add = new_email_set - current_email_set
        for email in emails_to_add:
            notification_email = models.AdminNotificationEmail(
                email=email,
                added_by_admin_id=admin_id
            )
            db.add(notification_email)
        
        db.commit()
        return db.query(models.AdminNotificationEmail).all()
