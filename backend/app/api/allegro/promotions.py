from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.db import schemas, models
from app.db.session import get_db
from app.db.repositories import AccountRepository
from app.core.auth import get_current_user
from app.infrastructure.marketplaces.allegro import promotion_service
from app.infrastructure.marketplaces.allegro.promotion_service import PromotionServiceError
from datetime import datetime, timedelta
import requests
from typing import Optional

router = APIRouter()

def get_valid_token(db: Session, current_user: models.User, account_id: int) -> str:
    """Helper to get a valid access token for an account."""
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Access denied to this account")
    
    from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
    return get_valid_token_with_reauth_handling(db, account_id)

@router.get("/", response_model=List[schemas.Promotion])
def list_promotions(
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all promotions for a given account."""
    access_token = get_valid_token(db, current_user, account_id)
    try:
        data = promotion_service.list_promotions(access_token)
        # Safely access 'name' using .get()
        return [schemas.Promotion(id=p['id'], name=p.get('name'), status=p.get('status', 'N/A')) for p in data.get('promotions', [])]
    except PromotionServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/", response_model=schemas.Promotion, status_code=status.HTTP_201_CREATED)
def create_promotion(
    account_id: int, 
    promo_data: schemas.PromotionCreate, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new promotion."""
    access_token = get_valid_token(db, current_user, account_id)
    try:
        created_promo = promotion_service.create_multipack_promotion(
            access_token=access_token,
            name=promo_data.name,
            offer_ids=promo_data.offer_ids,
            for_each_quantity=promo_data.for_each_quantity,
            percentage=promo_data.percentage
        )
        return schemas.Promotion(id=created_promo['id'], name=promo_data.name, status=created_promo.get('status', 'ACTIVATING'))
    except PromotionServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(
    account_id: int, 
    promotion_id: str, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a promotion by its ID."""
    access_token = get_valid_token(db, current_user, account_id)
    try:
        promotion_service.delete_promotion(access_token, promotion_id)
        return
    except PromotionServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Bundle/Multipack specific endpoints
@router.get("/bundles")
def get_bundles(
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bundle promotions for an account."""
    access_token = get_valid_token(db, current_user, account_id)
    
    try:
        # Fetch all MULTIPACK and CROSS_MULTIPACK promotions
        all_promotions = []
        
        # Fetch MULTIPACK promotions
        multipack_data = fetch_promotions_by_type(access_token, "MULTIPACK")
        all_promotions.extend(multipack_data.get('promotions', []))
        
        # Fetch CROSS_MULTIPACK promotions
        cross_multipack_data = fetch_promotions_by_type(access_token, "CROSS_MULTIPACK")
        all_promotions.extend(cross_multipack_data.get('promotions', []))
        
        # Format promotions to match frontend expectations
        formatted_promotions = []
        for promotion in all_promotions:
            # Extract offer IDs
            offers = []
            for criterion in promotion.get('offerCriteria', []):
                if criterion.get('type') == 'CONTAINS_OFFERS':
                    offers.extend([offer.get('id') for offer in criterion.get('offers', [])])
            
            # Extract discount and trigger info
            benefits = promotion.get('benefits', [])
            discount = None
            for_each_quantity = None
            promotion_type = "UNKNOWN"
            
            if benefits:
                benefit = benefits[0]
                specification = benefit.get('specification', {})
                promotion_type = specification.get('type', 'UNKNOWN')
                
                # Get discount percentage
                configuration = specification.get('configuration', {})
                if isinstance(configuration, dict):
                    discount = configuration.get('percentage')
                
                # Get trigger information
                trigger = specification.get('trigger', {})
                for_each_quantity = trigger.get('forEachQuantity')
            
            formatted_promotion = {
                'id': promotion.get('id'),
                'type': promotion_type,
                'discount': int(discount) if discount else None,
                'for_each_quantity': int(for_each_quantity) if for_each_quantity else None,
                'status': promotion.get('status'),
                'offers': offers,
                'valid_from': promotion.get('validFrom'),
                'valid_until': promotion.get('validUntil')
            }
            
            formatted_promotions.append(formatted_promotion)
        
        return formatted_promotions
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/bundles/grouped")
def create_grouped_bundles(
    request: schemas.CreateGroupedBundleRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple bundle promotions by grouping offers."""
    import logging
    logger = logging.getLogger(__name__)
    
    access_token = get_valid_token(db, current_user, request.account_id)
    
    logger.info(f"🚀 Starting promotion creation: {len(request.offer_ids)} offers, group_size={request.group_size}, quantity={request.for_each_quantity}, discount={request.percentage}%")
    
    try:
        # Split offers into groups
        offer_groups = [request.offer_ids[i:i + request.group_size] for i in range(0, len(request.offer_ids), request.group_size)]
        results = []
        success_count = 0
        successful_offer_ids = []
        
        logger.info(f"📦 Split into {len(offer_groups)} groups")
        
        for idx, offer_group in enumerate(offer_groups, 1):
            logger.info(f"Processing group {idx}/{len(offer_groups)} with {len(offer_group)} offers")
            try:
                # Create promotion for this group
                success = create_single_bundle_promotion(
                    access_token, offer_group, request.for_each_quantity, request.percentage
                )
                results.append(success)
                if success:
                    success_count += 1
                    # FIXED: Only track offers from SUCCESSFUL groups
                    successful_offer_ids.extend(offer_group)
            except Exception as e:
                logger.error(f"❌ Exception in group {idx}: {str(e)}")
                results.append(False)
        
        logger.info(f"✅ Promotion creation complete: {success_count}/{len(offer_groups)} groups successful")
        
        # Log to external system if user is admin or vsprint_employee
        webhook_error = None
        if successful_offer_ids:
            from app.services.external_logging_service import is_admin_or_vsprint, send_logs_batch, create_log_entry
            import logging
            logger = logging.getLogger(__name__)
            
            try:
                if is_admin_or_vsprint(current_user.id, db):
                    # Get account name
                    account = AccountRepository.get_by_id(db, request.account_id)
                    if account:
                        # Create batch logs for all successful offers
                        logs = []
                        for offer_id in successful_offer_ids:
                            logs.append(create_log_entry(
                                account_name=account.nazwa_konta,
                                kind=f"Dodanie rabatów na {request.for_each_quantity} sztukę",
                                offer_id=offer_id,
                                value=None,
                                value_before=None
                            ))
                        
                        # Send batch
                        result_log = send_logs_batch(logs, db)
                        if not result_log["success"]:
                            webhook_error = result_log["error"]
                            logger.error(f"Failed to log promotions to external system: {webhook_error}")
            except Exception as e:
                logger.error(f"Error logging to external system: {e}")
                webhook_error = str(e)
        
        response = {
            "success_count": success_count,
            "total_groups": len(offer_groups),
            "results": results
        }
        
        if webhook_error:
            response["webhook_logging_failed"] = True
            response["webhook_error"] = webhook_error
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/bundles/all")
def delete_all_bundles(
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all bundle promotions for an account."""
    access_token = get_valid_token(db, current_user, account_id)
    
    try:
        # Get all promotions first
        all_promotions = []
        
        # Fetch MULTIPACK promotions
        try:
            multipack_data = fetch_promotions_by_type(access_token, "MULTIPACK")
            all_promotions.extend(multipack_data.get('promotions', []))
        except Exception as e:
            print(f"Failed to fetch MULTIPACK promotions: {e}")
        
        # Fetch CROSS_MULTIPACK promotions  
        try:
            cross_multipack_data = fetch_promotions_by_type(access_token, "CROSS_MULTIPACK")
            all_promotions.extend(cross_multipack_data.get('promotions', []))
        except Exception as e:
            print(f"Failed to fetch CROSS_MULTIPACK promotions: {e}")
        
        # Delete each promotion
        deleted_count = 0
        failed_deletions = []
        
        for promotion in all_promotions:
            try:
                promotion_service.delete_promotion(access_token, promotion['id'])
                deleted_count += 1
            except Exception as e:
                failed_deletions.append(f"Promotion {promotion['id']}: {str(e)}")
                print(f"Failed to delete promotion {promotion['id']}: {e}")
        
        if failed_deletions:
            print(f"Some deletions failed: {failed_deletions}")
        
        return {"deleted_count": deleted_count, "failed_count": len(failed_deletions)}
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete promotion all: {str(e)}")

@router.delete("/bundles/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bundle(
    promotion_id: str, 
    account_id: int, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a single bundle promotion by its ID."""
    access_token = get_valid_token(db, current_user, account_id)
    try:
        promotion_service.delete_promotion(access_token, promotion_id)
        return
    except PromotionServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def fetch_promotions_by_type(access_token: str, promotion_type: str) -> dict:
    """Helper function to fetch promotions by type with pagination."""
    url = "https://api.allegro.pl/sale/loyalty/promotions"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }
    
    all_promotions = []
    offset = 0
    limit = 50
    
    while True:
        params = {
            'promotionType': promotion_type,
            'limit': limit,
            'offset': offset
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        promotions = data.get('promotions', [])
        all_promotions.extend(promotions)
        
        total_count = data.get('totalCount', 0)
        if (offset + limit) >= total_count:
            break
            
        offset += limit
    
    return {'promotions': all_promotions}

def create_single_bundle_promotion(access_token: str, offer_ids: List[str], for_each_quantity: int, percentage: int) -> bool:
    """Helper function to create a single bundle promotion."""
    import logging
    logger = logging.getLogger(__name__)
    
    url = "https://api.allegro.pl/sale/loyalty/promotions"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json'
    }
    
    payload = {
        "benefits": [{
            "specification": {
                "type": "UNIT_PERCENTAGE_DISCOUNT",
                "configuration": {
                    "percentage": str(percentage)
                },
                "trigger": {
                    "forEachQuantity": str(for_each_quantity),
                    "discountedNumber": "1"
                }
            }
        }],
        "offerCriteria": [{
            "type": "CONTAINS_OFFERS",
            "offers": [{"id": offer_id} for offer_id in offer_ids]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 201:
            logger.info(f"✅ Successfully created promotion for {len(offer_ids)} offers")
            return True
        else:
            # Try to parse Allegro error response
            error_detail = response.text[:500]
            try:
                error_json = response.json()
                if 'errors' in error_json and len(error_json['errors']) > 0:
                    error_info = error_json['errors'][0]
                    error_detail = f"{error_info.get('code', 'Unknown')}: {error_info.get('message', error_info.get('userMessage', response.text[:200]))}"
            except:
                pass
            
            logger.error(f"❌ Allegro API error - Status: {response.status_code}, Error: {error_detail}, Offers: {len(offer_ids)}, First: {offer_ids[0] if offer_ids else 'none'}")
            return False
    except Exception as e:
        logger.error(f"❌ Exception creating promotion: {str(e)}, Offers count: {len(offer_ids)}")
        return False 