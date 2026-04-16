from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, Enum, UniqueConstraint, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import or_, and_, exists
from .session import Base
import enum

class UserRole(enum.Enum):
    user = "user"
    admin = "admin"
    vsprint_employee = "vsprint_employee"

class RegistrationSource(enum.Enum):
    web = "web"
    asystenciai = "asystenciai"

class AIProvider(enum.Enum):
    anthropic = "anthropic"
    google = "google"

class KeySource(enum.Enum):
    user_custom = "user_custom"
    company_default = "company_default"

class MarketplaceType(str, enum.Enum):
    allegro = "allegro"
    amazon = "amazon"
    emag = "emag"
    kaufland = "kaufland"
    decathlon = "decathlon"
    castorama = "castorama"
    leroymerlin = "leroymerlin"

class AnthropicModel(enum.Enum):
    # Claude 4.5 Models
    claude_4_5_sonnet = "claude-sonnet-4-5-20250929"

    # Claude 4.1 Models
    claude_4_1_opus = "claude-opus-4-1-20250805"

    # Claude 4 Models
    claude_4_opus = "claude-opus-4-20250514"
    claude_4_sonnet = "claude-sonnet-4-20250514"
    
    # Claude 3.7 Models
    claude_3_7_sonnet = "claude-3-7-sonnet-20250219"
    
    # Claude 3.5 Models
    claude_3_5_haiku = "claude-3-5-haiku-20241022"

class GeminiModel(enum.Enum):
    # Gemini 2.5 Models
    gemini_2_5_pro = "gemini-2.5-pro"
    gemini_2_5_flash = "gemini-2.5-flash"
    gemini_2_5_flash_lite = "gemini-2.5-flash-lite-preview-06-17"
    
    # Gemini 2.0 Models
    gemini_2_0_flash = "gemini-2.0-flash"
    gemini_2_0_flash_lite = "gemini-2.0-flash-lite"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # nullable for Google SSO users
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    admin_approved = Column(Boolean, default=False)  # Admin approval for non-vsprint users
    role = Column(Enum(UserRole), default=UserRole.user)
    company_domain = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True)  # for SSO
    registration_source = Column(Enum(RegistrationSource), default=RegistrationSource.web)
    external_user_id = Column(String(255), nullable=True, index=True)  # ID from external system (asystenciai)
    # User management fields
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_by_admin_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    deactivation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships with cascade delete for security
    allegro_accounts = relationship("UserMarketplaceAccount", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    ai_config = relationship("UserAIConfig", back_populates="user", cascade="all, delete-orphan", uselist=False)
    module_permissions = relationship("UserModulePermission", foreign_keys="UserModulePermission.user_id", back_populates="user", cascade="all, delete-orphan")

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="email_verifications")

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="password_resets")

class UserMarketplaceAccount(Base):
    __tablename__ = "user_marketplace_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    is_owner = Column(Boolean, default=True)  # owner vs shared access
    shared_with_vsprint = Column(Boolean, default=False)  # shared with team
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="allegro_accounts")
    account = relationship("Account", back_populates="user_associations")
    
    # Unique user-account connection
    __table_args__ = (UniqueConstraint('user_id', 'account_id'),)

# Backward compatibility alias
UserAllegroAccount = UserMarketplaceAccount

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    nazwa_konta = Column(String, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)  # Access token expiry (12 hours)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)  # Refresh token expiry (3 months)
    needs_reauth = Column(Boolean, default=False, index=True)  # Flag for accounts needing re-authentication
    last_token_refresh = Column(DateTime(timezone=True), nullable=True)  # Last successful token refresh
    marketplace_type = Column(Enum(MarketplaceType), nullable=False, server_default='allegro', index=True)
    marketplace_specific_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    backups = relationship("OfferBackup", back_populates="account")
    user_associations = relationship("UserMarketplaceAccount", back_populates="account", cascade="all, delete-orphan")
    images = relationship("AccountImage", back_populates="account", cascade="all, delete-orphan")

class Template(Base):
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey('users.id'))  # User who created the template
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)  # Account the template belongs to
    prompt = Column(String)

    owner = relationship("User")
    account = relationship("Account")
    
    # Unique constraint: template names must be unique per account
    __table_args__ = (UniqueConstraint('name', 'account_id', name='uq_template_name_account_id'),)

class OfferBackup(Base):
    __tablename__ = 'offer_backups'
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(String, index=True, nullable=False)
    backup_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)

    account = relationship("Account", back_populates="backups")

