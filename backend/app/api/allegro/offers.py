from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body, File, Form, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, root_validator
import logging
import json
import base64

from app.db.session import get_db
from app.db import models
from app.db.repositories import AccountRepository, BackupRepository, TemplateRepository
from app.core.auth import get_current_user
from app.services.minio_service import minio_service
from app.infrastructure.marketplaces.factory import factory
from app.infrastructure.marketplaces.allegro.tasks import offer_tasks, image_tasks, attachment_tasks, title_tasks, storage_tasks
from app.db import schemas as db_schemas
from celery.result import AsyncResult
from app.celery_worker import celery
import requests


router = APIRouter()
logger = logging.getLogger(__name__)

class TaskResponse(db_schemas.BaseModel):
    task_id: str
    offer_id: str

class GeneratePdfRequest(db_schemas.BaseModel):
    account_id: int

class TitleEditItem(db_schemas.BaseModel):
    offer_id: str
    title: str

class BulkEditTitlesRequest(db_schemas.BaseModel):
    account_id: int
    items: List[TitleEditItem]

class BulkCopyRequest(db_schemas.BaseModel):
    requests: List[db_schemas.CopyOfferRequest]

class TemplateProcessingOptions(db_schemas.BaseModel):
    mode: str = "Oryginalny"  # Image processing mode
    frame_scale: int = 2235
    generate_pdf: bool = False
    auto_fill_images: bool = False
    save_original_images: bool = False
    save_processed_images: bool = False
    save_images_only: bool = False
    save_location: Optional[str] = None
    custom_path: Optional[str] = None

class TemplateSection(BaseModel):
    # Support both formats: backend format (items) and frontend format (type + values)
    items: Optional[List[dict]] = None
    type: Optional[str] = None
    values: Optional[dict] = None
    id: Optional[str] = None  # Frontend section ID
    
    @root_validator(pre=True)
    def validate_section_format(cls, values):
        """Ensure either items format or type+values format is provided"""
        # Check if we have items (backend format)
        if 'items' in values and values['items'] is not None:
            return values
        
        # Check if we have type and values (frontend format)
        if 'type' in values and 'values' in values:
            # For frontend format, set items to None so it passes validation
            # The actual conversion will happen in _extract_frame_info_from_template
            values['items'] = None
            return values
        
        # Neither format provided - this is an error
        raise ValueError('Either items (backend format) or type+values (frontend format) must be provided')

class TemplateContent(db_schemas.BaseModel):
    prompt: str = ""
    sections: List[TemplateSection]

class BulkUpdateOffersRequest(db_schemas.BaseModel):
    account_id: int
    offer_ids: List[str]
    template: TemplateContent
    options: TemplateProcessingOptions

