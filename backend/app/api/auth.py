from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db import schemas
from app.db.repositories import UserRepository, AdminRepository, PermissionRepository, AccountRepository
from app.core.auth import get_current_user, get_current_active_user
from app.core.security import create_access_token, create_refresh_token, verify_token, verify_password
from app.services.email_service import email_service
from app.services.google_oauth import google_oauth_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=schemas.MessageResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    # Check if registration is enabled
    from app.services.feature_flag_service import FeatureFlagService
    if not FeatureFlagService.is_registration_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="Rejestracja jest obecnie wyłączona"
        )
    
    # Check if user already exists
    existing_user = UserRepository.get_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Użytkownik z tym adresem email już istnieje"
        )
    
    # Prevent regular registration for vsprint domain
    if user_data.email.endswith('@vsprint.pl'):
        raise HTTPException(
            status_code=400,
            detail="Pracownicy Vsprint muszą używać logowania przez Google"
        )
    
    # Create user
    user = UserRepository.create(db, user_data)
    
    # Create email verification
    verification = UserRepository.create_email_verification(db, user.id)
    
    # Send verification email
    await email_service.send_verification_email(
        user.email, 
        verification.token,
        user.first_name
    )
    
    return {"message": "Rejestracja zakończona pomyślnie. Sprawdź email w celu weryfikacji konta. Po weryfikacji emaila Twoje konto będzie oczekiwać na zatwierdzenie przez administratora."}

@router.post("/login", response_model=schemas.Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = UserRepository.authenticate(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Konto jest nieaktywne"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email nie został zweryfikowany. Sprawdź email w celu weryfikacji konta."
        )
    
    if not user.admin_approved and user.role.value == "user":
        raise HTTPException(
            status_code=400,
            detail="Twoje konto oczekuje na zatwierdzenie przez administratora. Sprawdź email lub skontaktuj się z zespołem wsparcia."
        )
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google-login", response_model=schemas.Token)
async def google_login(
    google_data: schemas.GoogleLogin,
    db: Session = Depends(get_db)
):
    # Check if Google SSO is enabled
    from app.services.feature_flag_service import FeatureFlagService
    if not FeatureFlagService.is_google_sso_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="Logowanie przez Google jest obecnie wyłączone"
        )
    
    # Verify Google token
    google_user = await google_oauth_service.verify_google_token(google_data.token)
    if not google_user:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy token Google"
        )
    
    # Validate vsprint domain
    if not google_oauth_service.validate_vsprint_domain(google_user['email']):
        raise HTTPException(
            status_code=400,
            detail="Tylko domena vsprint.pl jest dozwolona dla logowania przez Google"
        )
    
    # Check if user exists
    user = UserRepository.get_by_email(db, google_user['email'])
    if not user:
        # Auto-create vsprint employee
        user_data = schemas.UserCreateSSO(
            email=google_user['email'],
            first_name=google_user['given_name'],
            last_name=google_user['family_name'],
            google_id=google_user['sub'],
            role=schemas.UserRole.vsprint_employee
        )
        user = UserRepository.create_sso(db, user_data)
    else:
        # Update Google ID if not set
        if not user.google_id:
            user.google_id = google_user['sub']
            db.commit()
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google-callback", response_model=schemas.Token)
async def google_callback(
    callback_data: schemas.GoogleCallback,
    db: Session = Depends(get_db)
):
    # Check if Google SSO is enabled
    from app.services.feature_flag_service import FeatureFlagService
    if not FeatureFlagService.is_google_sso_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="Logowanie przez Google jest obecnie wyłączone"
        )
    
    # Exchange code for token
    id_token = await google_oauth_service.exchange_code_for_token(callback_data.code)
    if not id_token:
        raise HTTPException(
            status_code=400,
            detail="Nie udało się wymienić kodu na token"
        )
    
    # Use the google_login logic
    return await google_login(schemas.GoogleLogin(token=id_token), db)

@router.get("/google-auth-url")
async def get_google_auth_url(db: Session = Depends(get_db)):
    """Get Google OAuth authorization URL"""
    # Check if Google SSO is enabled
    from app.services.feature_flag_service import FeatureFlagService
    if not FeatureFlagService.is_google_sso_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="Logowanie przez Google jest obecnie wyłączone"
        )
    return {"auth_url": google_oauth_service.get_authorization_url()}

@router.post("/verify-email/{token}", response_model=schemas.MessageResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    verification = UserRepository.get_valid_email_verification(db, token)
    if not verification:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy lub wygasły token weryfikacyjny"
        )
    
    # Verify user email
    success = UserRepository.verify_email(db, verification.user_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się zweryfikować emaila"
        )
    
    # Mark verification as used
    UserRepository.mark_email_verification_used(db, verification.id)
    
    # Get user to send admin notifications
    user = UserRepository.get_by_id(db, verification.user_id)
    if user and user.role.value == "user":
        # Send notifications to all admin emails
        admin_emails = AdminRepository.get_notification_emails(db)
        registration_date = user.created_at.strftime("%d.%m.%Y %H:%M")
        
        for admin_email_obj in admin_emails:
            try:
                await email_service.send_admin_new_registration_email(
                    admin_email_obj.email,
                    user.first_name,
                    user.last_name,
                    user.email,
                    registration_date
                )
            except Exception as e:
                # Log error but don't fail the verification
                print(f"Failed to send admin notification to {admin_email_obj.email}: {str(e)}")
        
        return {"message": "Email został pomyślnie zweryfikowany. Twoje konto oczekuje teraz na zatwierdzenie przez administratora."}
    
    return {"message": "Email został pomyślnie zweryfikowany"}

