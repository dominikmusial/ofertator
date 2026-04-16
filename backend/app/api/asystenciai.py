"""
Asystenciai Integration API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import schemas
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.core.asystenciai_integration import (
    decode_asystenciai_token,
    create_setup_token,
    decode_setup_token,
    validate_asystenciai_user_data,
    log_asystenciai_activity
)

router = APIRouter()


@router.get("/transfer-from-asystenciai")
async def transfer_from_asystenciai(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Handle user transfer from asystenciai application
    
    This endpoint processes JWT tokens from asystenciai and either:
    1. Logs in existing users automatically
    2. Redirects new users to account setup
    """
    client_ip = request.client.host
    
    try:
        # Decode and validate asystenciai token
        user_data = decode_asystenciai_token(token)
        
        # Validate user data
        validation_result = validate_asystenciai_user_data(user_data)
        if not validation_result["valid"]:
            log_asystenciai_activity(
                None, "transfer_failed", 
                {"reason": "validation_failed", "issues": validation_result["issues"]},
                client_ip
            )
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/auth/error?reason=invalid_user_data",
                status_code=302
            )
        
        # Check if user already exists
        existing_user = ExternalIntegrationRepository.check_asystencjai_user_exists(
            db, str(user_data.asystenciai_user_id), user_data.email
        )
        
        if existing_user:
            # User exists - log them in automatically
            if existing_user.external_user_id != str(user_data.asystenciai_user_id):
                # Link the external ID if not already set
                ExternalIntegrationRepository.update_external_id(db, existing_user.id, str(user_data.asystenciai_user_id))
            
            # Create access and refresh tokens
            access_token = create_access_token({"sub": str(existing_user.id)})
            refresh_token = create_refresh_token({"sub": str(existing_user.id)})
            
            log_asystenciai_activity(
                existing_user.id, "auto_login_success",
                {"asystenciai_user_id": user_data.asystenciai_user_id},
                client_ip
            )
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/auth/success?access_token={access_token}&refresh_token={refresh_token}",
                status_code=302
            )
        
        # Check if email exists with different registration source
        existing_by_email = UserRepository.get_by_email(db, user_data.email)
        if existing_by_email and existing_by_email.registration_source != schemas.RegistrationSource.asystenciai:
            log_asystenciai_activity(
                existing_by_email.id, "transfer_failed",
                {"reason": "email_exists_different_source", "asystenciai_user_id": user_data.asystenciai_user_id},
                client_ip
            )
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/auth/error?reason=email_exists",
                status_code=302
            )
        
        # New user - create setup token and redirect to setup page
        setup_token = create_setup_token(user_data)
        
        log_asystenciai_activity(
            None, "setup_redirect",
            {"asystenciai_user_id": user_data.asystenciai_user_id, "email": user_data.email},
            client_ip
        )
        
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/setup-account?token={setup_token}",
            status_code=302
        )
        
    except HTTPException as e:
        log_asystenciai_activity(
            None, "transfer_failed",
            {"reason": "http_exception", "detail": e.detail},
            client_ip
        )
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?reason=invalid_token",
            status_code=302
        )
    except Exception as e:
        log_asystenciai_activity(
            None, "transfer_failed",
            {"reason": "unexpected_error", "error": str(e)},
            client_ip
        )
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?reason=server_error",
            status_code=302
        )


@router.get("/setup-token-data")
async def get_setup_token_data(
    token: str,
    request: Request
):
    """
    Decode setup token and return user data for the setup form
    """
    try:
        user_data = decode_setup_token(token)
        
        return {
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "email_verified": user_data.email_verified,
            "terms_accepted": user_data.terms_accepted
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid setup token: {str(e)}"
        )


@router.post("/complete-setup", response_model=schemas.AsystenciaiSetupResponse)
async def complete_asystenciai_setup(
    request: Request,
    setup_data: schemas.AsystenciaiSetupRequest,
    db: Session = Depends(get_db)
):
    """
    Complete account setup for asystenciai user
    """
    client_ip = request.client.host
    
    try:
        # Decode and validate setup token
        token_data = decode_setup_token(setup_data.setup_token)
        
        # Check if user already exists (race condition protection)
        existing_user = ExternalIntegrationRepository.check_asystencjai_user_exists(
            db, str(token_data.asystenciai_user_id), token_data.email
        )
        
        if existing_user:
            log_asystenciai_activity(
                existing_user.id, "setup_failed",
                {"reason": "user_already_exists", "asystenciai_user_id": token_data.asystenciai_user_id},
                client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Użytkownik już istnieje"
            )
        
        # Update token data with user-provided data
        token_data.first_name = setup_data.first_name
        token_data.last_name = setup_data.last_name
        
        # Create user
        user = ExternalIntegrationRepository.create_asystencjai_user(db, token_data, setup_data.password)
        
        # Automatically create AI configuration with our Gemini key
        from app.core.config import settings
        if settings.GEMINI_API_KEY:
            try:
                # Create AI configuration with our Gemini key (gemini-2.0-flash)
                ai_config = AIConfigRepository.create(
                    db, 
                    user.id, 
                    "google",
                    "gemini-2.0-flash",
                    settings.GEMINI_API_KEY,
                    is_active=True
                )
                
                # Log successful AI config creation
                log_asystenciai_activity(
                    user.id, "ai_config_created",
                    {
                        "provider": "google", 
                        "model": "gemini-2.0-flash",
                        "is_active": True,
                        "config_id": ai_config.id,
                        "source": "default_gemini_key"
                    },
                    client_ip
                )
            except Exception as e:
                # Log AI config creation failure but don't fail the whole setup process
                log_asystenciai_activity(
                    user.id, "ai_config_creation_failed",
                    {"error": str(e), "provider": "google", "source": "default_gemini_key"},
                    client_ip
                )
        else:
            # Log warning about missing Gemini key
            log_asystenciai_activity(
                user.id, "ai_config_skipped",
                {"reason": "gemini_key_not_configured"},
                client_ip
            )
        
        # Create tokens for authentication
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # Log successful setup
        log_asystenciai_activity(
            user.id, "setup_completed",
            {"asystenciai_user_id": token_data.asystenciai_user_id},
            client_ip
        )
        
        return schemas.AsystenciaiSetupResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            redirect_url="/titles",
            user=schemas.UserResponse.model_validate(user)
        )
        
    except HTTPException as e:
        log_asystenciai_activity(
            None, "setup_failed",
            {"reason": "http_exception", "detail": e.detail},
            client_ip
        )
        raise e
    except Exception as e:
        log_asystenciai_activity(
            None, "setup_failed",
            {"reason": "unexpected_error", "error": str(e)},
            client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Wystąpił błąd podczas konfiguracji konta"
        )


@router.get("/health")
async def asystenciai_integration_health():
    """
    Health check endpoint for asystenciai integration
    """
    return {
        "status": "healthy",
        "integration": "asystenciai",
        "version": "1.0.0"
    }
