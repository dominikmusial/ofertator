from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import schemas, models
from app.db.repositories import TemplateRepository, AccountRepository
from app.db.session import get_db
from app.core.auth import get_current_verified_user
from typing import List
from pydantic import BaseModel

router = APIRouter()

class CopyTemplateRequest(BaseModel):
    template_id: int
    target_account_id: int

class DuplicateTemplateRequest(BaseModel):
    template_id: int
    new_name: str

@router.post("/", response_model=schemas.Template)
def create_template(
    template: schemas.TemplateCreate, 
    account_id: int = Query(..., description="Account ID where template will be created"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Create a new template. Account ID is required.
    """
    # Verify user has access to the account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    try:
        return TemplateRepository.create(db=db, template=template, owner_id=current_user.id, account_id=account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.Template])
def read_templates(
    account_id: int = Query(..., description="Account ID to get templates for"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Read all templates accessible to current user for specific account.
    """
    try:
        return TemplateRepository.get_user_accessible_templates(db=db, user=current_user, account_id=account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{template_id}", response_model=schemas.Template)
def read_template(
    template_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Read a single template by its ID.
    """
    db_template = TemplateRepository.get_by_id(db, template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if user can view this template
    if not TemplateRepository.can_user_view_template(db, current_user, db_template):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return db_template

@router.put("/{template_id}", response_model=schemas.Template)
def update_template(
    template_id: int, 
    template: schemas.TemplateUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Update a template. Only the owner can update their templates.
    """
    db_template = TemplateRepository.get_by_id(db, template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if user can edit this template
    if not TemplateRepository.can_user_edit_template(db, current_user, db_template):
        raise HTTPException(status_code=403, detail="Only the template owner can update it")
    
    # Check for name conflicts when updating
    if template.name and template.name != db_template.name:
        existing_template = TemplateRepository.get_by_name_and_account(db, template.name, db_template.account_id)
        if existing_template:
            raise HTTPException(status_code=400, detail=f"Template with name '{template.name}' already exists for this account")
    
    db_template = TemplateRepository.update(db=db, template_id=template_id, template_data=template)
    return db_template

@router.delete("/{template_id}", response_model=schemas.Template)
def delete_template(
    template_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Delete a template. Only the owner can delete their templates.
    """
    db_template = TemplateRepository.get_by_id(db, template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if user can edit this template
    if not TemplateRepository.can_user_edit_template(db, current_user, db_template):
        raise HTTPException(status_code=403, detail="Only the template owner can delete it")
    
    db_template = TemplateRepository.delete(db=db, template_id=template_id)
    return db_template

@router.post("/copy", response_model=schemas.Template)
def copy_template_to_account(
    copy_request: CopyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Copy a template to another account. User must have access to both source template and target account.
    """
    # Get the source template
    source_template = TemplateRepository.get_by_id(db, copy_request.template_id)
    if source_template is None:
        raise HTTPException(status_code=404, detail="Source template not found")
    
    # Check if user can view source template
    if not TemplateRepository.can_user_view_template(db, current_user, source_template):
        raise HTTPException(status_code=403, detail="Access denied to source template")
    
    # Find the target account by ID
    target_account = AccountRepository.get_by_id(db, copy_request.target_account_id)
    if target_account is None:
        raise HTTPException(status_code=404, detail="Target account not found")
    
    # Check if user has access to target account
    if not AccountRepository.can_user_access_account(db, current_user, target_account.id):
        raise HTTPException(status_code=403, detail="Access denied to target account")
    
    # Check if template already exists for target account
    existing_template = TemplateRepository.get_by_name_and_account(
        db, source_template.name, target_account.id
    )
    
    if existing_template:
        # Template with same name exists - suggest new name
        base_name = source_template.name
        counter = 2
        new_name = f"{base_name} (Copy)"
        
        # Keep trying until we find a unique name
        while TemplateRepository.get_by_name_and_account(db, new_name, target_account.id):
            new_name = f"{base_name} (Copy {counter})"
            counter += 1
        
        raise HTTPException(
            status_code=409, 
            detail={
                "error": "Template name conflict",
                "suggested_name": new_name,
                "original_name": base_name
            }
        )
    
    # Create the copied template
    template_data = schemas.TemplateCreate(
        name=source_template.name,
        content=source_template.content,
        prompt=source_template.prompt
    )
    
    try:
        copied_template = TemplateRepository.create(
            db=db, 
            template=template_data, 
            owner_id=current_user.id, 
            account_id=target_account.id
        )
        return copied_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/copy-with-name", response_model=schemas.Template)
def copy_template_with_custom_name(
    copy_request: CopyTemplateRequest,
    new_name: str = Query(..., description="New name for the copied template"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Copy a template to another account with a custom name.
    """
    # Get the source template
    source_template = TemplateRepository.get_by_id(db, copy_request.template_id)
    if source_template is None:
        raise HTTPException(status_code=404, detail="Source template not found")
    
    # Check if user can view source template
    if not TemplateRepository.can_user_view_template(db, current_user, source_template):
        raise HTTPException(status_code=403, detail="Access denied to source template")
    
    # Find the target account by ID
    target_account = AccountRepository.get_by_id(db, copy_request.target_account_id)
    if target_account is None:
        raise HTTPException(status_code=404, detail="Target account not found")
    
    # Check if user has access to target account
    if not AccountRepository.can_user_access_account(db, current_user, target_account.id):
        raise HTTPException(status_code=403, detail="Access denied to target account")
    
    # Create the copied template with new name
    template_data = schemas.TemplateCreate(
        name=new_name,
        content=source_template.content,
        prompt=source_template.prompt
    )
    
    try:
        copied_template = TemplateRepository.create(
            db=db, 
            template=template_data, 
            owner_id=current_user.id, 
            account_id=target_account.id
        )
        return copied_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/duplicate", response_model=schemas.Template)
def duplicate_template_within_account(
    duplicate_request: DuplicateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_verified_user)
):
    """
    Duplicate a template within the same account with a new name.
    """
    # Get the source template
    source_template = TemplateRepository.get_by_id(db, duplicate_request.template_id)
    if source_template is None:
        raise HTTPException(status_code=404, detail="Source template not found")
    
    # Check if user can view source template
    if not TemplateRepository.can_user_view_template(db, current_user, source_template):
        raise HTTPException(status_code=403, detail="Access denied to source template")
    
    # Check if user has access to the template's account
    if not AccountRepository.can_user_access_account(db, current_user, source_template.account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    # Check if template with new name already exists in the same account
    existing_template = TemplateRepository.get_by_name_and_account(
        db, duplicate_request.new_name, source_template.account_id
    )
    
    if existing_template:
        raise HTTPException(
            status_code=400, 
            detail=f"Template with name '{duplicate_request.new_name}' already exists in this account"
        )
    
    # Create the duplicated template
    template_data = schemas.TemplateCreate(
        name=duplicate_request.new_name,
        content=source_template.content,
        prompt=source_template.prompt
    )
    
    try:
        duplicated_template = TemplateRepository.create(
            db=db, 
            template=template_data, 
            owner_id=current_user.id, 
            account_id=source_template.account_id
        )
        return duplicated_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 