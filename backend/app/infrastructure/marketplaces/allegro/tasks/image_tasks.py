"""Allegro Image Tasks"""
import io
import os
import logging
import requests
import base64
from typing import List, Dict, Optional
from PIL import Image
from datetime import datetime
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db import schemas
from app.db.repositories import AccountRepository, BackupRepository
from app.infrastructure.marketplaces.factory import factory
from app.services.minio_service import minio_service
from app.infrastructure.marketplaces.allegro.services.pdf_generator import pdf_generator_service

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='bulk_replace_image_task')
def bulk_replace_image_task(self, account_id: int, offer_ids: List[str], image_url_to_replace: str, new_image_url: str):
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception(f"Account with id {account_id} not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        # Replace 'localhost' with 'minio' for Docker networking
        internal_new_image_url = new_image_url.replace("localhost:9000", "minio:9000")

        try:
            image_response = requests.get(internal_new_image_url, stream=True)
            image_response.raise_for_status()
            image_data = image_response.content
        except requests.RequestException as e:
            raise Exception(f"Failed to download new image from {internal_new_image_url}: {e}")

        uploaded_image_url = provider.upload_image(image_data, "replacement.jpg")

        successful_offers = []
        failed_offers = []

        for offer_id in offer_ids:
            try:
                offer_details = provider.get_offer(offer_id)
                BackupRepository.create(db, schemas.OfferBackupCreate(offer_id=offer_id, account_id=account_id, backup_data=offer_details))
                
                images = offer_details.get("images", [])
                new_images = []
                image_found = False
                for img_url in images:
                    if img_url == image_url_to_replace:
                        new_images.append(uploaded_image_url)
                        image_found = True
                    else:
                        new_images.append(img_url)
                
                if not image_found:
                    failed_offers.append({"offer_id": offer_id, "reason": "Image to replace not found in offer."})
                    continue

                payload = {"images": new_images}
                provider.update_offer(offer_id, payload)
                successful_offers.append(offer_id)

            except Exception as e:
                failed_offers.append({"offer_id": offer_id, "reason": str(e)})

        return {
            "status": "COMPLETED",
            "successful_offers": successful_offers,
            "failed_offers": failed_offers
        }
    except Exception as e:
        logger.error(f"Error in bulk_replace_image_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()


@celery.task(bind=True, name='bulk_manage_description_image_task')
def bulk_manage_description_image_task(self, account_id: int, offer_ids: List[str], image_url: str, position: str):
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception(f"Account with id {account_id} not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        new_image_section = {"items": [{"type": "IMAGE", "url": image_url}]}

        successful_offers = []
        failed_offers = []

        for offer_id in offer_ids:
            try:
                offer_details = provider.get_offer(offer_id)
                BackupRepository.create(db, schemas.OfferBackupCreate(offer_id=offer_id, account_id=account_id, backup_data=offer_details))
                
                description = offer_details.get("description", {})
                sections = description.get("sections", [])

                if position == "PREPEND":
                    sections.insert(0, new_image_section)
                else: # APPEND
                    sections.append(new_image_section)
                
                payload = {"description": {"sections": sections}}
                provider.update_offer(offer_id, payload)
                successful_offers.append(offer_id)
                
            except Exception as e:
                reason = str(e)
                if isinstance(e, requests.exceptions.HTTPError):
                    try:
                        error_data = e.response.json()
                        if 'errors' in error_data and error_data['errors']:
                            first_error = error_data['errors'][0]
                            if first_error.get('code') == 'GallerySizeException':
                                reason = first_error.get('userMessage', 'Image gallery limit reached.')
                    except (ValueError, KeyError):
                        pass # Response not JSON or wrong structure, use default reason
                failed_offers.append({"offer_id": offer_id, "reason": reason})

        return {
            "status": "COMPLETED",
            "successful_offers": successful_offers,
            "failed_offers": failed_offers
        }
    except Exception as e:
        logger.error(f"Error in bulk_manage_description_image_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e

@celery.task(bind=True, name='bulk_update_thumbnails_task')
def bulk_update_thumbnails_task(self, account_id: int, offer_ids: List[str], file_mapping: List[Dict], extract_ids_from_names: bool = False, user_id: Optional[int] = None):
    """
    Task to bulk update thumbnails for multiple offers using uploaded files.
    """
    db = SessionLocal()
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing thumbnail update...', 'progress': 0})
        
        # Get account and validate
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)
        
        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)
        
        # Create offer_id to image mapping
        image_mapping = {}
        
        if extract_ids_from_names:
            # Extract offer IDs from filenames by removing extensions
            import os
            for file_info in file_mapping:
                filename = file_info['filename']
                # Remove file extension to get offer ID
                offer_id = os.path.splitext(filename)[0]
                # Only use if it's a valid number
                if offer_id.isdigit():
                    image_mapping[offer_id] = file_info
        else:
            # Manual mapping - map images to offer IDs in order
            if file_mapping and offer_ids:
                # Map images to offer IDs in order (first image -> first offer ID, etc.)
                for i, offer_id in enumerate(offer_ids):
                    # If there are more offer IDs than images, cycle through the images
                    # If there are more images than offer IDs, use only the first N images
                    image_index = i % len(file_mapping)
                    image_mapping[offer_id] = file_mapping[image_index]
        
        successful_offers = []
        failed_offers = []
        total_offers = len(image_mapping)
        
        for i, (offer_id, file_info) in enumerate(image_mapping.items()):
            try:
                # Update progress
                progress = int((i / total_offers) * 100)
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': f'Processing thumbnail {i+1}/{total_offers} ({offer_id})', 
                        'progress': progress,
                        'successful': len(successful_offers),
                        'failed': len(failed_offers),
                        'total_offers': total_offers
                    }
                )
                
                # Get current offer details and create backup
                offer_details = provider.get_offer(offer_id)
                BackupRepository.create(db, schemas.OfferBackupCreate(
                    offer_id=offer_id, 
                    account_id=account_id, 
                    backup_data=offer_details
                ))
                
                # Upload image using provider
                # Decode base64 back to binary data
                import base64
                image_bytes = base64.b64decode(file_info['content'])
                new_image_url = provider.upload_image(image_bytes, file_info.get('filename', 'thumbnail.jpg'))
                
                # Update offer thumbnail (first image) - fixed approach
                current_images = offer_details.get("images", [])
                
                # Remove any existing instances of the new image URL to prevent duplicates
                # This is the key fix - we need to remove the new image from anywhere it might exist
                filtered_images = [img for img in current_images if img != new_image_url]
                
                # Remember the old thumbnail before we change anything
                old_thumbnail = current_images[0] if current_images else None
                
                # Set the new image as the first image (thumbnail)
                if filtered_images:
                    filtered_images[0] = new_image_url
                else:
                    filtered_images = [new_image_url]
                
                logger.info(f"Updating thumbnail for offer {offer_id}: replacing first image with {new_image_url}")
                
                # Update offer with the filtered images
                payload = {"images": filtered_images}
                
                # Also update description if the old thumbnail appears there
                # This is crucial - the API adds back images that are referenced in the description
                if old_thumbnail and 'description' in offer_details and 'sections' in offer_details['description']:
                    description_updated = False
                    sections = offer_details['description']['sections'][:]
                    
                    for section in sections:
                        if 'items' in section:
                            for item in section['items']:
                                if item.get('type') == 'IMAGE' and item.get('url') == old_thumbnail:
                                    item['url'] = new_image_url
                                    description_updated = True
                    
                    if description_updated:
                        payload['description'] = {'sections': sections}
                        logger.info(f"Updated description references for offer {offer_id}")
                
                provider.update_offer(offer_id, payload)
                
                successful_offers.append(offer_id)
                logger.info(f"Successfully updated thumbnail for offer {offer_id}")
                
            except requests.exceptions.HTTPError as e:
                # Handle specific HTTP errors with user-friendly messages
                if e.response.status_code == 403:
                    error_msg = f"Brak uprawnień do edycji oferty {offer_id}. Sprawdź czy oferta należy do tego konta i czy masz odpowiednie uprawnienia."
                elif e.response.status_code == 404:
                    error_msg = f"Oferta {offer_id} nie istnieje lub została usunięta z Allegro."
                elif e.response.status_code == 400:
                    error_msg = f"Nieprawidłowe dane dla oferty {offer_id}. Sprawdź format ID oferty i plików obrazów."
                elif e.response.status_code == 429:
                    error_msg = f"Zbyt wiele zapytań dla oferty {offer_id}. Spróbuj ponownie za chwilę."
                else:
                    error_msg = f"Błąd HTTP {e.response.status_code} dla oferty {offer_id}: {str(e)}"
                
                logger.error(f"HTTP error updating thumbnail for offer {offer_id}: {error_msg}")
                failed_offers.append({"offer_id": offer_id, "error": error_msg})
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd dla oferty {offer_id}: {str(e)}"
                logger.error(f"Failed to update thumbnail for offer {offer_id}: {e}")
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
                            kind="Zmiana miniatury",
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
        logger.error(f"Error in bulk_update_thumbnails_task_new: {e}")
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

