from pydantic import BaseModel, Json, EmailStr, validator
from typing import List, Optional, Any, Dict, Union, Literal
from enum import Enum
from datetime import datetime, date


# Base schemas
class BaseModel(BaseModel):
    class Config:
        from_attributes = True

# Schemas for Konto/Account
class AccountBase(BaseModel):
    nazwa_konta: str

class AccountCreate(AccountBase):
    access_token: str
    refresh_token: str
    token_expires_at: datetime

class Account(AccountBase):
    id: int
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    refresh_token_expires_at: Optional[datetime] = None
    needs_reauth: bool = False
    last_token_refresh: Optional[datetime] = None
    marketplace_type: str = "allegro"
    marketplace_specific_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # templates: List["Template"] = [] # Circular dependency, handle with care

    class Config:
        from_attributes = True

class AccountWithOwnership(Account):
    is_owner: bool = True
    shared_with_vsprint: bool = False

class AllegroAccountCreate(BaseModel):
    nazwa_konta: str
    device_code: str

# Schemas for Template
class TemplateBase(BaseModel):
    name: str
    content: dict
    prompt: Optional[str] = None

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[dict] = None
    prompt: Optional[str] = None

class Template(TemplateBase):
    id: int
    created_at: datetime
    owner_id: int
    account_id: Optional[int] = None

    class Config:
        from_attributes = True

# Update forward references
# Account.model_rebuild()
# Template.model_rebuild()

# Schemas for Promotions
class PromotionBase(BaseModel):
    name: str

class PromotionCreate(PromotionBase):
    offer_ids: List[str]
    for_each_quantity: int
    percentage: int

class Promotion(PromotionBase):
    id: str
    status: str
    name: Optional[str] = None
    # Add other relevant fields from the Allegro API response as needed

    class Config:
        from_attributes = True

# Schemas for Offer Copying
class CopyOfferOptions(BaseModel):
    target_account_id: int
    delivery_price_list_id: Optional[str] = None
    copy_images: bool = True
    copy_quantity: bool = False
    copy_description: bool = True
    copy_parameters: bool = True
    copy_shipping: bool = True
    copy_return_policy: bool = True
    copy_warranty: bool = True
    copy_price: bool = False
    # New fields for user selections
    selected_delivery_id: Optional[str] = None
    selected_warranty_id: Optional[str] = None
    selected_return_policy_id: Optional[str] = None

class CopyOfferRequest(BaseModel):
    source_account_id: int
    source_offer_id: str
    options: CopyOfferOptions 

# Schemas for Offer Editing
class OfferStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    
class OfferStatusChangeRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    status: OfferStatus

class BulkEditTitlesRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    append_text: Optional[str] = None
    prepend_text: Optional[str] = None
    replace_from: Optional[str] = None
    replace_to: Optional[str] = None

class DuplicateOfferItem(BaseModel):
    offer_id: str
    new_title: str

class DuplicateOffersRequest(BaseModel):
    account_id: int
    items: List[DuplicateOfferItem]
    activate_immediately: bool = False

# Schemas for Universal Bulk Edit
class BulkEditPrice(BaseModel):
    amount: str
    currency: str = "PLN"

class BulkEditStock(BaseModel):
    available: int

class BulkEditHandlingTime(BaseModel):
    handling_time: str # e.g. "PT24H"

class BulkEditActions(BaseModel):
    price: Optional[BulkEditPrice] = None
    stock: Optional[BulkEditStock] = None
    handling_time: Optional[BulkEditHandlingTime] = None

class BulkEditRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    actions: BulkEditActions

class BulkImageReplaceRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    image_url_to_replace: str
    new_image_url: str

class DescriptionImagePosition(str, Enum):
    PREPEND = "PREPEND"
    APPEND = "APPEND"

class BulkDescriptionImageRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    image_url: str
    position: DescriptionImagePosition

class BulkCompositeImageReplaceRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    image_position: int  # 1-16, which image position to replace
    overlay_image_url: str  # URL of the image to overlay on top

class BulkRestoreImagePositionRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    image_position: int  # 1-16, which image position to restore

