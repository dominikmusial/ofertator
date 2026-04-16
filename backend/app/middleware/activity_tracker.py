"""
Activity tracking middleware for logging user actions.
"""

import logging
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import json
import time
from datetime import datetime
import uuid

from app.db.session import SessionLocal
from app.db.repositories import UserRepository
from app.services.analytics_service import AnalyticsService
from app.core.auth import get_current_user_optional
from app.db.session import get_db

logger = logging.getLogger(__name__)

class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track user activities"""
    
    # Actions that should be tracked
    TRACKED_ACTIONS = {
        # Authentication
        'POST /api/v1/auth/login': 'user_login',
        'POST /api/v1/auth/logout': 'user_logout',
        'POST /api/v1/auth/register': 'user_register',
        'POST /api/v1/auth/google-login': 'user_google_login',
        'POST /api/v1/auth/verify-email/{token}': 'email_verify',
        'POST /api/v1/auth/google-callback': 'user_google_callback',
        'POST /api/v1/auth/resend-verification': 'email_resend_verification',
        'POST /api/v1/auth/forgot-password': 'password_forgot',
        'POST /api/v1/auth/reset-password': 'password_reset',
        'POST /api/v1/auth/change-password': 'password_change',
        'DELETE /api/v1/auth/delete-account': 'account_delete_user',
        
        # Account Management (Allegro)
        'POST /api/v1/allegro/auth/start': 'allegro_auth_start',
        'POST /api/v1/allegro/refresh-token/{account_id}': 'allegro_token_refresh',
        'DELETE /api/v1/accounts/{account_id}': 'allegro_account_delete',
        'POST /api/v1/accounts/share': 'allegro_account_share',
        
        # Templates (Allegro-specific)
        'POST /api/v1/allegro/templates/': 'template_create',
        'PUT /api/v1/allegro/templates/{template_id}': 'template_update',
        'DELETE /api/v1/allegro/templates/{template_id}': 'template_delete',
        'POST /api/v1/allegro/templates/copy': 'template_copy',
        'POST /api/v1/allegro/templates/copy-with-name': 'template_copy_named',
        
        # Offers - Core Operations (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-update-with-template': 'offer_bulk_update_template',
        'POST /api/v1/allegro/offers/bulk-restore': 'offer_bulk_restore',
        'POST /api/v1/allegro/offers/{offer_id}/restore-backup': 'offer_restore_backup',
        'POST /api/v1/allegro/offers/copy': 'offer_copy',
        'POST /api/v1/allegro/offers/{offer_id}/generate-pdf': 'offer_generate_pdf',
        
        # Offers - Title Management (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-edit-titles': 'titles_bulk_edit',
        'POST /api/v1/allegro/offers/pull-titles': 'titles_pull_from_allegro',
        'POST /api/v1/allegro/offers/duplicate-offers-with-titles': 'titles_duplicate_offers',
        
        # Offers - Status Management (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-change-status': 'offers_status_change',
        
        # Offers - Advanced Operations (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-edit': 'offers_bulk_edit',
        'POST /api/v1/allegro/offers/bulk-replace-image': 'offers_image_replace',
        'POST /api/v1/allegro/offers/bulk-manage-description-image': 'offers_description_image_manage',
        'POST /api/v1/allegro/offers/bulk-composite-image-replace': 'offers_composite_image_replace',
        'POST /api/v1/allegro/offers/bulk-restore-image-position': 'offers_image_position_restore',
        
        # Offers - Thumbnails (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-update-thumbnails': 'thumbnails_bulk_update',
        'POST /api/v1/allegro/offers/restore-thumbnails': 'thumbnails_restore',
        
        # Offers - Banners (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-banner-images': 'banners_bulk_generate',
        'POST /api/v1/allegro/offers/bulk-restore-banners': 'banners_bulk_restore',
        
        # Offers - Product Cards (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-generate-product-cards': 'product_cards_bulk_generate',
        
        # Offers - Attachments (Allegro-specific)
        'POST /api/v1/allegro/offers/bulk-delete-attachments': 'attachments_bulk_delete',
        'POST /api/v1/allegro/offers/bulk-restore-attachments': 'attachments_bulk_restore',
        'POST /api/v1/allegro/offers/upload-custom-attachment': 'attachment_custom_upload',
        
        # Offers - Saved Images Operations (Allegro-specific)
        'DELETE /api/v1/allegro/offers/saved-images/{account_id}/delete/{image_type}/{offer_id}/{filename}': 'saved_images_delete',
        'POST /api/v1/allegro/offers/saved-images/{account_id}/bulk-download/{image_type}': 'saved_images_bulk_download',
        'POST /api/v1/allegro/offers/saved-images/{account_id}/bulk-delete/{image_type}': 'saved_images_bulk_delete',
        
        # Images - Core Operations (Allegro-specific, but also mounted at /images for backward compat)
        'POST /api/v1/allegro/images/upload': 'image_upload_general',
        'POST /api/v1/allegro/images/process': 'image_process',
        'POST /api/v1/allegro/images/account/{account_id}/upload': 'image_upload_account',
        'POST /api/v1/allegro/images/account/{account_id}/check-duplicates': 'image_check_duplicates',
        'POST /api/v1/images/account/{account_id}/upload': 'image_upload_account',  # Backward compat
        
        # Images - Account Management (Allegro-specific, but also mounted at /images for backward compat)
        'POST /api/v1/allegro/images/account/{account_id}/set-logo': 'account_logo_set',
        'POST /api/v1/allegro/images/account/{account_id}/unset-logo': 'account_logo_unset',
        'POST /api/v1/allegro/images/account/{account_id}/set-fillers': 'account_fillers_set',
        'POST /api/v1/allegro/images/account/{account_id}/unset-fillers': 'account_fillers_unset',
        'DELETE /api/v1/allegro/images/account/{account_id}/images': 'account_images_delete',
        'DELETE /api/v1/images/account/{account_id}/images': 'account_images_delete',  # Backward compat
        
        # Promotions (Allegro-specific)
        'POST /api/v1/allegro/promotions/': 'promotion_create',
        'DELETE /api/v1/allegro/promotions/{promotion_id}': 'promotion_delete',
        'POST /api/v1/allegro/promotions/bundles/grouped': 'promotion_bundle_create',
        'DELETE /api/v1/allegro/promotions/bundles/{promotion_id}': 'promotion_bundle_delete',
        'DELETE /api/v1/allegro/promotions/bundles/all': 'promotion_bundles_delete_all',
        
        # AI Configuration
        'POST /api/v1/ai-config/test-key': 'ai_config_test_key',
        'POST /api/v1/ai-config/config': 'ai_config_create',
        'PUT /api/v1/ai-config/config': 'ai_config_update',
        'DELETE /api/v1/ai-config/config': 'ai_config_delete',
        'POST /api/v1/ai-config/config/deactivate': 'ai_config_deactivate',
        'POST /api/v1/ai-config/config/activate': 'ai_config_activate',
        
        # Analytics Maintenance
        'POST /api/v1/analytics/maintenance/cleanup-old-data': 'analytics_cleanup',
    }
    
    # Endpoints to skip tracking (too noisy)
    SKIP_TRACKING = {
        '/api/v1/auth/me',
        '/api/v1/auth/refresh-token',
        '/health',
        '/docs',
        '/openapi.json',
        '/analytics/',  # Skip analytics endpoints to avoid recursion
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Skip tracking for certain endpoints
        if any(skip_path in str(request.url.path) for skip_path in self.SKIP_TRACKING):
            return await call_next(request)
        
        # Get user information
        user = None
        session_id = None
        try:
            # Try to get user from request
            user = await self._get_user_from_request(request)
            session_id = self._get_session_id(request)
        except Exception as e:
            logger.debug(f"Could not get user from request: {e}")
        
        # Process the request
        response = await call_next(request)
        
        # Only track successful actions (2xx status codes) for authenticated users
        if user and 200 <= response.status_code < 300:
            try:
                await self._log_activity(request, response, user, session_id, start_time)
            except Exception as e:
                logger.error(f"Failed to log activity: {e}")
        
        return response
    
    async def _get_user_from_request(self, request: Request):
        """Extract user from request headers"""
        try:
            from fastapi.security import HTTPBearer
            from app.core.auth import get_current_user_optional
            from app.db.session import get_db
            
            # Get authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Verify token and get user
            from app.core.security import verify_token
            payload = verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Get user from database
            db = SessionLocal()
            try:
                user = UserRepository.get_by_id(db, int(user_id))
                return user
            finally:
                db.close()
                
        except Exception as e:
            logger.debug(f"Error getting user from request: {e}")
            return None
    
    def _get_session_id(self, request: Request) -> str:
        """Get or generate session ID"""
        # Try to get from headers first
        session_id = request.headers.get("x-session-id")
        if session_id:
            return session_id
        
        # Generate new session ID
        return str(uuid.uuid4())
    
    async def _log_activity(self, request: Request, response: Response, user, session_id: str, start_time: float):
        """Log the user activity"""
        try:
            # Determine action type
            method_path = f"{request.method} {request.url.path}"
            action_type = self._get_action_type(method_path, request.url.path)
            
            if not action_type:
                return  # Skip if not a tracked action
            
            # Extract resource information
            resource_type, resource_id = self._extract_resource_info(request, action_type)
            
            # Get request details
            details = await self._get_request_details(request, response, start_time)
            
            # Get client information
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent")
            
            # Extract account_id if present in the request
            account_id = await self._extract_account_id(request)
            
            # Log the activity
            db = SessionLocal()
            try:
                AnalyticsService.log_user_activity(
                    db=db,
                    user_id=user.id,
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    account_id=account_id
                )
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
    
    def _get_action_type(self, method_path: str, url_path: str) -> str:
        """Determine action type from method and path"""
        # Check exact matches first
        if method_path in self.TRACKED_ACTIONS:
            return self.TRACKED_ACTIONS[method_path]
        
        # Check for pattern matches
        for pattern, action in self.TRACKED_ACTIONS.items():
            if self._path_matches_pattern(method_path, pattern):
                return action
        
        return None
    
    def _path_matches_pattern(self, actual_path: str, pattern: str) -> bool:
        """Check if actual path matches pattern with wildcards"""
        # Handle patterns with IDs like /api/v1/templates/123
        actual_parts = actual_path.split('/')
        pattern_parts = pattern.split('/')
        
        if len(actual_parts) != len(pattern_parts):
            return False
        
        for actual, pattern_part in zip(actual_parts, pattern_parts):
            # Exact match
            if pattern_part == actual:
                continue
            # Pattern with parameter like {offer_id} or {template_id}
            elif pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue
            # Numeric ID in actual path
            elif actual.isdigit():
                continue
            else:
                return False
        
        return True
    
    def _extract_resource_info(self, request: Request, action_type: str) -> tuple:
        """Extract resource type and ID from request"""
        path_parts = request.url.path.split('/')
        
        # Common resource mappings
        resource_mappings = {
            'template_': 'template',
            'offer_': 'offer',
            'account_': 'account',
            'image_': 'image',
            'promotion_': 'promotion'
        }
        
        # Determine resource type from action
        resource_type = None
        for prefix, res_type in resource_mappings.items():
            if action_type.startswith(prefix):
                resource_type = res_type
                break
        
        # Try to extract ID from path
        resource_id = None
        if len(path_parts) > 3 and path_parts[-1].isdigit():
            resource_id = path_parts[-1]
        
        return resource_type, resource_id
    
    async def _get_request_details(self, request: Request, response: Response, start_time: float) -> dict:
        """Get additional request details"""
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        details = {
            'duration_ms': duration_ms,
            'status_code': response.status_code,
            'method': request.method,
            'path': str(request.url.path)
        }
        
        # Add query parameters if present
        if request.query_params:
            details['query_params'] = dict(request.query_params)
        
        # Add specific details based on action type
        try:
            if request.method == "POST" and request.headers.get("content-type", "").startswith("application/json"):
                # Don't read body for large requests
                content_length = request.headers.get("content-length")
                if content_length and int(content_length) < 1024:  # Only for small requests
                    body = await request.body()
                    if body:
                        details['request_size'] = len(body)
        except Exception:
            pass  # Ignore errors reading request body
        
        return details
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _extract_account_id(self, request: Request) -> int:
        """Extract account_id from request if present"""
        try:
            # Check query parameters
            account_id = request.query_params.get("account_id")
            if account_id and account_id.isdigit():
                return int(account_id)
            
            # Check path parameters
            path_parts = request.url.path.split('/')
            for i, part in enumerate(path_parts):
                if part == "accounts" and i + 1 < len(path_parts) and path_parts[i + 1].isdigit():
                    return int(path_parts[i + 1])
            
            # Try to extract from request body (for POST requests)
            if request.method == "POST":
                try:
                    content_type = request.headers.get("content-type", "")
                    if content_type.startswith("application/json"):
                        body = await request.body()
                        if body:
                            data = json.loads(body)
                            if isinstance(data, dict) and "account_id" in data:
                                return int(data["account_id"])
                except Exception:
                    pass
            
        except Exception as e:
            logger.debug(f"Error extracting account_id: {e}")
        
        return None
