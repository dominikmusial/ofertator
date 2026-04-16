from datetime import datetime, timedelta
from typing import Any, Union, Optional
import secrets
import string

from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, exists

from app.core.config import settings
from app.db.models import User, Account, UserMarketplaceAccount, UserRole

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password using bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_verification_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def generate_reset_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def get_user_accounts_query(db: Session, user: User):
    """Secure account access with vsprint sharing logic"""
    base_query = db.query(Account).join(UserMarketplaceAccount)
    
    if user.role == UserRole.vsprint_employee or user.role == UserRole.admin:
        # Vsprint employee or admin sees their accounts + shared by other vsprint employees or admins
        return base_query.filter(
            or_(
                UserMarketplaceAccount.user_id == user.id,
                and_(
                    UserMarketplaceAccount.shared_with_vsprint == True,
                    exists().where(
                        and_(
                            User.id == UserMarketplaceAccount.user_id,
                            or_(
                                User.role == UserRole.vsprint_employee,
                                User.role == UserRole.admin
                            )
                        )
                    )
                )
            )
        )
    else:
        # Regular user sees only their accounts
        return base_query.filter(UserMarketplaceAccount.user_id == user.id)

def verify_account_access(db: Session, user: User, account_id: int) -> bool:
    """Verify access to specific account"""
    allowed_accounts = get_user_accounts_query(db, user).filter(Account.id == account_id)
    return allowed_accounts.first() is not None

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None 