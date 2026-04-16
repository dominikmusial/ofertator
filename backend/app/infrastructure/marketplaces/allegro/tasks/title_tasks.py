"""Allegro Title Tasks"""
import io
import asyncio
import logging
import requests
from datetime import datetime
from typing import List, Optional, Dict
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db import schemas
from app.db.repositories import AccountRepository, BackupRepository, UserRepository, AIConfigRepository
from app.infrastructure.marketplaces.factory import factory
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)

# Import error handler - removed direct import
# from app.infrastructure.marketplaces.allegro.error_handler import parse_allegro_api_error as _parse_allegro_api_error


@celery.task(bind=True, name='update_offer_title_task')
def update_offer_title_task(self, account_id: int, offer_id: str, title: str, user_id: Optional[int] = None):
    """
    Task to update a single offer's title.
    Returns title in result for batch logging via chord callback.
    """
    logger.info(f"update_offer_title_task called with account_id={account_id}, offer_id='{offer_id}', title='{title}'")
    db = SessionLocal()
    try:
        # 1. Get account
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # 2. Get valid token (with automatic refresh if needed)
        from app.api.marketplace_token_utils import get_valid_token_for_task
        access_token = get_valid_token_for_task(db, account_id)

        # 3. Update offer title using provider
        provider = factory.get_provider_for_account(db, account_id)
        provider.update_offer(offer_id, {'name': title})

        # Return data for batch logging (handled by chord callback)
        return {
            "status": "SUCCESS",
            "offer_id": offer_id,
            "title": title,
            "account_name": account.nazwa_konta,
            "user_id": user_id
        }

    except Exception as e:
        # Use provider to normalize error
        error_msg = str(e)
        if 'provider' in locals():
            try:
                error_msg = provider.normalize_error(e)
            except:
                pass
        
        logger.error(f"Error updating offer title {offer_id}: {error_msg}")
        
        # Return error result instead of raising exception to allow chord to complete
        return {
            "status": "FAILURE",
            "offer_id": offer_id,
            "title": title,
            "error": error_msg,
            "user_id": user_id
        }
    finally:
        db.close()


@celery.task(bind=True, name='batch_log_title_updates_callback')
def batch_log_title_updates_callback(self, results):
    """
    Chord callback task that collects results from parallel title update tasks
    and sends batch logs to external system.
    
    Args:
        results: List of results from parallel update_offer_title_task tasks
    """
    logger.info(f"batch_log_title_updates_callback called with {len(results)} results")
    
    if not results:
        return {
            "status": "NO_RESULTS",
            "total_offers": 0,
            "success_count": 0,
            "failure_count": 0,
            "failed_offers": []
        }
    
    # Calculate counts for frontend
    total_offers = len(results)
    successful_results = [r for r in results if r and r.get("status") == "SUCCESS"]
    failed_results = [r for r in results if r and r.get("status") == "FAILURE"]
    success_count = len(successful_results)
    failure_count = len(failed_results)
    
    db = SessionLocal()
    try:
        if not successful_results:
            logger.info("No successful title updates to log")
            return {
                "status": "NO_SUCCESSFUL_UPDATES",
                "total_offers": total_offers,
                "success_count": success_count,
                "failure_count": failure_count,
                "failed_offers": failed_results
            }
        
        # Get user_id from first result (all should have same user_id)
        user_id = successful_results[0].get("user_id")
        
        if not user_id:
            logger.info("No user_id in results, skipping external logging")
            return {
                "status": "NO_USER_ID",
                "total_offers": total_offers,
                "success_count": success_count,
                "failure_count": failure_count,
                "failed_offers": failed_results
            }
        
        # Check if user is admin or vsprint_employee
        from app.services.external_logging_service import is_admin_or_vsprint, send_logs_batch, create_log_entry
        
        if not is_admin_or_vsprint(user_id, db):
            logger.info(f"User {user_id} is not admin/vsprint_employee, skipping external logging")
            return {
                "status": "USER_NOT_PRIVILEGED",
                "total_offers": total_offers,
                "success_count": success_count,
                "failure_count": failure_count,
                "failed_offers": failed_results
            }
        
        # Create batch logs
        logs = []
        for result in successful_results:
            logs.append(create_log_entry(
                account_name=result.get("account_name", ""),
                kind="Edycja tytułu",
                offer_id=result.get("offer_id", ""),
                value=result.get("title", ""),
                value_before=""
            ))
        
        # Send batch
        logger.info(f"Sending batch of {len(logs)} title update logs to external system")
        result_log = send_logs_batch(logs, db)
        
        if result_log["success"]:
            logger.info(f"Successfully sent batch of {len(logs)} logs to external system")
            return {
                "status": "SUCCESS",
                "total_offers": total_offers,
                "success_count": success_count,
                "failure_count": failure_count,
                "logged_count": len(logs),
                "failed_offers": failed_results
            }
        else:
            logger.error(f"Failed to send batch logs: {result_log['error']}")
            return {
                "status": "LOGGING_FAILED",
                "error": result_log["error"],
                "total_offers": total_offers,
                "success_count": success_count,
                "failure_count": failure_count,
                "logged_count": 0,
                "webhook_logging_failed": True,
                "webhook_error": result_log["error"],
                "failed_offers": failed_results
            }
            
    except Exception as e:
        logger.error(f"Error in batch_log_title_updates_callback: {e}")
        return {
            "status": "CALLBACK_ERROR",
            "error": str(e),
            "total_offers": total_offers,
            "success_count": success_count,
            "failure_count": failure_count,
            "webhook_logging_failed": True,
            "webhook_error": str(e),
            "failed_offers": failed_results
        }
    finally:
        db.close()


