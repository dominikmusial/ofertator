"""Allegro Price Scheduling Tasks"""
from datetime import datetime
import pytz
import logging
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db import models
from app.infrastructure.marketplaces.factory import factory

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='check_and_update_prices_task')
def check_and_update_prices_task(self):
    """
    Cron task that runs every hour.
    Checks all active HOURLY schedules and updates prices accordingly.
    """
    db = SessionLocal()
    # Use Warsaw timezone (matching Celery Beat timezone)
    warsaw_tz = pytz.timezone('Europe/Warsaw')
    current_time = datetime.now(warsaw_tz)
    current_day = current_time.strftime('%A').lower()  # "monday", "tuesday", etc.
    current_hour = current_time.hour

    logger.info(f"🕐 Running HOURLY price update check: {current_day} {current_hour}:00 (Warsaw time)")

    try:
        # Get all active HOURLY schedules
        schedules = db.query(models.PriceSchedule).filter(
            models.PriceSchedule.is_active == True,
            models.PriceSchedule.schedule_type == 'hourly'
        ).all()

        logger.info(f"📊 Found {len(schedules)} active price schedules")

        for schedule in schedules:
            try:
                # Get account token
                account = db.query(models.Account).filter(
                    models.Account.id == schedule.account_id
                ).first()

                if not account:
                    logger.error(f"❌ Account {schedule.account_id} not found for schedule {schedule.id}")
                    continue

                # Skip accounts that need re-authorization
                if account.needs_reauth:
                    logger.warning(f"⚠️ Skipping schedule {schedule.id}: Account '{account.nazwa_konta}' needs re-authorization")
                    continue

                # Refresh token if needed using centralized logic
                try:
                    from app.api.marketplace_token_utils import refresh_account_token_if_needed
                    access_token = refresh_account_token_if_needed(db, account, for_api=False)
                except Exception as token_error:
                    logger.error(f"❌ Token refresh failed for account '{account.nazwa_konta}': {token_error}")
                    continue

                # Parse schedule config for current day
                day_hours = schedule.schedule_config.get(current_day, [])

                # Determine target price based on schedule
                if current_hour in day_hours:
                    # We are in a scheduled hour window
                    target_price = schedule.scheduled_price
                    target_state = 'scheduled'
                else:
                    # Outside scheduled hours
                    target_price = schedule.original_price
                    target_state = 'original'

                # Always fetch current price from marketplace to verify it's correct
                try:
                    provider = factory.get_provider_for_account(db, schedule.account_id)
                    if hasattr(provider, 'get_offer_price'):
                        current_allegro_price = provider.get_offer_price(schedule.offer_id)
                        logger.info(f"📊 Schedule {schedule.id}: Current price: {current_allegro_price}, Target: {target_price}")
                    else:
                        logger.error(f"Price operations not supported for marketplace: {provider.get_marketplace_type()}")
                        continue
                except Exception as e:
                    logger.error(f"⚠️ Failed to fetch current price: {e}")
                    current_allegro_price = "unknown"

                # Check if price needs updating (compare actual Allegro price with target)
                needs_update = False

                if current_allegro_price != "unknown":
                    # Normalize prices for comparison (remove decimals if they're .00)
                    current_normalized = str(float(current_allegro_price))
                    target_normalized = str(float(target_price))

                    if current_normalized != target_normalized:
                        needs_update = True
                        logger.info(f"💡 Price mismatch detected! Current: {current_normalized} vs Target: {target_normalized}")
                elif schedule.current_price_state != target_state:
                    # Fallback: if we can't fetch price, check state change
                    needs_update = True
                    logger.info(f"💡 State change detected: {schedule.current_price_state} → {target_state}")

                if needs_update:
                    logger.info(f"🔄 Schedule {schedule.id}: Updating price from {current_allegro_price} to {target_price}")

                    # Update price via marketplace provider
                    provider = factory.get_provider_for_account(db, schedule.account_id)
                    if hasattr(provider, 'update_offer_price'):
                        success = provider.update_offer_price(
                            schedule.offer_id,
                            target_price
                        )
                    else:
                        logger.error(f"Price operations not supported for marketplace: {provider.get_marketplace_type()}")
                        success = False

                    # Log the change
                    log = models.PriceChangeLog(
                        schedule_id=schedule.id,
                        account_id=schedule.account_id,
                        offer_id=schedule.offer_id,
                        price_before=current_allegro_price,
                        price_after=target_price,
                        change_reason=f"cron_{target_state}",
                        success=success
                    )
                    db.add(log)

                    if success:
                        # Update schedule state
                        schedule.current_price_state = target_state
                        schedule.last_price_update = current_time
                        logger.info(f"✅ Successfully updated price for offer {schedule.offer_id} to {target_price} PLN")
                    else:
                        logger.error(f"❌ Failed to update price for offer {schedule.offer_id}")
                else:
                    logger.info(f"✓ Schedule {schedule.id}: Price already correct ({target_price} PLN)")

                # Update last check time regardless
                schedule.last_price_check = current_time
                db.commit()

            except Exception as e:
                logger.error(f"❌ Error processing schedule {schedule.id}: {e}")
                db.rollback()
                # Log failed attempt
                log = models.PriceChangeLog(
                    schedule_id=schedule.id,
                    account_id=schedule.account_id,
                    offer_id=schedule.offer_id,
                    price_before="unknown",
                    price_after="unknown",
                    change_reason="cron_error",
                    success=False,
                    error_message=str(e)
                )
                db.add(log)
                db.commit()

    except Exception as e:
        logger.error(f"❌ Critical error in price update cron: {e}")
    finally:
        db.close()

    logger.info("✅ Hourly price update check completed")


