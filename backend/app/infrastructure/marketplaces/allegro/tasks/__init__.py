"""
Allegro Celery Tasks

This module exports all Allegro-specific Celery tasks organized by category.
Currently migrated tasks are imported from their respective modules.
Remaining tasks will be migrated incrementally.
"""

# Auth tasks
from .auth_tasks import allegro_auth_task

# Price tasks  
from .price_tasks import (
    check_and_update_prices_task,
    check_and_update_prices_daily_task,
)

# Storage tasks
from .storage_tasks import (
    bulk_download_saved_images_task,
    bulk_delete_saved_images_task,
)

# Attachment tasks
from .attachment_tasks import (
    bulk_delete_attachments_task,
    bulk_restore_attachments_task,
    upload_custom_attachment_task,
)

# Title tasks
from .title_tasks import (
    update_offer_title_task,
    batch_log_title_updates_callback,
    batch_duplicate_offers_callback,
    pull_titles_task,
    optimize_titles_ai_task,
)

# Offer tasks
from .offer_tasks import (
    update_offer_task,
    duplicate_offer_with_title_task,
    update_offer_status_task,
    copy_offer_task,
    restore_offer_from_backup_task,
    generate_pdf_task,
    bulk_edit_task,
    bulk_update_offers_with_template_task,
)

# Image tasks
from .image_tasks import (
    bulk_replace_image_task,
    bulk_manage_description_image_task,
    bulk_update_thumbnails_task,
    restore_thumbnail_task,
    bulk_composite_image_replace_task,
    bulk_restore_image_position_task,
    bulk_banner_images_task,
    bulk_restore_banners_task,
    bulk_generate_product_cards_task,
)


__all__ = [
    # Auth
    'allegro_auth_task',
    
    # Price
    'check_and_update_prices_task',
    'check_and_update_prices_daily_task',
    
    # Storage
    'bulk_download_saved_images_task',
    'bulk_delete_saved_images_task',
    
    # Attachment
    'bulk_delete_attachments_task',
    'bulk_restore_attachments_task',
    'upload_custom_attachment_task',
    
    # Title
    'update_offer_title_task',
    'batch_log_title_updates_callback',
    'batch_duplicate_offers_callback',
    'pull_titles_task',
    'optimize_titles_ai_task',
    
    # Offer
    'update_offer_task',
    'duplicate_offer_with_title_task',
    'update_offer_status_task',
    'copy_offer_task',
    'restore_offer_from_backup_task',
    'generate_pdf_task',
    'bulk_edit_task',
    'bulk_update_offers_with_template_task',
    
    # Image
    'bulk_replace_image_task',
    'bulk_manage_description_image_task',
    'bulk_update_thumbnails_task',
    'restore_thumbnail_task',
    'bulk_composite_image_replace_task',
    'bulk_restore_image_position_task',
    'bulk_banner_images_task',
    'bulk_restore_banners_task',
    'bulk_generate_product_cards_task',
]
