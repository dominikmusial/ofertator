"""Permission Repository - Handles module permission operations."""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Dict
from app.db import models


class PermissionRepository:
    """Repository for module permission operations"""
    
    @staticmethod
    def get_all_modules(db: Session) -> List[models.Module]:
        return db.query(models.Module).order_by(models.Module.display_name).all()
    
    @staticmethod
    def get_restricted_modules(db: Session) -> List[models.Module]:
        return db.query(models.Module).filter(models.Module.is_core == False).order_by(models.Module.display_name).all()
    
    @staticmethod
    def get_module_by_name(db: Session, module_name: str) -> Optional[models.Module]:
        return db.query(models.Module).filter(models.Module.name == module_name).first()
    
    @staticmethod
    def get_module_by_route(db: Session, route_pattern: str) -> Optional[models.Module]:
        return db.query(models.Module).filter(models.Module.route_pattern == route_pattern).first()
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> List[models.UserModulePermission]:
        return db.query(models.UserModulePermission).filter(
            models.UserModulePermission.user_id == user_id
        ).join(models.Module).order_by(models.Module.display_name).all()
    
    @staticmethod
    def user_has_permission(db: Session, user_id: int, module_name: str) -> bool:
        from app.db.repositories import UserRepository
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return False
        
        module = PermissionRepository.get_module_by_name(db, module_name)
        if not module:
            return False
        
        if module.is_core:
            return True
        
        if user.role in [models.UserRole.admin, models.UserRole.vsprint_employee]:
            return True
        
        permission = db.query(models.UserModulePermission).filter(
            and_(
                models.UserModulePermission.user_id == user_id,
                models.UserModulePermission.module_id == module.id,
                models.UserModulePermission.granted == True
            )
        ).first()
        
        return permission is not None
    
    @staticmethod
    def grant_permission(db: Session, user_id: int, module_name: str, granted_by_admin_id: int) -> bool:
        from sqlalchemy import func
        module = PermissionRepository.get_module_by_name(db, module_name)
        if not module:
            return False
        
        existing = db.query(models.UserModulePermission).filter(
            and_(
                models.UserModulePermission.user_id == user_id,
                models.UserModulePermission.module_id == module.id
            )
        ).first()
        
        if existing:
            existing.granted = True
            existing.granted_at = func.now()
            existing.granted_by_admin_id = granted_by_admin_id
        else:
            permission = models.UserModulePermission(
                user_id=user_id,
                module_id=module.id,
                granted=True,
                granted_by_admin_id=granted_by_admin_id
            )
            db.add(permission)
        
        db.commit()
        return True
    
    @staticmethod
    def revoke_permission(db: Session, user_id: int, module_name: str, revoked_by_admin_id: int) -> bool:
        from sqlalchemy import func
        module = PermissionRepository.get_module_by_name(db, module_name)
        if not module or module.is_core:
            return False
        
        permission = db.query(models.UserModulePermission).filter(
            and_(
                models.UserModulePermission.user_id == user_id,
                models.UserModulePermission.module_id == module.id
            )
        ).first()
        
        if permission:
            permission.granted = False
            permission.granted_at = func.now()
            permission.granted_by_admin_id = revoked_by_admin_id
        
        db.commit()
        return True
    
    @staticmethod
    def user_has_permission_by_route(db: Session, user_id: int, route_pattern: str) -> bool:
        """Check if user has permission by route pattern"""
        from app.db.repositories import UserRepository
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return False
        
        module = PermissionRepository.get_module_by_route(db, route_pattern)
        if not module:
            return True  # No module associated, allow access
        
        if module.is_core:
            return True
        
        if user.role in [models.UserRole.admin, models.UserRole.vsprint_employee]:
            return True
        
        permission = db.query(models.UserModulePermission).filter(
            and_(
                models.UserModulePermission.user_id == user_id,
                models.UserModulePermission.module_id == module.id,
                models.UserModulePermission.granted == True
            )
        ).first()
        
        return permission is not None
    
    @staticmethod
    def bulk_update_permissions(db: Session, user_id: int, module_permissions: Dict[str, bool], admin_id: int) -> bool:
        """Bulk update user permissions"""
        from sqlalchemy import func
        
        for module_name, granted in module_permissions.items():
            module = PermissionRepository.get_module_by_name(db, module_name)
            if not module or module.is_core:
                continue
            
            if granted:
                PermissionRepository.grant_permission(db, user_id, module_name, admin_id)
            else:
                PermissionRepository.revoke_permission(db, user_id, module_name, admin_id)
        
        return True
    
    @staticmethod
    def get_permissions_dict(db: Session, user_id: int) -> Dict[str, bool]:
        """Get user permissions as dict"""
        permissions = PermissionRepository.get_user_permissions(db, user_id)
        return {
            perm.module.name: perm.granted
            for perm in permissions
        }
    
    @staticmethod
    def get_module_dependencies(db: Session, module_name: str) -> List[str]:
        """Get module dependencies (modules that this module depends on)"""
        module = PermissionRepository.get_module_by_name(db, module_name)
        if not module:
            return []
        
        # Get dependencies where this module is the parent (i.e., this module depends on others)
        dependencies = db.query(models.ModuleDependency).filter(
            models.ModuleDependency.parent_module_id == module.id
        ).all()
        
        return [
            dep.dependent_module.name
            for dep in dependencies
        ]
    
    @staticmethod
    def get_all_dependencies(db: Session) -> Dict[str, List[str]]:
        """Get all module dependencies"""
        modules = PermissionRepository.get_all_modules(db)
        return {
            module.name: PermissionRepository.get_module_dependencies(db, module.name)
            for module in modules
        }
    
    @staticmethod
    def validate_dependencies(db: Session, user_id: int, module_permissions: Dict[str, bool]) -> List[str]:
        """Validate permission dependencies - returns list of errors"""
        errors = []
        
        for module_name, granted in module_permissions.items():
            if not granted:
                continue
            
            dependencies = PermissionRepository.get_module_dependencies(db, module_name)
            for dep_name in dependencies:
                # Check if dependency is granted
                dep_granted = module_permissions.get(dep_name, False)
                
                if not dep_granted:
                    # Check if user already has the dependency
                    has_dep = PermissionRepository.user_has_permission(db, user_id, dep_name)
                    if not has_dep:
                        errors.append(
                            f"Module '{module_name}' requires '{dep_name}' to be enabled"
                        )
        
        return errors