@router.post("/resend-verification", response_model=schemas.MessageResponse)
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    email_data: schemas.EmailVerificationCreate,
    db: Session = Depends(get_db)
):
    user = UserRepository.get_by_email(db, email_data.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "Jeśli email istnieje, link weryfikacyjny został wysłany"}
    
    if user.is_verified:
        return {"message": "Email jest już zweryfikowany"}
    
    # Create new verification
    verification = UserRepository.create_email_verification(db, user.id)
    
    # Send verification email
    await email_service.send_verification_email(
        user.email,
        verification.token,
        user.first_name
    )
    
    return {"message": "Jeśli email istnieje, link weryfikacyjny został wysłany"}

@router.post("/forgot-password", response_model=schemas.MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    reset_data: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = UserRepository.get_by_email(db, reset_data.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "Jeśli email istnieje, link resetujący został wysłany"}
    
    if user.google_id and not user.password_hash:
        return {"message": "Użytkownicy Google SSO nie mogą resetować hasła"}
    
    # Create password reset
    reset = UserRepository.create_password_reset(db, user.id)
    
    # Send reset email
    await email_service.send_password_reset_email(
        user.email,
        reset.token,
        user.first_name
    )
    
    return {"message": "Jeśli email istnieje, link resetujący został wysłany"}

@router.post("/reset-password", response_model=schemas.MessageResponse)
async def reset_password(
    reset_data: schemas.PasswordReset,
    db: Session = Depends(get_db)
):
    reset_record = UserRepository.get_valid_password_reset(db, reset_data.token)
    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy lub wygasły token resetujący"
        )
    
    # Update password
    success = UserRepository.update_password(db, reset_record.user_id, reset_data.new_password)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się zaktualizować hasła"
        )
    
    # Mark reset as used
    UserRepository.mark_password_reset_used(db, reset_record.id)
    
    return {"message": "Hasło zostało pomyślnie zaktualizowane"}

@router.post("/refresh-token", response_model=schemas.Token)
async def refresh_token(
    token_data: schemas.TokenRefresh,
    db: Session = Depends(get_db)
):
    payload = verify_token(token_data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token odświeżania"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token odświeżania"
        )
    
    user = UserRepository.get_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik nie został znaleziony lub jest nieaktywny"
        )
    
    # Check admin approval for external users (same as login endpoint)
    if not user.admin_approved and user.role.value == "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Twoje konto oczekuje na zatwierdzenie przez administratora. Sprawdź email lub skontaktuj się z zespołem wsparcia."
        )
    
    # Create new tokens
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserWithAccounts)
async def get_current_user_info(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get user's accessible accounts
    accounts = AccountRepository.get_user_accounts(db, current_user)
    account_ids = [account.id for account in accounts]
    
    return schemas.UserWithAccounts(
        **current_user.__dict__,
        accessible_accounts=account_ids
    )

@router.post("/logout", response_model=schemas.MessageResponse)
async def logout():
    # Since we're using stateless JWT, logout is handled client-side
    # In a production app, you might want to maintain a blacklist of tokens
    return {"message": "Wylogowano pomyślnie"}

@router.post("/change-password", response_model=schemas.MessageResponse)
async def change_password(
    password_data: schemas.PasswordChange,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user has a password (not Google SSO only)
    if not current_user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="Użytkownicy Google SSO nie mogą zmieniać hasła"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowe obecne hasło"
        )
    
    # Update password
    success = UserRepository.update_password(db, current_user.id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się zaktualizować hasła"
        )
    
    return {"message": "Hasło zostało pomyślnie zmienione"}

@router.delete("/delete-account", response_model=schemas.MessageResponse)
async def delete_account(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if user is vsprint employee - they cannot delete their account
    if current_user.role == schemas.UserRole.vsprint_employee:
        raise HTTPException(
            status_code=403,
            detail="Pracownicy @vsprint.pl nie mogą usunąć swojego konta"
        )
    
    # Check if user is Google SSO user - they cannot delete their account
    if current_user.google_id:
        raise HTTPException(
            status_code=403,
            detail="Użytkownicy Google SSO nie mogą usunąć swojego konta"
        )
    
    # Delete user and all related data
    success = UserRepository.delete_with_data(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się usunąć konta"
        )
    
    return {"message": "Konto zostało pomyślnie usunięte"}

@router.get("/me/permissions")
async def get_current_user_permissions(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's module permissions"""
    
    # Get user permissions
    permissions = PermissionRepository.get_permissions_dict(db, current_user.id)
    
    # Get module dependencies for frontend
    dependencies = PermissionRepository.get_all_dependencies(db)
    
    return {
        "permissions": permissions,
        "dependencies": dependencies
    } 