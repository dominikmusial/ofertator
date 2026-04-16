"""Allegro Authentication Tasks"""
import time
import logging
from datetime import datetime, timedelta
from app.celery_worker import celery
from app.db.session import SessionLocal
from app.db import schemas, models
from app.db.repositories import AccountRepository
from app.infrastructure.marketplaces.allegro import auth as allegro_auth

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='allegro_auth_task')
def allegro_auth_task(self, device_code: str, interval: int, user_id: int, account_id: int = None):
    """
    A Celery task that polls Allegro API for access token and saves it to the database.
    If account_id is provided, updates existing account (re-authentication).
    Otherwise, creates a new account.
    """
    db = SessionLocal()
    max_retries = 100  # About 8 minutes
    retries = 0

    while retries < max_retries:
        self.update_state(state='PROGRESS', meta={'status': 'Polling Allegro...', 'attempt': retries})
        
        token_data = allegro_auth.get_token_from_device_code(device_code)
        
        error = token_data.get("error")

        if not error and "access_token" in token_data:
            # Success! Get user info from Allegro API
            try:
                # Get account name from Allegro API
                user_info = allegro_auth.get_user_info(token_data['access_token'])
                account_name = user_info.get('login', f"Allegro-{user_info.get('id', 'Unknown')}")
                
                # Calculate token expiration (refresh token: 3 months, access token: 12 hours)
                access_token_expires = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                refresh_token_expires = datetime.utcnow() + timedelta(days=90)  # 3 months
                
                if account_id:
                    # Re-authentication: Update existing account
                    account = db.query(models.Account).filter(models.Account.id == account_id).first()
                    if not account:
                        return {'status': 'FAILURE', 'error': f'Account {account_id} not found'}
                    
                    # SECURITY: Verify that the authorized Allegro account matches the one we're re-authenticating
                    if account.nazwa_konta != account_name:
                        logger.error(
                            f"Re-authentication failed: Account mismatch. "
                            f"Expected '{account.nazwa_konta}', but authorized as '{account_name}'"
                        )
                        return {
                            'status': 'FAILURE', 
                            'error': (
                                f"Błąd autoryzacji: Zalogowano się na nieprawidłowe konto Allegro. "
                                f"Oczekiwano: '{account.nazwa_konta}', "
                                f"otrzymano: '{account_name}'. "
                                f"Proszę zalogować się na właściwe konto Allegro."
                            )
                        }
                    
                    account.access_token = token_data['access_token']
                    account.refresh_token = token_data['refresh_token']
                    account.token_expires_at = access_token_expires
                    account.refresh_token_expires_at = refresh_token_expires
                    account.needs_reauth = False
                    account.last_token_refresh = datetime.utcnow()
                    db.commit()
                    db.refresh(account)
                    
                    return {
                        'status': 'SUCCESS', 
                        'account_name': account.nazwa_konta, 
                        'account_id': account.id,
                        'is_reauth': True
                    }
                else:
                    # New account creation
                    account_data = schemas.AccountCreate(
                        nazwa_konta=account_name,
                        access_token=token_data['access_token'],
                        refresh_token=token_data['refresh_token'],
                        token_expires_at=access_token_expires
                    )
                    
                    # Create new account (always create new, don't check for existing)
                    db_account = AccountRepository.create(db, schemas.AccountCreate(**account_data.dict()), user_id)
                    
                    # Set refresh token expiry and last refresh
                    db_account.refresh_token_expires_at = refresh_token_expires
                    db_account.last_token_refresh = datetime.utcnow()
                    db.commit()
                    
                    # For vsprint employees and admins, set shared_with_vsprint flag
                    # This allows all vsprint team members to see this account
                    from app.db.models import User, UserRole
                    user = db.query(User).filter(User.id == user_id).first()
                    if user and user.role in [UserRole.vsprint_employee, UserRole.admin]:
                        AccountRepository.share_with_vsprint(db, user_id, db_account.id)
                    
                    return {
                        'status': 'SUCCESS', 
                        'account_name': account_name, 
                        'account_id': db_account.id,
                        'is_reauth': False
                    }
            finally:
                db.close()

        elif error == "authorization_pending":
            # User has not yet authorized the app, wait and try again
            time.sleep(interval)
            retries += 1
        else:
            # A real error occurred
            db.close()
            # Mark task as failed
            self.update_state(state='FAILURE', meta={'status': f'Error: {error}'})
            # Stop the task
            return {'status': 'FAILURE', 'error': error, 'details': token_data}
    
    # If loop finishes, it means we timed out
    db.close()
    return {'status': 'FAILURE', 'error': 'Timeout. User did not authorize in time.'}
