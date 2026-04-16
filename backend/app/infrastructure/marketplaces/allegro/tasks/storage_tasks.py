"""Allegro Storage/MinIO Tasks"""
import io
import logging
import uuid
import zipfile
import requests
from typing import List, Optional
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db.repositories import AccountRepository
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='bulk_download_saved_images_task')
def bulk_download_saved_images_task(self, account_id: int, image_type: str, offer_ids: List[str] = None):
    """
    Task to create a bulk ZIP file containing saved images for multiple offers.
    
    Args:
        account_id: ID of the account
        image_type: 'original' or 'processed'
        offer_ids: List of offer IDs to include. If None, includes all offers.
    """
    db = SessionLocal()
    try:
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")
        
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise Exception("Invalid image type. Must be 'original' or 'processed'")
        
        bucket_name = f"offer-images-{image_type}"
        prefix = f"{account.nazwa_konta}/{image_type}/"
        
        # Get all objects from MinIO
        objects = minio_service.list_objects(bucket_name)
        matching_objects = []
        
        # Filter objects based on account and offer_ids
        for obj in objects:
            if obj.object_name.startswith(prefix):
                path_parts = obj.object_name.split('/')
                if len(path_parts) >= 4:
                    obj_offer_id = path_parts[2]
                    # Include if no specific offer_ids provided or if offer_id is in the list
                    if offer_ids is None or obj_offer_id in offer_ids:
                        matching_objects.append(obj)
        
        if not matching_objects:
            raise Exception(f"No {image_type} images found for the specified criteria")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Found {len(matching_objects)} images, creating ZIP file...',
                'progress': 10
            }
        )
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        processed_count = 0
        total_count = len(matching_objects)
        skipped_offers = []
        processed_offers = set()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for obj in matching_objects:
                try:
                    # Parse object path: account/type/offer_id/filename
                    path_parts = obj.object_name.split('/')
                    offer_id = path_parts[2]
                    filename = path_parts[3]
                    
                    # Get the image data from MinIO
                    image_url = minio_service.get_public_url(bucket_name, obj.object_name)
                    
                    # Download the image
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    
                    # Add to ZIP with folder structure: offer_id/filename
                    zip_path = f"{offer_id}/{filename}"
                    zip_file.writestr(zip_path, response.content)
                    
                    processed_offers.add(offer_id)
                    processed_count += 1
                    
                    # Update progress
                    progress = 10 + (processed_count / total_count) * 80
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Processing image {processed_count}/{total_count}...',
                            'progress': int(progress)
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing image {obj.object_name}: {e}")
                    # Continue processing other images
                    continue
        
        zip_buffer.seek(0)
        
        # Upload ZIP to a temporary bucket for download
        zip_filename = f"bulk_{image_type}_{account.nazwa_konta}_{uuid.uuid4().hex[:8]}.zip"
        
        # Upload to temporary downloads bucket
        temp_bucket = "temp-downloads"
        zip_url = minio_service.upload_file(
            bucket_name=temp_bucket,
            file_name=zip_filename,
            file_data=zip_buffer.getvalue(),
            content_type="application/zip"
        )
        
        # Final update
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'ZIP file created successfully!',
                'progress': 100
            }
        )
        
        return {
            "status": "SUCCESS",
            "download_url": zip_url,
            "filename": zip_filename,
            "total_images": processed_count,
            "total_offers": len(processed_offers),
            "processed_offers": list(processed_offers),
            "skipped_offers": skipped_offers
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE", 
            meta={"exc_type": type(e).__name__, "exc_message": str(e)}
        )
        raise
    finally:
        db.close()


@celery.task(bind=True, name='bulk_delete_saved_images_task')
def bulk_delete_saved_images_task(self, account_id: int, image_type: str, offer_ids: List[str] = None):
    """
    Task to delete saved images for multiple offers.
    
    Args:
        account_id: ID of the account
        image_type: 'original' or 'processed'
        offer_ids: List of offer IDs to include. If None, includes all offers.
    """
    db = SessionLocal()
    try:
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")
        
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise Exception("Invalid image type. Must be 'original' or 'processed'")
        
        bucket_name = f"offer-images-{image_type}"
        prefix = f"{account.nazwa_konta}/{image_type}/"
        
        # Get all objects from MinIO
        objects = minio_service.list_objects(bucket_name)
        matching_objects = []
        
        # Filter objects based on account and offer_ids
        for obj in objects:
            if obj.object_name.startswith(prefix):
                path_parts = obj.object_name.split('/')
                if len(path_parts) >= 4:
                    obj_offer_id = path_parts[2]
                    # Include if no specific offer_ids provided or if offer_id is in the list
                    if offer_ids is None or obj_offer_id in offer_ids:
                        matching_objects.append(obj)
        
        if not matching_objects:
            raise Exception(f"No {image_type} images found for the specified criteria")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Found {len(matching_objects)} images, starting deletion...',
                'progress': 10
            }
        )
        
        deleted_count = 0
        total_count = len(matching_objects)
        failed_deletions = []
        deleted_offers = set()
        
        for obj in matching_objects:
            try:
                # Parse object path: account/type/offer_id/filename
                path_parts = obj.object_name.split('/')
                offer_id = path_parts[2]
                filename = path_parts[3]
                
                # Delete the object from MinIO
                minio_service.client.remove_object(bucket_name, obj.object_name)
                
                deleted_offers.add(offer_id)
                deleted_count += 1
                
                # Update progress
                progress = 10 + (deleted_count / total_count) * 80
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Deleting image {deleted_count}/{total_count}...',
                        'progress': int(progress)
                    }
                )
                
                logger.info(f"Deleted image: {obj.object_name}")
                
            except Exception as e:
                logger.error(f"Error deleting image {obj.object_name}: {e}")
                failed_deletions.append({
                    'object_name': obj.object_name,
                    'error': str(e)
                })
                continue
        
        # Final update
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Bulk deletion completed!',
                'progress': 100
            }
        )
        
        return {
            "status": "SUCCESS",
            "deleted_count": deleted_count,
            "failed_count": len(failed_deletions),
            "total_offers": len(deleted_offers),
            "deleted_offers": list(deleted_offers),
            "failed_deletions": failed_deletions
        }

    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={"exc_type": type(e).__name__, "exc_message": str(e)}
        )
        raise
    finally:
        db.close()