@celery.task(bind=True, name="check_and_update_prices_daily")
def check_and_update_prices_daily_task(self):
    """
    Cron task that runs once a day (00:01).
    Checks all active DAILY schedules and updates prices accordingly.
    """
    db = SessionLocal()
    # Use Warsaw timezone (matching Celery Beat timezone)
    warsaw_tz = pytz.timezone('Europe/Warsaw')
    current_time = datetime.now(warsaw_tz)
    current_day_of_month = current_time.day  # 1-31

    logger.info(f"📅 Running DAILY price update check: Day {current_day_of_month} of month (Warsaw time)")

    try:
        # Get all active DAILY schedules
        schedules = db.query(models.PriceSchedule).filter(
            models.PriceSchedule.is_active == True,
            models.PriceSchedule.schedule_type == 'daily'
        ).all()

        logger.info(f"📊 Found {len(schedules)} active daily price schedules")

        for schedule in schedules:
            try:
                # Get account token
                account = db.query(models.Account).filter(
                    models.Account.id == schedule.account_id
                ).first()

                if not account:
                    logger.error(f"❌ Account {schedule.account_id} not found for schedule {schedule.id}")
                    continue

                # Skip accounts that need re-authorization
                if account.needs_reauth:
                    logger.warning(f"⚠️ Skipping schedule {schedule.id}: Account '{account.nazwa_konta}' needs re-authorization")
                    continue

                # Refresh token if needed using centralized logic
                try:
                    from app.api.marketplace_token_utils import refresh_account_token_if_needed
                    access_token = refresh_account_token_if_needed(db, account, for_api=False)
                except Exception as token_error:
                    logger.error(f"❌ Token refresh failed for account '{account.nazwa_konta}': {token_error}")
                    continue

                # Parse daily schedule config
                active_days = schedule.daily_schedule_config.get('days', []) if schedule.daily_schedule_config else []

                # Determine target price based on current day of month
                if current_day_of_month in active_days:
                    # Today is a promotion day
                    target_price = schedule.scheduled_price
                    target_state = 'scheduled'
                else:
                    # Not a promotion day
                    target_price = schedule.original_price
                    target_state = 'original'

                # Always fetch current price from marketplace to verify it's correct
                try:
                    provider = factory.get_provider_for_account(db, schedule.account_id)
                    if hasattr(provider, 'get_offer_price'):
                        current_allegro_price = provider.get_offer_price(schedule.offer_id)
                        logger.info(f"📊 Schedule {schedule.id}: Current price: {current_allegro_price}, Target: {target_price}")
                    else:
                        logger.error(f"Price operations not supported for marketplace: {provider.get_marketplace_type()}")
                        continue
                except Exception as e:
                    logger.error(f"⚠️ Failed to fetch current price: {e}")
                    current_allegro_price = "unknown"

                # Check if price needs updating (compare actual Allegro price with target)
                needs_update = False

                if current_allegro_price != "unknown":
                    # Normalize prices for comparison (remove decimals if they're .00)
                    current_normalized = str(float(current_allegro_price))
                    target_normalized = str(float(target_price))

                    if current_normalized != target_normalized:
                        needs_update = True
                        logger.info(f"💡 Price mismatch detected! Current: {current_normalized} vs Target: {target_normalized}")
                elif schedule.current_price_state != target_state:
                    # Fallback: if we can't fetch price, check state change
                    needs_update = True
                    logger.info(f"💡 State change detected: {schedule.current_price_state} → {target_state}")

                if needs_update:
                    logger.info(f"🔄 Daily Schedule {schedule.id}: Updating price from {current_allegro_price} to {target_price}")

                    # Update price via marketplace provider
                    provider = factory.get_provider_for_account(db, schedule.account_id)
                    if hasattr(provider, 'update_offer_price'):
                        success = provider.update_offer_price(
                            schedule.offer_id,
                            target_price
                        )
                    else:
                        logger.error(f"Price operations not supported for marketplace: {provider.get_marketplace_type()}")
                        success = False

                    # Log the change
                    log = models.PriceChangeLog(
                        schedule_id=schedule.id,
                        account_id=schedule.account_id,
                        offer_id=schedule.offer_id,
                        price_before=current_allegro_price,
                        price_after=target_price,
                        change_reason=f"cron_daily_{target_state}",
                        success=success
                    )
                    db.add(log)

                    if success:
                        # Update schedule state
                        schedule.current_price_state = target_state
                        schedule.last_price_update = current_time
                        logger.info(f"✅ Successfully updated price for offer {schedule.offer_id} to {target_price} PLN")
                    else:
                        logger.error(f"❌ Failed to update price for offer {schedule.offer_id}")
                else:
                    logger.info(f"✓ Schedule {schedule.id}: Price already correct ({target_price} PLN)")

                # Update last check time regardless
                schedule.last_price_check = current_time
                db.commit()

            except Exception as e:
                logger.error(f"❌ Error processing daily schedule {schedule.id}: {e}")
                db.rollback()
                # Log failed attempt
                log = models.PriceChangeLog(
                    schedule_id=schedule.id,
                    account_id=schedule.account_id,
                    offer_id=schedule.offer_id,
                    price_before="unknown",
                    price_after="unknown",
                    change_reason="cron_daily_error",
                    success=False,
                    error_message=str(e)
                )
                db.add(log)
                db.commit()

    except Exception as e:
        logger.error(f"❌ Critical error in daily price update cron: {e}")
    finally:
        db.close()

    logger.info("✅ Daily price update check completed")