@celery.task(bind=True, name='restore_thumbnail_task')
def restore_thumbnail_task(self, account_id: int, offer_id: str):
    """
    Restores the thumbnail (first image) of an offer from its latest backup.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting thumbnail restore for offer {offer_id} on account {account_id}")

        # Get account and use centralized token refresh with proper error handling
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)
        
        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)
        
        # Get latest backup
        latest_backup = BackupRepository.get_latest(db, offer_id, account_id)
        if not latest_backup:
            raise Exception(f"No backup found for offer {offer_id}")
        
        # Extract images from backup
        backup_images = latest_backup.backup_data.get('images', [])
        if not backup_images:
            raise Exception(f"No images found in backup for offer {offer_id}")
        
        # Get current offer details
        current_offer = provider.get_offer(offer_id)
        current_images = current_offer.get('images', [])
        
        # Get the backup thumbnail URL
        backup_thumbnail_url = backup_images[0]
        
        # Remove any existing instances of the backup image URL to prevent duplicates
        # This is the key fix - we need to remove the backup image from anywhere it might exist
        filtered_images = [img for img in current_images if img != backup_thumbnail_url]
        
        # Remember the old thumbnail before we change anything
        old_thumbnail = current_images[0] if current_images else None
        
        # Set the backup image as the first image (thumbnail)
        if filtered_images:
            filtered_images[0] = backup_thumbnail_url
        else:
            filtered_images = [backup_thumbnail_url]
        
        logger.info(f"Restoring thumbnail for offer {offer_id}: replacing first image with {backup_thumbnail_url}")
        
        # Update offer with the filtered images
        payload = {"images": filtered_images}
        
        # Also update description if the old thumbnail appears there
        # This is crucial - the API adds back images that are referenced in the description
        if old_thumbnail and 'description' in current_offer and 'sections' in current_offer['description']:
            description_updated = False
            sections = current_offer['description']['sections'][:]
            
            for section in sections:
                if 'items' in section:
                    for item in section['items']:
                        if item.get('type') == 'IMAGE' and item.get('url') == old_thumbnail:
                            item['url'] = backup_thumbnail_url
                            description_updated = True
            
            if description_updated:
                payload['description'] = {'sections': sections}
                logger.info(f"Updated description references for offer {offer_id}")
        
        provider.update_offer(offer_id, payload)
        
        logger.info(f"Successfully restored thumbnail for offer {offer_id} from backup created at {latest_backup.created_at}")
        return {'status': 'SUCCESS', 'offer_id': offer_id}
        
    except requests.exceptions.HTTPError as e:
        # Handle specific HTTP errors with user-friendly messages
        if e.response.status_code == 403:
            error_msg = f"Brak uprawnień do edycji oferty {offer_id}. Sprawdź czy oferta należy do tego konta i czy masz odpowiednie uprawnienia."
        elif e.response.status_code == 404:
            error_msg = f"Oferta {offer_id} nie istnieje lub została usunięta z Allegro."
        elif e.response.status_code == 400:
            error_msg = f"Nieprawidłowe dane dla oferty {offer_id}. Sprawdź format ID oferty."
        elif e.response.status_code == 429:
            error_msg = f"Zbyt wiele zapytań dla oferty {offer_id}. Spróbuj ponownie za chwilę."
        else:
            error_msg = f"Błąd HTTP {e.response.status_code} dla oferty {offer_id}: {str(e)}"
        
        logger.error(f"HTTP error restoring thumbnail for offer {offer_id}: {error_msg}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': error_msg})
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Nieoczekiwany błąd dla oferty {offer_id}: {str(e)}"
        logger.error(f"Error restoring thumbnail for offer {offer_id}: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': error_msg})
        raise Exception(error_msg)
    finally:
        db.close()

@celery.task(bind=True, name='bulk_composite_image_replace_task')
def bulk_composite_image_replace_task(self, account_id: int, offer_ids: List[str], image_position: int, overlay_image_url: str):
    """
    Creates composite images by overlaying the provided image on top of existing images at specified positions.
    This recreates the functionality from the old tab7_replace_image.py.
    """
    from PIL import Image
    import requests
    from io import BytesIO
    import tempfile
    import os
    
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception(f"Account with id {account_id} not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        # Download the overlay image from MinIO
        internal_overlay_url = overlay_image_url.replace("localhost:9000", "minio:9000")
        try:
            overlay_response = requests.get(internal_overlay_url, stream=True)
            overlay_response.raise_for_status()
            overlay_img = Image.open(BytesIO(overlay_response.content)).convert('RGBA')
        except requests.RequestException as e:
            raise Exception(f"Failed to download overlay image from {internal_overlay_url}: {e}")

        successful_offers = []
        failed_offers = []

        for i, offer_id in enumerate(offer_ids):
            self.update_state(state='PROGRESS', meta={'current': i + 1, 'total': len(offer_ids), 'status': f'Processing offer {offer_id}'})
            
            try:
                # Get current offer data and create backup
                try:
                    offer_details = provider.get_offer(offer_id)
                except requests.HTTPError as e:
                    if e.response.status_code == 403:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Access denied (403): Offer may not belong to selected account or insufficient permissions"})
                        continue
                    elif e.response.status_code == 404:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Offer not found (404): Offer ID {offer_id} does not exist"})
                        continue
                    else:
                        failed_offers.append({"offer_id": offer_id, "reason": f"API Error ({e.response.status_code}): {str(e)}"})
                        continue
                
                BackupRepository.create(db, schemas.OfferBackupCreate(offer_id=offer_id, account_id=account_id, backup_data=offer_details))
                
                current_images = offer_details.get('images', [])
                if not current_images:
                    failed_offers.append({"offer_id": offer_id, "reason": "No images found in offer"})
                    continue
                    
                if image_position > len(current_images):
                    failed_offers.append({"offer_id": offer_id, "reason": f"Offer has only {len(current_images)} images, cannot replace position {image_position}"})
                    continue
                
                # Get the original image URL at the specified position
                original_image_url = current_images[image_position - 1]
                
                # Download the original image
                try:
                    original_response = requests.get(original_image_url)
                    original_response.raise_for_status()
                    original_img = Image.open(BytesIO(original_response.content)).convert('RGBA')
                except Exception as e:
                    failed_offers.append({"offer_id": offer_id, "reason": f"Failed to download original image: {str(e)}"})
                    continue
                
                # Create composite image (overlay on top of original)
                # Resize overlay to match original dimensions if needed
                if overlay_img.size != original_img.size:
                    overlay_resized = overlay_img.resize(original_img.size, Image.LANCZOS)
                else:
                    overlay_resized = overlay_img
                
                # Create composite
                if overlay_resized.mode in ('RGBA', 'LA') or (overlay_resized.mode == 'P' and 'transparency' in overlay_resized.info):
                    # Use alpha channel for compositing
                    composite = Image.alpha_composite(original_img, overlay_resized)
                else:
                    # If no alpha channel, just paste the overlay on top
                    original_img.paste(overlay_resized, (0, 0))
                    composite = original_img
                
                # Convert back to RGB for JPEG compression
                composite = composite.convert('RGB')
                
                # Save composite to temporary file and upload directly to Allegro
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    composite.save(temp_file.name, format="JPEG", quality=95)
                    
                    # Read file content and upload using provider
                    with open(temp_file.name, 'rb') as f:
                        file_content = f.read()
                    
                    # Upload using provider
                    new_image_url = provider.upload_image(file_content, f"composite_{offer_id}.jpg")
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
                
                # Update the offer with the new composite image
                new_images = current_images[:]
                new_images[image_position - 1] = new_image_url
                
                payload = {"images": new_images}
                
                # Also update description if the old image appears there
                if 'description' in offer_details and 'sections' in offer_details['description']:
                    description_updated = False
                    sections = offer_details['description']['sections']
                    for section in sections:
                        if 'items' in section:
                            for item in section['items']:
                                if item.get('type') == 'IMAGE' and item.get('url') == original_image_url:
                                    item['url'] = new_image_url
                                    description_updated = True
                    
                    if description_updated:
                        payload['description'] = offer_details['description']

                provider.update_offer(offer_id, payload)
                successful_offers.append(offer_id)

            except Exception as e:
                failed_offers.append({"offer_id": offer_id, "reason": str(e)})

        return {
            "status": "COMPLETED",
            "successful_offers": successful_offers,
            "failed_offers": failed_offers,
            "total_processed": len(offer_ids),
            "success_count": len(successful_offers),
            "failure_count": len(failed_offers)
        }
    except Exception as e:
        logger.error(f"Error in bulk_composite_image_replace_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()

@celery.task(bind=True, name='bulk_restore_image_position_task')
def bulk_restore_image_position_task(self, account_id: int, offer_ids: List[str], image_position: int):
    """
    Restores images at specified positions from backups.
    This recreates the restore functionality from the old tab7_replace_image.py.
    """
    import json
    
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception(f"Account with id {account_id} not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        successful_offers = []
        failed_offers = []

        for i, offer_id in enumerate(offer_ids):
            self.update_state(state='PROGRESS', meta={'current': i + 1, 'total': len(offer_ids), 'status': f'Restoring offer {offer_id}'})
            
            try:
                # Get backup data
                backup = BackupRepository.get_latest(db, offer_id, account_id)
                if not backup:
                    failed_offers.append({"offer_id": offer_id, "reason": "No backup found for offer"})
                    continue
                
                # Parse backup data
                if isinstance(backup.backup_data, str):
                    try:
                        old_data = json.loads(backup.backup_data)
                    except json.JSONDecodeError as e:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Failed to parse backup data: {str(e)}"})
                        continue
                else:
                    old_data = backup.backup_data
                
                # Check if backup has images
                if 'images' not in old_data or not old_data['images']:
                    failed_offers.append({"offer_id": offer_id, "reason": "No images found in backup"})
                    continue
                
                # Check if the specified position exists in backup
                if image_position > len(old_data['images']):
                    failed_offers.append({"offer_id": offer_id, "reason": f"Backup has only {len(old_data['images'])} images, cannot restore position {image_position}"})
                    continue
                
                # Get current offer data
                try:
                    current_data = provider.get_offer(offer_id)
                except requests.HTTPError as e:
                    if e.response.status_code == 403:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Access denied (403): Offer may not belong to selected account or insufficient permissions"})
                        continue
                    elif e.response.status_code == 404:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Offer not found (404): Offer ID {offer_id} does not exist"})
                        continue
                    else:
                        failed_offers.append({"offer_id": offer_id, "reason": f"API Error ({e.response.status_code}): {str(e)}"})
                        continue
                
                current_images = current_data.get('images', [])
                
                # Get the old image URL for the specified position
                old_image_url = old_data['images'][image_position - 1]
                
                # Get current image URL for description replacement
                current_image_url = None
                if image_position <= len(current_images):
                    current_image_url = current_images[image_position - 1]
                
                # Create new images list
                new_images = current_images[:]
                
                # Extend list if needed
                while len(new_images) < image_position:
                    new_images.append("")
                
                # Replace the image at the specified position
                new_images[image_position - 1] = old_image_url
                
                payload = {'images': new_images}
                
                # Update description if the current image appears there
                if 'description' in current_data and 'sections' in current_data['description'] and current_image_url:
                    description_updated = False
                    sections = current_data['description']['sections'][:]
                    
                    for section in sections:
                        if 'items' in section:
                            for item in section['items']:
                                if item.get('type') == 'IMAGE' and item.get('url') == current_image_url:
                                    item['url'] = old_image_url
                                    description_updated = True
                    
                    if description_updated:
                        payload['description'] = {'sections': sections}

                provider.update_offer(offer_id, payload)
                successful_offers.append(offer_id)

            except Exception as e:
                failed_offers.append({"offer_id": offer_id, "reason": str(e)})

        return {
            "status": "COMPLETED",
            "successful_offers": successful_offers,
            "failed_offers": failed_offers,
            "total_processed": len(offer_ids),
            "success_count": len(successful_offers),
            "failure_count": len(failed_offers)
        }
    except Exception as e:
        logger.error(f"Error in bulk_restore_image_position_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()

@celery.task(bind=True, name='bulk_banner_images_task')
def bulk_banner_images_task(self, account_id: int, offer_ids: List[str], settings: dict):
    """
    Creates banners with product image overlays based on specified dimensions and settings.
    This recreates the functionality from the old tab9_banner_images.py.
    """
    from PIL import Image, ImageDraw
    import requests
    from io import BytesIO
    import tempfile
    import os
    import numpy as np
    
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception(f"Account with id {account_id} not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        # Extract settings
        banner_width = settings['width']
        banner_height = settings['height']
        size_percent = settings['size_percent']
        horizontal_pos_percent = settings['horizontal_position_percent']
        vertical_pos_percent = settings['vertical_position_percent']
        shape = settings['shape']
        remove_bg = settings['remove_background']

        successful_offers = []
        failed_offers = []
        banners_updated = 0

        def create_circular_mask(size):
            """Create a circular mask for the product image"""
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)
            return mask

        def create_square_mask(size):
            """Create a square mask for the product image"""
            return Image.new('L', size, 255)  # Fully opaque mask

        def remove_background(image):
            """Remove white/light background from an image"""
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
                
            data = np.array(image)
            r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
            
            # Calculate brightness
            brightness = (0.299*r + 0.587*g + 0.114*b)
            
            # Create mask for light colors
            threshold = 240
            mask = np.zeros_like(a)
            mask[brightness > threshold] = 255
            
            # Softer threshold for edge pixels
            edge_lower = 220
            edge_pixels = (brightness <= threshold) & (brightness > edge_lower)
            if np.any(edge_pixels):
                mask[edge_pixels] = ((brightness[edge_pixels] - edge_lower) / 
                                    (threshold - edge_lower) * 255).astype(np.uint8)
            
            # Invert the mask and apply
            mask = 255 - mask
            data[:,:,3] = np.minimum(a, mask)
            
            return Image.fromarray(data)

        def create_banner_with_overlay(banner_img, product_img, offer_id):
            """Create a banner with product image overlay"""
            try:
                banner_img = banner_img.convert('RGBA')
                product_img = product_img.convert('RGBA')
                
                # Apply background removal if selected
                if remove_bg:
                    product_img = remove_background(product_img)
                
                # Calculate size based on banner height and user setting
                size_factor = size_percent / 100.0
                product_aspect = product_img.width / product_img.height
                new_height = int(banner_height * size_factor)
                new_width = int(new_height * product_aspect)
                
                # Resize product image
                product_img = product_img.resize((new_width, new_height), Image.LANCZOS)
                
                # Calculate positions
                right_padding = int(banner_width * horizontal_pos_percent / 100.0)
                y_position = int((banner_height - product_img.height) * vertical_pos_percent / 100.0)
                
                # Apply shape mask
                if shape == "circle":
                    mask = create_circular_mask(product_img.size)
                    shaped_product_img = Image.new('RGBA', product_img.size, (0, 0, 0, 0))
                    shaped_product_img.paste(product_img, (0, 0), mask)
                elif shape == "square":
                    mask = create_square_mask(product_img.size)
                    shaped_product_img = product_img
                else:  # "original"
                    shaped_product_img = product_img
                
                # Paste product image onto banner
                x_position = banner_width - shaped_product_img.width - right_padding
                banner_img.paste(shaped_product_img, (x_position, y_position), shaped_product_img)
                
                return banner_img
                
            except Exception as e:
                raise Exception(f"Error creating banner overlay for offer {offer_id}: {str(e)}")



        for i, offer_id in enumerate(offer_ids):
            self.update_state(state='PROGRESS', meta={
                'current': i + 1, 
                'total': len(offer_ids), 
                'status': f'Processing offer {offer_id}',
                'banners_updated': banners_updated
            })
            
            try:
                # Get current offer data
                try:
                    offer_details = provider.get_offer(offer_id)
                except requests.HTTPError as e:
                    if e.response.status_code == 403:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Access denied (403): Offer may not belong to selected account"})
                        continue
                    elif e.response.status_code == 404:
                        failed_offers.append({"offer_id": offer_id, "reason": f"Offer not found (404): Offer ID {offer_id} does not exist"})
                        continue
                    else:
                        failed_offers.append({"offer_id": offer_id, "reason": f"API Error ({e.response.status_code}): {str(e)}"})
                        continue
                
                # Create backup
                BackupRepository.create(db, schemas.OfferBackupCreate(
                    offer_id=offer_id, 
                    account_id=account_id, 
                    backup_data=offer_details
                ))
                
                current_images = offer_details.get('images', [])
                if not current_images:
                    failed_offers.append({"offer_id": offer_id, "reason": "No images found in offer"})
                    continue
                
                # Get the first product image for overlay
                first_product_image_url = current_images[0]
                
                # Download product image
                try:
                    product_response = requests.get(first_product_image_url)
                    product_response.raise_for_status()
                    product_img = Image.open(BytesIO(product_response.content))
                except Exception as e:
                    failed_offers.append({"offer_id": offer_id, "reason": f"Failed to download product image: {str(e)}"})
                    continue
                
                # Find matching banners in gallery and description
                matching_banners = []
                
                # Check gallery images
                for img_idx, image_url in enumerate(current_images):
                    try:
                        img_response = requests.get(image_url)
                        img_response.raise_for_status()
                        img = Image.open(BytesIO(img_response.content))
                        img_width, img_height = img.size
                        
                        if img_width == banner_width and img_height == banner_height:
                            matching_banners.append(('gallery', img_idx, image_url, img))
                    except Exception as e:
                        logger.warning(f"Failed to check image dimensions for offer {offer_id}, image {img_idx}: {e}")
                
                # Check description images
                if 'description' in offer_details and 'sections' in offer_details['description']:
                    sections = offer_details['description']['sections']
                    for section_idx, section in enumerate(sections):
                        if 'items' in section:
                            for item_idx, item in enumerate(section['items']):
                                if item.get('type') == 'IMAGE':
                                    image_url = item.get('url')
                                    if image_url:
                                        try:
                                            img_response = requests.get(image_url)
                                            img_response.raise_for_status()
                                            img = Image.open(BytesIO(img_response.content))
                                            img_width, img_height = img.size
                                            
                                            if img_width == banner_width and img_height == banner_height:
                                                matching_banners.append(('description', section_idx, item_idx, image_url, img))
                                        except Exception as e:
                                            logger.warning(f"Failed to check description image for offer {offer_id}: {e}")
                
                if not matching_banners:
                    failed_offers.append({"offer_id": offer_id, "reason": f"No banners found with dimensions {banner_width}x{banner_height}"})
                    continue
                
                # Process each matching banner
                offer_updated = False
                new_images = current_images[:]
                new_description = None
                
                for banner_info in matching_banners:
                    try:
                        if banner_info[0] == 'gallery':
                            _, img_idx, banner_url, banner_img = banner_info
                            
                            # Create banner with overlay
                            composite_banner = create_banner_with_overlay(banner_img, product_img, offer_id)
                            
                            # Convert to RGB and save as temporary file
                            composite_banner = composite_banner.convert('RGB')
                            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                                composite_banner.save(temp_file.name, format="JPEG", quality=95)
                                
                                # Upload using provider
                                with open(temp_file.name, 'rb') as f:
                                    file_content = f.read()
                                new_image_url = provider.upload_image(file_content, f"banner_gallery_{offer_id}.jpg")
                                
                                # Clean up temp file
                                os.unlink(temp_file.name)
                            
                            # Update gallery
                            new_images[img_idx] = new_image_url
                            offer_updated = True
                            banners_updated += 1
                            
                        else:  # description
                            _, section_idx, item_idx, banner_url, banner_img = banner_info
                            
                            # Create banner with overlay
                            composite_banner = create_banner_with_overlay(banner_img, product_img, offer_id)
                            
                            # Convert to RGB and save as temporary file
                            composite_banner = composite_banner.convert('RGB')
                            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                                composite_banner.save(temp_file.name, format="JPEG", quality=95)
                                
                                # Upload using provider
                                with open(temp_file.name, 'rb') as f:
                                    file_content = f.read()
                                new_image_url = provider.upload_image(file_content, f"banner_desc_{offer_id}.jpg")
                                
                                # Clean up temp file
                                os.unlink(temp_file.name)
                            
                            # Update description
                            if new_description is None:
                                new_description = offer_details['description'].copy()
                            new_description['sections'][section_idx]['items'][item_idx]['url'] = new_image_url
                            offer_updated = True
                            banners_updated += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to process banner for offer {offer_id}: {e}")
                        failed_offers.append({"offer_id": offer_id, "reason": f"Failed to process banner: {str(e)}"})
                        continue
                
                # Update the offer if any banners were processed
                if offer_updated:
                    payload = {"images": new_images}
                    if new_description is not None:
                        payload["description"] = new_description
                    
                    provider.update_offer(offer_id, payload)
                    successful_offers.append(offer_id)
                
            except Exception as e:
                failed_offers.append({"offer_id": offer_id, "reason": str(e)})

        return {
            "status": "COMPLETED",
            "successful_offers": successful_offers,
            "failed_offers": failed_offers,
            "total_processed": len(offer_ids),
            "success_count": len(successful_offers),
            "failure_count": len(failed_offers),
            "banners_updated": banners_updated
        }
    except Exception as e:
        logger.error(f"Error in bulk_banner_images_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()

@celery.task(bind=True, name='bulk_restore_banners_task')
def bulk_restore_banners_task(self, account_id: int, offer_ids: List[str]):
    """
    Restores original banners from database backups.
    """
    db = SessionLocal()
    try:
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception(f"Account with id {account_id} not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        successful_offers = []
        failed_offers = []

        for i, offer_id in enumerate(offer_ids):
            self.update_state(state='PROGRESS', meta={
                'current': i + 1, 
                'total': len(offer_ids), 
                'status': f'Restoring banners for offer {offer_id}'
            })
            
            try:
                # Get the latest backup for this offer
                backup = BackupRepository.get_latest(db, offer_id, account_id)
                if not backup:
                    failed_offers.append({"offer_id": offer_id, "reason": "No backup found for this offer"})
                    continue
                
                backup_data = backup.backup_data
                if not backup_data:
                    failed_offers.append({"offer_id": offer_id, "reason": "Invalid backup data"})
                    continue
                
                # Prepare update data from backup
                update_data = {}
                
                # Restore gallery images
                if 'images' in backup_data and backup_data['images']:
                    # Deduplicate images to avoid Allegro API validation errors
                    original_images = backup_data['images']
                    unique_images = []
                    seen_urls = set()
                    
                    for image_url in original_images:
                        if image_url not in seen_urls:
                            unique_images.append(image_url)
                            seen_urls.add(image_url)
                        else:
                            logger.warning(f"Duplicate image found and removed in offer {offer_id}: {image_url}")
                    
                    update_data['images'] = unique_images
                    logger.info(f"Restoring {len(unique_images)} images (removed {len(original_images) - len(unique_images)} duplicates) for offer {offer_id}")
                
                # Restore description
                if 'description' in backup_data and backup_data['description']:
                    update_data['description'] = backup_data['description']
                
                if not update_data:
                    failed_offers.append({"offer_id": offer_id, "reason": "No images or description found in backup"})
                    continue
                
                # Update the offer
                provider.update_offer(offer_id, update_data)
                successful_offers.append(offer_id)
                
            except Exception as e:
                failed_offers.append({"offer_id": offer_id, "reason": str(e)})

        return {
            "status": "COMPLETED",
            "successful_offers": successful_offers,
            "failed_offers": failed_offers,
            "total_processed": len(offer_ids),
            "success_count": len(successful_offers),
            "failure_count": len(failed_offers)
        }
    except Exception as e:
        logger.error(f"Error in bulk_restore_banners_task: {e}")
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        db.close()

@celery.task(bind=True, name='bulk_generate_product_cards_task')
def bulk_generate_product_cards_task(self, account_id: int, offer_ids: List[str], user_id: int = None):
    """
    Task to generate product cards for multiple offers.
    Note: HTML stripping is now always done internally in generate_single_product_card.
    """
    logger.info(f"bulk_generate_product_cards_task called with account_id={account_id}, offer_count={len(offer_ids)}")
    db = SessionLocal()
    
    try:
        # Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)
        account_name = account.nazwa_konta

        success_count = 0
        successful_offers = []
        failed_offers = []
        
        for i, offer_id in enumerate(offer_ids):
            try:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Generowanie karty produktowej dla oferty {offer_id}...',
                        'progress': int((i / len(offer_ids)) * 100),
                        'current_offer': offer_id,
                        'processed': i,
                        'total': len(offer_ids),
                        'success_count': success_count,
                        'failed_count': len(failed_offers)
                    }
                )
                
                from app.infrastructure.marketplaces.allegro.services.pdf_generator import generate_single_product_card
                
                result = generate_single_product_card(access_token, offer_id, account_id)
                if result is True:
                    success_count += 1
                    successful_offers.append(offer_id)
                    logger.info(f"Successfully generated product card for offer {offer_id}")
                elif result == "already_exists":
                    failed_offers.append({
                        'offer_id': offer_id,
                        'error': 'Karta produktowa już istnieje dla tej oferty. Aby wygenerować nową, najpierw usuń istniejącą kartę.'
                    })
                    logger.warning(f"Product card already exists for offer {offer_id}")
                elif result is False:
                    failed_offers.append({
                        'offer_id': offer_id,
                        'error': 'Failed to generate product card'
                    })
                    logger.error(f"Failed to generate product card for offer {offer_id}")
                else:
                    # result is an error message string
                    failed_offers.append({
                        'offer_id': offer_id,
                        'error': result
                    })
                    logger.error(f"Error generating product card for offer {offer_id}: {result}")
                    
            except requests.exceptions.HTTPError as e:
                # Handle specific HTTP errors with user-friendly messages
                if e.response.status_code == 403:
                    error_msg = f"Brak uprawnień do odczytu oferty {offer_id}. Sprawdź czy oferta należy do tego konta i czy masz odpowiednie uprawnienia."
                elif e.response.status_code == 404:
                    error_msg = f"Oferta {offer_id} nie istnieje lub została usunięta z Allegro."
                elif e.response.status_code == 400:
                    error_msg = f"Nieprawidłowe dane dla oferty {offer_id}. Sprawdź format ID oferty."
                elif e.response.status_code == 429:
                    error_msg = f"Zbyt wiele zapytań dla oferty {offer_id}. Spróbuj ponownie za chwilę."
                else:
                    error_msg = f"Błąd HTTP {e.response.status_code} dla oferty {offer_id}: {str(e)}"
                
                logger.error(f"HTTP error generating product card for offer {offer_id}: {error_msg}")
                failed_offers.append({"offer_id": offer_id, "error": error_msg})
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd dla oferty {offer_id}: {str(e)}"
                failed_offers.append({
                    'offer_id': offer_id,
                    'error': error_msg
                })
                logger.error(f"Error generating product card for offer {offer_id}: {error_msg}")

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
                            account_name=account_name,
                            kind="Generowanie karty produktowej",
                            offer_id=offer_id,
                            value="",
                            value_before=""
                        ))
                    
                    # Send batch
                    result_log = send_logs_batch(logs, db)
                    if not result_log["success"]:
                        webhook_error = result_log["error"]
                        logger.error(f"Failed to log product cards to external system: {webhook_error}")
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")
                webhook_error = str(e)

        result = {
            "status": "SUCCESS",
            "success_count": success_count,
            "failed_count": len(failed_offers),
            "total_offers": len(offer_ids),
            "failed_offers": failed_offers
        }
        
        if webhook_error:
            result["webhook_logging_failed"] = True
            result["webhook_error"] = webhook_error

        return result

    except Exception as e:
        self.update_state(
            state="FAILURE", 
            meta={"exc_type": type(e).__name__, "exc_message": str(e)}
        )
        raise
    finally:
        db.close()


