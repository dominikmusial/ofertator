from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd

from app.db.session import get_db
from app.db import models, schemas
from app.db.repositories import AccountRepository
from app.core.auth import get_current_user, require_module_permission
from app.infrastructure.marketplaces.factory import factory
from app.infrastructure.marketplaces.base import MarketplaceType
from app.infrastructure.marketplaces.allegro.services.file_parser import (
    generate_template_excel,
    generate_template_csv,
    validate_file_size
)
from app.infrastructure.marketplaces.allegro.services.schedule_import import ScheduleImportService, export_schedules_to_data
import pytz

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependency for price scheduler module
require_price_scheduler = require_module_permission("allegro_harmonogram_cen")


def get_valid_token(db: Session, current_user: models.User, account_id: int) -> str:
    """Helper to get a valid access token for an account, refreshing if necessary."""
    # Check if user has access to this account
    if not AccountRepository.can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego konta")

    from app.api.marketplace_token_utils import get_valid_token_with_reauth_handling
    return get_valid_token_with_reauth_handling(db, account_id)


def check_and_apply_immediate_execution(
    db: Session,
    schedule: models.PriceSchedule,
    access_token: str
) -> None:
    """
    Check if schedule should be active right now and apply price change immediately.
    Logs warnings on failure but doesn't raise exceptions.

    Args:
        db: Database session
        schedule: The newly created schedule
        access_token: Allegro API access token
    """
    try:
        warsaw_tz = pytz.timezone('Europe/Warsaw')
        current_time = datetime.now(warsaw_tz)

        should_execute = False

        # Check if schedule should be active now
        if schedule.schedule_type == 'hourly' and schedule.schedule_config:
            # Check current day of week and hour
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            current_day_name = day_names[current_time.weekday()]
            current_hour = current_time.hour

            day_hours = schedule.schedule_config.get(current_day_name, [])
            if current_hour in day_hours:
                should_execute = True
                logger.info(f"Schedule {schedule.id}: Hourly schedule matches current time ({current_day_name} {current_hour}:00)")

        elif schedule.schedule_type == 'daily' and schedule.daily_schedule_config:
            # Check current day of month
            current_day_of_month = current_time.day
            active_days = schedule.daily_schedule_config.get('days', [])

            if current_day_of_month in active_days:
                should_execute = True
                logger.info(f"Schedule {schedule.id}: Daily schedule matches current day ({current_day_of_month})")

        # Execute price change if schedule is active now
        if should_execute:
            logger.info(f"Schedule {schedule.id}: Executing immediate price change to {schedule.scheduled_price}")

            # Update price via marketplace provider (Allegro-specific)
            provider = factory.get_provider_for_account(db, schedule.account_id)
            if hasattr(provider, 'update_offer_price'):
                # Price operations are Allegro-specific
                success = provider.update_offer_price(
                    schedule.offer_id,
                    schedule.scheduled_price
                )
            else:
                logger.warning(f"Price scheduling not supported for marketplace type: {provider.get_marketplace_type()}")
                success = False

            if success:
                # Update schedule state
                schedule.current_price_state = 'scheduled'
                schedule.last_price_update = current_time

                # Create log entry
                log = models.PriceChangeLog(
                    schedule_id=schedule.id,
                    account_id=schedule.account_id,
                    offer_id=schedule.offer_id,
                    price_before=schedule.original_price,
                    price_after=schedule.scheduled_price,
                    change_reason='schedule_activated_immediately',
                    success=True
                )
                db.add(log)
                db.commit()

                logger.info(f"Schedule {schedule.id}: Immediate execution successful")
            else:
                logger.warning(f"Schedule {schedule.id}: Immediate execution failed - price update unsuccessful")
        else:
            logger.info(f"Schedule {schedule.id}: No immediate execution needed (schedule not active at current time)")

    except Exception as e:
        logger.warning(f"Schedule {schedule.id}: Immediate execution failed with error: {e}")
        # Don't raise - schedule creation should succeed even if immediate execution fails