@celery.task(bind=True, name='batch_duplicate_offers_callback')
def batch_duplicate_offers_callback(self, results):
    """
    Chord callback task that collects results from parallel duplicate offer tasks
    and sends batch logs to external system.
    
    Args:
        results: List of results from parallel duplicate_offer_with_title_task tasks
    """
    logger.info(f"batch_duplicate_offers_callback called with {len(results)} results")
    
    if not results:
        return {
            "status": "NO_RESULTS",
            "total_offers": 0,
            "success_count": 0,
            "failure_count": 0,
            "duplicated_offers": [],
            "failed_offers": []
        }
    
    # Calculate counts for frontend
    total_offers = len(results)
    successful_results = [r for r in results if r and r.get("status") == "SUCCESS"]
    failed_results = [r for r in results if r and r.get("status") == "FAILURE"]
    success_count = len(successful_results)
    failure_count = len(failed_results)
    
    # Build duplicated_offers list with old_id -> new_id mapping
    duplicated_offers = [
        {
            "old_id": r["offer_id"],
            "new_id": r["new_offer_id"],
            "title": r["title"]
        }
        for r in successful_results
    ]
    
    # Build failed_offers list
    failed_offers = [
        {
            "offer_id": r["offer_id"],
            "title": r["title"],
            "error": r.get("error", "Unknown error")
        }
        for r in failed_results
    ]
    
    db = SessionLocal()
    try:
        if not successful_results:
            logger.info("No successful offer duplications to log")
            return {
                "status": "ALL_FAILED",
                "total_offers": total_offers,
                "success_count": 0,
                "failure_count": failure_count,
                "duplicated_offers": [],
                "failed_offers": failed_offers
            }
        
        # Log to external system if any user is admin or vsprint_employee
        from app.services.external_logging_service import is_admin_or_vsprint, send_logs_batch, create_log_entry
        
        # Check if any of the users should trigger logging
        user_ids = [r.get("user_id") for r in successful_results if r.get("user_id")]
        should_log = False
        for user_id in user_ids:
            if is_admin_or_vsprint(user_id, db):
                should_log = True
                break
        
        if should_log:
            logger.info(f"Creating batch logs for {len(successful_results)} successful duplications")
            logs = []
            for result in successful_results:
                log_entry = create_log_entry(
                    account_name=result.get("account_name", "Unknown"),
                    kind="Duplikacja oferty",
                    offer_id=result.get("offer_id"),
                    value=f"Nowa oferta: {result.get('new_offer_id')}",
                    value_before=f"Tytuł: {result.get('title')}"
                )
                logs.append(log_entry)
            
            result_log = send_logs_batch(logs, db)
            
            if result_log.get("success"):
                logged_count = result_log.get("logged_count", 0)
                logger.info(f"Successfully logged {logged_count} duplications to external system")
                return {
                    "status": "SUCCESS",
                    "total_offers": total_offers,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "duplicated_offers": duplicated_offers,
                    "failed_offers": failed_offers,
                    "logged_count": logged_count
                }
            else:
                logger.error(f"Failed to send batch logs: {result_log['error']}")
                return {
                    "status": "LOGGING_FAILED",
                    "error": result_log["error"],
                    "total_offers": total_offers,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "duplicated_offers": duplicated_offers,
                    "failed_offers": failed_offers,
                    "webhook_logging_failed": True,
                    "webhook_error": result_log["error"]
                }
        else:
            logger.info("No admin/vsprint users - skipping external logging")
            return {
                "status": "SUCCESS",
                "total_offers": total_offers,
                "success_count": success_count,
                "failure_count": failure_count,
                "duplicated_offers": duplicated_offers,
                "failed_offers": failed_offers,
                "logged_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in batch_duplicate_offers_callback: {e}")
        return {
            "status": "CALLBACK_ERROR",
            "error": str(e),
            "total_offers": total_offers,
            "success_count": success_count,
            "failure_count": failure_count,
            "duplicated_offers": duplicated_offers,
            "failed_offers": failed_offers,
            "webhook_logging_failed": True,
            "webhook_error": str(e)
        }
    finally:
        db.close()


