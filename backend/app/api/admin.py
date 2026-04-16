from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import math

from app.db.session import get_db
from app.db import schemas, models
from app.db.repositories import UserRepository, AdminRepository, PermissionRepository, SystemConfigRepository
from app.core.auth import require_admin, get_current_user
from app.services.email_service import email_service
from app.services.user_management_service import UserManagementService
from app.services.analytics_archive_service import AnalyticsArchiveService
from app.services import external_logging_service
import logging

router = APIRouter()

@router.get("/users/pending", response_model=schemas.PendingUsersResponse)
async def get_pending_users(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get all users pending admin approval"""
    pending_users = UserRepository.get_pending_approval(db)
    
    admin_users = []
    for user in pending_users:
        admin_user = schemas.AdminUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            admin_approved=user.admin_approved,
            role=user.role,
            company_domain=user.company_domain,
            google_id=user.google_id,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        admin_users.append(admin_user)
    
    return {
        "pending_users": admin_users,
        "total_count": len(admin_users)
    }

@router.get("/users/all", response_model=List[schemas.AdminUserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get all users for admin management"""
    users = UserRepository.get_all(db, skip=skip, limit=limit)
    
    admin_users = []
    for user in users:
        admin_user = schemas.AdminUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            admin_approved=user.admin_approved,
            role=user.role,
            company_domain=user.company_domain,
            google_id=user.google_id,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        admin_users.append(admin_user)
    
    return admin_users

@router.get("/users/search", response_model=schemas.UsersSearchResponse)
async def search_users(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(25, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role_filter: Optional[str] = Query(None, description="Filter by role: user, admin, vsprint_employee"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, inactive, verified, unverified, approved, unapproved"),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Search and filter users with pagination"""
    # Validate filters
    if role_filter and role_filter not in ["user", "admin", "vsprint_employee"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role filter. Must be one of: user, admin, vsprint_employee"
        )
    
    if status_filter and status_filter not in ["active", "inactive", "verified", "unverified", "approved", "unapproved"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status filter. Must be one of: active, inactive, verified, unverified, approved, unapproved"
        )
    
    # Get users with search and filters
    users, total_count = AdminRepository.search_users(
        db=db,
        page=page,
        per_page=per_page,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter
    )
    
    # Convert to response format
    admin_users = []
    for user in users:
        admin_user = schemas.AdminUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            admin_approved=user.admin_approved,
            role=user.role,
            company_domain=user.company_domain,
            google_id=user.google_id,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        admin_users.append(admin_user)
    
    # Calculate pagination info
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    
    return {
        "users": admin_users,
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page
    }

@router.post("/users/create", response_model=schemas.UserResponse)
async def create_user(
    user_data: schemas.AdminUserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Create a new user with admin privileges.
    All admin-created users will have vsprint_employee role to preserve account sharing functionality.
    """
    # Check if user with this email already exists
    existing_user = UserRepository.get_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # Create user with vsprint_employee role
    from app.core.security import get_password_hash
    
    new_user = models.User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password_hash=get_password_hash(user_data.password),
        role=models.UserRole.vsprint_employee,  # Always vsprint_employee for admin-created users
        is_verified=True,  # Auto-verified
        admin_approved=True,  # Auto-approved
        is_active=True,
        company_domain='client'  # Mark as client user
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome email with credentials (optional for client version)
    try:
        await email_service.send_admin_created_user_email(
            to_email=new_user.email,
            user_name=f"{new_user.first_name} {new_user.last_name}",
            email=user_data.email,
            password=user_data.password
        )
    except Exception as e:
        logging.error(f"Failed to send welcome email to {new_user.email}: {str(e)}")
        # Don't fail the request if email fails (expected for client version without email config)
    
    # Log the action for audit trail
    logging.info(f"Admin {current_user.email} created user {new_user.email} with role vsprint_employee")
    
    return schemas.UserResponse(
        id=new_user.id,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        admin_approved=new_user.admin_approved,
        role=new_user.role,
        company_domain=new_user.company_domain,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

@router.post("/users/{user_id}/approve", response_model=schemas.MessageResponse)
async def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Approve user for access"""
    # Get user details for email
    user = UserRepository.get_for_admin(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie został znaleziony"
        )
    
    if user.admin_approved:
        raise HTTPException(
            status_code=400,
            detail="Użytkownik jest już zatwierdzony"
        )
    
    # Approve user
    success = UserRepository.approve(db, user_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się zatwierdzić użytkownika"
        )
    
    # Send approval email
    try:
        await email_service.send_user_approval_email(
            user.email,
            user.first_name
        )
    except Exception as e:
        print(f"Failed to send approval email to {user.email}: {str(e)}")
        # Don't fail the approval if email fails
    
    return {"message": f"Użytkownik {user.email} został pomyślnie zatwierdzony"}

@router.post("/users/{user_id}/reject", response_model=schemas.MessageResponse)
async def reject_user(
    user_id: int,
    request: schemas.UserApprovalRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Reject user and delete account"""
    # Get user details for email
    user = UserRepository.get_for_admin(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie został znaleziony"
        )
    
    if user.admin_approved:
        raise HTTPException(
            status_code=400,
            detail="Nie można odrzucić zatwierdzonego użytkownika"
        )
    
    # Store user data for email before deletion
    user_email = user.email
    user_first_name = user.first_name
    rejection_reason = request.rejection_reason or ""
    
    # Reject (delete) user
    success = UserRepository.reject(db, user_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się odrzucić użytkownika"
        )
    
    # Send rejection email
    try:
        await email_service.send_user_rejection_email(
            user_email,
            user_first_name,
            rejection_reason
        )
    except Exception as e:
        print(f"Failed to send rejection email to {user_email}: {str(e)}")
        # Don't fail the rejection if email fails
    
    return {"message": f"Użytkownik {user_email} został odrzucony i usunięty z systemu"}

# NEW USER MANAGEMENT ENDPOINTS

@router.get("/users/{user_id}/management-info", response_model=schemas.UserManagementInfo)
async def get_user_management_info(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get user info for management operations"""
    try:
        user_info = UserManagementService.get_user_management_info(db, user_id)
        return user_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/users/{user_id}/deactivate", response_model=schemas.UserManagementResponse)
async def deactivate_user(
    user_id: int,
    request: schemas.UserDeactivationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Deactivate a user account (reversible)"""
    try:
        result = await UserManagementService.deactivate_user(
            db=db,
            user_id=user_id,
            admin_id=current_user.id,
            reason=request.reason
        )
        
        return schemas.UserManagementResponse(
            success=result["success"],
            message=result["message"],
            user_email=result["user_email"],
            action_timestamp=result["deactivated_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/users/{user_id}/reactivate", response_model=schemas.UserManagementResponse)
async def reactivate_user(
    user_id: int,
    request: schemas.UserReactivationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Reactivate a deactivated user account"""
    try:
        result = await UserManagementService.reactivate_user(
            db=db,
            user_id=user_id,
            admin_id=current_user.id
        )
        
        return schemas.UserManagementResponse(
            success=result["success"],
            message=result["message"],
            user_email=result["user_email"],
            action_timestamp=result["reactivated_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}/delete", response_model=schemas.UserManagementResponse)
async def delete_user(
    user_id: int,
    request: schemas.UserDeletionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Delete a user account (permanent)"""
    try:
        # Get user to determine type
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Use appropriate deletion method based on user type
        if user.role.value in ["vsprint_employee", "admin"]:
            result = await UserManagementService.delete_vsprint_user(
                db=db,
                user_id=user_id,
                admin_id=current_user.id,
                keep_accounts=request.keep_accounts,
                keep_templates=request.keep_templates,
                keep_images=request.keep_images,
                reason=request.reason
            )
        else:
            result = await UserManagementService.delete_external_user(
                db=db,
                user_id=user_id,
                admin_id=current_user.id,
                reason=request.reason
            )
        
        return schemas.UserManagementResponse(
            success=result["success"],
            message=result["message"],
            user_email=result["user_email"],
            user_type=result.get("user_type"),
            transferred_data=result.get("transferred_data"),
            archived_data=result.get("archived_data"),
            action_timestamp=result["deleted_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ANALYTICS ARCHIVE ENDPOINTS

@router.get("/analytics/archived-users", response_model=List[schemas.ArchivedUserInfo])
async def get_archived_users(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get list of all users with archived analytics data"""
    try:
        archived_users = AnalyticsArchiveService.get_all_archived_users(db)
        return archived_users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/archived-users/{user_display_name}", response_model=schemas.ArchivedAnalyticsData)
async def get_archived_user_analytics(
    user_display_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get archived analytics data for a specific deleted user"""
    try:
        analytics_data = AnalyticsArchiveService.get_archived_user_analytics(db, user_display_name)
        return analytics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/team-with-archived", response_model=schemas.TeamAnalyticsWithArchived)
async def get_team_analytics_with_archived(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get team analytics including archived user data"""
    try:
        analytics_data = AnalyticsArchiveService.get_team_analytics_with_archived(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        return analytics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notification-emails", response_model=schemas.AdminNotificationEmailsListResponse)
async def get_admin_notification_emails(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get list of admin notification emails"""
    emails = AdminRepository.get_notification_emails(db)
    
    email_responses = []
    for email in emails:
        email_response = schemas.AdminNotificationEmailResponse(
            id=email.id,
            email=email.email,
            is_active=email.is_active,
            created_at=email.created_at,
            created_by_admin_id=email.created_by_admin_id
        )
        email_responses.append(email_response)
    
    return {
        "emails": email_responses,
        "total_count": len(email_responses)
    }

@router.post("/notification-emails", response_model=schemas.AdminNotificationEmailsListResponse)
async def update_admin_notification_emails(
    request: schemas.AdminNotificationEmailsListRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update list of admin notification emails"""
    # Update emails in database
    emails = AdminRepository.update_notification_emails(db, request.emails, current_user.id)
    
    email_responses = []
    for email in emails:
        email_response = schemas.AdminNotificationEmailResponse(
            id=email.id,
            email=email.email,
            is_active=email.is_active,
            created_at=email.created_at,
            created_by_admin_id=email.created_by_admin_id
        )
        email_responses.append(email_response)
    
    return {
        "emails": email_responses,
        "total_count": len(email_responses)
    }

@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get admin dashboard statistics"""
    pending_users = UserRepository.get_pending_approval(db)
    all_users = UserRepository.get_all(db, skip=0, limit=1000)  # Get reasonable number for stats
    
    # Count by role
    user_counts = {
        "pending_approval": len(pending_users),
        "total_users": len(all_users),
        "external_users": len([u for u in all_users if u.role == schemas.UserRole.user]),
        "vsprint_employees": len([u for u in all_users if u.role == schemas.UserRole.vsprint_employee]),
        "admins": len([u for u in all_users if u.role == schemas.UserRole.admin]),
    }
    
    return {
        "user_stats": user_counts,
        "pending_users_preview": [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at
            }
            for user in pending_users[:5]  # Show only first 5 for preview
        ]
    }

# ============================================================================
# MODULE PERMISSIONS MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/modules", response_model=List[schemas.Module])
async def get_modules(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get all available modules"""
    return PermissionRepository.get_all_modules(db)

@router.get("/modules/restricted", response_model=List[schemas.Module])
async def get_restricted_modules(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get all restricted (non-core) modules"""
    return PermissionRepository.get_restricted_modules(db)

@router.get("/users/{user_id}/permissions", response_model=schemas.ModulePermissionsResponse)
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get user's module permissions"""
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie został znaleziony"
        )
    
    permissions = PermissionRepository.get_permissions_dict(db, user_id)
    
    # Get dependencies for all modules
    dependencies = {}
    modules = PermissionRepository.get_restricted_modules(db)
    for module in modules:
        dependencies[module.name] = PermissionRepository.get_module_dependencies(db, module.name)
    
    return {
        "permissions": permissions,
        "dependencies": dependencies
    }

@router.post("/users/{user_id}/permissions", response_model=schemas.MessageResponse)
async def update_user_permissions(
    user_id: int,
    request: schemas.ModulePermissionsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update user's module permissions"""
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie został znaleziony"
        )
    
    # Validate dependencies
    errors = PermissionRepository.validate_dependencies(db, user_id, request.permissions)
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Błędy walidacji: {'; '.join(errors)}"
        )
    
    # Update permissions
    success = PermissionRepository.bulk_update_permissions(db, user_id, request.permissions, current_user.id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się zaktualizować uprawnień użytkownika"
        )
    
    return {"message": f"Uprawnienia użytkownika zostały zaktualizowane"}

@router.post("/users/{user_id}/permissions/{module_name}/grant", response_model=schemas.MessageResponse)
async def grant_user_permission(
    user_id: int,
    module_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Grant specific module permission to user"""
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie został znaleziony"
        )
    
    module = PermissionRepository.get_module_by_name(db, module_name)
    if not module:
        raise HTTPException(
            status_code=404,
            detail="Moduł nie został znaleziony"
        )
    
    success = PermissionRepository.grant_permission(db, user_id, module_name, current_user.id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się przyznać uprawnienia"
        )
    
    return {"message": f"Uprawnienie do modułu '{module.display_name}' zostało przyznane"}

@router.post("/users/{user_id}/permissions/{module_name}/revoke", response_model=schemas.MessageResponse)
async def revoke_user_permission(
    user_id: int,
    module_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Revoke specific module permission from user"""
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Użytkownik nie został znaleziony"
        )
    
    module = PermissionRepository.get_module_by_name(db, module_name)
    if not module:
        raise HTTPException(
            status_code=404,
            detail="Moduł nie został znaleziony"
        )
    
    if module.is_core:
        raise HTTPException(
            status_code=400,
            detail="Nie można odebrać uprawnień do modułów podstawowych"
        )
    
    success = PermissionRepository.revoke_permission(db, user_id, module_name, current_user.id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się odebrać uprawnienia"
        )
    
    return {"message": f"Uprawnienie do modułu '{module.display_name}' zostało odebrane"}


# ============ System Configuration Endpoints ============

logger = logging.getLogger(__name__)

def require_admin_or_vsprint(current_user: models.User = Depends(get_current_user)):
    """
    Dependency to require user to be admin or vsprint_employee.
    """
    if current_user.role not in [models.UserRole.admin, models.UserRole.vsprint_employee]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or vsprint_employee role required"
        )
    return current_user


@router.get("/config/external-logging-webhook")
def get_external_logging_webhook(
    current_user: models.User = Depends(require_admin_or_vsprint),
    db: Session = Depends(get_db)
):
    """
    Get current webhook URL for external logging.
    
    Only accessible by admin and vsprint_employee users.
    """
    config = SystemConfigRepository.get(db, "external_logging_webhook_url")
    return {
        "webhook_url": config.config_value if config else "",
        "updated_at": config.updated_at if config else None
    }


@router.put("/config/external-logging-webhook")
def update_external_logging_webhook(
    request: schemas.SystemConfigUpdate,
    current_user: models.User = Depends(require_admin_or_vsprint),
    db: Session = Depends(get_db)
):
    """
    Update webhook URL for external logging.
    
    Only accessible by admin and vsprint_employee users.
    
    To authenticate this API call:
    1. Log in to the app in browser
    2. Open browser DevTools (F12)
    3. Go to Network tab
    4. Make any API request
    5. Find Authorization header: "Bearer <token>"
    6. Use this token in your API call:
       curl -X PUT https://ofertator.vautomate.pl/api/v1/admin/config/external-logging-webhook \
         -H "Authorization: Bearer YOUR_TOKEN_HERE" \
         -H "Content-Type: application/json" \
         -d '{"webhook_url": "https://script.google.com/macros/s/NEW_URL/exec"}'
    """
    webhook_url = request.webhook_url
    
    # Validate URL format
    if webhook_url and not webhook_url.startswith("https://script.google.com"):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook URL - must start with https://script.google.com"
        )
    
    # Update in database
    config = SystemConfigRepository.update(
        db, 
        "external_logging_webhook_url", 
        webhook_url,
        current_user.id,
        description="Google Apps Script webhook URL for external logging"
    )
    
    # Clear cache to force immediate refresh
    external_logging_service.clear_webhook_cache()
    
    logger.info(f"Webhook URL updated by user {current_user.id} ({current_user.email})")
    
    return {
        "success": True,
        "webhook_url": config.config_value,
        "updated_at": config.updated_at
    }


# AI Configuration Endpoints
@router.get("/ai-config", response_model=schemas.AdminAIConfigResponse)
def get_ai_config(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all AI configurations for Titles module.
    
    Only accessible by admin users.
    """
    import json
    
    all_configs = SystemConfigRepository.get_all_ai_configs(db)
    
    # Organize configs by provider -> parameters (only for Titles)
    response = {
        "titles": {
            "anthropic": {},
            "gemini": {}
        }
    }
    
    for key, value in all_configs.items():
        parts = key.split('.')
        if len(parts) >= 4 and parts[0] == 'ai' and parts[1] == 'titles':
            provider = parts[2]  # anthropic or gemini
            param = '.'.join(parts[3:])  # parameter name (may contain dots)
            
            if provider in response["titles"]:
                # Parse value based on parameter type
                if param == 'stop_sequences':
                    try:
                        response["titles"][provider][param] = json.loads(value) if value else []
                    except json.JSONDecodeError:
                        response["titles"][provider][param] = []
                elif param in ['temperature', 'top_p']:
                    try:
                        response["titles"][provider][param] = float(value) if value else None
                    except (ValueError, TypeError):
                        response["titles"][provider][param] = None
                elif param in ['max_output_tokens', 'top_k']:
                    try:
                        response["titles"][provider][param] = int(value) if value else None
                    except (ValueError, TypeError):
                        response["titles"][provider][param] = None
                else:
                    response["titles"][provider][param] = value
    
    return response


def validate_ai_parameters(provider: str, module: str, params: Dict) -> None:
    """
    Validate AI parameters based on provider and module constraints.
    
    Raises HTTPException if validation fails.
    """
    # Validate temperature range
    if 'temperature' in params and params['temperature'] is not None:
        temp = params['temperature']
        if provider == 'anthropic':
            if not (0.0 <= temp <= 1.0):
                raise HTTPException(
                    status_code=400,
                    detail=f"Temperature for Anthropic must be between 0.0 and 1.0 (got {temp})"
                )
        elif provider == 'gemini':
            if not (0.0 <= temp <= 2.0):
                raise HTTPException(
                    status_code=400,
                    detail=f"Temperature for Gemini must be between 0.0 and 2.0 (got {temp})"
                )
    
    # Validate top_p range
    if 'top_p' in params and params['top_p'] is not None:
        top_p = params['top_p']
        if not (0.0 <= top_p <= 1.0):
            raise HTTPException(
                status_code=400,
                detail=f"top_p must be between 0.0 and 1.0 (got {top_p})"
            )
    
    # Validate max_output_tokens
    if 'max_output_tokens' in params and params['max_output_tokens'] is not None:
        tokens = params['max_output_tokens']
        if tokens < 1:
            raise HTTPException(
                status_code=400,
                detail=f"max_output_tokens must be at least 1 (got {tokens})"
            )
        if provider == 'anthropic' and tokens > 8192:
            raise HTTPException(
                status_code=400,
                detail=f"max_output_tokens for Anthropic should not exceed 8192 (got {tokens})"
            )
        if provider == 'gemini' and tokens > 8192:
            raise HTTPException(
                status_code=400,
                detail=f"max_output_tokens for Gemini should not exceed 8192 (got {tokens})"
            )
    
    # Validate top_k
    if 'top_k' in params and params['top_k'] is not None:
        top_k = params['top_k']
        if top_k < 1:
            raise HTTPException(
                status_code=400,
                detail=f"top_k must be at least 1 (got {top_k})"
            )
    
    # Validate stop_sequences
    if 'stop_sequences' in params and params['stop_sequences'] is not None:
        sequences = params['stop_sequences']
        if not isinstance(sequences, list):
            raise HTTPException(
                status_code=400,
                detail="stop_sequences must be an array of strings"
            )
        if len(sequences) > 4:
            raise HTTPException(
                status_code=400,
                detail="Maximum 4 stop sequences allowed"
            )
    
    # Anthropic-specific constraint: temperature and top_p cannot both be specified
    if provider == 'anthropic':
        has_temperature = 'temperature' in params and params['temperature'] is not None
        has_top_p = 'top_p' in params and params['top_p'] is not None
        if has_temperature and has_top_p:
            logger.warning(
                f"Anthropic config has both temperature and top_p. "
                f"Only temperature will be used (top_p will be ignored)."
            )
            # Note: We allow saving both but the runtime code will prioritize temperature
    
    # Validate required prompts
    if module == 'titles':
        if 'prompt' not in params or not params['prompt']:
            raise HTTPException(
                status_code=400,
                detail="Prompt is required for Titles module"
            )


@router.put("/ai-config/titles/{provider}")
def update_ai_config(
    provider: str,
    config: Dict[str, Any],
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update AI configuration for Titles module and specific provider.
    
    Only accessible by admin users.
    
    Args:
        provider: Provider name ('anthropic' or 'gemini')
        config: Configuration parameters to update
    """
    import json
    
    module = 'titles'  # Fixed to titles only
    
    # Validate provider
    if provider not in ['anthropic', 'gemini']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {provider}. Must be 'anthropic' or 'gemini'"
        )
    
    # Validate parameters
    validate_ai_parameters(provider, module, config)
    
    # Update each configuration parameter
    updated_keys = []
    for param_name, param_value in config.items():
        config_key = f"ai.{module}.{provider}.{param_name}"
        
        # Convert value to string for storage
        if param_name == 'stop_sequences':
            value_str = json.dumps(param_value if param_value else [])
        elif param_value is None:
            value_str = ''
        else:
            value_str = str(param_value)
        
        # Upsert configuration
        SystemConfigRepository.update(
            db,
            config_key,
            value_str,
            current_user.id,
            description=f"{param_name} for {module} module - {provider} provider"
        )
        updated_keys.append(config_key)
    
    logger.info(f"AI config updated by admin {current_user.id} ({current_user.email}): {module}/{provider}")
    
    return {
        "success": True,
        "message": f"Updated {len(updated_keys)} configuration parameters",
        "updated_keys": updated_keys
    }
