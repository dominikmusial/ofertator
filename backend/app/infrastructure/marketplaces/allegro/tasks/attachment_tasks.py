"""Allegro Attachment Tasks"""
import base64
import io
import logging
import requests
from typing import List, Optional, Dict
from PIL import Image
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db import schemas
from app.db.repositories import AccountRepository, BackupRepository
from app.infrastructure.marketplaces.factory import factory

logger = logging.getLogger(__name__)


def _process_image_for_allegro(file_content: bytes, file_name: str, attachment_type: str) -> tuple[bytes, str]:
    """
    Process and validate image for Allegro API compatibility.
    Converts WEBP, BMP, TIFF, GIF and other formats to JPEG.
    
    Returns:
        tuple: (processed_file_content, updated_file_name)
    """
    import os
    
    # Try to open and validate the image
    img = Image.open(io.BytesIO(file_content))
    img.verify()  # This will raise an exception if the image is corrupted
    
    # Re-open the image to get format info (verify() closes the image)
    img = Image.open(io.BytesIO(file_content))
    logger.info(f"Image format: {img.format}, size: {img.size}, mode: {img.mode}")
    
    # Convert to RGB if it's not already (some formats like RGBA might cause issues)
    needs_conversion = False
    if img.mode not in ['RGB', 'L']:  # L is for grayscale
        logger.info(f"Converting image from {img.mode} to RGB")
        img = img.convert('RGB')
        needs_conversion = True
    
    # Convert WEBP and other formats to JPEG for Allegro compatibility
    if img.format in ['WEBP', 'BMP', 'TIFF', 'GIF'] or needs_conversion:
        logger.info(f"Converting {img.format} image to JPEG for Allegro compatibility")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=95)
        file_content = img_buffer.getvalue()
        logger.info(f"Converted image size: {len(file_content)} bytes")
        
        # Update the filename to reflect the new format
        if not file_name.lower().endswith(('.jpg', '.jpeg')):
            base_name = os.path.splitext(file_name)[0]
            file_name = f"{base_name}.jpg"
            logger.info(f"Updated filename to: {file_name}")
    
    return file_content, file_name