class ThumbnailUpdateRequest(BaseModel):
    offer_id: str
    new_thumbnail_url: str

class BulkThumbnailUpdateRequest(BaseModel):
    account_id: int
    updates: List[ThumbnailUpdateRequest]

class OfferBackupBase(BaseModel):
    offer_id: str
    backup_data: dict

class OfferBackupCreate(OfferBackupBase):
    account_id: int

class OfferBackup(OfferBackupBase):
    id: int
    created_at: datetime
    account_id: int

    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    task_id: str

class Task(TaskBase):
    status: str
    result: Optional[dict] = None

# Update forward references
# Account.model_rebuild()
# Template.model_rebuild() 

# User schemas
class UserRole(str, Enum):
    user = "user"
    admin = "admin"  
    vsprint_employee = "vsprint_employee"

class RegistrationSource(str, Enum):
    web = "web"
    asystenciai = "asystenciai"

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserCreateSSO(UserBase):
    google_id: str
    role: UserRole = UserRole.vsprint_employee

class AdminUserCreate(UserBase):
    """Schema for admin-created users"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    admin_approved: bool
    role: UserRole
    company_domain: Optional[str] = None
    google_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithAccounts(UserResponse):
    accessible_accounts: List[int] = []

# Authentication schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

class GoogleLogin(BaseModel):
    token: str

class GoogleCallback(BaseModel):
    code: str

# Email verification schemas
class EmailVerificationCreate(BaseModel):
    email: EmailStr

class EmailVerification(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: datetime
    is_used: bool
    
    class Config:
        from_attributes = True

# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Hasło musi mieć co najmniej 8 znaków')
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Hasło musi mieć co najmniej 8 znaków')
        return v

# User-Account relationship schemas
class UserMarketplaceAccountBase(BaseModel):
    is_owner: bool = True
    shared_with_vsprint: bool = False

class UserMarketplaceAccountCreate(UserMarketplaceAccountBase):
    account_id: int

class UserMarketplaceAccount(UserMarketplaceAccountBase):
    id: int
    user_id: int
    account_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Backward compatibility aliases (deprecated)
UserAllegroAccountBase = UserMarketplaceAccountBase
UserAllegroAccountCreate = UserMarketplaceAccountCreate
UserAllegroAccount = UserMarketplaceAccount

class AccountSharing(BaseModel):
    account_id: int
    shared_with_vsprint: bool

# Image schemas
class ImageBase(BaseModel):
    filename: str
    content_type: str
    size: int

class ImageCreate(ImageBase):
    pass

class Image(ImageBase):
    id: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True

# Bulk operations schemas
class BulkEditTitles(BaseModel):
    offer_ids: List[str]
    title_template: str
    account_id: int

class BulkChangeStatus(BaseModel):  
    offer_ids: List[str]
    action: str  # 'activate' or 'deactivate'
    account_id: int

class BulkReplaceImages(BaseModel):
    offer_ids: List[str]
    old_image_url: str
    new_image_url: str
    account_id: int

# Task status schemas
class TaskStatus(BaseModel):
    task_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None

# API Response schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

# Bundle promotion schemas
class CreateGroupedBundleRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    for_each_quantity: int
    percentage: int
    group_size: int 

# Banner Images schemas
class BannerImageSettings(BaseModel):
    width: int
    height: int
    size_percent: float  # Size as percentage of banner height
    horizontal_position_percent: float  # Distance from right edge as percentage
    vertical_position_percent: float  # Vertical position as percentage from top
    shape: str  # "circle", "square", "original"
    remove_background: bool = False

class BulkBannerImagesRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    settings: BannerImageSettings

class BulkRestoreBannersRequest(BaseModel):
    account_id: int
    offer_ids: List[str]

# Product Cards schemas
class AttachmentType(str, Enum):
    MANUAL = "MANUAL"
    SPECIAL_OFFER_RULES = "SPECIAL_OFFER_RULES"
    COMPETITION_RULES = "COMPETITION_RULES"
    BOOK_EXCERPT = "BOOK_EXCERPT"
    USER_MANUAL = "USER_MANUAL"
    INSTALLATION_INSTRUCTIONS = "INSTALLATION_INSTRUCTIONS"
    GAME_INSTRUCTIONS = "GAME_INSTRUCTIONS"
    ENERGY_LABEL = "ENERGY_LABEL"
    PRODUCT_INFORMATION_SHEET = "PRODUCT_INFORMATION_SHEET"
    TIRE_LABEL = "TIRE_LABEL"
    SAFETY_INFORMATION_MANUAL = "SAFETY_INFORMATION_MANUAL"

class BulkGenerateProductCardsRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    strip_html: bool = True  # Deprecated: HTML stripping is now always done internally

class BulkDeleteAttachmentsRequest(BaseModel):
    account_id: int
    offer_ids: List[str]

class BulkRestoreAttachmentsRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    original_attachments: dict

class UploadCustomAttachmentRequest(BaseModel):
    account_id: int
    offer_ids: List[str]
    attachment_type: AttachmentType
    file_name: str
    file_content: str  # Base64 encoded file content

# Account Images schemas
class AccountImageBase(BaseModel):
    filename: str
    original_filename: str
    content_type: str
    size: int

class AccountImageCreate(AccountImageBase):
    pass

class AccountImage(AccountImageBase):
    id: int
    account_id: int
    url: str
    is_logo: bool = False
    is_filler: bool = False
    filler_position: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AccountImageUploadRequest(BaseModel):
    account_id: int

class AccountImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    url: str
    content_type: str
    size: int
    is_logo: bool = False
    is_filler: bool = False
    filler_position: Optional[int] = None
    created_at: datetime

class SetLogoRequest(BaseModel):
    account_id: int
    image_id: int

class SetFillerRequest(BaseModel):
    account_id: int
    image_ids: List[int]

class DeleteImagesRequest(BaseModel):
    account_id: int
    image_ids: List[int] 

# AI Configuration Schemas
class AIProviderInfo(BaseModel):
    """Information about available AI providers and models"""
    providers: Dict[str, List[Dict[str, str]]]  # {"anthropic": [{"id": "claude-3.5", "name": "Claude 3.5 Sonnet"}]}
    default_provider: str
    default_model: str

class AIConfigBase(BaseModel):
    ai_provider: str  # "anthropic" or "google"
    model_name: str
    api_key: str

class AIConfigCreate(AIConfigBase):
    """Create AI configuration with validation"""
    
    @validator('ai_provider')
    def validate_provider(cls, v):
        if v not in ['anthropic', 'google']:
            raise ValueError('Provider must be either "anthropic" or "google"')
        return v

class AIConfigUpdate(BaseModel):
    """Update AI configuration - all fields optional"""
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('ai_provider')
    def validate_provider(cls, v):
        if v is not None and v not in ['anthropic', 'google']:
            raise ValueError('Provider must be either "anthropic" or "google"')
        return v

class AIConfigResponse(BaseModel):
    """AI configuration response (without sensitive data)"""
    id: int
    ai_provider: str
    model_name: str
    is_active: bool
    last_validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TestAPIKeyRequest(BaseModel):
    """Request to test API key"""
    provider: str
    model_name: str
    api_key: str
    
    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['anthropic', 'google']:
            raise ValueError('Provider must be either "anthropic" or "google"')
        return v

class TestAPIKeyResponse(BaseModel):
    """Response from API key test"""
    is_valid: bool
    error_message: Optional[str] = None

class AIConfigStatus(BaseModel):
    """Status of user's AI configuration"""
    has_config: bool
    is_active: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None
    last_validated: Optional[datetime] = None
    can_use_default: bool = False  # True for vSprint employees
    default_provider: Optional[str] = None  # Provider used when no custom config
    default_model: Optional[str] = None  # Model used when no custom config

