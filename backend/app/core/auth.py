from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.repositories import UserRepository, PermissionRepository
from app.core.security import verify_token
from app.db.models import User

security = HTTPBearer()

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided and valid, otherwise return None"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    user = UserRepository.get_by_id(db, int(user_id))
    return user

def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Get current user - raises 401 if not authenticated"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieuwierzytelniony",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user - raises 400 if user is inactive"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Konto jest nieaktywne")
    return current_user

def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user - raises 400 if user is not verified"""
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email nie został zweryfikowany")
    return current_user

def require_admin(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """Require admin role"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wymagany dostęp administratora"
        )
    return current_user

def require_vsprint_or_admin(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """Require vsprint employee or admin role"""
    if current_user.role.value not in ["admin", "vsprint_employee"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wymagany dostęp pracownika Vsprint lub administratora"
        )
    return current_user

def require_module_permission(module_name: str):
    """Dependency factory for requiring module permission"""
    def check_permission(
        current_user: User = Depends(get_current_verified_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has permission for the specified module"""
        if not PermissionRepository.user_has_permission(db, current_user.id, module_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Brak dostępu do modułu: {module_name}"
            )
        return current_user
    return check_permission 