@celery.task(bind=True, name='bulk_delete_attachments_task')
def bulk_delete_attachments_task(self, account_id: int, offer_ids: List[str], user_id: int = None):
    """
    Task to delete attachments from multiple offers and backup them for restore
    """
    logger.info(f"bulk_delete_attachments_task called with account_id={account_id}, offer_count={len(offer_ids)}")
    db = SessionLocal()
    
    # Store original attachments for restore functionality
    original_attachments = {}
    
    try:
        # Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        success_count = 0
        successful_offers = []
        failed_offers = []
        
        for i, offer_id in enumerate(offer_ids):
            try:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Usuwanie załączników z oferty {offer_id}...',
                        'progress': int((i / len(offer_ids)) * 100),
                        'current_offer': offer_id,
                        'processed': i,
                        'total': len(offer_ids),
                        'success_count': success_count,
                        'failed_count': len(failed_offers)
                    }
                )
                
                # Get current offer data
                current_data = provider.get_offer(offer_id)
                if not current_data:
                    failed_offers.append({
                        'offer_id': offer_id,
                        'error': 'Failed to get offer data'
                    })
                    continue
                
                # Backup original attachments
                if 'attachments' in current_data and current_data['attachments']:
                    original_attachments[offer_id] = current_data['attachments']
                    logger.info(f"Backed up {len(current_data['attachments'])} attachments for offer {offer_id}")
                    
                    # Remove attachments
                    update_data = {'attachments': []}
                    
                    # Use Allegro-specific attachment operations
                    provider = factory.get_provider_for_account(db, account_id)
                    if hasattr(provider, 'update_offer_attachments'):
                        if provider.update_offer_attachments(offer_id, update_data):
                            success_count += 1
                            successful_offers.append(offer_id)
                            logger.info(f"Successfully deleted attachments from offer {offer_id}")
                        else:
                            failed_offers.append({
                                'offer_id': offer_id,
                                'error': 'Failed to update offer attachments'
                            })
                    else:
                        logger.warning(f"Attachment operations not supported for marketplace: {provider.get_marketplace_type()}")
                else:
                    # No attachments to delete, but count as success
                    success_count += 1
                    successful_offers.append(offer_id)
                    logger.info(f"No attachments to delete for offer {offer_id}")
                    
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
                
                logger.error(f"HTTP error deleting attachments for offer {offer_id}: {error_msg}")
                failed_offers.append({"offer_id": offer_id, "error": error_msg})
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd dla oferty {offer_id}: {str(e)}"
                failed_offers.append({
                    'offer_id': offer_id,
                    'error': error_msg
                })
                logger.error(f"Error deleting attachments from offer {offer_id}: {error_msg}")

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
                            kind="Usunięcie załączników",
                            offer_id=offer_id,
                            value="",
                            value_before=""
                        ))
                    
                    # Send batch
                    result_log = send_logs_batch(logs, db)
                    if not result_log["success"]:
                        webhook_error = result_log["error"]
                        logger.error(f"Failed to log attachment deletions to external system: {webhook_error}")
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")
                webhook_error = str(e)

        result = {
            "status": "SUCCESS",
            "success_count": success_count,
            "failed_count": len(failed_offers),
            "total_offers": len(offer_ids),
            "failed_offers": failed_offers,
            "original_attachments": original_attachments  # Store for restore functionality
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


@celery.task(bind=True, name='bulk_restore_attachments_task')
def bulk_restore_attachments_task(self, account_id: int, offer_ids: List[str], original_attachments: dict, user_id: int = None):
    """
    Task to restore attachments to multiple offers
    """
    logger.info(f"bulk_restore_attachments_task called with account_id={account_id}, offer_count={len(offer_ids)}")
    db = SessionLocal()
    
    try:
        # Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        success_count = 0
        successful_offers = []
        failed_offers = []
        restorable_offers = [offer_id for offer_id in offer_ids if offer_id in original_attachments]
        
        for i, offer_id in enumerate(restorable_offers):
            try:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Przywracanie załączników do oferty {offer_id}...',
                        'progress': int((i / len(restorable_offers)) * 100),
                        'current_offer': offer_id,
                        'processed': i,
                        'total': len(restorable_offers),
                        'success_count': success_count,
                        'failed_count': len(failed_offers)
                    }
                )
                
                # Restore attachments
                update_data = {'attachments': original_attachments[offer_id]}
                
                # Use Allegro-specific attachment operations
                provider = factory.get_provider_for_account(db, account_id)
                if hasattr(provider, 'update_offer_attachments'):
                    if provider.update_offer_attachments(offer_id, update_data):
                        success_count += 1
                        successful_offers.append(offer_id)
                        logger.info(f"Successfully restored attachments to offer {offer_id}")
                    else:
                        failed_offers.append({
                            'offer_id': offer_id,
                            'error': 'Failed to restore attachments'
                        })
                else:
                    logger.warning(f"Attachment operations not supported for marketplace: {provider.get_marketplace_type()}")
                    
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
                
                logger.error(f"HTTP error restoring attachments for offer {offer_id}: {error_msg}")
                failed_offers.append({"offer_id": offer_id, "error": error_msg})
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd dla oferty {offer_id}: {str(e)}"
                failed_offers.append({
                    'offer_id': offer_id,
                    'error': error_msg
                })
                logger.error(f"Error restoring attachments to offer {offer_id}: {error_msg}")

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
                            kind="Przywrócenie załączników",
                            offer_id=offer_id,
                            value="",
                            value_before=""
                        ))
                    
                    # Send batch
                    result_log = send_logs_batch(logs, db)
                    if not result_log["success"]:
                        webhook_error = result_log["error"]
                        logger.error(f"Failed to log attachment restorations to external system: {webhook_error}")
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")
                webhook_error = str(e)

        result = {
            "status": "SUCCESS",
            "success_count": success_count,
            "failed_count": len(failed_offers),
            "total_offers": len(restorable_offers),
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


@celery.task(bind=True, name='upload_custom_attachment_task')
def upload_custom_attachment_task(self, account_id: int, offer_ids: List[str], attachment_type: str, file_name: str, file_content_b64: str, user_id: int = None):
    """
    Task to upload custom attachment to multiple offers
    """
    logger.info(f"upload_custom_attachment_task called with account_id={account_id}, offer_count={len(offer_ids)}, attachment_type={attachment_type}")
    db = SessionLocal()
    
    try:
        # Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import refresh_account_token_if_needed
        access_token = refresh_account_token_if_needed(db, account, for_api=False)

        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)

        # Decode base64 file content
        file_content = base64.b64decode(file_content_b64)
        logger.info(f"Decoded file content size: {len(file_content)} bytes")
        
        # Process image files for Allegro compatibility
        if attachment_type in ['ENERGY_LABEL', 'TIRE_LABEL'] and file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                file_content, file_name = _process_image_for_allegro(file_content, file_name, attachment_type)
            except Exception as e:
                logger.error(f"Image processing failed: {e}")
                raise Exception(f"Invalid image file: {e}")
        
        # First, create attachment object and upload file
        from app.infrastructure.marketplaces.allegro.services.pdf_generator import create_attachment_object, upload_file_content
        
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Tworzenie obiektu załącznika typu {attachment_type}...',
                'progress': 5,
                'processed': 0,
                'total': len(offer_ids) + 1  # +1 for file upload
            }
        )
        
        attachment_id, upload_url = create_attachment_object(access_token, attachment_type, file_name)
        if not attachment_id or not upload_url:
            raise Exception("Failed to create attachment object")
        
        # Determine content type based on attachment type and file processing
        content_type = 'application/pdf'
        if attachment_type in ['ENERGY_LABEL', 'TIRE_LABEL']:
            # For image attachment types, we always convert to JPEG for compatibility
            content_type = 'image/jpeg'
        elif file_name.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif file_name.lower().endswith('.png'):
            content_type = 'image/png'
        
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Przesyłanie pliku {file_name}...',
                'progress': 10,
                'processed': 0,
                'total': len(offer_ids) + 1
            }
        )
        
        if not upload_file_content(upload_url, file_content, access_token, content_type):
            # Provide more specific error message based on attachment type
            if attachment_type in ['ENERGY_LABEL', 'TIRE_LABEL']:
                raise Exception(f"Failed to upload file. {attachment_type} attachments require image files (JPG, PNG) only.")
            else:
                raise Exception(f"Failed to upload file. Check if the file format is compatible with {attachment_type} attachment type.")

        success_count = 0
        successful_offers = []
        failed_offers = []
        
        for i, offer_id in enumerate(offer_ids):
            try:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Dodawanie załącznika do oferty {offer_id}...',
                        'progress': int(((i + 1) / len(offer_ids)) * 90) + 10,
                        'current_offer': offer_id,
                        'processed': i,
                        'total': len(offer_ids),
                        'success_count': success_count,
                        'failed_count': len(failed_offers)
                    }
                )
                
                # Get current offer data
                current_data = provider.get_offer(offer_id)
                if not current_data:
                    failed_offers.append({
                        'offer_id': offer_id,
                        'error': 'Failed to get offer data'
                    })
                    continue
                
                # Add new attachment (remove existing attachment of same type)
                current_attachments = current_data.get('attachments', [])
                
                # Filter out existing attachments of the same type
                # We need to check attachment details since attachments don't include type
                filtered_attachments = []
                headers = {
                    'Accept': 'application/vnd.allegro.public.v1+json',
                    'Authorization': f'Bearer {access_token}'
                }
                
                for attachment in current_attachments:
                    if isinstance(attachment, dict):
                        attachment_id_existing = attachment.get('id')
                        if attachment_id_existing:
                            try:
                                # Get attachment details to check its type
                                details_url = f'https://api.allegro.pl/sale/offer-attachments/{attachment_id_existing}'
                                response = requests.get(details_url, headers=headers)
                                if response.status_code == 200:
                                    details = response.json()
                                    existing_type = details.get('type')
                                    # Only keep attachments that are NOT of the same type
                                    if existing_type != attachment_type:
                                        filtered_attachments.append(attachment)
                                else:
                                    # If we can't get details, keep the attachment to be safe
                                    filtered_attachments.append(attachment)
                            except Exception as e:
                                logger.error(f"Error checking attachment {attachment_id_existing}: {e}")
                                # If there's an error, keep the attachment to be safe
                                filtered_attachments.append(attachment)
                        else:
                            filtered_attachments.append(attachment)
                    else:
                        filtered_attachments.append(attachment)
                
                # Add the new attachment
                filtered_attachments.append({'id': attachment_id})
                
                update_data = {'attachments': filtered_attachments}
                
                # Use Allegro-specific attachment operations
                provider = factory.get_provider_for_account(db, account_id)
                if hasattr(provider, 'update_offer_attachments'):
                    if provider.update_offer_attachments(offer_id, update_data):
                        success_count += 1
                        successful_offers.append(offer_id)
                        logger.info(f"Successfully uploaded custom attachment to offer {offer_id}")
                    else:
                        failed_offers.append({
                            'offer_id': offer_id,
                            'error': 'Failed to update offer attachments'
                        })
                else:
                    logger.warning(f"Attachment operations not supported for marketplace: {provider.get_marketplace_type()}")
                    logger.info(f"Successfully added attachment to offer {offer_id}")
                    
            except requests.exceptions.HTTPError as e:
                # Handle specific HTTP errors with user-friendly messages
                if e.response.status_code == 403:
                    error_msg = f"Brak uprawnień do edycji oferty {offer_id}. Sprawdź czy oferta należy do tego konta i czy masz odpowiednie uprawnienia."
                elif e.response.status_code == 404:
                    error_msg = f"Oferta {offer_id} nie istnieje lub została usunięta z Allegro."
                elif e.response.status_code == 400:
                    error_msg = f"Nieprawidłowe dane dla oferty {offer_id}. Sprawdź format ID oferty i pliku załącznika."
                elif e.response.status_code == 429:
                    error_msg = f"Zbyt wiele zapytań dla oferty {offer_id}. Spróbuj ponownie za chwilę."
                else:
                    error_msg = f"Błąd HTTP {e.response.status_code} dla oferty {offer_id}: {str(e)}"
                
                logger.error(f"HTTP error adding attachment to offer {offer_id}: {error_msg}")
                failed_offers.append({"offer_id": offer_id, "error": error_msg})
            except Exception as e:
                error_msg = f"Nieoczekiwany błąd dla oferty {offer_id}: {str(e)}"
                failed_offers.append({
                    'offer_id': offer_id,
                    'error': error_msg
                })
                logger.error(f"Error adding attachment to offer {offer_id}: {error_msg}")

        # Log to external system if user is admin or vsprint_employee
        webhook_error = None
        if user_id and successful_offers:
            from app.services.external_logging_service import is_admin_or_vsprint, send_logs_batch, create_log_entry
            try:
                if is_admin_or_vsprint(user_id, db):
                    # Get account for logging
                    account = AccountRepository.get_by_id(db, account_id)
                    if account:
                        # Create batch logs for all successful offers
                        logs = []
                        for offer_id in successful_offers:
                            logs.append(create_log_entry(
                                account_name=account.nazwa_konta,
                                kind="Wgranie własnej karty produktowej",
                                offer_id=offer_id,
                                value=f"Typ: {attachment_type}",
                                value_before=""
                            ))
                        
                        # Send batch
                        result_log = send_logs_batch(logs, db)
                        if not result_log["success"]:
                            webhook_error = result_log["error"]
                            logger.error(f"Failed to log custom attachments to external system: {webhook_error}")
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")
                webhook_error = str(e)

        result = {
            "status": "SUCCESS",
            "success_count": success_count,
            "failed_count": len(failed_offers),
            "total_offers": len(offer_ids),
            "failed_offers": failed_offers,
            "attachment_id": attachment_id
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