@celery.task(bind=True, name='pull_titles_task')
def pull_titles_task(self, account_id: int, offer_ids: List[str]):
    """
    Task to pull titles from specified offers and prepare them for download.
    Returns a downloadable file with offer IDs and titles.
    """
    db = SessionLocal()
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Pobieranie tytułów ofert...', 'progress': 0})
        
        # Get account and validate
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")

        # Get valid token (with automatic refresh if needed)
        from app.api.marketplace_token_utils import get_valid_token_for_task
        access_token = get_valid_token_for_task(db, account_id)
        
        # Get provider for this account
        provider = factory.get_provider_for_account(db, account_id)
        
        titles_data = []
        total_offers = len(offer_ids)
        
        for i, offer_id in enumerate(offer_ids):
            try:
                # Update progress
                progress = int((i / total_offers) * 100)
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': f'Pobieranie tytułu {i+1}/{total_offers} ({offer_id})', 
                        'progress': progress
                    }
                )
                
                # Get offer details
                offer_details = provider.get_offer(offer_id)
                if offer_details and 'name' in offer_details:
                    titles_data.append({
                        'ID': offer_id,
                        'Tytuły': offer_details['name']
                    })
                    logger.info(f"Successfully fetched title for offer {offer_id}")
                else:
                    logger.warning(f"No title found for offer {offer_id}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch title for offer {offer_id}: {e}")
        
        # Check if we got any titles - if not, this should be considered a failure
        if len(titles_data) == 0:
            error_msg = f"Nie udało się pobrać żadnych tytułów z {total_offers} ofert. Sprawdź czy oferty należą do tego konta i czy masz odpowiednie uprawnienia."
            logger.error(f"No titles fetched for any of the {total_offers} offers")
            self.update_state(state='FAILURE', meta={'exc_type': 'NoTitlesFetched', 'exc_message': error_msg})
            raise Exception(error_msg)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'tytuły_{timestamp}.csv'
        
        # Create CSV file in memory
        import pandas as pd
        df = pd.DataFrame(titles_data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=False, encoding='utf-8', sep=',')
        csv_data = csv_buffer.getvalue().encode('utf-8')
        
        # Upload to MinIO
        try:
            file_url = minio_service.upload_file(
                bucket_name="exports",
                file_name=filename,
                file_data=csv_data,
                content_type="text/csv"
            )
        except Exception as minio_error:
            # Provide more specific error message for MinIO connection issues
            if "Network is unreachable" in str(minio_error) or "Connection refused" in str(minio_error):
                error_msg = (
                    "❌ Nie można połączyć się z serwerem plików (MinIO). "
                    "Sprawdź czy SSH tunel jest uruchomiony: ssh -N -L 9000:localhost:9000 sokol@34.140.91.224"
                )
            else:
                error_msg = f"❌ Błąd serwera plików: {str(minio_error)}"
            
            logger.error(f"MinIO error in pull_titles_task: {minio_error}")
            raise Exception(error_msg)
        
        result = {
            "status": "SUCCESS",
            "total_offers": total_offers,
            "fetched_titles": len(titles_data),
            "download_url": file_url,
            "filename": filename
        }
        
        self.update_state(state='SUCCESS', meta=result)
        return result

    except Exception as e:
        logger.error(f"Error in pull_titles_task: {e}")
        self.update_state(
            state="FAILURE", 
            meta={"exc_type": type(e).__name__, "exc_message": str(e)}
        )
        raise
    finally:
        db.close()