# Analytics and tracking schemas
class AITokenUsageResponse(BaseModel):
    """AI token usage record"""
    id: int
    user_id: int
    account_id: Optional[int] = None
    operation_type: str
    ai_provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_usd: str
    output_cost_usd: str
    total_cost_usd: str
    request_timestamp: datetime
    offer_id: Optional[str] = None
    template_id: Optional[int] = None
    batch_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class AIUsageDailyStatsResponse(BaseModel):
    """Daily aggregated AI usage stats"""
    id: int
    user_id: int
    date: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: str
    operations_breakdown: Optional[dict] = None
    
    class Config:
        from_attributes = True

class AIUsageSummary(BaseModel):
    """Summary of AI usage for a time period"""
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: str
    date_range: str
    operation_breakdown: dict
    daily_stats: List[AIUsageDailyStatsResponse]

class UserActivityLogResponse(BaseModel):
    """User activity log record"""
    id: int
    user_id: int
    action_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    session_id: Optional[str] = None
    account_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserSessionResponse(BaseModel):
    """User session record"""
    id: int
    user_id: int
    session_id: str
    session_start: datetime
    session_end: Optional[datetime] = None
    ip_address: Optional[str] = None
    login_method: Optional[str] = None
    activity_count: int
    last_activity: datetime
    
    class Config:
        from_attributes = True

