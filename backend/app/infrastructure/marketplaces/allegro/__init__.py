"""
Allegro marketplace provider.

Exports commonly used functions and classes for easy access.
"""
from .client import AllegroMarketplaceClient
from .auth import (
    start_device_flow,
    get_token_from_device_code,
    refresh_allegro_token,
    get_user_info
)
from .api import (
    get_offer_details,
    create_product_offer,
    update_offer,
    update_offer_title,
    list_offers,
    upload_image,
    get_categories
)
from .html_sanitizer import sanitize_html_content
from .template_processor import process_template_sections_for_offer
from .price_operations import (
    get_offer_price,
    update_offer_price,
    fetch_active_offers
)
from .offer_operations import (
    update_offer_status,
    bulk_edit_offers,
    update_offer_attachments
)
from .error_handler import (
    get_polish_error_message,
    parse_allegro_api_error,
    handle_parameter_validation_error
)
from . import promotion_service

__all__ = [
    'AllegroMarketplaceClient',
    # Auth
    'start_device_flow',
    'get_token_from_device_code',
    'refresh_allegro_token',
    'get_user_info',
    # API
    'get_offer_details',
    'create_product_offer',
    'update_offer',
    'update_offer_title',
    'list_offers',
    'upload_image',
    'get_categories',
    # HTML
    'sanitize_html_content',
    # Template
    'process_template_sections_for_offer',
    # Price
    'get_offer_price',
    'update_offer_price',
    'fetch_active_offers',
    # Offer operations
    'update_offer_status',
    'bulk_edit_offers',
    'update_offer_attachments',
    # Error handling
    'get_polish_error_message',
    'parse_allegro_api_error',
    'handle_parameter_validation_error',
    # Promotions
    'promotion_service',
]