@celery.task(bind=True, name='optimize_titles_ai_task')
def optimize_titles_ai_task(
    self,
    titles_data: List[Dict],
    user_id: int,
    account_id: int,
    include_offer_parameters: bool = False
):
    """
    Task to optimize multiple titles using AI with progress updates.
    Processes titles in batches and updates progress for each batch.
    
    Args:
        titles_data: List of dicts with 'offer_id' and 'current_title'
        user_id: User ID for AI configuration
        account_id: Account ID for access token (if parameters are needed)
        include_offer_parameters: Whether to fetch and include offer parameters
    
    Returns:
        Dict with optimization results
    """
    import asyncio
    from app.infrastructure.marketplaces.allegro.services.title_optimizer_service import TitleOptimizerService
    from app.db import models
    
    db = SessionLocal()
    try:
        self.update_state(state='PROGRESS', meta={
            'status': 'Inicjalizacja optymalizacji AI...',
            'progress': 0,
            'processed': 0,
            'total': len(titles_data),
            'successful': 0,
            'failed': 0
        })
        
        # Get user and account
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise Exception("User not found")
        
        account = AccountRepository.get_by_id(db, account_id)
        if not account:
            raise Exception("Account not found")
        
        # Get access token if parameters are requested
        access_token = None
        if include_offer_parameters:
            # Get valid token (with automatic refresh if needed)
            from app.api.marketplace_token_utils import get_valid_token_for_task
            access_token = get_valid_token_for_task(db, account_id)
        
        # Convert titles_data to schemas
        titles = [
            schemas.TitleToOptimize(
                offer_id=t['offer_id'],
                current_title=t['current_title']
            )
            for t in titles_data
        ]
        
        # Get AI client and configuration
        from app.services.ai_provider_service import ai_provider_service
        from app.services.ai_config_service import ai_config_service
        
        user_config = AIConfigRepository.get_user_config(db, user_id)
        ai_client, model_name = ai_provider_service.get_user_ai_client(
            user_config=user_config,
            fallback_to_default=True,
            user_role=user.role,
            registration_source=user.registration_source
        )
        
        if not ai_client:
            raise Exception("No AI client available")
        
        # Get configuration
        provider_name = "anthropic" if hasattr(ai_client, 'messages') else "google"
        
        user_prompt = ai_config_service.get_prompt_for_titles(db, provider_name, marketplace_type='allegro')
        gen_params = ai_config_service.get_generation_params(db, "titles", provider_name)
        
        logger.info(f"Using configured max_output_tokens: {gen_params.get('max_output_tokens', 'not set')}")
        
        # Fetch offer parameters if requested
        offer_params = {}
        if include_offer_parameters:
            offer_ids = [t.offer_id for t in titles]
            offer_params = TitleOptimizerService._fetch_offer_parameters(account_id, offer_ids, user_id)
        
        # Determine batch size - will retry with smaller batches if MAX_TOKENS error occurs
        batch_size = 10 if include_offer_parameters else 15
        
        all_results = []
        total_successful = 0
        total_failed = 0
        total_titles = len(titles)
        
        logger.info(f"Starting AI optimization for {total_titles} titles in batches of {batch_size}")
        
        # Process in batches (synchronous loop with async batch processing)
        for i in range(0, len(titles), batch_size):
            batch = titles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(titles) + batch_size - 1) // batch_size
            
            # Update progress
            progress = int((i / total_titles) * 100)
            logger.info(f"Przetwarzanie partii {batch_num}/{total_batches} ({len(batch)} tytułów) - Postęp: {progress}%")
            self.update_state(state='PROGRESS', meta={
                'status': f'Przetwarzanie partii {batch_num}/{total_batches} ({len(batch)} tytułów)...',
                'progress': progress,
                'processed': i,
                'total': total_titles,
                'successful': total_successful,
                'failed': total_failed
            })
            
            # Process batch asynchronously
            async def process_batch():
                return await TitleOptimizerService._optimize_single_batch(
                    titles=batch,
                    ai_client=ai_client,
                    model_name=model_name,
                    user_prompt=user_prompt,
                    gen_params=gen_params,
                    include_offer_parameters=include_offer_parameters,
                    access_token=access_token,
                    user_id=user_id,
                    offer_params=offer_params
                )
            
            batch_results, batch_successful, batch_failed = asyncio.run(process_batch())
            
            # Check if batch failed due to MAX_TOKENS and retry with smaller batches
            had_retry = False
            if batch_failed == len(batch) and any("MAX_TOKENS" in r.error for r in batch_results if r.error):
                logger.warning(f"Batch {batch_num} hit MAX_TOKENS, splitting into smaller batches")
                smaller_batch_size = max(2, len(batch) // 2)
                had_retry = True
                
                batch_results = []
                batch_successful = 0
                batch_failed = 0
                
                for j in range(0, len(batch), smaller_batch_size):
                    mini_batch = batch[j:j + smaller_batch_size]
                    mini_batch_num = (j // smaller_batch_size) + 1
                    total_mini_batches = (len(batch) + smaller_batch_size - 1) // smaller_batch_size
                    
                    # Update progress BEFORE mini-batch
                    current_processed = i + j
                    current_progress = int((current_processed / total_titles) * 100)
                    logger.info(f"  Ponowna próba {mini_batch_num}/{total_mini_batches} z {len(mini_batch)} tytułami...")
                    self.update_state(state='PROGRESS', meta={
                        'status': f'Ponowna próba {mini_batch_num}/{total_mini_batches} z {len(mini_batch)} tytułami...',
                        'progress': current_progress,
                        'processed': current_processed,
                        'total': total_titles,
                        'successful': total_successful,
                        'failed': total_failed
                    })
                    
                    async def process_mini_batch():
                        return await TitleOptimizerService._optimize_single_batch(
                            titles=mini_batch,
                            ai_client=ai_client,
                            model_name=model_name,
                            user_prompt=user_prompt,
                            gen_params=gen_params,
                            include_offer_parameters=include_offer_parameters,
                            access_token=access_token,
                            user_id=user_id,
                            offer_params=offer_params
                        )
                    
                    mini_results, mini_successful, mini_failed = asyncio.run(process_mini_batch())
                    
                    batch_results.extend(mini_results)
                    batch_successful += mini_successful
                    batch_failed += mini_failed
                    
                    # Update totals and progress AFTER mini-batch completes
                    total_successful += mini_successful
                    total_failed += mini_failed
                    completed_processed = i + j + len(mini_batch)
                    completed_progress = int((completed_processed / total_titles) * 100)
                    
                    logger.info(f"  Mini-partia {mini_batch_num}/{total_mini_batches} zakończona: {mini_successful} sukces, {mini_failed} błędów")
                    self.update_state(state='PROGRESS', meta={
                        'status': f'Zakończono mini-partię {mini_batch_num}/{total_mini_batches}',
                        'progress': completed_progress,
                        'processed': completed_processed,
                        'total': total_titles,
                        'successful': total_successful,
                        'failed': total_failed
                    })
            
            # Add results to all_results
            all_results.extend(batch_results)
            
            # Update totals only if no retry (retry already updated them in the loop)
            if not had_retry:
                total_successful += batch_successful
                total_failed += batch_failed
        
        # Convert results to dict format for JSON serialization
        results_dict = [
            {
                'offer_id': r.offer_id,
                'current_title': r.current_title,
                'optimized_title': r.optimized_title,
                'analysis': r.analysis,
                'character_count': r.character_count,
                'success': r.success,
                'error': r.error
            }
            for r in all_results
        ]
        
        result = {
            'results': results_dict,
            'total_processed': total_titles,
            'successful': total_successful,
            'failed': total_failed
        }
        
        logger.info(f"AI optimization completed: {result['successful']}/{result['total_processed']} successful")
        return result
        
    except Exception as e:
        logger.error(f"Error in optimize_titles_ai_task: {e}", exc_info=True)
        raise
    finally:
        db.close()


