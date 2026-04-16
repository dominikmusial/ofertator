"""
Service for importing and validating price schedules from files
"""
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.db import models, schemas
from app.infrastructure.marketplaces.factory import factory
from .file_parser import parse_schedule_file, FileParserError
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)


class ScheduleImportService:
    """Service for handling price schedule imports"""

    def __init__(self, db: Session, account_id: int, access_token: str):
        self.db = db
        self.account_id = account_id
        self.access_token = access_token

    def validate_and_import(
        self,
        file_content: bytes,
        filename: str
    ) -> schemas.ScheduleImportResponse:
        """
        Validate and import price schedules from file.
        All-or-nothing operation: if any validation fails, nothing is imported.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            ScheduleImportResponse with success status and details
        """
        try:
            # Step 1: Parse file
            logger.info(f"Parsing file: {filename}")
            parsed_rows = parse_schedule_file(file_content, filename)
            logger.info(f"Parsed {len(parsed_rows)} rows from file")

            # Step 2: Validate all rows
            logger.info("Validating all rows...")
            validation_errors = []

            for row_data in parsed_rows:
                try:
                    # Validate using Pydantic schema
                    schemas.ScheduleImportRow(**row_data)
                except Exception as e:
                    validation_errors.append(schemas.ScheduleImportError(
                        row=row_data.get('row_number', 0),
                        offer_id=row_data.get('offer_id', 'unknown'),
                        error=str(e)
                    ))

            if validation_errors:
                return schemas.ScheduleImportResponse(
                    success=False,
                    message=f"Znaleziono {len(validation_errors)} błędów walidacji",
                    errors=validation_errors
                )

            # Step 3: Verify offers exist in Allegro and fetch original prices
            logger.info("Verifying offers in Allegro...")
            offer_prices = {}  # offer_id -> original_price

            for row_data in parsed_rows:
                offer_id = row_data['offer_id']

                # Skip if already fetched
                if offer_id in offer_prices:
                    continue

                try:
                    # Fetch current price from marketplace (this will be the "original price")
                    provider = factory.get_provider_for_account(self.db, self.account_id)
                    if hasattr(provider, 'get_offer_price'):
                        current_price = provider.get_offer_price(offer_id)
                        offer_prices[offer_id] = current_price
                    else:
                        logger.error(f"Price operations not supported for this marketplace")
                        failed_offers.append({'offer_id': offer_id, 'error': 'Price operations not supported'})
                        continue
                    logger.info(f"Offer {offer_id}: current price = {current_price}")

                except Exception as e:
                    validation_errors.append(schemas.ScheduleImportError(
                        row=row_data.get('row_number', 0),
                        offer_id=offer_id,
                        error=f"Nie można pobrać ceny z Allegro: {str(e)}"
                    ))

            if validation_errors:
                return schemas.ScheduleImportResponse(
                    success=False,
                    message=f"Nie można zweryfikować {len(validation_errors)} ofert w Allegro",
                    errors=validation_errors
                )

            # Step 4: Delete all existing schedules for this account (atomic operation)
            logger.info(f"Deleting all existing schedules for account {self.account_id}...")
            existing_schedules = self.db.query(models.PriceSchedule).filter(
                models.PriceSchedule.account_id == self.account_id
            ).all()
            deleted_count = len(existing_schedules)

            for schedule in existing_schedules:
                self.db.delete(schedule)

            logger.info(f"Deleted {deleted_count} existing schedules")

            # Step 5: Create new schedules
            logger.info("Creating new schedules...")
            created_count = 0

            for row_data in parsed_rows:
                offer_id = row_data['offer_id']
                original_price = offer_prices[offer_id]

                # Create price snapshot for backup
                snapshot = models.PriceSnapshot(
                    account_id=self.account_id,
                    offer_id=offer_id,
                    price=original_price,
                    snapshot_reason='schedule_created'
                )
                self.db.add(snapshot)

                # Create schedule
                schedule = models.PriceSchedule(
                    account_id=self.account_id,
                    offer_id=offer_id,
                    offer_name=row_data['offer_name'],
                    sku=row_data.get('sku'),  # Optional SKU field
                    original_price=original_price,
                    scheduled_price=row_data['scheduled_price'],
                    schedule_type='daily',
                    schedule_config=None,  # Not used for daily schedules
                    daily_schedule_config={'days': row_data['days']},
                    is_active=True,
                    current_price_state='original'
                )
                self.db.add(schedule)
                created_count += 1

                # Create initial log entry
                log = models.PriceChangeLog(
                    schedule_id=None,  # Will be set after commit
                    account_id=self.account_id,
                    offer_id=offer_id,
                    price_before=original_price,
                    price_after=original_price,
                    change_reason='schedule_created',
                    success=True
                )
                self.db.add(log)

            # Commit all changes atomically
            self.db.commit()
            logger.info(f"Successfully imported {created_count} schedules")

            # Check immediate execution for all schedules after commit
            self._check_immediate_execution_for_all(parsed_rows)

            return schemas.ScheduleImportResponse(
                success=True,
                message=f"Pomyślnie zaimportowano {created_count} harmonogramów",
                imported_count=created_count,
                deleted_count=deleted_count,
                errors=None
            )

        except FileParserError as e:
            logger.error(f"File parsing error: {e}")
            self.db.rollback()
            return schemas.ScheduleImportResponse(
                success=False,
                message=str(e),
                errors=None
            )

        except Exception as e:
            logger.error(f"Unexpected error during import: {e}", exc_info=True)
            self.db.rollback()
            return schemas.ScheduleImportResponse(
                success=False,
                message=f"Nieoczekiwany błąd: {str(e)}",
                errors=None
            )

    def _check_immediate_execution_for_all(self, parsed_rows: List[dict]) -> None:
        """
        Check all imported schedules and execute price changes for those active now.
        Runs after commit, logs warnings on failures.
        """
        try:
            warsaw_tz = pytz.timezone('Europe/Warsaw')
            current_time = datetime.now(warsaw_tz)
            current_day_of_month = current_time.day

            # Get all schedules we just created (daily schedules for this account)
            schedules = self.db.query(models.PriceSchedule).filter(
                models.PriceSchedule.account_id == self.account_id,
                models.PriceSchedule.schedule_type == 'daily'
            ).all()

            logger.info(f"Checking immediate execution for {len(schedules)} daily schedules (current day: {current_day_of_month})")

            for schedule in schedules:
                try:
                    # Check if this schedule should be active today
                    active_days = schedule.daily_schedule_config.get('days', []) if schedule.daily_schedule_config else []

                    if current_day_of_month in active_days:
                        logger.info(f"Schedule {schedule.id} (offer {schedule.offer_id}): Matches current day - executing immediate price change")

                        # Update price via marketplace provider
                        provider = factory.get_provider_for_account(self.db, self.account_id)
                        if hasattr(provider, 'update_offer_price'):
                            success = provider.update_offer_price(
                                schedule.offer_id,
                                schedule.scheduled_price
                            )
                        else:
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
                            self.db.add(log)

                            logger.info(f"Schedule {schedule.id}: Immediate execution successful")
                        else:
                            logger.warning(f"Schedule {schedule.id}: Immediate execution failed - price update unsuccessful")
                    else:
                        logger.debug(f"Schedule {schedule.id}: Not active today (active on days: {active_days})")

                except Exception as e:
                    logger.warning(f"Schedule {schedule.id}: Immediate execution failed: {e}")
                    # Continue with other schedules

            # Commit all immediate execution changes
            self.db.commit()
            logger.info("Completed immediate execution check for all schedules")

        except Exception as e:
            logger.error(f"Error during immediate execution check: {e}")
            # Don't raise - import succeeded, immediate execution is optional


def export_schedules_to_data(
    db: Session,
    account_id: int
) -> List[dict]:
    """
    Export existing daily schedules to data format suitable for Excel/CSV.

    Args:
        db: Database session
        account_id: Account ID

    Returns:
        List of dicts with schedule data
    """
    schedules = db.query(models.PriceSchedule).filter(
        models.PriceSchedule.account_id == account_id,
        models.PriceSchedule.schedule_type == 'daily'
    ).all()

    export_data = []
    for schedule in schedules:
        # Build row with offer info and days marked (including SKU)
        row = {
            'ID Oferty': schedule.offer_id,
            'SKU': schedule.sku or '',  # Include SKU (empty string if None)
            'Nazwa Oferty': schedule.offer_name or '',
            'Cena Promocyjna': schedule.scheduled_price
        }

        # Get active days from config
        active_days = schedule.daily_schedule_config.get('days', []) if schedule.daily_schedule_config else []

        # Mark days 1-31
        for day in range(1, 32):
            row[str(day)] = 'x' if day in active_days else ''

        export_data.append(row)

    return export_data