class UserSummaryExtended(BaseModel):
    """Extended user summary with role, registration source, and key source"""
    user_id: int
    user_name: str
    user_email: str
    role: str
    registration_source: str
    key_source: Optional[str] = None  # 'company_default', 'user_custom', or 'none'
    activity_count: int
    ai_requests: int = 0
    cost: str = "0.00"
    last_activity: Optional[datetime] = None

class TeamActivitySummary(BaseModel):
    """Team activity summary for managers"""
    total_active_users: int
    total_operations_today: int
    total_cost_today: str
    recent_activities: List[UserActivityLogResponse]
    activities: List[UserActivityLogResponse]  # All activities (with limit)
    user_summaries: List[UserSummaryExtended]
    total_activities: int  # List of user activity summaries

class UsageExportRequest(BaseModel):
    """Request for usage data export"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: str = "csv"  # csv, pdf
    operation_type: Optional[str] = None

# Admin user management schemas
class AdminUserResponse(UserResponse):
    """Extended user info for admin management"""
    updated_at: Optional[datetime] = None

class UserApprovalRequest(BaseModel):
    """Request to approve or reject user"""
    user_id: int
    approved: bool
    rejection_reason: Optional[str] = None

class PendingUsersResponse(BaseModel):
    """List of users pending approval"""
    pending_users: List[AdminUserResponse]
    total_count: int

class UsersSearchRequest(BaseModel):
    """Request for searching and filtering users"""
    page: int = 1
    per_page: int = 25
    search: Optional[str] = None
    role_filter: Optional[str] = None  # "user", "admin", "vsprint_employee", or None for all
    status_filter: Optional[str] = None  # "active", "inactive", "verified", "unverified", "approved", "unapproved", or None for all

class UsersSearchResponse(BaseModel):
    """Paginated response for user search"""
    users: List[AdminUserResponse]
    total_count: int
    total_pages: int
    current_page: int
    per_page: int

class AdminNotificationEmailBase(BaseModel):
    """Base schema for admin notification emails"""
    email: EmailStr

class AdminNotificationEmailCreate(AdminNotificationEmailBase):
    """Create admin notification email"""
    pass

class AdminNotificationEmailResponse(AdminNotificationEmailBase):
    """Admin notification email response"""
    id: int
    is_active: bool
    created_at: datetime
    created_by_admin_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class AdminNotificationEmailsListRequest(BaseModel):
    """Request to update admin notification emails list"""
    emails: List[str]

class AdminNotificationEmailsListResponse(BaseModel):
    """Response with admin notification emails list"""
    emails: List[AdminNotificationEmailResponse]
    total_count: int

# ============================================================================
# MODULE PERMISSIONS SCHEMAS
# ============================================================================

class ModuleBase(BaseModel):
    """Base module schema"""
    name: str
    display_name: str
    route_pattern: str
    description: Optional[str] = None
    is_core: bool = False

class Module(ModuleBase):
    """Module response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserModulePermissionBase(BaseModel):
    """Base user module permission schema"""
    user_id: int
    module_id: int
    granted: bool = True

class UserModulePermission(UserModulePermissionBase):
    """User module permission response schema"""
    id: int
    granted_at: datetime
    granted_by_admin_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserModulePermissionWithModule(UserModulePermission):
    """User module permission with module details"""
    module: Module
    
    class Config:
        from_attributes = True