class AccountImage(Base):
    __tablename__ = 'account_images'
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    filename = Column(String, nullable=False)  # Generated filename in MinIO
    original_filename = Column(String, nullable=False)  # Original uploaded filename
    url = Column(String, nullable=False)  # MinIO public URL
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    is_logo = Column(Boolean, default=False)
    is_filler = Column(Boolean, default=False)
    filler_position = Column(Integer, nullable=True)  # Position number for filler images
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    account = relationship("Account", back_populates="images")

class UserAIConfig(Base):
    __tablename__ = 'user_ai_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    ai_provider = Column(Enum(AIProvider), nullable=False)
    model_name = Column(String, nullable=False)  # Store model string directly for flexibility
    encrypted_api_key = Column(Text, nullable=False)  # Encrypted API key
    is_active = Column(Boolean, default=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)  # When API key was last tested
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="ai_config")

class AITokenUsage(Base):
    __tablename__ = 'ai_token_usage'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    operation_type = Column(String, nullable=False)  # offer_update, bulk_update, template_generation, etc.
    ai_provider = Column(Enum(AIProvider), nullable=False)
    model_name = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    input_cost_usd = Column(String, nullable=False)  # Using String for precise decimal representation
    output_cost_usd = Column(String, nullable=False)
    total_cost_usd = Column(String, nullable=False)
    pricing_version = Column(String, nullable=True)  # Track which pricing was used
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    offer_id = Column(String, nullable=True)  # For offer-specific operations
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=True)
    batch_id = Column(String, nullable=True)  # For bulk operations
    key_source = Column(Enum(KeySource), nullable=True, index=True)  # Track if company or user key was used
    
    # Relationships
    user = relationship("User")
    account = relationship("Account")
    template = relationship("Template")

class AIUsageDailyStats(Base):
    __tablename__ = 'ai_usage_daily_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(String, nullable=False, index=True)  # YYYY-MM-DD format
    total_requests = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(String, default='0.00')  # Using String for precise decimal representation
    operations_breakdown = Column(JSON, nullable=True)  # {operation_type: count}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User")
    
    # Unique constraint: one record per user per day
    __table_args__ = (UniqueConstraint('user_id', 'date', name='uq_user_daily_stats'),)

class UserActivityLog(Base):
    __tablename__ = 'user_activity_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action_type = Column(String, nullable=False, index=True)  # login, offer_update, template_create, etc.
    resource_type = Column(String, nullable=True)  # account, template, offer, image, etc.
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)  # Operation-specific data
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    session_id = Column(String, nullable=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)  # Which account was being worked on
    
    # Relationships
    user = relationship("User")
    account = relationship("Account")

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String, nullable=False, unique=True, index=True)
    session_start = Column(DateTime(timezone=True), server_default=func.now())
    session_end = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    login_method = Column(String, nullable=True)  # password, google_sso
    activity_count = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")

class AdminNotificationEmail(Base):
    __tablename__ = "admin_notification_emails"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_admin_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    created_by = relationship("User")

class Module(Base):
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # e.g., 'allegro_edytor_ofert', 'decathlon_wystawianie_ofert'
    display_name = Column(String, nullable=False)  # 'Edytor Ofert', 'Kopiowanie Ofert'
    route_pattern = Column(String, nullable=False)  # '/offer-editor', '/copy-offers'
    description = Column(Text, nullable=True)
    is_core = Column(Boolean, default=False)  # Dashboard, Konta Marketplace, Profil always accessible
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_permissions = relationship("UserModulePermission", back_populates="module", cascade="all, delete-orphan")
    parent_dependencies = relationship("ModuleDependency", foreign_keys="ModuleDependency.parent_module_id", back_populates="parent_module", cascade="all, delete-orphan")
    child_dependencies = relationship("ModuleDependency", foreign_keys="ModuleDependency.dependent_module_id", back_populates="dependent_module", cascade="all, delete-orphan")

class UserModulePermission(Base):
    __tablename__ = "user_module_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    granted = Column(Boolean, default=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by_admin_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="module_permissions")
    module = relationship("Module", back_populates="user_permissions")
    granted_by = relationship("User", foreign_keys=[granted_by_admin_id])
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('user_id', 'module_id'),)

# Archive tables for deleted user analytics
class AITokenUsageArchive(Base):
    __tablename__ = "ai_token_usage_archive"
    
    id = Column(Integer, primary_key=True, index=True)
    original_id = Column(Integer, nullable=False, index=True)  # Original record ID
    user_id = Column(Integer, nullable=False)  # Original user_id (now deleted)
    account_id = Column(Integer, nullable=True)
    operation_type = Column(String, nullable=False)
    ai_provider = Column(Enum(AIProvider), nullable=False)
    model_name = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    input_cost_usd = Column(String, nullable=False)
    output_cost_usd = Column(String, nullable=False)
    total_cost_usd = Column(String, nullable=False)
    pricing_version = Column(String, nullable=True)
    request_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    offer_id = Column(String, nullable=True)
    template_id = Column(Integer, nullable=True)
    batch_id = Column(String, nullable=True)
    
    # Deletion metadata
    deleted_user_display_name = Column(String, nullable=False)
    deleted_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_by_admin_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    deleted_by = relationship("User")