@router.post("/{offer_id}/generate-pdf", response_model=TaskResponse)
def generate_offer_pdf(
    offer_id: str,
    request: GeneratePdfRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers a background task to generate a PDF product sheet for an offer.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    task = offer_tasks.generate_pdf_task.delay(request.account_id, offer_id)
    return TaskResponse(task_id=task.id, offer_id=offer_id)

@router.post("/bulk-edit-titles", response_model=db_schemas.TaskBase)
def bulk_edit_titles(
    request: BulkEditTitlesRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers a bulk update of offer titles using parallel tasks with batch logging.
    Uses Celery chord for parallel execution with final callback for batch logging.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Use Celery chord: parallel tasks + callback for batch logging
    from celery import chord
    
    # Create parallel tasks for each title update
    parallel_tasks = [
        title_tasks.update_offer_title_task.s(
            account_id=request.account_id,
            offer_id=item.offer_id,
            title=item.title,
            user_id=current_user.id
        )
        for item in request.items
    ]
    
    # Execute as chord: all tasks run in parallel, then callback with results
    chord_result = chord(parallel_tasks)(title_tasks.batch_log_title_updates_callback.s())

    return {"task_id": chord_result.id}

@router.post("/duplicate-offers-with-titles", response_model=db_schemas.TaskBase)
def duplicate_offers_with_titles(
    request: db_schemas.DuplicateOffersRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Duplicates offers with new titles on the same account using parallel tasks.
    Uses Celery chord for parallel execution with final callback for batch logging.
    Useful for A/B testing with different titles.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Use Celery chord: parallel tasks + callback for batch logging
    from celery import chord
    
    # Create parallel tasks for each duplication
    parallel_tasks = [
        offer_tasks.duplicate_offer_with_title_task.s(
            account_id=request.account_id,
            offer_id=item.offer_id,
            new_title=item.new_title,
            activate_immediately=request.activate_immediately,
            user_id=current_user.id
        )
        for item in request.items
    ]
    
    # Execute as chord: all tasks run in parallel, then callback with results
    chord_result = chord(parallel_tasks)(title_tasks.batch_duplicate_offers_callback.s())

    return {"task_id": chord_result.id}

@router.post("/bulk-change-status", response_model=List[TaskResponse])
def bulk_change_status(
    request: db_schemas.OfferStatusChangeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers a bulk status change for offers.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    tasks = []
    for offer_id in request.offer_ids:
        task = offer_tasks.update_offer_status_task.delay(
            account_id=request.account_id,
            offer_id=offer_id,
            status=request.status.value,
            user_id=current_user.id
        )
        tasks.append(TaskResponse(task_id=task.id, offer_id=offer_id))

    return tasks

@router.post("/copy", response_model=List[TaskResponse])
def copy_offers(
    request: BulkCopyRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers background tasks to copy multiple offers.
    """
    tasks = []
    for copy_request in request.requests:
        # Check access to source account
        if not AccountRepository.can_user_access_account(db, current_user, copy_request.source_account_id):
            raise HTTPException(status_code=403, detail=f"Access denied to source account {copy_request.source_account_id}")
        
        # Check access to target account
        if not AccountRepository.can_user_access_account(db, current_user, copy_request.options.target_account_id):
            raise HTTPException(status_code=403, detail=f"Access denied to target account {copy_request.options.target_account_id}")
        
        # Basic validation
        source_account = AccountRepository.get_by_id(db, copy_request.source_account_id)
        if not source_account:
            raise HTTPException(status_code=404, detail=f"Source account {copy_request.source_account_id} not found")
        
        target_account = AccountRepository.get_by_id(db, copy_request.options.target_account_id)
        if not target_account:
            raise HTTPException(status_code=404, detail=f"Target account {copy_request.options.target_account_id} not found")

        task = offer_tasks.copy_offer_task.delay(
            source_account_id=copy_request.source_account_id,
            source_offer_id=copy_request.source_offer_id,
            options=copy_request.options.model_dump()
        )
        tasks.append(TaskResponse(task_id=task.id, offer_id=copy_request.source_offer_id))

    return tasks

@router.post("/bulk-edit", response_model=db_schemas.TaskBase)
def universal_bulk_edit(
    request: db_schemas.BulkEditRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Universally bulk edit various attributes of offers.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    task = offer_tasks.bulk_edit_task.delay(
        request.account_id,
        request.offer_ids,
        request.actions.model_dump(exclude_none=True)
    )
    return {"task_id": task.id}

@router.post("/bulk-replace-image", response_model=db_schemas.TaskBase)
def bulk_replace_image(
    request: db_schemas.BulkImageReplaceRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk replaces an image URL in specified offers.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    task = image_tasks.bulk_replace_image_task.delay(
        request.account_id,
        request.offer_ids,
        request.image_url_to_replace,
        request.new_image_url
    )
    return {"task_id": task.id}

# Old bulk-update-thumbnails endpoint removed - replaced with new multipart version below

@router.post("/bulk-manage-description-image", response_model=db_schemas.TaskBase)
def bulk_manage_description_image(
    request: db_schemas.BulkDescriptionImageRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adds or removes an image from the description of multiple offers.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    task = image_tasks.bulk_manage_description_image_task.delay(
        request.account_id,
        request.offer_ids,
        request.image_url,
        request.position.value
    )
    return {"task_id": task.id}

@router.post("/bulk-composite-image-replace", response_model=db_schemas.TaskBase)
def bulk_composite_image_replace(
    request: db_schemas.BulkCompositeImageReplaceRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates composite images by overlaying provided image on existing images at specified positions.
    This recreates the functionality from the old desktop app's "Replace Image" feature.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Validate image position
    if request.image_position < 1 or request.image_position > 16:
        raise HTTPException(status_code=400, detail="Image position must be between 1 and 16")
    
    task = image_tasks.bulk_composite_image_replace_task.delay(
        request.account_id,
        request.offer_ids,
        request.image_position,
        request.overlay_image_url
    )
    return {"task_id": task.id}

@router.post("/bulk-restore-image-position", response_model=db_schemas.TaskBase)
def bulk_restore_image_position(
    request: db_schemas.BulkRestoreImagePositionRequest, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores images at specified positions from backups.
    This recreates the restore functionality from the old desktop app's "Replace Image" feature.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Validate image position
    if request.image_position < 1 or request.image_position > 16:
        raise HTTPException(status_code=400, detail="Image position must be between 1 and 16")
    
    task = image_tasks.bulk_restore_image_position_task.delay(
        request.account_id,
        request.offer_ids,
        request.image_position
    )
    return {"task_id": task.id}

@router.post("/{offer_id}/restore-backup", response_model=db_schemas.TaskBase)
def restore_offer_backup(
    offer_id: str, 
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores an offer to its last backed-up state.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    latest_backup = BackupRepository.get_latest(db, offer_id, account_id)
    if not latest_backup:
        raise HTTPException(status_code=404, detail=f"No backup found for offer {offer_id}")

    task = offer_tasks.restore_offer_from_backup_task.delay(account_id, offer_id)
    return {"task_id": task.id}

@router.get("/{offer_id}", response_model=Dict)
def get_offer_details(
    offer_id: str, 
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the details of a single offer from Allegro.
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
        access_token = get_valid_token_with_reauth_handling(db, account_id)
        
        # Use provider to get offer details
        provider = factory.get_provider_for_account(db, account_id)
        offer_details = provider.get_offer(offer_id)
        return offer_details
    except Exception as e:
        logger.error(f"Failed to get offer {offer_id} details: {e}", exc_info=True)
        # Re-raise as HTTPException to be handled by FastAPI
        raise HTTPException(status_code=500, detail=f"Failed to retrieve offer details: {str(e)}")

@router.get("/")
def list_offers(
    account_id: int, 
    status: Optional[str] = None, 
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    category_id: Optional[str] = None,
    offer_ids: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List seller offers with enhanced filtering capabilities.
    
    Query Parameters:
        - account_id: Account ID (required)
        - status: Filter by publication status (ACTIVE, ENDED, etc.)
        - search: Search by offer title/name
        - limit: Number of results per page (default: 50, max: 1000)
        - offset: Pagination offset (default: 0)
        - price_from: Minimum price filter
        - price_to: Maximum price filter
        - category_id: Filter by category ID
        - offer_ids: Comma-separated list of offer IDs to filter
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Validate input parameters
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be >= 0")
        if price_from is not None and price_from < 0:
            raise HTTPException(status_code=400, detail="price_from must be >= 0")
        if price_to is not None and price_to < 1:
            raise HTTPException(status_code=400, detail="price_to must be >= 1")
        if price_from is not None and price_to is not None and price_from > price_to:                                                                          
            raise HTTPException(status_code=400, detail="price_from must be <= price_to")                                                                      

        from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
        access_token = get_valid_token_with_reauth_handling(db, account_id)

        # Parse offer_ids if provided
        offer_ids_list = None
        if offer_ids:
            offer_ids_list = [id.strip() for id in offer_ids.split(',') if id.strip()]

        # Use marketplace provider
        provider = factory.get_provider_for_account(db, account_id)
        api_response = provider.list_offers({
            'status': status,
            'search': search,
            'limit': limit,
            'offset': offset,
            'price_from': price_from,
            'price_to': price_to,
            'category_id': category_id,
            'offer_ids': offer_ids_list
        })
        
        if api_response is None:
            logger.error("Provider list_offers returned None")
            return {"items": [], "total": 0}

        # Handle both dict and list responses
        # Allegro returns dict: {'offers': [...], 'count': X, 'totalCount': Y}
        # Decathlon returns list directly: [{...}, {...}]
        if isinstance(api_response, dict):
            logger.info(f"Provider list_offers response keys: {list(api_response.keys())}")
            offers_list = api_response.get('offers') or api_response.get('items') or []
        elif isinstance(api_response, list):
            logger.info(f"Provider list_offers returned list with {len(api_response)} offers")
            offers_list = api_response
        else:
            logger.error(f"Unexpected response type: {type(api_response)}")
            return {"items": [], "total": 0}

        items = []
        for offer in offers_list or []:
            if not offer:
                continue
            selling = offer.get('sellingMode') or {}
            price_obj = selling.get('price') or {}
            publication = offer.get('publication') or {}
            category = offer.get('category') or {}
            primary_image = offer.get('primaryImage') or {}
            items.append({
                'id': offer.get('id'),
                'name': offer.get('name') or offer.get('title'),
                'title': offer.get('name') or offer.get('title'),  # Keep for backward compatibility
                'price': price_obj.get('amount'),
                'quantity': offer.get('stock', {}).get('available'),
                'status': publication.get('status'),
                'category_id': category.get('id'),
                'image_url': primary_image.get('url')
            })

        # Calculate total count
        if isinstance(api_response, dict):
            total = api_response.get('totalCount') or api_response.get('count') or len(items)
        else:
            total = len(items)
        
        return {'items': items, 'total': total}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list offers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list offers")

@router.get("/categories/{account_id}")
def get_offer_categories(
    account_id: int,
    parent_id: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Allegro categories for filtering offers.
    
    Query Parameters:
        - parent_id: Get subcategories of a parent category (optional)
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
        access_token = get_valid_token_with_reauth_handling(db, account_id)

        # Use marketplace provider to get categories
        provider = factory.get_provider_for_account(db, account_id)
        api_response = provider.get_categories(parent_id)
        
        return api_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")

@router.get('/task-status/{task_id}')
def get_task_status(task_id: str):
    try:
        task_result = AsyncResult(task_id, app=celery)
        
        # Handle different task states
        if task_result.state == 'PENDING':
            return {
                'task_id': task_id,
                'status': 'PENDING',
                'result': None,
                'meta': None
            }
        elif task_result.state == 'PROGRESS':
            return {
                'task_id': task_id,
                'status': 'PROGRESS',
                'result': task_result.info  # Return info as result for frontend compatibility
            }
        elif task_result.state == 'SUCCESS':
            return {
                'task_id': task_id,
                'status': 'SUCCESS',
                'result': task_result.result,
                'meta': None
            }
        elif task_result.state == 'FAILURE':
            # Handle failure case safely
            try:
                result = task_result.result
                if isinstance(result, Exception):
                    error_info = {
                        'error': str(result),
                        'exc_type': type(result).__name__
                    }
                else:
                    error_info = result
            except Exception:
                error_info = {
                    'error': 'Task failed with unknown error',
                    'exc_type': 'Unknown'
                }
            
            return {
                'task_id': task_id,
                'status': 'FAILURE',
                'result': error_info,
                'meta': getattr(task_result, 'info', None)
            }
        else:
            return {
                'task_id': task_id,
                'status': task_result.state,
                'result': None,
                'meta': getattr(task_result, 'info', None)
            }
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'result': {'error': f'Failed to get task status: {str(e)}'},
            'meta': None
        }

@router.post("/bulk-update-with-template", response_model=db_schemas.TaskBase)
def bulk_update_offers_with_template(
    request: BulkUpdateOffersRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk updates multiple offers using a template with processing options.
    Similar to the old Python app's update_offers functionality.
    """
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Validate offer IDs
    if not request.offer_ids:
        raise HTTPException(status_code=400, detail="No offer IDs provided")

    # Start the bulk update task
    task = offer_tasks.bulk_update_offers_with_template_task.delay(
        account_id=request.account_id,
        offer_ids=request.offer_ids,
        template_data=request.template.model_dump(),
        options=request.options.model_dump(),
        user_id=current_user.id
    )

    return {"task_id": task.id}

@router.post("/bulk-restore", response_model=List[TaskResponse])
def bulk_restore_offers(
    account_id: int,
    offer_ids: List[str] = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers bulk restore of offers from their backups.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    tasks = []
    for offer_id in offer_ids:
        task = offer_tasks.restore_offer_from_backup_task.delay(account_id, offer_id)
        tasks.append(TaskResponse(task_id=task.id, offer_id=offer_id))

    return tasks

# New endpoints for Titles functionality
@router.post("/pull-titles", response_model=db_schemas.TaskBase)
def pull_titles(
    account_id: int,
    offer_ids: List[str] = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pulls titles from specified offers and returns them as downloadable data.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    task = title_tasks.pull_titles_task.delay(account_id, offer_ids)
    return {"task_id": task.id}

@router.post("/optimize-titles-ai", response_model=db_schemas.TaskBase)
async def optimize_titles_ai(
    request: db_schemas.OptimizeTitlesAIRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize product titles using AI (Tytułomat functionality).
    Returns task_id for progress polling. Use /task-status/{task_id} to check progress.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Validate titles
    if not request.titles:
        raise HTTPException(status_code=400, detail="No titles provided")
    
    # Validate max titles based on whether parameters are included
    max_titles = 20 if request.include_offer_parameters else 50
    if len(request.titles) > max_titles:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many titles. Maximum is {max_titles} titles {'with' if request.include_offer_parameters else 'without'} parameters."
        )
    
    # Convert titles to dict format for Celery serialization
    titles_data = [
        {
            'offer_id': t.offer_id,
            'current_title': t.current_title
        }
        for t in request.titles
    ]
    
    # Launch the task
    task = title_tasks.optimize_titles_ai_task.delay(
        titles_data=titles_data,
        user_id=current_user.id,
        account_id=request.account_id,
        include_offer_parameters=request.include_offer_parameters
    )
    
    return {"task_id": task.id}


# New endpoints for Thumbnails functionality
@router.post("/bulk-update-thumbnails", response_model=List[TaskResponse])
async def bulk_update_thumbnails(
    account_id: int,  # Query parameter
    offer_ids: str = Form(""),  # JSON string of offer IDs
    image_files: List[UploadFile] = File(...),
    extract_ids_from_names: bool = Form(False),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk updates thumbnails for multiple offers.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Parse offer IDs from JSON string
    import json
    try:
        parsed_offer_ids = json.loads(offer_ids) if offer_ids else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid offer_ids format")
    
    # Process uploaded files and create mapping
    import base64
    file_mapping = []
    for file in image_files:
        file_content = await file.read()
        # Convert binary data to base64 for Celery serialization
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        file_mapping.append({
            "filename": file.filename,
            "content": file_content_b64,
            "content_type": file.content_type
        })

    task = image_tasks.bulk_update_thumbnails_task.delay(
        account_id,
        parsed_offer_ids,
        file_mapping,
        extract_ids_from_names,
        user_id=current_user.id
    )
    
    # Return a single task for all operations
    return [TaskResponse(task_id=task.id, offer_id="bulk")]

@router.post("/restore-thumbnails", response_model=List[TaskResponse])
def restore_thumbnails(
    account_id: int,
    offer_ids: List[str] = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores old thumbnails for multiple offers from backups.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    tasks = []
    for offer_id in offer_ids:
        # Check if backup exists
        latest_backup = BackupRepository.get_latest(db, offer_id, account_id)
        if not latest_backup:
            continue  # Skip offers without backups
            
        task = image_tasks.restore_thumbnail_task.delay(account_id, offer_id)
        tasks.append(TaskResponse(task_id=task.id, offer_id=offer_id))

    return tasks

# Banner Images functionality
@router.post("/bulk-banner-images", response_model=db_schemas.TaskBase)
def bulk_banner_images(
    request: db_schemas.BulkBannerImagesRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates banners with product image overlays based on specified dimensions and settings.
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    task = image_tasks.bulk_banner_images_task.delay(
        account_id=request.account_id,
        offer_ids=request.offer_ids,
        settings=request.settings.model_dump()
    )
    return {"task_id": task.id}

@router.post("/bulk-restore-banners", response_model=db_schemas.TaskBase)
def bulk_restore_banners(
    request: db_schemas.BulkRestoreBannersRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk restore banner images for multiple offers
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    task = image_tasks.bulk_restore_banners_task.delay(
        request.account_id,
        request.offer_ids
    )
    return {"task_id": task.id}

@router.post("/bulk-generate-product-cards", response_model=db_schemas.TaskBase)
def bulk_generate_product_cards(
    request: db_schemas.BulkGenerateProductCardsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate product cards for multiple offers
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    task = image_tasks.bulk_generate_product_cards_task.delay(
        request.account_id,
        request.offer_ids,
        current_user.id
    )
    return {"task_id": task.id}

@router.post("/bulk-delete-attachments", response_model=db_schemas.TaskBase)
def bulk_delete_attachments(
    request: db_schemas.BulkDeleteAttachmentsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete attachments from multiple offers (with backup for restore)
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    task = attachment_tasks.bulk_delete_attachments_task.delay(
        request.account_id,
        request.offer_ids,
        current_user.id
    )
    return {"task_id": task.id}

@router.post("/bulk-restore-attachments", response_model=db_schemas.TaskBase)
def bulk_restore_attachments(
    request: db_schemas.BulkRestoreAttachmentsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore attachments to multiple offers
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, request.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Use the original_attachments from the request
    task = attachment_tasks.bulk_restore_attachments_task.delay(
        request.account_id,
        request.offer_ids,
        request.original_attachments,
        current_user.id
    )
    return {"task_id": task.id}

@router.post("/upload-custom-attachment")
async def upload_custom_attachment(
    account_id: int = Form(...),
    offer_ids: str = Form(...),  # JSON string of offer IDs
    attachment_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload custom attachment to multiple offers
    """
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Parse offer IDs
    try:
        offer_ids_list = json.loads(offer_ids)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid offer_ids format")

    # Read file content and encode as base64 for Celery serialization
    file_content = await file.read()
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    task = attachment_tasks.upload_custom_attachment_task.delay(
        account_id,
        offer_ids_list,
        attachment_type,
        file.filename,
        file_content_b64,
        current_user.id
    )
    return {"task_id": task.id}

@router.get("/saved-images/{account_id}")
async def list_saved_images(
    account_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all saved images for an account, organized by offer and type.
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        from app.services.minio_service import minio_service
        
        # List images from both original and processed buckets
        saved_images = {
            'original': {},
            'processed': {}
        }
        
        for image_type in ['original', 'processed']:
            bucket_name = f"offer-images-{image_type}"
            try:
                objects = minio_service.list_objects(bucket_name)
                
                for obj in objects:
                    # Parse the filename: account/type/offer_id/image_N.ext
                    path_parts = obj.object_name.split('/')
                    if len(path_parts) >= 4 and path_parts[0] == account.nazwa_konta:
                        offer_id = path_parts[2]
                        filename = path_parts[3]
                        
                        if offer_id not in saved_images[image_type]:
                            saved_images[image_type][offer_id] = []
                        
                        # Use proxy URL instead of direct MinIO URL (without /api/v1 prefix since axios will add it)
                        proxy_url = f"/allegro/offers/saved-images/{account_id}/proxy/{image_type}/{offer_id}/{filename}"
                        
                        saved_images[image_type][offer_id].append({
                            'filename': filename,
                            'url': proxy_url,
                            'size': obj.size if hasattr(obj, 'size') else 0
                        })
                        
            except Exception as e:
                logger.warning(f"Could not list {image_type} images: {e}")
        
        return {
            'account_name': account.nazwa_konta,
            'saved_images': saved_images
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list saved images: {str(e)}")

@router.get("/saved-images/{account_id}/download/{image_type}/{offer_id}")
async def download_saved_images_zip(
    account_id: int,
    image_type: str,
    offer_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download saved images for a specific offer as a ZIP file.
    """
    try:
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise HTTPException(status_code=400, detail="Invalid image type. Must be 'original' or 'processed'")
        
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        from app.services.minio_service import minio_service
        import zipfile
        import io
        import requests
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        bucket_name = f"offer-images-{image_type}"
        prefix = f"{account.nazwa_konta}/{image_type}/{offer_id}/"
        
        try:
            objects = minio_service.list_objects(bucket_name)
            matching_objects = [obj for obj in objects if obj.object_name.startswith(prefix)]
            
            if not matching_objects:
                raise HTTPException(status_code=404, detail=f"No {image_type} images found for offer {offer_id}")
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for obj in matching_objects:
                    # Get the image data from MinIO
                    image_url = minio_service.get_public_url(bucket_name, obj.object_name)
                    
                    # Download the image
                    response = requests.get(image_url)
                    response.raise_for_status()
                    
                    # Add to ZIP with just the filename (not the full path)
                    filename = obj.object_name.split('/')[-1]
                    zip_file.writestr(filename, response.content)
            
            zip_buffer.seek(0)
            
            # Return ZIP file as response
            from fastapi.responses import Response
            
            zip_filename = f"{account.nazwa_konta}_{image_type}_{offer_id}.zip"
            
            return Response(
                content=zip_buffer.getvalue(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
            )
            
        except Exception as e:
            logger.error(f"Error creating ZIP file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create ZIP file: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download images: {str(e)}")

@router.delete("/saved-images/{account_id}/delete/{image_type}/{offer_id}/{filename}")
async def delete_saved_image(
    account_id: int,
    image_type: str,
    offer_id: str,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific saved image.
    """
    try:
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise HTTPException(status_code=400, detail="Invalid image type. Must be 'original' or 'processed'")
        
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        from app.services.minio_service import minio_service
        
        # Construct the object path
        bucket_name = f"offer-images-{image_type}"
        object_path = f"{account.nazwa_konta}/{image_type}/{offer_id}/{filename}"
        
        try:
            # Check if the object exists
            minio_service.get_object_stat(bucket_name, object_path)
            
            # Delete the object
            minio_service.client.remove_object(bucket_name, object_path)
            
            logger.info(f"Deleted image: {object_path} from bucket {bucket_name}")
            return {"message": f"Successfully deleted {filename}"}
            
        except Exception as e:
            logger.error(f"Error deleting image {object_path}: {e}")
            raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

@router.get("/saved-images/{account_id}/proxy/{image_type}/{offer_id}/{filename}")
async def proxy_saved_image(
    account_id: int,
    image_type: str,
    offer_id: str,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint to serve saved images from MinIO to the frontend.
    """
    try:
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise HTTPException(status_code=400, detail="Invalid image type. Must be 'original' or 'processed'")
        
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        from app.services.minio_service import minio_service
        
        # Construct the object path
        bucket_name = f"offer-images-{image_type}"
        object_path = f"{account.nazwa_konta}/{image_type}/{offer_id}/{filename}"
        
        try:
            # Get the image data directly from MinIO client
            response = minio_service.client.get_object(bucket_name, object_path)
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
            
            from fastapi.responses import Response
            return Response(
                content=image_data,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Content-Disposition": f"inline; filename={filename}"
                }
            )
            
        except Exception as e:
            logger.error(f"Error proxying image {object_path}: {e}")
            raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to proxy image: {str(e)}")

@router.post("/saved-images/{account_id}/bulk-download/{image_type}")
async def bulk_download_saved_images(
    account_id: int,
    image_type: str,
    offer_ids: Optional[List[str]] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a bulk download task for saved images.
    
    Args:
        account_id: ID of the account
        image_type: 'original' or 'processed'
        offer_ids: Optional list of specific offer IDs to include. If None, includes all offers.
    """
    try:
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise HTTPException(status_code=400, detail="Invalid image type. Must be 'original' or 'processed'")
        
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Start the bulk download task
        task = storage_tasks.bulk_download_saved_images_task.delay(
            account_id=account_id,
            image_type=image_type,
            offer_ids=offer_ids
        )
        
        return {"task_id": task.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bulk download: {str(e)}")

@router.get("/saved-images/{account_id}/bulk-download/status/{task_id}")
async def get_bulk_download_status(
    account_id: int,
    task_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a bulk download task.
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get task result
        task_result = AsyncResult(task_id, app=celery)
        
        if task_result.state == 'PENDING':
            return {
                "state": "PENDING",
                "status": "Task is waiting to be processed..."
            }
        elif task_result.state == 'PROGRESS':
            return {
                "state": "PROGRESS",
                "status": task_result.info.get('status', 'Processing...'),
                "progress": task_result.info.get('progress', 0)
            }
        elif task_result.state == 'SUCCESS':
            return {
                "state": "SUCCESS",
                "result": task_result.result
            }
        else:
            # Task failed
            return {
                "state": "FAILURE",
                "error": str(task_result.info)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/saved-images/{account_id}/bulk-download/download/{filename}")
async def download_bulk_zip(
    account_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the bulk ZIP file created by the bulk download task.
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get the ZIP file from temporary downloads bucket
        temp_bucket = "temp-downloads"
        
        try:
            # Get the ZIP file data directly from MinIO client
            response = minio_service.client.get_object(temp_bucket, filename)
            zip_data = response.read()
            response.close()
            
            # Return ZIP file as response
            from fastapi.responses import Response
            
            return Response(
                content=zip_data,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            logger.error(f"Error downloading bulk ZIP file {filename}: {e}")
            raise HTTPException(status_code=404, detail=f"ZIP file not found: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download ZIP file: {str(e)}")


@router.post("/saved-images/{account_id}/bulk-delete/{image_type}")
async def bulk_delete_saved_images(
    account_id: int,
    image_type: str,
    offer_ids: Optional[List[str]] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a bulk delete task for saved images.
    
    Args:
        account_id: ID of the account
        image_type: 'original' or 'processed'
        offer_ids: Optional list of specific offer IDs to include. If None, includes all offers.
    """
    try:
        # Validate image_type
        if image_type not in ['original', 'processed']:
            raise HTTPException(status_code=400, detail="Invalid image type. Must be 'original' or 'processed'")
        
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get account details
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Start the bulk delete task
        task = storage_tasks.bulk_delete_saved_images_task.delay(
            account_id=account_id,
            image_type=image_type,
            offer_ids=offer_ids
        )
        
        return {"task_id": task.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bulk delete: {str(e)}")

@router.get("/saved-images/{account_id}/bulk-delete/status/{task_id}")
async def get_bulk_delete_status(
    task_id: str,
    account_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a bulk delete task.
    """
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Get task status
        from app.celery_worker import celery
        task_result = celery.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return {
                "state": "PENDING",
                "status": "Task is waiting to be processed"
            }
        elif task_result.state == 'PROGRESS':
            return {
                "state": "PROGRESS",
                "status": task_result.info.get('status', ''),
                "progress": task_result.info.get('progress', 0)
            }
        elif task_result.state == 'SUCCESS':
            return {
                "state": "SUCCESS",
                "result": task_result.result
            }
        else:
            return {
                "state": "FAILURE",
                "error": str(task_result.info)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/account-settings/{account_id}/delivery")
def get_delivery_settings(
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get delivery settings for an account from Allegro API.
    """
    logger.info(f"Getting delivery settings for account {account_id}")
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
        access_token = get_valid_token_with_reauth_handling(db, account_id)
        
        # Fetch delivery settings from Allegro API
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.allegro.public.v1+json'
        }
        
        logger.info(f"Making request to Allegro API for shipping rates")
        response = requests.get(
            'https://api.allegro.pl/sale/shipping-rates',
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Received shipping rates: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        
        # Transform the response to match our expected structure
        # Based on API docs, response structure is:
        # {
        #   "shippingRates": [
        #     {
        #       "id": "758fcd59-fbfa-4453-ae07-4800d72c2ca0",
        #       "name": "Cennik z wysyłką do Czech",
        #       "marketplaces": [{"id": "allegro-pl"}, {"id": "allegro-cz"}]
        #     }
        #   ]
        # }
        
        delivery_methods = []
        if isinstance(data, dict) and 'shippingRates' in data:
            for rate in data['shippingRates']:
                delivery_methods.append({
                    'id': rate.get('id'),
                    'name': rate.get('name')
                })
        
        result = {
            'deliveryMethods': delivery_methods
        }
        logger.info(f"Returning real delivery methods: {len(delivery_methods)} shipping rates found")
        return result
    except requests.HTTPError as e:
        logger.error(f"Allegro API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Allegro API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Failed to get delivery settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve delivery settings: {str(e)}")


@router.get("/account-settings/{account_id}/after-sales-services")
def get_after_sales_services(
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get after-sales services (returns and warranty) for an account from Allegro API.
    """
    logger.info(f"Getting after-sales services for account {account_id}")
    try:
        # Check if user has access to this account
        if not AccountRepository.can_user_access_account(db, current_user, account_id):
            raise HTTPException(status_code=403, detail="Access denied to this account")
        
        # Use centralized token refresh with proper error handling
        from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
        access_token = get_valid_token_with_reauth_handling(db, account_id)
        
        # Fetch after-sales services from Allegro API
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.allegro.public.v1+json'
        }
        
        logger.info("Fetching warranties from Allegro API")
        try:
            response = requests.get(
                'https://api.allegro.pl/after-sales-service-conditions/warranties',
                headers=headers
            )
            response.raise_for_status()
            warranties_data = response.json()
            logger.info(f"Received warranties: {list(warranties_data.keys()) if isinstance(warranties_data, dict) else type(warranties_data)}")
        except requests.HTTPError as e:
            logger.warning(f"Failed to fetch warranties: {e.response.status_code} - {e.response.text}")
            warranties_data = []
        
        logger.info("Fetching return policies from Allegro API")
        try:
            response = requests.get(
                'https://api.allegro.pl/after-sales-service-conditions/return-policies',
                headers=headers
            )
            response.raise_for_status()
            returns_data = response.json()
            logger.info(f"Received returns: {list(returns_data.keys()) if isinstance(returns_data, dict) else type(returns_data)}")
        except requests.HTTPError as e:
            logger.warning(f"Failed to fetch return policies: {e.response.status_code} - {e.response.text}")
            returns_data = []
        
        # Process real API response based on documented structure
        # Warranties response: {"count": 0, "warranties": [{"id": "string", "name": "string"}]}
        # Returns response: {"count": 0, "returnPolicies": [{"id": "...", "name": "...", ...}]}
        
        warranties = []
        if isinstance(warranties_data, dict) and 'warranties' in warranties_data:
            warranties = warranties_data['warranties']
        elif isinstance(warranties_data, list):
            warranties = warranties_data
            
        returns = []
        if isinstance(returns_data, dict) and 'returnPolicies' in returns_data:
            returns = returns_data['returnPolicies']
        elif isinstance(returns_data, list):
            returns = returns_data
        
        result = {
            'warranties': warranties,
            'returns': returns
        }
        logger.info(f"Returning real after-sales services: warranties={len(warranties)}, returns={len(returns)}")
        return result
    except Exception as e:
        logger.error(f"Failed to get after-sales services: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve after-sales services: {str(e)}")
