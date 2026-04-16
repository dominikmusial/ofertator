import uuid
import json
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl
from typing import List, Literal, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.minio_service import minio_service, MinioService
from app.infrastructure.marketplaces.allegro.services.image_processor import image_processor_service, ImageProcessorService
from app.db.session import get_db
from app.db import models
from app.db.repositories import AccountRepository
from app.db.schemas import (
    AccountImageResponse, SetLogoRequest, SetFillerRequest, DeleteImagesRequest
)
from app.core.auth import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ImageResponse(BaseModel):
    id: str
    url: str
    filename: str
    size: int
    upload_date: str
    content_type: str

class ProcessImageRequest(BaseModel):
    image_url: HttpUrl
    operations: List[Literal["remove_background", "crop_to_square", "add_blur_effect"]]

@router.get("/", response_model=List[ImageResponse])
async def list_images(
    search: Optional[str] = Query(None, description="Search images by filename"),
    minio: MinioService = Depends(lambda: minio_service)
):
    """
    Lists all images from MinIO storage with metadata.
    """
    try:
        bucket_name = "allegro-images"
        objects = minio.list_objects(bucket_name)
        
        images = []
        for obj in objects:
            # Filter by search if provided
            if search and search.lower() not in obj.object_name.lower():
                continue
                
            # Get object metadata
            try:
                stat = minio.get_object_stat(bucket_name, obj.object_name)
                images.append(ImageResponse(
                    id=obj.object_name,
                    url=minio.get_public_url(bucket_name, obj.object_name),
                    filename=obj.object_name,
                    size=stat.size if hasattr(stat, 'size') else obj.size,
                    upload_date=stat.last_modified.isoformat() if hasattr(stat, 'last_modified') else datetime.now().isoformat(),
                    content_type=stat.content_type if hasattr(stat, 'content_type') else 'image/jpeg'
                ))
            except Exception as e:
                # If we can't get metadata, create a basic entry
                images.append(ImageResponse(
                    id=obj.object_name,
                    url=minio.get_public_url(bucket_name, obj.object_name),
                    filename=obj.object_name,
                    size=obj.size if hasattr(obj, 'size') else 0,
                    upload_date=datetime.now().isoformat(),
                    content_type='image/jpeg'
                ))
        
        # Sort by upload date (newest first)
        images.sort(key=lambda x: x.upload_date, reverse=True)
        return images
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    minio: MinioService = Depends(lambda: minio_service)
):
    """
    Uploads an image to MinIO and returns its public URL.
    """
    try:
        # Generate a unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Read file content
        file_content = await file.read()

        # Upload to MinIO
        bucket_name = "allegro-images"
        public_url = minio.upload_file(
            bucket_name=bucket_name,
            file_name=unique_filename,
            file_data=file_content,
            content_type=file.content_type
        )

        return {"url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.post("/process")
async def process_image(
    request: ProcessImageRequest,
    processor: ImageProcessorService = Depends(lambda: image_processor_service)
):
    """
    Applies a series of processing steps to an image.
    """
    try:
        current_url = str(request.image_url)
        for operation in request.operations:
            if operation == "remove_background":
                current_url = processor.remove_background(current_url)
            elif operation == "crop_to_square":
                current_url = processor.crop_to_square(current_url)
            elif operation == "add_blur_effect":
                current_url = processor.add_blur_effect(current_url)
        
        return {"url": current_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

# Account-specific image management endpoints

@router.get("/account/{account_id}", response_model=List[AccountImageResponse])
async def list_account_images(
    account_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all images for a specific account."""
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get all images for this account
        images = db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id
        ).order_by(models.AccountImage.created_at.desc()).all()
        
        return [
            AccountImageResponse(
                id=img.id,
                filename=img.filename,
                original_filename=img.original_filename,
                url=f"/images/account/{account_id}/proxy/{img.filename}",
                content_type=img.content_type,
                size=img.size,
                is_logo=img.is_logo,
                is_filler=img.is_filler,
                filler_position=img.filler_position,
                created_at=img.created_at
            ) for img in images
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list account images: {str(e)}")

@router.post("/account/{account_id}/check-duplicates")
async def check_duplicate_filenames(
    account_id: int,
    filenames: List[str],
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check for duplicate filenames and suggest alternatives."""
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get existing filenames for this account
        existing_images = db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id
        ).all()
        existing_filenames = {img.original_filename for img in existing_images}
        
        def generate_unique_filename(filename: str) -> str:
            """Generate a unique filename by adding a counter if needed."""
            if filename not in existing_filenames:
                return filename
            
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            counter = 1
            while True:
                new_name = f"{name} ({counter})"
                if ext:
                    new_name += f".{ext}"
                if new_name not in existing_filenames:
                    return new_name
                counter += 1
        
        result = []
        for filename in filenames:
            is_duplicate = filename in existing_filenames
            suggested_name = generate_unique_filename(filename) if is_duplicate else filename
            result.append({
                "original_filename": filename,
                "is_duplicate": is_duplicate,
                "suggested_filename": suggested_name
            })
        
        return {"duplicates": result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check duplicates: {str(e)}")

@router.post("/account/{account_id}/upload")
async def upload_account_images(
    account_id: int,
    files: List[UploadFile] = File(...),
    filename_overrides: str = Form(None),  # Optional filename overrides as JSON string
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    minio: MinioService = Depends(lambda: minio_service)
):
    """Upload multiple images to a specific account."""
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Verify account exists
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get existing filenames for this account
        existing_images = db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id
        ).all()
        existing_filenames = {img.original_filename for img in existing_images}
        
        # Parse filename overrides if provided
        overrides = {}
        if filename_overrides:
            try:
                overrides = json.loads(filename_overrides)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid filename_overrides format")
        
        uploaded_images = []
        skipped_files = []
        
        for file in files:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                continue  # Skip non-image files
            
            # Determine the original filename to use
            original_filename = file.filename
            if overrides and file.filename in overrides:
                original_filename = overrides[file.filename]
            
            # Check for duplicates
            if original_filename in existing_filenames:
                skipped_files.append({
                    "filename": file.filename,
                    "reason": "Duplicate filename",
                    "existing_filename": original_filename
                })
                continue
            
            # Generate unique filename for storage
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"account_{account_id}_{uuid.uuid4()}.{file_extension}"
            
            # Read file content
            file_content = await file.read()
            
            # Upload to MinIO in account-specific bucket
            bucket_name = "account-images"
            public_url = minio.upload_file(
                bucket_name=bucket_name,
                file_name=unique_filename,
                file_data=file_content,
                content_type=file.content_type
            )
            
            # Save to database with proxy URL
            proxy_url = f"/images/account/{account_id}/proxy/{unique_filename}"
            db_image = models.AccountImage(
                account_id=account_id,
                filename=unique_filename,
                original_filename=original_filename,
                url=proxy_url,
                content_type=file.content_type,
                size=len(file_content)
            )
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            
            # Add to existing filenames set for subsequent files
            existing_filenames.add(original_filename)
            
            uploaded_images.append(AccountImageResponse(
                id=db_image.id,
                filename=db_image.filename,
                original_filename=db_image.original_filename,
                url=proxy_url,
                content_type=db_image.content_type,
                size=db_image.size,
                is_logo=db_image.is_logo,
                is_filler=db_image.is_filler,
                filler_position=db_image.filler_position,
                created_at=db_image.created_at
            ))
        
        return {
            "uploaded_images": uploaded_images, 
            "count": len(uploaded_images),
            "skipped_files": skipped_files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(e)}")

@router.post("/account/{account_id}/set-logo")
async def set_account_logo(
    account_id: int,
    image_id: int = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set an image as the account logo."""
    try:
        # Check access
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Clear existing logo
        db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id,
            models.AccountImage.is_logo == True
        ).update({"is_logo": False})
        
        # Set new logo
        image = db.query(models.AccountImage).filter(
            models.AccountImage.id == image_id,
            models.AccountImage.account_id == account_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image.is_logo = True
        db.commit()
        
        return {"message": "Logo set successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set logo: {str(e)}")

@router.post("/account/{account_id}/set-fillers")
async def set_account_fillers(
    account_id: int,
    image_ids: List[int] = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set images as account fillers."""
    try:
        # Check access
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Clear existing fillers
        db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id,
            models.AccountImage.is_filler == True
        ).update({"is_filler": False, "filler_position": None})
        
        # Set new fillers
        for i, image_id in enumerate(image_ids, 1):
            image = db.query(models.AccountImage).filter(
                models.AccountImage.id == image_id,
                models.AccountImage.account_id == account_id
            ).first()
            
            if image:
                image.is_filler = True
                image.filler_position = i
        
        db.commit()
        
        return {"message": f"Set {len(image_ids)} filler images successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set fillers: {str(e)}")

@router.delete("/account/{account_id}/images")
async def delete_account_images(
    account_id: int,
    image_ids: List[int] = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple images from an account."""
    try:
        # Check access
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Delete images from database
        deleted_count = db.query(models.AccountImage).filter(
            models.AccountImage.id.in_(image_ids),
            models.AccountImage.account_id == account_id
        ).delete(synchronize_session=False)
        
        db.commit()
        
        # Note: We could also delete from MinIO here, but for safety we'll keep the files
        # and implement a cleanup job separately
        
        return {"message": f"Deleted {deleted_count} images successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete images: {str(e)}")

@router.post("/account/{account_id}/unset-logo")
async def unset_account_logo(
    account_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove logo designation from account."""
    try:
        # Check access
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Clear logo
        db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id,
            models.AccountImage.is_logo == True
        ).update({"is_logo": False})
        
        db.commit()
        
        return {"message": "Logo removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove logo: {str(e)}")

@router.post("/account/{account_id}/unset-fillers")
async def unset_account_fillers(
    account_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove filler designation from all account images."""
    try:
        # Check access
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Clear fillers
        db.query(models.AccountImage).filter(
            models.AccountImage.account_id == account_id,
            models.AccountImage.is_filler == True
        ).update({"is_filler": False, "filler_position": None})
        
        db.commit()
        
        return {"message": "Filler images removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove fillers: {str(e)}") 

@router.get("/account/{account_id}/proxy/{filename}")
@router.head("/account/{account_id}/proxy/{filename}")
async def proxy_account_image(
    account_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    minio: MinioService = Depends(lambda: minio_service)
):
    """
    Proxy endpoint to serve account images from MinIO to the frontend.
    This bypasses CORS issues by serving images through the backend.
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get the image data directly from MinIO client
        bucket_name = "account-images"
        
        try:
            response = minio.client.get_object(bucket_name, filename)
            image_data = response.read()
            response.close()
            
            # Determine content type based on file extension
            content_type = "image/jpeg"
            if filename.lower().endswith('.png'):
                content_type = "image/png"
            elif filename.lower().endswith('.gif'):
                content_type = "image/gif"
            elif filename.lower().endswith('.webp'):
                content_type = "image/webp"
            
            return Response(
                content=image_data,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Content-Disposition": f"inline; filename={filename}",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
                }
            )
            
        except Exception as e:
            logger.error(f"Error proxying image {filename}: {e}")
            raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to proxy image: {str(e)}") 