class AIUsageDailyStatsArchive(Base):
    __tablename__ = "ai_usage_daily_stats_archive"
    
    id = Column(Integer, primary_key=True, index=True)
    original_id = Column(Integer, nullable=False, index=True)  # Original record ID
    user_id = Column(Integer, nullable=False)  # Original user_id (now deleted)
    date = Column(String, nullable=False, index=True)  # YYYY-MM-DD format
    total_requests = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost_usd = Column(String, default='0.00')
    operations_breakdown = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Deletion metadata
    deleted_user_display_name = Column(String, nullable=False)
    deleted_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_by_admin_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    deleted_by = relationship("User")

class UserActivityLogArchive(Base):
    __tablename__ = "user_activity_logs_archive"
    
    id = Column(Integer, primary_key=True, index=True)
    original_id = Column(Integer, nullable=False, index=True)  # Original record ID
    user_id = Column(Integer, nullable=False)  # Original user_id (now deleted)
    action_type = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    account_id = Column(Integer, nullable=True)
    
    # Deletion metadata
    deleted_user_display_name = Column(String, nullable=False)
    deleted_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_by_admin_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    deleted_by = relationship("User")

class ModuleDependency(Base):
    __tablename__ = "module_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    dependent_module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    parent_module = relationship("Module", foreign_keys=[parent_module_id], back_populates="parent_dependencies")
    dependent_module = relationship("Module", foreign_keys=[dependent_module_id], back_populates="child_dependencies")
    
    # Unique constraint and prevent self-reference
    __table_args__ = (
        UniqueConstraint('parent_module_id', 'dependent_module_id'),
    )

class PriceSchedule(Base):
    __tablename__ = "price_schedules"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    offer_id = Column(String, nullable=False, index=True)
    offer_name = Column(String, nullable=True)  # Cached for display
    sku = Column(String, nullable=True, index=True)  # SKU/EAN code (optional)

    # Price storage
    original_price = Column(String, nullable=False)    # "XX.XX" - captured at creation
    scheduled_price = Column(String, nullable=False)   # "XX.XX" - user input

    # Schedule type: 'hourly' (weekly hours) or 'daily' (month days)
    schedule_type = Column(String, default='hourly', nullable=False)  # 'hourly' | 'daily'

    # Schedule configuration (flexible per-day hours)
    # Format: {"monday": [8, 9, 10, ...], "tuesday": [10, 11, ...], ...}
    schedule_config = Column(JSON, nullable=True)  # Used for 'hourly' type

    # Daily schedule configuration (for 'daily' type)
    # Format: {"days": [1, 3, 5, 15, 20, 31]}
    daily_schedule_config = Column(JSON, nullable=True)  # Used for 'daily' type

    # State tracking
    is_active = Column(Boolean, default=True)
    current_price_state = Column(String, default='original')  # 'original' or 'scheduled'
    last_price_check = Column(DateTime(timezone=True), nullable=True)
    last_price_update = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    account = relationship("Account")
    change_logs = relationship("PriceChangeLog", back_populates="schedule", cascade="all, delete-orphan")

class PriceChangeLog(Base):
    __tablename__ = "price_change_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey('price_schedules.id'), nullable=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    offer_id = Column(String, nullable=False, index=True)

    # Price tracking
    price_before = Column(String, nullable=False)
    price_after = Column(String, nullable=False)
    change_reason = Column(String, nullable=False)  # 'schedule_activated', 'schedule_deactivated', 'manual_restore'

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    allegro_response = Column(JSON, nullable=True)  # Store API response for debugging

    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    schedule = relationship("PriceSchedule", back_populates="change_logs")
    account = relationship("Account")

class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    offer_id = Column(String, nullable=False, index=True)
    price = Column(String, nullable=False)
    snapshot_reason = Column(String, nullable=False)  # 'schedule_created', 'periodic_backup', 'manual'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    account = relationship("Account")

    __table_args__ = (Index('idx_offer_snapshot', 'offer_id', 'created_at'),)


class SystemConfig(Base):
    """System-wide configuration stored in database for runtime modification."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, index=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationship
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])