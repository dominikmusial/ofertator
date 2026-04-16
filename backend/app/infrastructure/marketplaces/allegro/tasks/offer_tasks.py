"""Allegro Celery tasks - Offer Tasks"""
import io
import json
import copy
import logging
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db import schemas, models
from app.db.repositories import AccountRepository, BackupRepository, TemplateRepository
from app.infrastructure.marketplaces.factory import factory
from app.infrastructure.marketplaces.allegro.error_handler import (
    get_polish_error_message as _get_polish_error_message,
    handle_parameter_validation_error as _handle_parameter_validation_error
)

logger = logging.getLogger(__name__)


# Helper Functions
def _save_images_to_minio(minio_service, image_urls: List[str], account_name: str, offer_id: str, image_type: str):
    """
    Save images to MinIO storage following the same directory structure as the old app.
    
    Args:
        minio_service: MinIO service instance
        image_urls: List of image URLs to download and save
        account_name: Account name for directory structure
        offer_id: Offer ID for directory structure  
        image_type: 'original' or 'processed' for directory organization
    """
    import requests
    from io import BytesIO
    
    if not image_urls:
        logger.info(f"No {image_type} images to save for offer {offer_id}")
        return
    
    # Create bucket name following the pattern: offer-images-{image_type}
    bucket_name = f"offer-images-{image_type}"
    
    logger.info(f"Saving {len(image_urls)} {image_type} images for offer {offer_id}")
    
    for idx, image_url in enumerate(image_urls, start=1):
        try:
            # Download the image
            logger.info(f"Downloading {image_type} image {idx}: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension from content type or URL
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            else:
                # Try to get extension from URL
                ext = image_url.split('.')[-1] if '.' in image_url else '.jpg'
                if not ext.startswith('.'):
                    ext = f'.{ext}'
            
            # Create filename following old app pattern: account/offer_type/offer_id/image_N.ext
            filename = f"{account_name}/{image_type}/{offer_id}/image_{idx}{ext}"
            
            # Upload to MinIO
            public_url = minio_service.upload_file(
                bucket_name=bucket_name,
                file_name=filename,
                file_data=response.content,
                content_type=content_type or 'image/jpeg'
            )
            
            logger.info(f"Saved {image_type} image {idx} for offer {offer_id}: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save {image_type} image {idx} for offer {offer_id}: {e}")
            # Continue with next image even if one fails
            continue
    
    logger.info(f"Completed saving {image_type} images for offer {offer_id}")


@celery.task(bind=True, name='update_offer_task')
def update_offer_task(self, account_id: int, offer_id: str, template_id: int, image_mapping: Optional[Dict[str, str]] = None, user_id: Optional[int] = None):
    """
    Task to update a single offer's description using a template.
    """
    db = SessionLocal()
    try:
        # 1. Get account and template
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        template = TemplateRepository.get_by_id(db, template_id)
        if not template or template.owner_id != account_id:
            raise Exception("Template not found or does not belong to the account")
        
        # 2. Get valid token (with automatic refresh if needed)
        from app.api.marketplace_token_utils import get_valid_token_for_task
        access_token = get_valid_token_for_task(db, account_id)

        # 3. Get offer details using provider
        provider = factory.get_provider_for_account(db, account_id)
        offer_details = provider.get_offer(offer_id)

        # 4. Generate new description and collect image replacements
        # Use Allegro-specific template processing
        provider = factory.get_provider_for_account(db, account_id)
        if hasattr(provider, 'process_template_sections_for_offer'):
            new_description, image_replacements = provider.process_template_sections_for_offer(
                template_sections=template.content, 
                offer_details=offer_details,
            template_prompt=template.prompt,
            image_mapping=image_mapping,
            user_id=user_id,
            account_id=account_id,
            account_name=account.nazwa_konta,
            processing_mode="Oryginalny",  # Default mode for single offer updates
            auto_fill_images=True  # Default for single offer updates
        )
        
        # 5. Update offer with both description and images (if applicable)
        payload = {"description": {"sections": new_description}}
        
        # Update image gallery if there are frame replacements
        if image_replacements:
            logger.info(f"Updating image gallery for offer {offer_id} with {len(image_replacements)} replacements")
            current_images = offer_details.get("images", [])[:]  # Create a copy
            
            # Apply image replacements to the gallery
            # Process thumbnail duplications first, then normal replacements
            thumbnail_insertions = {k: v for k, v in image_replacements.items() if v.get('action') == 'duplicate_thumbnail'}
            normal_replacements = {k: v for k, v in image_replacements.items() if v.get('action') != 'duplicate_thumbnail'}
            
            # Handle thumbnail duplications first
            for original_url, replacement_info in thumbnail_insertions.items():
                new_url = replacement_info['new_url']
                position = replacement_info['position']
                original_placeholder = replacement_info['original_placeholder']
                
                # For thumbnails, insert the framed version at position 2 (index 1)
                if position == 0:  # Thumbnail is at position 0
                    current_images.insert(1, new_url)
                    logger.info(f"Duplicated thumbnail {original_placeholder}: original kept at position 1, framed version inserted at position 2")
            
            # Handle normal replacements after thumbnail insertions (positions may have shifted)
            for original_url, replacement_info in normal_replacements.items():
                new_url = replacement_info['new_url']
                original_position = replacement_info['position']
                original_placeholder = replacement_info['original_placeholder']
                
                # Adjust position if thumbnail was inserted (shifts positions by 1)
                position_offset = len(thumbnail_insertions)  # Number of thumbnail insertions
                adjusted_position = original_position + position_offset if original_position > 0 else original_position
                
                # Ensure position is within bounds and find the original image
                if 0 <= adjusted_position < len(current_images):
                    if current_images[adjusted_position] == original_url:
                        current_images[adjusted_position] = new_url
                        logger.info(f"Replaced image at position {adjusted_position + 1} ({original_placeholder}): {original_url} -> {new_url}")
                    else:
                        # Search for the original URL in case position shifted
                        found_at = -1
                        for i, img_url in enumerate(current_images):
                            if img_url == original_url:
                                found_at = i
                                break
                        
                        if found_at >= 0:
                            current_images[found_at] = new_url
                            logger.info(f"Found and replaced image at position {found_at + 1} ({original_placeholder}): {original_url} -> {new_url}")
                        else:
                            logger.warning(f"Could not find original image {original_url} to replace with {new_url}")
                else:
                    logger.warning(f"Position {adjusted_position + 1} out of bounds for offer {offer_id} (has {len(current_images)} images)")
            
            payload["images"] = current_images
            logger.info(f"Updated image gallery for offer {offer_id}: {len(current_images)} images")
        
        # Update the offer using provider
        provider.update_offer(offer_id, payload)

        return {"status": "SUCCESS", "offer_id": offer_id}

    except Exception as e:
        # Use provider to normalize error if available
        error_msg = str(e)
        try:
            # We need to get provider again or use local variable if it exists in scope
            # Since 'provider' variable is defined in try block, check if it's bound
            if 'provider' in locals():
                error_msg = provider.normalize_error(e)
        except:
            pass
            
        logger.error(f"Error updating offer {offer_id}: {error_msg}")
        self.update_state(
            state="FAILURE", meta={"exc_type": type(e).__name__, "exc_message": error_msg}
        )
        raise Exception(error_msg)
    finally:
        db.close()


@celery.task(bind=True, name='duplicate_offer_with_title_task')
def duplicate_offer_with_title_task(self, account_id: int, offer_id: str, new_title: str, activate_immediately: bool = False, user_id: Optional[int] = None):
    """
    Task to duplicate a single offer with a new title on the same account.
    Returns result for batch logging via chord callback.
    """
    logger.info(f"duplicate_offer_with_title_task called with account_id={account_id}, offer_id='{offer_id}', new_title='{new_title}', activate={activate_immediately}")
    db = SessionLocal()
    try:
        # 1. Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # 2. Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        # 3. Fetch offer details
        logger.info(f"Fetching offer details for {offer_id}")
        offer_data = provider.get_offer(offer_id)
        logger.info(f"Offer data fetched, keys: {list(offer_data.keys()) if offer_data else 'None'}")
        
        # Debug: Log images structure
        if offer_data and 'images' in offer_data:
            logger.info(f"=== OFFER TOP-LEVEL IMAGES COUNT === {len(offer_data.get('images', []))}")
        if offer_data and 'productSet' in offer_data and len(offer_data.get('productSet', [])) > 0:
            first_product = offer_data['productSet'][0].get('product', {})
            logger.info(f"=== FULL PRODUCT STRUCTURE === {first_product}")
            if 'images' in first_product:
                logger.info(f"=== PRODUCT CATALOG IMAGES COUNT === {len(first_product.get('images', []))}")

        # 4. Prepare payload for duplication
        # For duplication on same account, we don't need to copy images (same URLs work)
        url_mapping = {}  # Empty mapping - images already accessible
        
        # Extract language from parent offer for both header and body
        parent_language = offer_data.get('language', 'pl-PL')  # Default to Polish if not specified
        logger.info(f"=== PARENT OFFER LANGUAGE === {parent_language}")
        
        # Full copy options - copy everything
        options = {
            "copy_images": False,  # Don't copy images, use same URLs
            "copy_description": True,
            "copy_parameters": True,
            "copy_shipping": True,
            "copy_return_policy": True,
            "copy_warranty": True,
            "copy_price": True,
            "copy_quantity": True,
            "same_account_duplicate": True  # Duplication on same account - keep afterSalesServices
        }
        
        logger.info("Preparing offer payload for duplication")
        new_offer_payload = _prepare_offer_payload_for_copy(offer_data, url_mapping, options)
        
        # 5. Override title with new title
        new_offer_payload['name'] = new_title
        logger.info(f"Set new title: {new_title}")
        
        # 6. Ensure language is preserved in the payload
        if parent_language and 'language' in new_offer_payload:
            logger.info(f"=== FINAL OFFER LANGUAGE IN BODY === {new_offer_payload['language']}")
        elif parent_language:
            # If language was removed during processing, add it back
            new_offer_payload['language'] = parent_language
            logger.warning(f"=== RESTORED LANGUAGE TO BODY === {parent_language}")
        
        # 7. Set publication status
        if 'publication' not in new_offer_payload:
            new_offer_payload['publication'] = {}
        new_offer_payload['publication']['status'] = 'ACTIVE' if activate_immediately else 'INACTIVE'
        logger.info(f"Set publication status: {new_offer_payload['publication']['status']}")
        
        # 8. Create new offer with language in header
        logger.info("Creating duplicate offer...")
        logger.info(f"=== FINAL DELIVERY === {new_offer_payload.get('delivery', {})}")
        logger.info(f"=== ACCEPT-LANGUAGE HEADER === {parent_language}")
        
        # Debug: Log final images structure
        if 'images' in new_offer_payload:
            logger.info(f"=== FINAL TOP-LEVEL IMAGES COUNT === {len(new_offer_payload.get('images', []))}")
        if 'productSet' in new_offer_payload and len(new_offer_payload.get('productSet', [])) > 0:
            first_product = new_offer_payload['productSet'][0].get('product', {})
            logger.info(f"=== FINAL PRODUCT STRUCTURE BEING SENT === {first_product}")
            if 'images' in first_product:
                logger.info(f"=== FINAL PRODUCT CATALOG IMAGES COUNT === {len(first_product.get('images', []))}")
        
        created_offer = provider.create_offer(new_offer_payload)
        new_offer_id = created_offer.get('id')
        logger.info(f"Duplicate offer created with ID: {new_offer_id}")

        # Return data for batch logging
        return {
            "status": "SUCCESS",
            "offer_id": offer_id,
            "new_offer_id": new_offer_id,
            "title": new_title,
            "account_name": account.nazwa_konta,
            "user_id": user_id
        }

    except Exception as e:
        # Use provider to normalize error
        error_msg = str(e)
        if 'provider' in locals():
            try:
                error_msg = provider.normalize_error(e)
            except:
                pass
        
        logger.error(f"Error duplicating offer {offer_id}: {error_msg}")
        
        # Return error result instead of raising exception to allow chord to complete
        return {
            "status": "FAILURE",
            "offer_id": offer_id,
            "title": new_title,
            "error": error_msg,
            "user_id": user_id
        }
    finally:
        db.close()


@celery.task(bind=True, name='update_offer_status_task')
def update_offer_status_task(self, account_id: int, offer_id: str, status: str, user_id: int = None):
    """
    Task to update a single offer's status.
    """
    db = SessionLocal()
    try:
        # 1. Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # 2. Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        # 3. Update offer status
        # Use Allegro-specific status update logic (PATCH for ENDED, PUT command for ACTIVE)
        provider = factory.get_provider_for_account(db, account_id)
        if hasattr(provider, 'update_offer_status'):
            provider.update_offer_status(offer_id, status)
        else:
            raise ValueError(f"Status updates not supported for marketplace: {provider.get_marketplace_type()}")

        # 4. Log to external system if user is admin or vsprint_employee
        if user_id:
            from app.services.external_logging_service import is_admin_or_vsprint, send_logs_batch, create_log_entry
            try:
                if is_admin_or_vsprint(user_id, db):
                    status_text = "Zakończenie oferty" if status == "ENDED" else "Przywrócenie oferty"
                    logs = [create_log_entry(
                        account_name=account.nazwa_konta,
                        kind=status_text,
                        offer_id=offer_id,
                        value="",
                        value_before=""
                    )]
                    send_logs_batch(logs, db)
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")

        return {"status": "SUCCESS", "offer_id": offer_id, "new_status": status}

    except Exception as e:
        self.update_state(
            state="FAILURE", meta={"exc_type": type(e).__name__, "exc_message": str(e)}
        )
        raise
    finally:
        db.close()

def _prepare_offer_payload_for_copy(offer_data: dict, url_mapping: dict, options: dict) -> dict:
    """Prepares the offer payload for creating a new offer using a hybrid approach."""
    payload = copy.deepcopy(offer_data)
    
    # Determine offer type - catalog-based or free-form
    has_catalog_product = False
    if 'productSet' in offer_data and isinstance(offer_data['productSet'], list) and offer_data['productSet']:
        first_product = offer_data['productSet'][0]
        if isinstance(first_product, dict) and 'product' in first_product:
            product = first_product['product']
            if isinstance(product, dict) and product.get('id'):
                has_catalog_product = True
                logger.info(f"Preparing catalog offer (product: {product.get('id')})")

    # Apply appropriate cleaning strategy
    if has_catalog_product:
        payload = _prepare_catalog_offer_payload(payload, url_mapping, options)
    else:
        logger.info("Preparing free-form offer")
        payload = _prepare_free_form_offer_payload(payload, url_mapping, options)

    return payload


def _should_preserve_field(field: str, parent_key: str, same_account: bool) -> bool:
    """Determine if a field should be preserved during cleaning"""
    # Always preserve IDs in critical structures
    if field == 'id' and parent_key in ['parameters', 'category', 'warranty', 'returnPolicy', 
                                         'afterSalesServices', 'product', 'shippingRates', 'delivery']:
        return True
    return False


def _clean_catalog_product_fields(product: dict, same_account: bool) -> dict:
    """Clean read-only and duplicate-causing fields from catalog products"""
    # Remove read-only fields that cause API errors
    product.pop('publication', None)
    product.pop('isAiCoCreated', None)
    
    if same_account:
        # For duplicates: remove images and language to avoid catalog defaults
        product.pop('images', None)
        product.pop('language', None)
        # Set empty images array to override catalog defaults
        product['images'] = []
    
    return product


def _should_skip_deep_clean(parent_key: str, same_account: bool) -> bool:
    """Check if a structure should be skipped during deep cleaning"""
    
    # For same-account duplicates, preserve critical structures entirely
    if same_account and parent_key in ['afterSalesServices', 'delivery', 'shippingRates', 
                                        'returnPolicy', 'warranty', 'impliedWarranty', 
                                        'responsibleProducer', 'responsiblePerson']:
        return True
    
    # For cross-account copies, preserve structures that will be handled later
    if not same_account and parent_key in ['delivery', 'afterSalesServices', 'shippingRates', 
                                            'returnPolicy', 'warranty', 'impliedWarranty']:
        return True
    
    return False


def _prepare_catalog_offer_payload(payload: dict, url_mapping: dict, options: dict) -> dict:
    """Prepare payload for offers that have catalog products (productSet with valid product.id)"""
    
    same_account = options.get("same_account_duplicate", False)
    
    # Fields to remove for catalog offers
    fields_to_remove = [
        "id", "external", "publication", "promotion", 
        "sizeTable", "additionalServices", "b2b", "updatedAt", "createdAt",
        "attachments", "validation", "warnings",
        "additionalMarketplaces", "discounts", "fundraising",
        "tecdocSpecification", "marketplace", "isAiCoCreated"
    ]
    
    # For cross-account copies, also remove language
    if not same_account:
        fields_to_remove.append("language")
    
    # Preserve category structure
    if 'category' in payload and isinstance(payload['category'], dict) and 'id' in payload['category']:
        category_id = payload['category']['id']
        payload['category'] = {'id': category_id}
    
    # Remove top-level fields
    for field in fields_to_remove:
        payload.pop(field, None)
    
    # Deep clean nested structures using helper functions
    def deep_clean_catalog(obj, level=0, parent_key=None):
        if level > 5:  # Prevent infinite recursion
            return obj
            
        if isinstance(obj, dict):
            # Check if this structure should be skipped entirely
            if _should_skip_deep_clean(parent_key, same_account):
                # Special handling for product fields
                if parent_key == 'product':
                    return _clean_catalog_product_fields(obj, same_account)
                return obj
            
            # Remove fields that shouldn't be in the payload
            for field in fields_to_remove:
                if field in obj and not _should_preserve_field(field, parent_key, same_account):
                    obj.pop(field, None)
            
            # Recursively clean nested objects
            for key, value in list(obj.items()):
                obj[key] = deep_clean_catalog(value, level + 1, parent_key=key)
                
        elif isinstance(obj, list):
            # Clean each item in the list
            for i, item in enumerate(obj):
                obj[i] = deep_clean_catalog(item, level + 1, parent_key=parent_key)
        
        return obj
    
    payload = deep_clean_catalog(payload)
    
    # Clean parameters
    if 'parameters' in payload:
        cleaned_parameters = []
        for param in payload['parameters']:
            if isinstance(param, dict):
                cleaned_param = {}
                essential_fields = ['id', 'name', 'values', 'valuesIds', 'rangeValue']
                for field in essential_fields:
                    if field in param:
                        cleaned_param[field] = param[field]
                
                if (cleaned_param.get('name') or cleaned_param.get('id')) and cleaned_param.get('values'):
                    cleaned_parameters.append(cleaned_param)
        
        payload['parameters'] = cleaned_parameters
        logger.info(f"Cleaned catalog parameters count: {len(cleaned_parameters)}")

    return _apply_common_options(payload, url_mapping, options)


def _prepare_free_form_offer_payload(payload: dict, url_mapping: dict, options: dict) -> dict:
    """Prepare payload for offers that don't have catalog products (free-form offers)"""
    
    # For free-form offers, remove productSet entirely
    payload.pop('productSet', None)
    
    # Fields to remove for free-form offers
    fields_to_remove = [
        "id", "external", "publication", "promotion", 
        "sizeTable", "additionalServices", "b2b", "updatedAt", "createdAt",
        "attachments", "validation", "warnings", "additionalMarketplaces", 
        "discounts", "fundraising", "language", "tecdocSpecification", 
        "marketplace", "compatibilityList", "isAiCoCreated"
    ]
    
    # Preserve category structure
    if 'category' in payload and isinstance(payload['category'], dict) and 'id' in payload['category']:
        category_id = payload['category']['id']
        payload['category'] = {'id': category_id}
    
    # Remove fields
    for field in fields_to_remove:
        payload.pop(field, None)
    
    # Clean parameters - keep only essential ones
    if 'parameters' in payload:
        cleaned_parameters = []
        for param in payload['parameters']:
            if isinstance(param, dict):
                cleaned_param = {}
                # For free-form offers, we need less strict parameter validation
                essential_fields = ['id', 'name', 'values', 'valuesIds']
                for field in essential_fields:
                    if field in param:
                        cleaned_param[field] = param[field]
                
                # Only require name and values for free-form offers
                if cleaned_param.get('name') and cleaned_param.get('values'):
                    cleaned_parameters.append(cleaned_param)
        
        payload['parameters'] = cleaned_parameters
        logger.info(f"Cleaned free-form parameters count: {len(cleaned_parameters)}")

    return _apply_common_options(payload, url_mapping, options)


def _apply_delivery_options(payload: dict, options: dict) -> None:
    """Apply delivery and shipping options for cross-account copies"""
    
    # Legacy option: delivery_price_list_id (old copy offers API)
    if options.get("delivery_price_list_id"):
        payload.setdefault("delivery", {})["shippingRates"] = {"id": options["delivery_price_list_id"]}
        return
    
    # New options: selected_delivery_id (new copy offers UI)
    if options.get("selected_delivery_id"):
        logger.info(f"Applying selected delivery: {options['selected_delivery_id']}")
        if "delivery" in payload:
            payload["delivery"]["shippingRates"] = {"id": options["selected_delivery_id"]}
        else:
            payload["delivery"] = {
                "handlingTime": "PT24H",
                "shippingRates": {"id": options["selected_delivery_id"]}
            }
        return
    
    # Check copy_shipping checkbox (default: True = copy original)
    if options.get("copy_shipping", True):
        # Keep the delivery structure as-is (including shippingRates)
        logger.info("Keeping original delivery settings")
    else:
        # User doesn't want to copy shipping - strip to minimal delivery info
        logger.info("Removing shipping rates (user choice)")
        if "delivery" in payload:
            essential_delivery = {"handlingTime": payload["delivery"].get("handlingTime", "PT24H")}
            payload["delivery"] = essential_delivery


def _apply_after_sales_options(payload: dict, options: dict) -> None:
    """Apply warranty and return policy options for cross-account copies"""
    
    after_sales_services = {}
    
    # Handle warranty
    if options.get("selected_warranty_id"):
        logger.info(f"Applying selected warranty: {options['selected_warranty_id']}")
        after_sales_services["warranty"] = {"id": options["selected_warranty_id"]}
    elif options.get("copy_warranty", True) and "afterSalesServices" in payload:
        if "warranty" in payload["afterSalesServices"]:
            after_sales_services["warranty"] = payload["afterSalesServices"]["warranty"]
            logger.info("Keeping original warranty")
    
    # Handle return policy
    if options.get("selected_return_policy_id"):
        logger.info(f"Applying selected return policy: {options['selected_return_policy_id']}")
        after_sales_services["returnPolicy"] = {"id": options["selected_return_policy_id"]}
    elif options.get("copy_return_policy", True) and "afterSalesServices" in payload:
        if "returnPolicy" in payload["afterSalesServices"]:
            after_sales_services["returnPolicy"] = payload["afterSalesServices"]["returnPolicy"]
            logger.info("Keeping original return policy")
    
    # Always preserve impliedWarranty if it exists
    if "afterSalesServices" in payload and "impliedWarranty" in payload["afterSalesServices"]:
        after_sales_services["impliedWarranty"] = payload["afterSalesServices"]["impliedWarranty"]
    
    # Replace afterSalesServices entirely or remove if empty
    if after_sales_services:
        payload["afterSalesServices"] = after_sales_services
    else:
        payload.pop("afterSalesServices", None)


def _apply_common_options(payload: dict, url_mapping: dict, options: dict) -> dict:
    """Apply common options and settings to both catalog and free-form offers"""
    
    same_account = options.get("same_account_duplicate", False)
    
    # Clean read-only fields from sellingMode
    if "sellingMode" in payload:
        payload["sellingMode"].pop("popularity", None)
        payload["sellingMode"].pop("bidCount", None)

    # Update image URLs if mapping provided
    if url_mapping:
        if "images" in payload and payload["images"]:
            new_images = []
            for old_url in payload["images"]:
                if isinstance(old_url, str):
                    new_url = url_mapping.get(old_url, old_url)
                    new_images.append(new_url)
            payload["images"] = new_images
        
        if "description" in payload:
            for section in payload["description"].get("sections", []):
                for item in section.get("items", []):
                    if item.get("type") == "IMAGE":
                        item["url"] = url_mapping.get(item["url"], item["url"])

    # Handle quantity
    copy_quantity = options.get("copy_quantity", False)
    if not copy_quantity:
        payload.setdefault("stock", {})["available"] = 1
    
    if "available" in payload.get("stock", {}):
        try:
            payload["stock"]["available"] = int(payload["stock"]["available"])
        except (ValueError, TypeError):
            payload["stock"]["available"] = 1

    # Handle payments
    if "payments" in payload and not payload["payments"].get("invoice"):
        payload.pop("payments")

    # Handle copy options
    if not options.get("copy_description", True):
        payload.pop("description", None)
    
    if not options.get("copy_parameters", True):
        payload.pop("parameters", None)
    
    if not options.get("copy_price", False):
        if "sellingMode" in payload and "price" in payload["sellingMode"]:
            payload["sellingMode"]["price"] = {"amount": "1.00", "currency": "PLN"}
    
    # Handle delivery/shipping - skip for same-account duplicates (already preserved)
    if not same_account:
        _apply_delivery_options(payload, options)
    
    # Handle warranty and returns - skip for same-account duplicates (already preserved)
    if not same_account:
        _apply_after_sales_options(payload, options)
    
    # Ensure required fields exist
    payload.setdefault("delivery", {}).setdefault("handlingTime", "PT24H")
    payload.setdefault("location", {}).setdefault("countryCode", "PL")
    payload.setdefault("location", {}).setdefault("city", "Brak")
    payload.setdefault("location", {}).setdefault("postCode", "00-000")

    # Clean empty parameters
    if "parameters" in payload:
        payload["parameters"] = [
            param for param in payload["parameters"]
            if param.get("values") and any(str(v).strip() for v in param.get("values", []))
        ]

    # Set default publication status
    payload["publication"] = {"status": "INACTIVE"}

    # Remove null fields
    def remove_null_fields(obj):
        if isinstance(obj, dict):
            return {k: remove_null_fields(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_null_fields(item) for item in obj if item is not None]
        else:
            return obj
    
    payload = remove_null_fields(payload)
    
    logger.info(f"Payload prepared with fields: {', '.join(payload.keys())}")
    return payload


@celery.task(bind=True, name='copy_offer_task')
def copy_offer_task(self, source_account_id: int, source_offer_id: str, options: dict):
    """
    Task to copy a single offer from a source account to a target account.
    """
    logger.info(f"Copying offer {source_offer_id} from account {source_account_id} to {options.get('target_account_id')}")
    db = SessionLocal()
    target_account_id = options.get("target_account_id")

    if source_account_id == target_account_id:
        self.update_state(state='FAILURE', meta={'status': 'Source and target accounts cannot be the same.'})
        raise Exception("Source and target accounts cannot be the same.")

    self.update_state(state='PROGRESS', meta={'status': f'Starting copy of offer {source_offer_id} from account {source_account_id} to {target_account_id}'})
    
    try:
        source_account = AccountRepository.get_by_id(db, source_account_id)
        target_account = AccountRepository.get_by_id(db, target_account_id)

        if not source_account or not target_account:
            raise Exception("Source or target account not found.")

        # Use centralized token refresh with proper error handling for both accounts
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        source_access_token = refresh_account_token_if_needed(db, source_account, for_api=False)
        target_access_token = refresh_account_token_if_needed(db, target_account, for_api=False)

        self.update_state(state='PROGRESS', meta={'status': 'Fetching original offer data...'})
        logger.info(f"=== FETCHING OFFER DATA === offer_id:{source_offer_id}")
        
        # NEW: Use provider to get offer details
        source_provider = factory.get_provider_for_account(db, source_account_id)
        offer_data = source_provider.get_offer(source_offer_id)
        logger.info(f"=== OFFER DATA FETCHED === keys:{list(offer_data.keys()) if offer_data else 'None'}")

        url_mapping = {}
        if options.get("copy_images", False) and offer_data.get("images"):
            self.update_state(state='PROGRESS', meta={'status': 'Copying images...'})
            
            image_urls = [img['url'] for img in offer_data.get("images", []) if isinstance(img, dict) and 'url' in img]

            for i, old_url in enumerate(image_urls):
                try:
                    self.update_state(state='PROGRESS', meta={'status': f'Copying image {i+1}/{len(image_urls)}...'})
                    response = requests.get(old_url)
                    response.raise_for_status()
                    image_bytes = response.content
                    
                    # NEW: Use provider to upload image
                    target_provider = factory.get_provider_for_account(db, target_account_id)
                    new_url = target_provider.upload_image(image_bytes, f"image_{i}.jpg")
                    url_mapping[old_url] = new_url
                    logger.info(f"Image {old_url} copied to {new_url}")

                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to download image {old_url}: {e}")
                    url_mapping[old_url] = old_url # fallback to old url

        self.update_state(state='PROGRESS', meta={'status': 'Preparing new offer payload...'})
        
        # Extract language from source offer for header
        source_language = offer_data.get('language', 'pl-PL')  # Default to Polish
        logger.info(f"=== SOURCE OFFER LANGUAGE === {source_language}")
        
        new_offer_payload = _prepare_offer_payload_for_copy(offer_data, url_mapping, options)
        
        # Debug logging to see what's being sent
        logger.info(f"Prepared payload keys: {list(new_offer_payload.keys())}")
        if 'compatibilityList' in new_offer_payload:
            logger.warning(f"compatibilityList still present in payload: {new_offer_payload['compatibilityList']}")
        
        # Log the entire payload for debugging (truncated)
        import json
        payload_str = json.dumps(new_offer_payload, indent=2, default=str)
        logger.info(f"Full payload (first 2000 chars): {payload_str[:2000]}")

        self.update_state(state='PROGRESS', meta={'status': 'Creating new offer...'})
        # NEW: Use provider to create offer
        target_provider = factory.get_provider_for_account(db, target_account_id)
        created_offer = target_provider.create_offer(new_offer_payload)
        
        # Success case - update state and return result
        status = 'SUCCESS'
        result = {'status': 'SUCCESS', 'new_offer_id': created_offer.get('id')}
        
        self.update_state(state=status, meta=result)
        return result

    except Exception as e:
        logger.error(f"Error in copy_offer_task: {e}", exc_info=True)
        
        error_msg = str(e)
        # Try to use target provider first, then source provider
        provider_to_use = locals().get('target_provider') or locals().get('source_provider')
        if provider_to_use:
            try:
                error_msg = provider_to_use.normalize_error(e)
            except:
                pass

        # Prepare proper error metadata for Celery
        error_meta = {
            'error': error_msg,
            'exc_type': type(e).__name__,
            'exc_message': error_msg
        }
        
        self.update_state(state='FAILURE', meta=error_meta)
        
        return {
            'status': 'FAILURE',
            'error': error_msg,
            'exc_type': type(e).__name__
        }
    finally:
        db.close()


@celery.task(bind=True, name='restore_offer_from_backup_task')
def restore_offer_from_backup_task(self, account_id: int, offer_id: str):
    """
    Restores a single offer from its latest backup in the database.
    This task assumes the backup exists, as the check is performed in the API layer.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting offer restore for offer {offer_id} on account {account_id}")

        # Get account and validate access token (same pattern as other tasks)
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Get valid token (with automatic refresh if needed)
        from app.api.marketplace_token_utils import get_valid_token_for_task
        access_token = get_valid_token_for_task(db, account_id)
        
        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)
        
        # Get the latest backup
        latest_backup = BackupRepository.get_latest(db, offer_id, account_id)
        if not latest_backup:
            raise Exception(f"No backup found for offer {offer_id}")
        
        # Extract only the fields that should be restored (images, description, name)
        # This matches the old app's behavior in save_offer_to_database and aktualizuj_opis_oferty
        backup_data = latest_backup.backup_data
        if isinstance(backup_data, str):
            backup_data = json.loads(backup_data)
        
        # Create restore data with only the necessary fields
        restore_data = {}
        if 'images' in backup_data:
            # Deduplicate images to avoid Allegro API validation errors
            original_images = backup_data['images']
            unique_images = []
            seen_urls = set()
            
            for image_url in original_images:
                if image_url not in seen_urls:
                    unique_images.append(image_url)
                    seen_urls.add(image_url)
                else:
                    logger.warning(f"Duplicate image found and removed: {image_url}")
            
            restore_data['images'] = unique_images
            logger.info(f"Restoring {len(unique_images)} images (removed {len(original_images) - len(unique_images)} duplicates)")
        
        if 'description' in backup_data:
            restore_data['description'] = backup_data['description']
            if 'sections' in backup_data['description']:
                logger.info(f"Restoring description with {len(backup_data['description']['sections'])} sections")
        
        if 'name' in backup_data:
            restore_data['name'] = backup_data['name']
            logger.info(f"Restoring offer name: {backup_data['name'][:50]}...")
        
        logger.info(f"Restore data keys: {list(restore_data.keys())}")
        
        # Use provider to restore only the necessary data
        logger.info(f"Restoring offer {offer_id} from backup created at {latest_backup.created_at}")
        provider.update_offer(offer_id, restore_data)
        
        logger.info(f"Successfully restored offer {offer_id} from backup created at {latest_backup.created_at}")
        return {'status': 'SUCCESS', 'offer_id': offer_id}
    except Exception as e:
        logger.error(f"Error restoring offer {offer_id} from backup: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()


@celery.task(bind=True, name='generate_pdf_task')
def generate_pdf_task(self, account_id: int, offer_id: str):
    """
    Task to generate a PDF product sheet for a given offer.
    """
    db = SessionLocal()
    try:
        # 1. Get account and use centralized token refresh
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # 2. Get offer details using provider
        provider = factory.get_provider_for_account(db, account_id)
        offer_details = provider.get_offer(offer_id)

        # 3. Extract data for PDF using the centralized extract_product_info function
        from app.infrastructure.marketplaces.allegro.services.pdf_generator import extract_product_info
        
        title, description_html, parameters, images, code_number = extract_product_info(offer_details)

        # 4. Generate PDF
        pdf_bytes = pdf_generator_service.generate_pdf(
            title=title,
            description=description_html,
            images=images,
            parameters=parameters
        )

        # 5. Upload PDF to MinIO
        pdf_filename = f"product-sheet-{offer_id}-{uuid.uuid4()}.pdf"
        pdf_url = minio_service.upload_file(
            bucket_name="product-sheets",
            file_name=pdf_filename,
            file_data=pdf_bytes,
            content_type="application/pdf"
        )
        
        return {"status": "SUCCESS", "offer_id": offer_id, "pdf_url": pdf_url}

    except Exception as e:
        self.update_state(
            state="FAILURE", meta={"exc_type": type(e).__name__, "exc_message": str(e)}
        )
        raise
    finally:
        db.close()


@celery.task(bind=True, name='bulk_edit_task')
def bulk_edit_task(self, account_id: int, offer_ids: List[str], actions: dict):
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)
        
        # Use Allegro-specific bulk edit (Allegro bulk commands)
        provider = factory.get_provider_for_account(db, account_id)
        if hasattr(provider, 'bulk_edit_offers'):
            command_id = provider.bulk_edit_offers(offer_ids, actions)
            return {"status": "SUCCESS", "command_id": command_id}
        else:
            raise ValueError(f"Bulk edit not supported for marketplace: {provider.get_marketplace_type()}")
    except Exception as e:
        logger.error(f"Error in bulk_edit_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()


@celery.task(bind=True, name='bulk_update_offers_with_template_task')
def bulk_update_offers_with_template_task(self, account_id: int, offer_ids: List[str], template_data: dict, options: dict, user_id: Optional[int] = None):
    """
    Task to bulk update multiple offers using a template with processing options.
    Implements the core functionality from the desktop app's offer update system.
    """
    db = SessionLocal()
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing bulk template update...', 'progress': 0})
        
        # Log input data for debugging
        logger.info(f"Starting bulk update for account {account_id}")
        logger.info(f"Offer IDs: {offer_ids}")
        logger.info(f"Template data keys: {list(template_data.keys()) if template_data else 'None'}")
        logger.info(f"Options: {options}")
        
        # Get account and validate
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Get valid token (with automatic refresh if needed)
        from app.api.marketplace_token_utils import get_valid_token_for_task
        access_token = get_valid_token_for_task(db, account_id)
        
        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)
        
        # Check if we're in "only save images" mode
        save_images_only = options.get('save_images_only', False)
        save_original_images = options.get('save_original_images', False)
        save_processed_images = options.get('save_processed_images', False)
        
        # Import MinIO service for image saving
        from app.services.minio_service import minio_service
        
        successful_offers = []
        failed_offers = []
        total_offers = len(offer_ids)
        
        for i, offer_id in enumerate(offer_ids):
            try:
                # Update progress
                progress = int((i / total_offers) * 100)
                status_msg = f'Processing offer {i+1}/{total_offers} ({offer_id})'
                if save_images_only:
                    status_msg = f'Saving images for offer {i+1}/{total_offers} ({offer_id})'
                
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': status_msg, 
                        'progress': progress,
                        'successful': len(successful_offers),
                        'failed': len(failed_offers)
                    }
                )
                
                # Get offer details for template processing
                logger.info(f"Fetching offer details for offer {offer_id}")
                offer_details = provider.get_offer(offer_id)
                logger.info(f"Successfully fetched offer details for {offer_id}")
                
                # Save original images if requested
                if save_original_images:
                    self.update_state(
                        state='PROGRESS', 
                        meta={
                            'status': f'Saving original images for offer {i+1}/{total_offers} ({offer_id})', 
                            'progress': progress,
                            'successful': len(successful_offers),
                            'failed': len(failed_offers)
                        }
                    )
                    logger.info(f"Saving original images for offer {offer_id}")
                    _save_images_to_minio(
                        minio_service, 
                        offer_details.get('images', []), 
                        account.nazwa_konta, 
                        offer_id, 
                        'original'
                    )
                    logger.info(f"Original images saved for offer {offer_id}")
                
                # If we're only saving images without processed images, skip processing entirely
                if save_images_only and not save_processed_images:
                    logger.info(f"Skipping processing for offer {offer_id} (save original images only mode)")
                    successful_offers.append(offer_id)
                    continue
                
                # Create backup before updating (matching old app behavior)
                logger.info(f"Creating backup for offer {offer_id}")
                backup_data = {
                    'images': offer_details.get('images', []),
                    'description': offer_details.get('description', {}),
                    'name': offer_details.get('name', '')
                }
                backup_create = schemas.OfferBackupCreate(
                    offer_id=offer_id,
                    account_id=account_id,
                    backup_data=backup_data
                )
                BackupRepository.create(db, backup_create)
                logger.info(f"Backup created for offer {offer_id}")
                
                # Process template with offer data
                logger.info(f"Processing template for offer {offer_id}")
                
                # Extract template sections - frontend sends {prompt, sections}
                template_sections = template_data.get('sections', [])
                template_prompt = template_data.get('prompt', '')
                
                logger.info(f"Template sections count: {len(template_sections)}")
                logger.info(f"Template prompt: {template_prompt}")
                logger.info(f"Template sections type: {type(template_sections)}")
                if template_sections:
                    logger.info(f"First section type: {type(template_sections[0])}")
                    logger.info(f"First section content: {template_sections[0]}")
                
                # Convert Pydantic models to dictionaries if needed
                if template_sections and hasattr(template_sections[0], 'dict'):
                    logger.info("Converting Pydantic models to dictionaries")
                    template_sections = [section.dict() for section in template_sections]
                    logger.info(f"Converted first section: {template_sections[0]}")
                
                # Process template sections with marketplace provider
                provider = factory.get_provider_for_account(db, account_id)
                if hasattr(provider, 'process_template_sections_for_offer'):
                    new_description, image_replacements = provider.process_template_sections_for_offer(
                        template_sections=template_sections,
                        offer_details=offer_details,
                    template_prompt=template_prompt,
                    image_mapping=options.get('image_mapping'),
                    user_id=user_id,
                    account_id=account_id,
                    frame_scale=options.get('frame_scale', 2235),
                    account_name=account.nazwa_konta,
                    processing_mode=options.get('mode', 'Oryginalny'),
                    auto_fill_images=options.get('auto_fill_images', True),
                    save_processed_images=save_processed_images
                )
                logger.info(f"Generated {len(new_description)} description sections for offer {offer_id}")
                logger.info(f"Found {len(image_replacements)} image replacements for offer {offer_id}")
                
                # Handle process-only mode: save processed images without updating offer
                if save_images_only and save_processed_images:
                    logger.info(f"Process-only mode: saving processed images for offer {offer_id} without updating offer")
                    
                    # Extract processed image URLs from the template processing
                    processed_image_urls = []
                    for section in new_description:
                        for item in section.get('items', []):
                            if item.get('type') == 'IMAGE' and item.get('url'):
                                processed_image_urls.append(item['url'])
                    
                    # Also get processed images from image_replacements
                    for replacement_info in image_replacements.values():
                        if replacement_info.get('new_url'):
                            processed_image_urls.append(replacement_info['new_url'])
                    
                    # Remove duplicates
                    processed_image_urls = list(set(processed_image_urls))
                    
                    if processed_image_urls:
                        logger.info(f"Saving {len(processed_image_urls)} processed images for offer {offer_id}")
                        _save_images_to_minio(
                            minio_service, 
                            processed_image_urls, 
                            account.nazwa_konta, 
                            offer_id, 
                            'processed'
                        )
                        logger.info(f"Processed images saved for offer {offer_id}")
                    else:
                        logger.warning(f"No processed images found for offer {offer_id}")
                    
                    # Skip offer update and continue to next offer
                    successful_offers.append(offer_id)
                    continue
                
                # Prepare update payload - include current parameters to avoid validation conflicts
                payload = {"description": {"sections": new_description}}
                
                # Don't include parameters initially - let Allegro preserve existing ones
                # If we get parameter validation errors, we'll handle them with retry logic
                
                # Update image gallery if there are frame replacements
                if image_replacements:
                    logger.info(f"Updating image gallery for offer {offer_id} with {len(image_replacements)} replacements")
                    current_images = offer_details.get("images", [])[:]  # Create a copy
                    
                    # Apply image replacements to the gallery
                    # Process thumbnail duplications first, then normal replacements
                    thumbnail_insertions = {k: v for k, v in image_replacements.items() if v.get('action') == 'duplicate_thumbnail'}
                    normal_replacements = {k: v for k, v in image_replacements.items() if v.get('action') != 'duplicate_thumbnail'}
                    
                    # Handle thumbnail duplications first
                    for original_url, replacement_info in thumbnail_insertions.items():
                        new_url = replacement_info['new_url']
                        position = replacement_info['position']
                        original_placeholder = replacement_info['original_placeholder']
                        
                        # For thumbnails, insert the framed version at position 2 (index 1)
                        if position == 0:  # Thumbnail is at position 0
                            current_images.insert(1, new_url)
                            logger.info(f"Duplicated thumbnail {original_placeholder}: original kept at position 1, framed version inserted at position 2")
                    
                    # Handle normal replacements after thumbnail insertions (positions may have shifted)
                    for original_url, replacement_info in normal_replacements.items():
                        new_url = replacement_info['new_url']
                        original_position = replacement_info['position']
                        original_placeholder = replacement_info['original_placeholder']
                        
                        # Adjust position if thumbnail was inserted (shifts positions by 1)
                        position_offset = len(thumbnail_insertions)  # Number of thumbnail insertions
                        adjusted_position = original_position + position_offset if original_position > 0 else original_position
                        
                        # Ensure position is within bounds and find the original image
                        if 0 <= adjusted_position < len(current_images):
                            if current_images[adjusted_position] == original_url:
                                current_images[adjusted_position] = new_url
                                logger.info(f"Replaced image at position {adjusted_position + 1} ({original_placeholder}): {original_url} -> {new_url}")
                            else:
                                # Search for the original URL in case position shifted
                                found_at = -1
                                for i, img_url in enumerate(current_images):
                                    if img_url == original_url:
                                        found_at = i
                                        break
                                
                                if found_at >= 0:
                                    current_images[found_at] = new_url
                                    logger.info(f"Found and replaced image at position {found_at + 1} ({original_placeholder}): {original_url} -> {new_url}")
                                else:
                                    logger.warning(f"Could not find original image {original_url} to replace with {new_url}")
                        else:
                            logger.warning(f"Position {adjusted_position + 1} out of bounds for offer {offer_id} (has {len(current_images)} images)")
                    
                    # Handle duplicate removal carefully - preserve thumbnail duplicates when intentional
                    new_urls = {info['new_url'] for info in image_replacements.values()}
                    thumbnail_duplicates = {info['new_url'] for info in image_replacements.values() if info.get('action') == 'duplicate_thumbnail'}
                    
                    for i, img_url in enumerate(current_images):
                        # Don't remove thumbnail duplicates - they are intentional
                        if img_url in thumbnail_duplicates:
                            logger.info(f"Preserving intentional thumbnail duplicate at position {i + 1}: {img_url}")
                            continue
                            
                        # Remove other duplicates
                        if img_url in new_urls and i not in [info['position'] for info in image_replacements.values()]:
                            logger.info(f"Found duplicate framed image at position {i + 1}: {img_url} (keeping as-is)")
                            # Note: We log but don't actually remove - let Allegro handle duplicates
                    
                    payload["images"] = current_images
                    logger.info(f"Updated image gallery for offer {offer_id}: {len(current_images)} images")
                
                # Update the offer with both description and images (if applicable)
                logger.info(f"Updating offer {offer_id} with payload keys: {list(payload.keys())}")
                
                try:
                    provider.update_offer(offer_id, payload)
                    logger.info(f"Successfully updated offer {offer_id}")
                except requests.exceptions.HTTPError as patch_error:
                    # Try to handle parameter validation errors
                    clean_payload = _handle_parameter_validation_error(patch_error, offer_id, payload)
                    
                    if clean_payload:
                        logger.info(f"Retrying offer {offer_id} update with clean payload: {list(clean_payload.keys())}")
                        provider.update_offer(offer_id, clean_payload)
                        logger.info(f"Successfully updated offer {offer_id} on retry")
                    else:
                        # Re-raise the original error if we can't handle it
                        raise patch_error
                
                # Save processed images if requested (after processing)
                # Skip if we're in process-only mode since we already saved them earlier
                if save_processed_images and not save_images_only:
                    self.update_state(
                        state='PROGRESS', 
                        meta={
                            'status': f'Saving processed images for offer {i+1}/{total_offers} ({offer_id})', 
                            'progress': progress,
                            'successful': len(successful_offers),
                            'failed': len(failed_offers)
                        }
                    )
                    logger.info(f"Saving processed images for offer {offer_id}")
                    # Get the updated offer details to save processed images
                    updated_offer_details = provider.get_offer(offer_id)
                    _save_images_to_minio(
                        minio_service, 
                        updated_offer_details.get('images', []), 
                        account.nazwa_konta, 
                        offer_id, 
                        'processed'
                    )
                    logger.info(f"Processed images saved for offer {offer_id}")
                
                # Cleanup processed images from MinIO if user doesn't want to archive them
                # Images are already uploaded to Allegro, so we don't need duplicates in our MinIO
                # ONLY collect images that were ACTUALLY PROCESSED during this update (from image_replacements)
                # DO NOT collect original user images - they should be kept in MinIO for future use
                processed_image_urls = set()
                
                # Only collect images from image_replacements - these are newly created processed/framed images
                for replacement_info in image_replacements.values():
                    new_url = replacement_info.get('new_url')
                    if new_url and new_url.startswith(settings.MINIO_PUBLIC_URL):
                        processed_image_urls.add(new_url)
                
                if processed_image_urls:
                    if not save_processed_images and not save_images_only:
                        logger.info(f"🗑️  Cleaning up {len(processed_image_urls)} processed images from MinIO for offer {offer_id} (user chose not to archive)")
                        deleted_count = 0
                        for url in processed_image_urls:
                            if minio_service.delete_file_by_url(url):
                                deleted_count += 1
                        logger.info(f"✅ Successfully deleted {deleted_count}/{len(processed_image_urls)} processed images from MinIO for offer {offer_id}")
                    else:
                        archive_reason = "archiving enabled" if save_processed_images else "save-images-only mode"
                        logger.info(f"💾 Keeping {len(processed_image_urls)} processed images in MinIO for offer {offer_id} ({archive_reason})")
                
                successful_offers.append(offer_id)
                
                # Generate PDF if requested
                if options.get('generate_pdf', False):
                    try:
                        self.update_state(
                            state='PROGRESS', 
                            meta={
                                'status': f'Generating PDF for offer {i+1}/{total_offers} ({offer_id})', 
                                'progress': progress,
                                'successful': len(successful_offers),
                                'failed': len(failed_offers)
                            }
                        )
                        logger.info(f"Generating PDF for offer {offer_id}")
                        from app.infrastructure.marketplaces.allegro.services.pdf_generator import generate_single_product_card
                        logger.info(f"Successfully imported generate_single_product_card function")
                        
                        # Extract AI-generated description - find first 2 sections with TEXT, starting from index 2
                        # This matches the logic in extract_product_info() for consistency
                        ai_generated_description = None
                        if new_description:
                            sections_to_check = new_description[2:] if len(new_description) > 2 else new_description
                            logger.info(f"Searching for 2 text sections for PDF starting from index 2, checking {len(sections_to_check)} sections")
                            
                            section_texts = []
                            target_text_sections = 2
                            
                            for section_index, section in enumerate(sections_to_check):
                                actual_index = section_index + 2  # Adjust for starting at index 2
                                
                                if len(section_texts) >= target_text_sections:
                                    logger.info(f"Already collected {len(section_texts)} text sections for PDF, stopping")
                                    break
                                
                                if 'items' in section:
                                    section_content = []
                                    for item in section.get('items', []):
                                        if item.get('type') == 'TEXT' and 'content' in item:
                                            section_content.append(item['content'])
                                    
                                    # If this section has text content, add it
                                    if section_content:
                                        joined_content = ' '.join(section_content)
                                        section_texts.append(joined_content)
                                        logger.info(f"Section {actual_index} added to PDF description ({len(joined_content)} chars) - total: {len(section_texts)}")
                                    else:
                                        logger.info(f"Section {actual_index} has no TEXT items for PDF, skipping")
                            
                            # Join sections with double newline for visual separation
                            ai_generated_description = '\n\n'.join(section_texts) if section_texts else None
                        
                        if ai_generated_description:
                            logger.info(f"Using AI-generated description for PDF: {len(ai_generated_description)} characters")
                        
                        # strip_html parameter is no longer needed - stripping is done inside generate_single_product_card
                        pdf_result = generate_single_product_card(
                            access_token, 
                            offer_id, 
                            account.id,
                            custom_description=ai_generated_description
                        )
                        logger.info(f"PDF generation function returned: {pdf_result}")
                        
                        if pdf_result is True:
                            logger.info(f"PDF successfully generated and attached to offer {offer_id}")
                        elif pdf_result == "already_exists":
                            logger.warning(f"PDF already exists for offer {offer_id}")
                        else:
                            logger.error(f"PDF generation failed for offer {offer_id}")
                    except Exception as pdf_error:
                        logger.error(f"PDF generation failed for offer {offer_id}: {pdf_error}")
                        import traceback
                        logger.error(f"PDF generation traceback: {traceback.format_exc()}")
                        
            except Exception as e:
                # Use provider to normalize error
                error_msg = str(e)
                if 'provider' in locals():
                    try:
                        error_msg = provider.normalize_error(e)
                    except:
                        pass
                        
                logger.error(f"Failed to update offer {offer_id}: {error_msg}")
                failed_offers.append({"offer_id": offer_id, "error": error_msg})
        
        # Log to external system if user is admin or vsprint_employee
        webhook_error = None
        if user_id and successful_offers:
            from app.services.external_logging_service import is_admin_or_vsprint, send_logs_batch, create_log_entry
            try:
                if is_admin_or_vsprint(user_id, db):
                    # Create batch logs for all successful offers
                    logs = []
                    for offer_id in successful_offers:
                        logs.append(create_log_entry(
                            account_name=account.nazwa_konta,
                            kind="Edycja opisu oferty (pełna)",
                            offer_id=offer_id,
                            value="",
                            value_before=""
                        ))
                    
                    # Send batch
                    result_log = send_logs_batch(logs, db)
                    if not result_log["success"]:
                        webhook_error = result_log["error"]
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")
                webhook_error = str(e)
        
        # Final result
        result = {
            "status": "COMPLETED",
            "total_offers": total_offers,
            "successful_offers": successful_offers,
            "failed_offers": failed_offers,
            "success_count": len(successful_offers),
            "failure_count": len(failed_offers)
        }
        
        if webhook_error:
            result["webhook_logging_failed"] = True
            result["webhook_error"] = webhook_error
        
        self.update_state(state='SUCCESS', meta=result)
        return result

    except Exception as e:
        logger.error(f"Error in bulk_update_offers_with_template_task: {e}")
        self.update_state(
            state="FAILURE", 
            meta={
                "exc_type": type(e).__name__, 
                "exc_message": str(e),
                "successful_offers": locals().get('successful_offers', []),
                "failed_offers": locals().get('failed_offers', [])
            }
        )
        raise
    finally:
        db.close()