class ModulePermissionsRequest(BaseModel):
    """Request to update user module permissions"""
    permissions: Dict[str, bool]  # {module_name: granted}

class ModulePermissionsResponse(BaseModel):
    """Response with user module permissions"""
    permissions: Dict[str, bool]  # {module_name: granted}
    dependencies: Dict[str, List[str]]  # {module_name: [dependent_module_names]}

class UserWithPermissions(UserBase):
    """User with module permissions"""
    id: int
    is_active: bool
    is_verified: bool
    admin_approved: bool
    role: UserRole
    company_domain: Optional[str] = None
    google_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: Dict[str, bool]
    
    class Config:
        from_attributes = True

# User Management Schemas
class UserDeactivationRequest(BaseModel):
    """Request to deactivate a user"""
    reason: Optional[str] = None

class UserReactivationRequest(BaseModel):
    """Request to reactivate a user"""
    pass  # No additional fields needed

class UserDeletionRequest(BaseModel):
    """Request to delete a user"""
    reason: Optional[str] = None
    # For vsprint users - data transfer options
    keep_accounts: bool = True
    keep_templates: bool = True
    keep_images: bool = True

class UserManagementResponse(BaseModel):
    """Response for user management operations"""
    success: bool
    message: str
    user_email: str
    user_type: Optional[str] = None
    transferred_data: Optional[Dict[str, int]] = None
    archived_data: Optional[Dict[str, int]] = None
    action_timestamp: str

class UserManagementInfo(BaseModel):
    """User info for management operations"""
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_deactivated: bool
    deactivated_at: Optional[str] = None
    deactivation_reason: Optional[str] = None
    data_counts: Dict[str, Union[int, Dict[str, int]]]
    can_delete: bool
    can_deactivate: bool
    is_vsprint: bool

# Analytics Archive Schemas
class ArchivedUserInfo(BaseModel):
    """Info about deleted user with archived data"""
    display_name: str
    deleted_at: datetime
    deleted_by_admin_id: int
    archive_counts: Dict[str, int]

class ArchivedAnalyticsData(BaseModel):
    """Archived analytics data for a deleted user"""
    user_display_name: str
    token_usage_records: int
    daily_stats_records: int
    activity_log_records: int
    token_usage: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]

class TeamAnalyticsWithArchived(BaseModel):
    """Team analytics including archived user data"""
    active_users: List[Dict[str, Any]]
    archived_users: List[Dict[str, Any]]
    total_cost: str
    total_requests: int

# ============================================================================
# ASYSTENCIAI INTEGRATION SCHEMAS
# ============================================================================

class AsystenciaiUserData(BaseModel):
    """Data from asystenciai JWT token"""
    asystenciai_user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    email_verified: bool
    terms_accepted: bool
    iat: int
    exp: int

class AsystenciaiSetupRequest(BaseModel):
    """Request to setup account from asystenciai"""
    setup_token: str
    first_name: str
    last_name: str
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Hasło musi mieć co najmniej 8 znaków')
        return v

