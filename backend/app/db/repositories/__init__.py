"""
Repository Layer - Domain-based database operations.

Repositories organize CRUD operations by business domain rather than by database table.
Each repository is responsible for all database operations related to a specific domain.

Usage:
    from app.db.repositories import UserRepository, AccountRepository
    
    user = UserRepository.get_by_id(db, user_id)
    account = AccountRepository.get_by_id(db, account_id)
"""
from .user_repository import UserRepository
from .account_repository import AccountRepository
from .template_repository import TemplateRepository
from .permission_repository import PermissionRepository
from .ai_config_repository import AIConfigRepository
from .backup_repository import BackupRepository
from .admin_repository import AdminRepository
from .system_config_repository import SystemConfigRepository
from .external_integration_repository import ExternalIntegrationRepository

__all__ = [
    'UserRepository',
    'AccountRepository',
    'TemplateRepository',
    'PermissionRepository',
    'AIConfigRepository',
    'BackupRepository',
    'AdminRepository',
    'SystemConfigRepository',
    'ExternalIntegrationRepository',
]
