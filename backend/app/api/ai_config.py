"""
API endpoints for AI configuration management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List

from app.db import schemas, models
from app.db.repositories import AIConfigRepository
from app.db.session import get_db
from app.core.auth import get_current_user, get_current_active_user
from app.services.ai_provider_service import ai_provider_service
from app.services.encryption_service import encryption_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/providers", response_model=schemas.AIProviderInfo)
async def get_available_providers():
    """Get all available AI providers and models"""
    providers = ai_provider_service.get_available_models()
    default_provider, default_model = ai_provider_service.get_default_model()
    
    return schemas.AIProviderInfo(
        providers=providers,
        default_provider=default_provider,
        default_model=default_model
    )

@router.get("/status", response_model=schemas.AIConfigStatus)
async def get_ai_config_status(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's AI configuration status"""
    config = AIConfigRepository.get_user_config(db, current_user.id)
    
    # Check if user can use default (all users - vsprint employees, admins, external users, Asystenci AI)
    can_use_default = (
        current_user.role in [models.UserRole.vsprint_employee, models.UserRole.admin, models.UserRole.user] or
        current_user.registration_source == models.RegistrationSource.asystenciai
    )
    
    # Determine default provider/model that would be used if no custom config
    default_provider = None
    default_model = None
    
    if can_use_default and not (config and config.is_active):
        # User would use fallback - determine which one
        if current_user.registration_source == models.RegistrationSource.asystenciai:
            default_provider = "google"
            default_model = "gemini-2.5-pro"
        elif current_user.role == models.UserRole.user:
            # Regular external users get Gemini
            default_provider = "google"
            default_model = "gemini-2.5-pro"
        elif current_user.role in [models.UserRole.vsprint_employee, models.UserRole.admin]:
            # vSprint employees and admins get Anthropic
            from app.services.ai_provider_service import ai_provider_service
            default_provider, default_model = ai_provider_service.get_default_model()
    
    if config:
        return schemas.AIConfigStatus(
            has_config=True,
            is_active=config.is_active,
            provider=config.ai_provider.value,
            model=config.model_name,
            last_validated=config.last_validated_at,
            can_use_default=can_use_default,
            default_provider=default_provider,
            default_model=default_model
        )
    else:
        return schemas.AIConfigStatus(
            has_config=False,
            can_use_default=can_use_default,
            default_provider=default_provider,
            default_model=default_model
        )

@router.get("/config", response_model=schemas.AIConfigResponse)
async def get_ai_config(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's AI configuration (without sensitive data)"""
    config = AIConfigRepository.get_user_config(db, current_user.id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Konfiguracja AI nie została znaleziona"
        )
    
    return schemas.AIConfigResponse.from_orm(config)

@router.post("/test-key", response_model=schemas.TestAPIKeyResponse)
async def test_api_key(
    request: schemas.TestAPIKeyRequest,
    current_user: models.User = Depends(get_current_user)
):
    """Test API key validity"""
    try:
        is_valid, error_message = await ai_provider_service.test_api_key(
            request.provider,
            request.api_key,
            request.model_name
        )
        
        return schemas.TestAPIKeyResponse(
            is_valid=is_valid,
            error_message=error_message
        )
    except Exception as e:
        logger.error(f"Error testing API key: {e}")
        return schemas.TestAPIKeyResponse(
            is_valid=False,
            error_message=f"Błąd podczas testowania klucza API: {str(e)}"
        )

@router.post("/config", response_model=schemas.AIConfigResponse)
async def create_ai_config(
    config_data: schemas.AIConfigCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update AI configuration"""
    try:
        # First test the API key
        is_valid, error_message = await ai_provider_service.test_api_key(
            config_data.ai_provider,
            config_data.api_key,
            config_data.model_name
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nieprawidłowy klucz API: {error_message}"
            )
        
        # Create/update configuration
        config = AIConfigRepository.create(
            db,
            current_user.id,
            config_data.ai_provider,
            config_data.model_name,
            config_data.api_key
        )
        
        return schemas.AIConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating AI config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas tworzenia konfiguracji AI"
        )

@router.put("/config", response_model=schemas.AIConfigResponse)
async def update_ai_config(
    config_data: schemas.AIConfigUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update AI configuration"""
    try:
        # Check if user has existing config
        existing_config = AIConfigRepository.get_user_config(db, current_user.id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konfiguracja AI nie została znaleziona"
            )
        
        # If API key is being updated, test it first
        if config_data.api_key:
            provider = config_data.ai_provider or existing_config.ai_provider.value
            model = config_data.model_name or existing_config.model_name
            
            is_valid, error_message = await ai_provider_service.test_api_key(
                provider,
                config_data.api_key,
                model
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Nieprawidłowy klucz API: {error_message}"
                )
        
        # Update configuration
        config = AIConfigRepository.update(
            db,
            current_user.id,
            config_data.ai_provider,
            config_data.model_name,
            config_data.api_key,
            config_data.is_active
        )
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konfiguracja AI nie została znaleziona"
            )
        
        return schemas.AIConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktualizacji konfiguracji AI"
        )

@router.delete("/config")
async def delete_ai_config(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete AI configuration"""
    try:
        success = AIConfigRepository.delete(db, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konfiguracja AI nie została znaleziona"
            )
        
        return {"message": "Konfiguracja AI została usunięta"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting AI config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas usuwania konfiguracji AI"
        )

@router.post("/config/deactivate")
async def deactivate_ai_config(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate AI configuration (keep data but disable usage)"""
    try:
        success = AIConfigRepository.deactivate(db, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konfiguracja AI nie została znaleziona"
            )
        
        return {"message": "Konfiguracja AI została dezaktywowana"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating AI config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas dezaktywacji konfiguracji AI"
        )

@router.post("/config/activate")
async def activate_ai_config(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate AI configuration"""
    try:
        success = AIConfigRepository.activate(db, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konfiguracja AI nie została znaleziona"
            )
        
        return {"message": "Konfiguracja AI została aktywowana"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating AI config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Błąd podczas aktywacji konfiguracji AI"
        ) 