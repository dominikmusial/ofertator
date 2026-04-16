"""Template Repository - Handles template-related database operations."""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db import models, schemas


class TemplateRepository:
    """Repository for template-related operations"""
    
    @staticmethod
    def get_by_id(db: Session, template_id: int) -> Optional[models.Template]:
        return db.query(models.Template).filter(models.Template.id == template_id).first()
    
    @staticmethod
    def get_by_name_and_account(db: Session, template_name: str, account_id: int) -> Optional[models.Template]:
        return db.query(models.Template).filter(
            models.Template.name == template_name,
            models.Template.account_id == account_id
        ).first()
    
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> List[models.Template]:
        """Get templates owned by specific user"""
        return db.query(models.Template).filter(models.Template.owner_id == user_id).all()
    
    @staticmethod
    def get_by_account_id(db: Session, account_id: int) -> List[models.Template]:
        """Get templates for specific account"""
        return db.query(models.Template).filter(models.Template.account_id == account_id).all()
    
    @staticmethod
    def get_shared_vsprint_templates(db: Session) -> List[models.Template]:
        """Get all templates created by vsprint employees"""
        vsprint_users = db.query(models.User).filter(models.User.role == models.UserRole.vsprint_employee).all()
        vsprint_user_ids = [user.id for user in vsprint_users]
        
        if not vsprint_user_ids:
            return []
            
        return db.query(models.Template).filter(models.Template.owner_id.in_(vsprint_user_ids)).all()
    
    @staticmethod
    def get_user_accessible_templates(db: Session, user: models.User, account_id: int) -> List[models.Template]:
        """Get all templates accessible to user for specific account"""
        if not account_id:
            raise ValueError("account_id is required")
        
        # Check if user has direct access to this account
        user_account = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == user.id,
            models.UserMarketplaceAccount.account_id == account_id
        ).first()
        
        # For vSprint employees/admins, also check if account is shared with vSprint
        if user.role in [models.UserRole.vsprint_employee, models.UserRole.admin]:
            shared_account = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == account_id,
                models.UserMarketplaceAccount.shared_with_vsprint == True
            ).join(models.User).filter(
                models.User.role.in_([models.UserRole.vsprint_employee, models.UserRole.admin])
            ).first()
            
            if user_account or shared_account:
                return db.query(models.Template).filter(models.Template.account_id == account_id).all()
            else:
                return []
        else:
            if not user_account:
                return []
            
            if user_account.shared_with_vsprint:
                return db.query(models.Template).filter(models.Template.account_id == account_id).all()
            else:
                return db.query(models.Template).filter(
                    models.Template.account_id == account_id,
                    models.Template.owner_id == user.id
                ).all()
    
    @staticmethod
    def can_user_edit_template(db: Session, user: models.User, template: models.Template) -> bool:
        """Check if user can edit/delete a template"""
        if template.owner_id != user.id:
            return False
        
        if not template.account_id:
            return False
        
        user_account = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == user.id,
            models.UserMarketplaceAccount.account_id == template.account_id
        ).first()
        
        if user.role in [models.UserRole.vsprint_employee, models.UserRole.admin]:
            shared_account = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == template.account_id,
                models.UserMarketplaceAccount.shared_with_vsprint == True
            ).join(models.User).filter(
                models.User.role.in_([models.UserRole.vsprint_employee, models.UserRole.admin])
            ).first()
            
            return user_account is not None or shared_account is not None
        else:
            return user_account is not None
    
    @staticmethod
    def can_user_view_template(db: Session, user: models.User, template: models.Template) -> bool:
        """Check if user can view a template"""
        if not template.account_id:
            return False
        
        user_account = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == user.id,
            models.UserMarketplaceAccount.account_id == template.account_id
        ).first()
        
        if user.role in [models.UserRole.vsprint_employee, models.UserRole.admin]:
            shared_account = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.account_id == template.account_id,
                models.UserMarketplaceAccount.shared_with_vsprint == True
            ).join(models.User).filter(
                models.User.role.in_([models.UserRole.vsprint_employee, models.UserRole.admin])
            ).first()
            
            if user_account or shared_account:
                return True
            else:
                return False
        else:
            if not user_account:
                return False
            
            if user_account.shared_with_vsprint:
                return True
            else:
                return template.owner_id == user.id
    
    @staticmethod
    def create(db: Session, template: schemas.TemplateCreate, owner_id: int, account_id: int) -> models.Template:
        """Create a new template"""
        if not account_id:
            raise ValueError("account_id is required when creating templates")
        
        existing_template = TemplateRepository.get_by_name_and_account(db, template.name, account_id)
        if existing_template:
            raise ValueError(f"Template with name '{template.name}' already exists for this account")
        
        template_data = template.model_dump()
        template_data['owner_id'] = owner_id
        template_data['account_id'] = account_id
        
        db_template = models.Template(**template_data)
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    
    @staticmethod
    def update(db: Session, template_id: int, template_data: schemas.TemplateUpdate) -> Optional[models.Template]:
        db_template = TemplateRepository.get_by_id(db, template_id)
        if db_template:
            update_data = template_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_template, key, value)
            db.commit()
            db.refresh(db_template)
        return db_template
    
    @staticmethod
    def delete(db: Session, template_id: int) -> Optional[models.Template]:
        db_template = TemplateRepository.get_by_id(db, template_id)
        if db_template:
            db.delete(db_template)
            db.commit()
        return db_template