@router.get("/offers/active/{account_id}", response_model=schemas.ActiveOffersResponse)
async def get_active_offers(
    account_id: int,
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """Fetch all active offers from Allegro API for an account"""
    # Get valid token (with automatic refresh if needed)
    access_token = get_valid_token(db, current_user, account_id)

    try:
        # Get provider for the account
        provider = factory.get_provider_for_account(db, account_id)
        
        # Check if provider supports fetching active offers (Allegro-specific feature)
        if not hasattr(provider, 'fetch_active_offers'):
            raise HTTPException(
                status_code=400,
                detail=f"Marketplace {provider.get_marketplace_type().value} does not support active offers fetching"
            )
        
        # Fetch offers using marketplace-specific method
        offers = provider.fetch_active_offers()
        return {"offers": offers, "count": len(offers)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch active offers: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania ofert: {str(e)}")


@router.post("/price-schedules/", response_model=schemas.PriceScheduleResponse)
async def create_price_schedule(
    schedule_data: schemas.PriceScheduleCreate,
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """Create a new price schedule"""
    # Get valid token (with automatic refresh if needed)
    access_token = get_valid_token(db, current_user, schedule_data.account_id)

    # Fetch current price via marketplace provider (this becomes the "original price")
    try:
        provider = factory.get_provider_for_account(db, schedule_data.account_id)
        if hasattr(provider, 'get_offer_price'):
            current_price = provider.get_offer_price(schedule_data.offer_id)
        else:
            raise HTTPException(status_code=400, detail="Price operations not supported for this marketplace")
    except Exception as e:
        logger.error(f"Failed to fetch offer price: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Nie można pobrać aktualnej ceny oferty: {str(e)}"
        )

    # Create price snapshot for backup
    snapshot = models.PriceSnapshot(
        account_id=schedule_data.account_id,
        offer_id=schedule_data.offer_id,
        price=current_price,
        snapshot_reason='schedule_created'
    )
    db.add(snapshot)

    # Create schedule
    schedule = models.PriceSchedule(
        account_id=schedule_data.account_id,
        offer_id=schedule_data.offer_id,
        offer_name=schedule_data.offer_name,
        sku=schedule_data.sku,  # Include SKU
        original_price=current_price,  # Store current price as baseline
        scheduled_price=schedule_data.scheduled_price,
        schedule_type=schedule_data.schedule_type,
        schedule_config=schedule_data.schedule_config,
        daily_schedule_config=schedule_data.daily_schedule_config,
        current_price_state='original'
    )
    db.add(schedule)

    try:
        db.commit()
        db.refresh(schedule)
        logger.info(f"Created price schedule {schedule.id} for offer {schedule.offer_id}")

        # Check if schedule should execute immediately
        check_and_apply_immediate_execution(db, schedule, access_token)

        return schedule
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create price schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas tworzenia harmonogramu: {str(e)}")


@router.get("/price-schedules/{account_id}")
async def list_price_schedules(
    account_id: int,
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """List all price schedules for an account"""
    if not can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego konta")

    schedules = db.query(models.PriceSchedule).filter(
        models.PriceSchedule.account_id == account_id
    ).order_by(models.PriceSchedule.created_at.desc()).all()

    return {"schedules": schedules, "count": len(schedules)}


@router.put("/price-schedules/{schedule_id}", response_model=schemas.PriceScheduleResponse)
async def update_price_schedule(
    schedule_id: int,
    update_data: schemas.PriceScheduleUpdate,
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """Update an existing price schedule"""
    schedule = db.query(models.PriceSchedule).filter(
        models.PriceSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Harmonogram nie znaleziony")

    if not can_user_access_account(db, current_user, schedule.account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu")

    # Update fields
    if update_data.scheduled_price is not None:
        schedule.scheduled_price = update_data.scheduled_price
    if update_data.schedule_config is not None:
        schedule.schedule_config = update_data.schedule_config
    if update_data.is_active is not None:
        schedule.is_active = update_data.is_active

    try:
        db.commit()
        db.refresh(schedule)
        logger.info(f"Updated price schedule {schedule_id}")
        return schedule
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update price schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas aktualizacji: {str(e)}")


@router.delete("/price-schedules/{schedule_id}")
async def delete_price_schedule(
    schedule_id: int,
    restore_original: bool = True,
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """Delete a price schedule and optionally restore original price"""
    schedule = db.query(models.PriceSchedule).filter(
        models.PriceSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Harmonogram nie znaleziony")

    if not can_user_access_account(db, current_user, schedule.account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu")

    # Restore original price if requested
    if restore_original:
        # Get valid token (with automatic refresh if needed)
        access_token = get_valid_token(db, current_user, schedule.account_id)

        try:
            provider = factory.get_provider_for_account(db, schedule.account_id)
            if hasattr(provider, 'update_offer_price'):
                success = provider.update_offer_price(
                    schedule.offer_id,
                    schedule.original_price
                )
            else:
                success = False
                logger.error("update_offer_price not supported for this marketplace")

            if success:
                # Log the restoration
                log = models.PriceChangeLog(
                    schedule_id=schedule.id,
                    account_id=schedule.account_id,
                    offer_id=schedule.offer_id,
                    price_before=schedule.scheduled_price,
                    price_after=schedule.original_price,
                    change_reason='schedule_deleted_restore',
                    success=True
                )
                db.add(log)
                logger.info(f"Restored original price for offer {schedule.offer_id}")
        except Exception as e:
            logger.error(f"Failed to restore price: {e}")
            # Continue with deletion even if restore fails

    # Delete schedule
    db.delete(schedule)

    try:
        db.commit()
        logger.info(f"Deleted price schedule {schedule_id}")
        return {"message": "Harmonogram został usunięty", "restored_price": restore_original}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete price schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas usuwania: {str(e)}")


@router.get("/price-schedules/{schedule_id}/logs")
async def get_price_change_logs(
    schedule_id: int,
    limit: int = 100,
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """Get price change history for a schedule"""
    schedule = db.query(models.PriceSchedule).filter(
        models.PriceSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Harmonogram nie znaleziony")

    if not can_user_access_account(db, current_user, schedule.account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu")

    logs = db.query(models.PriceChangeLog).filter(
        models.PriceChangeLog.schedule_id == schedule_id
    ).order_by(models.PriceChangeLog.changed_at.desc()).limit(limit).all()

    return {"logs": logs, "count": len(logs)}


# ========================================
# Import/Export Endpoints for Daily Schedules
# ========================================

@router.get("/price-schedules/template/{account_id}")
async def download_template(
    account_id: int,
    format: str = 'xlsx',  # 'xlsx' or 'csv'
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """
    Download empty template for price schedule import.

    Query params:
    - format: 'xlsx' (default) or 'csv'
    """
    # Verify account access
    if not can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego konta")

    try:
        if format == 'csv':
            content = generate_template_csv()
            media_type = 'text/csv'
            filename = 'szablon_harmonogram_cen.csv'
            output = BytesIO(content.encode('utf-8'))
        else:  # xlsx
            content = generate_template_excel()
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'szablon_harmonogram_cen.xlsx'
            output = BytesIO(content)

        output.seek(0)
        return StreamingResponse(
            output,
            media_type=media_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas generowania szablonu: {str(e)}")


@router.post("/price-schedules/import/{account_id}", response_model=schemas.ScheduleImportResponse)
async def import_schedules(
    account_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """
    Import price schedules from Excel or CSV file.
    This will DELETE all existing schedules for the account and create new ones.

    File format:
    - Columns: ID Oferty, Nazwa Oferty, Cena Promocyjna, 1, 2, 3, ..., 31
    - Mark active days with 'x', 'X', '1', or 'true'
    """
    # Verify account access
    if not can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego konta")

    # Validate file type
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy format pliku. Użyj .xlsx lub .csv"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Validate file size (max 5MB)
        validate_file_size(file_content, max_size_mb=5)

        # Get valid Allegro token (with auto-refresh)
        access_token = get_valid_token(db, current_user, account_id)

        # Create import service and process
        import_service = ScheduleImportService(db, account_id, access_token)
        result = import_service.validate_and_import(file_content, file.filename)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd podczas importu: {str(e)}")


@router.get("/price-schedules/export/{account_id}")
async def export_schedules(
    account_id: int,
    format: str = 'xlsx',  # 'xlsx' or 'csv'
    current_user: models.User = Depends(require_price_scheduler),
    db: Session = Depends(get_db)
):
    """
    Export existing daily schedules to Excel or CSV.

    Query params:
    - format: 'xlsx' (default) or 'csv'
    """
    # Verify account access
    if not can_user_access_account(db, current_user, account_id):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego konta")

    try:
        # Export schedules to data
        export_data = export_schedules_to_data(db, account_id)

        if not export_data:
            raise HTTPException(
                status_code=404,
                detail="Brak dziennych harmonogramów do wyeksportowania"
            )

        # Create DataFrame
        df = pd.DataFrame(export_data)

        # Generate file
        if format == 'csv':
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            media_type = 'text/csv'
            filename = f'harmonogram_cen_export_{account_id}.csv'
        else:  # xlsx
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Harmonogram Cen')
            output.seek(0)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'harmonogram_cen_export_{account_id}.xlsx'

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd podczas eksportu: {str(e)}")
