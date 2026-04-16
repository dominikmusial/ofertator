"""
Asystenciai Integration utilities for JWT token handling and validation
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from app.core.config import settings
from app.db import schemas


def decode_asystenciai_token(token: str) -> schemas.AsystenciaiUserData:
    """
    Decode and validate JWT token from asystenciai
    
    Args:
        token: JWT token from asystenciai
        
    Returns:
        AsystenciaiUserData with validated user data
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.ASYSTENCIAI_SHARED_SECRET,
            algorithms=["HS256"]
        )
        
        # Validate required fields
        required_fields = [
            'asystenciai_user_id', 'email', 'first_name', 'last_name',
            'email_verified', 'terms_accepted', 'iat', 'exp'
        ]
        
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Token missing required field: {field}"
                )
        
        # Validate expiry
        if payload['exp'] < datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token has expired"
            )
        
        return schemas.AsystenciaiUserData(**payload)
        
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token data: {str(e)}"
        )


def create_setup_token(user_data: schemas.AsystenciaiUserData) -> str:
    """
    Create a setup token for account configuration
    
    Args:
        user_data: Validated user data from asystenciai
        
    Returns:
        JWT token for account setup (valid for 30 minutes)
    """
    now = datetime.utcnow()
    exp = now + timedelta(minutes=settings.ASYSTENCIAI_SETUP_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "asystenciai_user_id": user_data.asystenciai_user_id,
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "email_verified": user_data.email_verified,
        "terms_accepted": user_data.terms_accepted,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "token_type": "asystenciai_setup"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_setup_token(token: str) -> schemas.SetupTokenData:
    """
    Decode and validate setup token
    
    Args:
        token: Setup token for account configuration
        
    Returns:
        SetupTokenData with user information
        
    Raises:
        HTTPException: If token is invalid, expired, or not a setup token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Validate token type
        if payload.get("token_type") != "asystenciai_setup":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        # Validate expiry
        if payload['exp'] < datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Setup token has expired"
            )
        
        return schemas.SetupTokenData(
            asystenciai_user_id=payload['asystenciai_user_id'],
            email=payload['email'],
            first_name=payload['first_name'],
            last_name=payload['last_name'],
            email_verified=payload['email_verified'],
            terms_accepted=payload['terms_accepted'],
            iat=payload['iat'],
            exp=payload['exp']
        )
        
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid setup token: {str(e)}"
        )


def validate_asystenciai_user_data(user_data: schemas.AsystenciaiUserData) -> Dict[str, Any]:
    """
    Validate user data from asystenciai and return validation results
    
    Args:
        user_data: User data from decoded token
        
    Returns:
        Dict with validation results
    """
    issues = []
    
    # Check email verification
    if not user_data.email_verified:
        issues.append("Email not verified in asystenciai")
    
    # Check terms acceptance
    if not user_data.terms_accepted:
        issues.append("Terms not accepted in asystenciai")
    
    # Check required fields
    if not user_data.email:
        issues.append("Email is required")
    
    if not user_data.first_name and not user_data.last_name:
        issues.append("At least first name or last name is required")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def log_asystenciai_activity(
    user_id: Optional[int],
    action: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Log asystenciai integration activity
    
    Args:
        user_id: User ID (if available)
        action: Action performed
        details: Additional details
        ip_address: Client IP address
    """
    # This can be implemented to log to database or external service
    # For now, we'll use basic logging
    import logging
    
    logger = logging.getLogger("asystenciai_integration")
    
    log_data = {
        "user_id": user_id,
        "action": action,
        "details": details,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Asystenciai integration activity: {log_data}")