class AsystenciaiSetupResponse(BaseModel):
    """Response from setup completion"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    redirect_url: str
    user: UserResponse

class SetupTokenData(BaseModel):
    """Data encoded in setup token"""
    asystenciai_user_id: int
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    terms_accepted: bool
    iat: int
    exp: int

# Price Scheduling Schemas
class PriceScheduleCreate(BaseModel):
    """Schema for creating a price schedule"""
    account_id: int
    offer_id: str
    offer_name: str
    sku: Optional[str] = None
    scheduled_price: str
    schedule_type: str = 'hourly'  # 'hourly' | 'daily'
    schedule_config: Optional[Dict[str, List[int]]] = None  # For 'hourly' type
    daily_schedule_config: Optional[Dict[str, List[int]]] = None  # For 'daily' type: {"days": [1,3,5...]}

class PriceScheduleUpdate(BaseModel):
    """Schema for updating a price schedule"""
    scheduled_price: Optional[str] = None
    schedule_config: Optional[Dict[str, List[int]]] = None
    is_active: Optional[bool] = None

class PriceScheduleResponse(BaseModel):
    """Schema for price schedule response"""
    id: int
    account_id: int
    offer_id: str
    offer_name: Optional[str]
    sku: Optional[str]
    original_price: str
    scheduled_price: str
    schedule_type: str
    schedule_config: Optional[Dict[str, List[int]]]
    daily_schedule_config: Optional[Dict[str, List[int]]]
    is_active: bool
    current_price_state: str
    last_price_check: Optional[datetime]
    last_price_update: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PriceChangeLogResponse(BaseModel):
    """Schema for price change log response"""
    id: int
    schedule_id: Optional[int]
    account_id: int
    offer_id: str
    price_before: str
    price_after: str
    change_reason: str
    success: bool
    error_message: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True

class ActiveOffersResponse(BaseModel):
    """Schema for active offers response"""
    offers: List[Dict[str, Any]]
    count: int

# ============ System Config Schemas ============

class SystemConfigBase(BaseModel):
    """Base schema for system configuration."""
    config_key: str
    config_value: str
    description: Optional[str] = None

class SystemConfigResponse(SystemConfigBase):
    """Response schema for system configuration with metadata."""
    id: int
    updated_at: datetime
    updated_by_user_id: Optional[int]
    
    class Config:
        from_attributes = True

class SystemConfigUpdate(BaseModel):
    """Schema for updating system configuration."""
    webhook_url: str

# AI Title Optimization Schemas
class TitleToOptimize(BaseModel):
    """Single title to optimize"""
    offer_id: str
    current_title: str

class OptimizedTitleResult(BaseModel):
    """Result of AI title optimization"""
    offer_id: str
    current_title: str
    optimized_title: str
    analysis: Optional[str] = None
    character_count: int
    success: bool = True
    error: Optional[str] = None

class OptimizeTitlesAIRequest(BaseModel):
    """Request for AI title optimization"""
    account_id: int
    titles: List[TitleToOptimize]
    include_offer_parameters: bool = False

class OptimizeTitlesAIResponse(BaseModel):
    """Response from AI title optimization"""
    results: List[OptimizedTitleResult]
    total_processed: int
    successful: int
    failed: int


# AI Configuration Schemas for Admin Panel
class AIPromptConfig(BaseModel):
    """Configuration for AI prompts and parameters (Titles module)"""
    prompt: str
    temperature: float
    max_output_tokens: int
    top_p: float
    top_k: Optional[int] = None
    stop_sequences: List[str] = []


class AIConfigUpdateRequest(BaseModel):
    """Request to update AI configuration for Titles"""
    provider: Literal["anthropic", "gemini"]
    config: Dict[str, Any]  # AIPromptConfig


class AdminAIConfigResponse(BaseModel):
    """Response with all AI configurations for admin panel"""
    titles: Dict[str, Dict[str, Any]]  # provider -> config

# Import/Export Schemas for Daily Schedules
class ScheduleImportRow(BaseModel):
    """Schema for validating a single row from import file"""
    offer_id: str
    sku: Optional[str] = None
    offer_name: str
    scheduled_price: str
    days: List[int]  # List of day numbers (1-31) where promotion is active

    @validator('scheduled_price')
    def validate_price(cls, v):
        try:
            price = float(v)
            if price <= 0:
                raise ValueError('Price must be positive')
            return f"{price:.2f}"
        except ValueError:
            raise ValueError(f'Invalid price format: {v}')

    @validator('days')
    def validate_days(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one day must be selected')
        for day in v:
            if not isinstance(day, int) or day < 1 or day > 31:
                raise ValueError(f'Invalid day number: {day}. Must be between 1-31')
        return sorted(list(set(v)))  # Remove duplicates and sort

class ScheduleImportError(BaseModel):
    """Schema for import validation error"""
    row: int
    offer_id: str
    error: str

class ScheduleImportResponse(BaseModel):
    """Schema for import response"""
    success: bool
    message: str
    imported_count: Optional[int] = None
    deleted_count: Optional[int] = None
    errors: Optional[List[ScheduleImportError]] = None