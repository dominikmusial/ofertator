from sqlalchemy.orm import Session
from app.db import models
from app.db.repositories import UserRepository, AdminRepository
from app.services.email_service import email_service
from app.services.analytics_archive_service import AnalyticsArchiveService
from datetime import datetime
from typing import Dict, Optional, List


class UserManagementService:
    
    @staticmethod
    def get_user_management_info(db: Session, user_id: int) -> Dict:
        """Get comprehensive user info for management operations"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Count user's data
        accounts_count = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == user_id,
            models.UserMarketplaceAccount.is_owner == True
        ).count()
        
        templates_count = db.query(models.Template).filter(
            models.Template.owner_id == user_id
        ).count()
        
        # Count images associated with user's accounts
        user_account_ids = db.query(models.UserMarketplaceAccount.account_id).filter(
            models.UserMarketplaceAccount.user_id == user_id
        ).subquery()
        
        images_count = db.query(models.AccountImage).filter(
            models.AccountImage.account_id.in_(user_account_ids)
        ).count()
        
        # Determine if user can be deleted and if they're vsprint
        is_vsprint = user.role.value in ["vsprint_employee", "admin"]
        can_delete = user.role.value != "admin"  # Cannot delete admin users
        can_deactivate = user.role.value != "admin"  # Cannot deactivate admin users
        
        return {
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_deactivated": user.deactivated_at is not None,
            "deactivated_at": user.deactivated_at.isoformat() if user.deactivated_at else None,
            "deactivation_reason": user.deactivation_reason,
            "data_counts": {
                "accounts": accounts_count,
                "templates": templates_count,
                "images": images_count
            },
            "can_delete": can_delete,
            "can_deactivate": can_deactivate,
            "is_vsprint": is_vsprint
        }
    
    @staticmethod
    async def deactivate_user(db: Session, user_id: int, admin_id: int, reason: Optional[str] = None) -> Dict:
        """Deactivate a user account (reversible)"""
        user = UserRepository.get_by_id(db, user_id)
        admin = UserRepository.get_by_id(db, admin_id)
        if not user or not admin:
            raise ValueError("User or admin not found")
        
        if not user.is_active:
            raise ValueError("User is already deactivated")
        
        # Prevent deactivation of admin users
        if user.role == models.UserRole.admin:
            raise ValueError("Cannot deactivate administrator users")
        
        # Update user status
        user.is_active = False
        user.deactivated_at = datetime.now()
        user.deactivated_by_admin_id = admin_id
        user.deactivation_reason = reason
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # TODO: Invalidate user sessions (if you have session management)
        # UserRepository.delete_sessions(db, user_id)
        
        # Send notification emails
        try:
            # Email to the user
            await email_service.send_user_deactivation_email(
                user.email,
                user.first_name,
                reason=reason or "",
                admin_email=admin.email
            )
            
            # Email to all admin notification addresses
            admin_emails = AdminRepository.get_notification_emails(db)
            for admin_email in admin_emails:
                await email_service.send_admin_user_deactivated_email(
                    admin_email.email,
                    user.first_name,
                    user.last_name,
                    user.email,
                    reason or "Brak podanego powodu",
                    admin.email
                )
        except Exception as e:
            print(f"Failed to send deactivation emails: {str(e)}")
            # Don't fail the operation if email fails
        
        return {
            "success": True,
            "message": f"Użytkownik {user.email} został dezaktywowany",
            "user_email": user.email,
            "deactivated_at": user.deactivated_at.isoformat()
        }
    
    @staticmethod
    async def reactivate_user(db: Session, user_id: int, admin_id: int) -> Dict:
        """Reactivate a deactivated user account"""
        user = UserRepository.get_by_id(db, user_id)
        admin = UserRepository.get_by_id(db, admin_id)
        if not user or not admin:
            raise ValueError("User or admin not found")
        
        if user.is_active:
            raise ValueError("User is already active")
        
        # Update user status
        user.is_active = True
        user.deactivated_at = None
        user.deactivated_by_admin_id = None
        user.deactivation_reason = None
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send notification emails
        try:
            # Email to the user
            await email_service.send_user_reactivation_email(
                user.email,
                user.first_name,
                admin_email=admin.email
            )
            
            # Email to all admin notification addresses
            admin_emails = AdminRepository.get_notification_emails(db)
            for admin_email in admin_emails:
                await email_service.send_admin_user_reactivated_email(
                    admin_email.email,
                    user.first_name,
                    user.last_name,
                    user.email,
                    admin.email
                )
        except Exception as e:
            print(f"Failed to send reactivation emails: {str(e)}")
            # Don't fail the operation if email fails
        
        return {
            "success": True,
            "message": f"Użytkownik {user.email} został przywrócony",
            "user_email": user.email,
            "reactivated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    async def delete_external_user(db: Session, user_id: int, admin_id: int, reason: Optional[str] = None) -> Dict:
        """Delete an external user account (permanent)"""
        user = UserRepository.get_by_id(db, user_id)
        admin = UserRepository.get_by_id(db, admin_id)
        if not user or not admin:
            raise ValueError("User or admin not found")
        
        # Prevent deletion of admin users
        if user.role == models.UserRole.admin:
            raise ValueError("Cannot delete administrator users")
        
        user_display_name = f"{user.first_name} {user.last_name} ({user.email})"
        user_email = user.email
        
        # Archive analytics data before deleting the user
        AnalyticsArchiveService.archive_user_analytics(db, user_id, admin_id, user_display_name)
        
        # Use existing crud function for deletion
        success = UserRepository.delete_with_data(db, user_id)
        if not success:
            raise ValueError("Failed to delete user")
        
        # Send notification emails
        try:
            # Email to the user (before deletion)
            await email_service.send_user_deletion_email(
                user_email,
                user.first_name,
                reason=reason or "",
                admin_email=admin.email
            )
            
            # Email to all admin notification addresses
            admin_emails = AdminRepository.get_notification_emails(db)
            for admin_email in admin_emails:
                await email_service.send_admin_user_deleted_email(
                    admin_email.email,
                    user.first_name,
                    user.last_name,
                    user_email,
                    "Użytkownik zewnętrzny",
                    reason or "Brak podanego powodu",
                    admin.email
                )
        except Exception as e:
            print(f"Failed to send deletion emails: {str(e)}")
            # Don't fail the operation if email fails
        
        return {
            "success": True,
            "message": f"Użytkownik {user_email} został usunięty",
            "user_email": user_email,
            "user_type": "external",
            "deleted_at": datetime.now().isoformat()
        }
    
    @staticmethod
    async def delete_vsprint_user(
        db: Session, 
        user_id: int, 
        admin_id: int, 
        keep_accounts: bool, 
        keep_templates: bool, 
        keep_images: bool, 
        reason: Optional[str] = None
    ) -> Dict:
        """Delete a vsprint user account with selective data transfer"""
        user = UserRepository.get_by_id(db, user_id)
        admin = UserRepository.get_by_id(db, admin_id)
        if not user or not admin:
            raise ValueError("User or admin not found")
        
        # Prevent deletion of admin users
        if user.role == models.UserRole.admin:
            raise ValueError("Cannot delete administrator users")
        
        user_display_name = f"{user.first_name} {user.last_name} ({user.email})"
        user_email = user.email
        
        # Archive analytics data before deleting the user
        AnalyticsArchiveService.archive_user_analytics(db, user_id, admin_id, user_display_name)
        
        # Transfer data to admin
        transferred_data = UserManagementService._transfer_user_data_to_admin(
            db, user_id, admin_id, keep_accounts, keep_templates, keep_images
        )
        
        # Delete the user
        db.delete(user)
        db.commit()
        
        # Send notification emails
        try:
            # Email to the user
            await email_service.send_user_deletion_email(
                user_email,
                user.first_name,
                reason=reason or "",
                admin_email=admin.email
            )
            
            # Email to all admin notification addresses
            admin_emails = AdminRepository.get_notification_emails(db)
            for admin_email in admin_emails:
                await email_service.send_admin_user_deleted_email(
                    admin_email.email,
                    user.first_name,
                    user.last_name,
                    user_email,
                    "Pracownik vsprint",
                    reason or "Brak podanego powodu",
                    admin.email,
                    transferred_data=transferred_data
                )
        except Exception as e:
            print(f"Failed to send deletion emails: {str(e)}")
            # Don't fail the operation if email fails
        
        return {
            "success": True,
            "message": f"Użytkownik {user_email} został usunięty",
            "user_email": user_email,
            "user_type": "vsprint",
            "transferred_data": transferred_data,
            "deleted_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def _transfer_user_data_to_admin(
        db: Session, user_id: int, admin_id: int, keep_accounts: bool, keep_templates: bool, keep_images: bool
    ) -> Dict[str, int]:
        """Transfer user data to admin"""
        transferred = {"accounts": 0, "templates": 0, "images": 0}
        
        # Transfer Marketplace Accounts
        if keep_accounts:
            user_marketplace_accounts = db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.user_id == user_id,
                models.UserMarketplaceAccount.is_owner == True  # Only transfer owned accounts
            ).all()
            
            for user_acc_rel in user_marketplace_accounts:
                # Reassign ownership to admin
                user_acc_rel.user_id = admin_id
                db.add(user_acc_rel)
                transferred["accounts"] += 1
        
        # Transfer Templates
        if keep_templates:
            templates = db.query(models.Template).filter(models.Template.owner_id == user_id).all()
            for template in templates:
                template.owner_id = admin_id
                db.add(template)
                transferred["templates"] += 1
        
        # Transfer Images (implicitly handled by account transfer)
        if keep_images and keep_accounts:
            # Count images associated with transferred accounts
            account_ids = [rel.account_id for rel in db.query(models.UserMarketplaceAccount).filter(
                models.UserMarketplaceAccount.user_id == admin_id
            ).all()]
            if account_ids:
                images_count = db.query(models.AccountImage).filter(
                    models.AccountImage.account_id.in_(account_ids)
                ).count()
                transferred["images"] = images_count
        
        db.flush()  # Flush changes before final commit in calling function
        return transferred