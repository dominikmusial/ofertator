from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.infrastructure.marketplaces.allegro import auth as allegro_auth
from app.infrastructure.marketplaces.allegro.tasks.auth_tasks import allegro_auth_task
from celery.result import AsyncResult
from app.celery_worker import celery
from app.core.auth import get_current_verified_user, require_vsprint_or_admin
from app.core.config import settings
import os
from pathlib import Path
from dotenv import dotenv_values
from app.db.session import get_db
from app.db.models import User, Account, UserMarketplaceAccount
from app.db import schemas, models
from app.db.repositories import AccountRepository
from typing import List, Dict, Any
import httpx
import json
from sqlalchemy import or_
import threading
import time
import uuid
from app.db.session import SessionLocal

router = APIRouter()

# Allegro API configuration
ALLEGRO_AUTH_URL = "https://allegro.pl/auth/oauth/device"
ALLEGRO_TOKEN_URL = "https://allegro.pl/auth/oauth/token"

_local_tasks: Dict[str, Dict[str, Any]] = {}
_local_tasks_lock = threading.Lock()


def _should_use_local_tasks() -> bool:
    try:
        return settings.DATABASE_URL.startswith("sqlite")
    except Exception:
        return True


def _set_local_task(task_id: str, status: str, result: Any = None) -> None:
    with _local_tasks_lock:
        _local_tasks[task_id] = {"task_id": task_id, "status": status, "result": result}


def _run_local_allegro_auth_task(*, task_id: str, device_code: str, interval: int, user_id: int, account_id: int = None) -> None:
    _set_local_task(task_id, "PROGRESS", {"status": "Polling Allegro..."})
    db = SessionLocal()
    try:
        max_retries = 100
        retries = 0
        while retries < max_retries:
            token_data = allegro_auth.get_token_from_device_code(device_code)
            error = token_data.get("error")

            if not error and "access_token" in token_data:
                try:
                    from datetime import datetime, timedelta

                    user_info = allegro_auth.get_user_info(token_data["access_token"])
                    account_name = user_info.get("login", f"Allegro-{user_info.get('id', 'Unknown')}")
                    access_token_expires = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
                    refresh_token_expires = datetime.utcnow() + timedelta(days=90)

                    if account_id:
                        account = db.query(models.Account).filter(models.Account.id == account_id).first()
                        if not account:
                            _set_local_task(task_id, "FAILURE", {"status": "FAILURE", "error": f"Account {account_id} not found"})
                            return

                        if account.nazwa_konta != account_name:
                            _set_local_task(
                                task_id,
                                "FAILURE",
                                {
                                    "status": "FAILURE",
                                    "error": (
                                        f"Błąd autoryzacji: Zalogowano się na nieprawidłowe konto Allegro. "
                                        f"Oczekiwano: '{account.nazwa_konta}', "
                                        f"otrzymano: '{account_name}'. "
                                        f"Proszę zalogować się na właściwe konto Allegro."
                                    ),
                                },
                            )
                            return

                        account.access_token = token_data["access_token"]
                        account.refresh_token = token_data["refresh_token"]
                        account.token_expires_at = access_token_expires
                        account.refresh_token_expires_at = refresh_token_expires
                        account.needs_reauth = False
                        account.last_token_refresh = datetime.utcnow()
                        db.commit()
                        db.refresh(account)

                        _set_local_task(
                            task_id,
                            "SUCCESS",
                            {"status": "SUCCESS", "account_name": account.nazwa_konta, "account_id": account.id, "is_reauth": True},
                        )
                        return

                    account_data = schemas.AccountCreate(
                        nazwa_konta=account_name,
                        access_token=token_data["access_token"],
                        refresh_token=token_data["refresh_token"],
                        token_expires_at=access_token_expires,
                    )
                    db_account = AccountRepository.create(db, schemas.AccountCreate(**account_data.dict()), user_id)
                    db_account.refresh_token_expires_at = refresh_token_expires
                    db_account.last_token_refresh = datetime.utcnow()
                    db.commit()

                    user = db.query(models.User).filter(models.User.id == user_id).first()
                    if user and user.role in [models.UserRole.vsprint_employee, models.UserRole.admin]:
                        AccountRepository.share_with_vsprint(db, user_id, db_account.id)

                    _set_local_task(
                        task_id,
                        "SUCCESS",
                        {"status": "SUCCESS", "account_name": account_name, "account_id": db_account.id, "is_reauth": False},
                    )
                    return
                except Exception as e:
                    _set_local_task(task_id, "FAILURE", {"status": "FAILURE", "error": str(e)})
                    return

            if error == "authorization_pending":
                _set_local_task(task_id, "PROGRESS", {"status": "Polling Allegro...", "attempt": retries})
                time.sleep(interval)
                retries += 1
                continue

            if error:
                _set_local_task(task_id, "FAILURE", {"status": "FAILURE", "error": error, "details": token_data})
                return

            _set_local_task(task_id, "FAILURE", {"status": "FAILURE", "error": "Unexpected response", "details": token_data})
            return

        _set_local_task(task_id, "FAILURE", {"status": "FAILURE", "error": "Timeout. User did not authorize in time."})
    finally:
        try:
            db.close()
        except Exception:
            pass

@router.post("/auth/start")
def allegro_auth_start(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    client_id = os.getenv("ALLEGRO_CLIENT_ID") or ""
    client_secret = os.getenv("ALLEGRO_CLIENT_SECRET") or ""
    if (not client_id or not client_secret) or client_id == "DUMMY" or client_secret == "DUMMY":
        env_values = dotenv_values(Path(__file__).resolve().parents[4] / ".env")
        client_id = str(env_values.get("ALLEGRO_CLIENT_ID") or "")
        client_secret = str(env_values.get("ALLEGRO_CLIENT_SECRET") or "")
    if not client_id or not client_secret or client_id == "DUMMY" or client_secret == "DUMMY":
        raise HTTPException(
            status_code=400,
            detail="Brak konfiguracji Allegro. Ustaw ALLEGRO_CLIENT_ID i ALLEGRO_CLIENT_SECRET w pliku .env (dane z Allegro Developer)."
        )
    try:
        device_flow_data = allegro_auth.start_device_flow()

        if _should_use_local_tasks():
            task_id = str(uuid.uuid4())
            _set_local_task(task_id, "PENDING", None)
            thread = threading.Thread(
                target=_run_local_allegro_auth_task,
                kwargs={
                    "task_id": task_id,
                    "device_code": device_flow_data["device_code"],
                    "interval": int(device_flow_data["interval"]),
                    "user_id": int(current_user.id),
                },
                daemon=True,
            )
            thread.start()
            return {
                "user_code": device_flow_data["user_code"],
                "verification_uri": device_flow_data["verification_uri"],
                "task_id": task_id
            }

        task = allegro_auth_task.delay(
            device_code=device_flow_data["device_code"],
            interval=device_flow_data["interval"],
            user_id=current_user.id
        )

        return {
            "user_code": device_flow_data["user_code"],
            "verification_uri": device_flow_data["verification_uri"],
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Allegro auth: {e}")

@router.get("/auth/status/{task_id}")
def get_task_status(task_id: str):
    with _local_tasks_lock:
        if task_id in _local_tasks:
            data = _local_tasks[task_id]
            return {"task_id": task_id, "status": data.get("status"), "result": data.get("result")}
    task_result = AsyncResult(task_id, app=celery)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result,
    }

@router.post("/accounts/{account_id}/re-authenticate/start")
def re_authenticate_account_start(
    account_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Start re-authentication for an existing account using device flow"""
    
    # Verify user has access to this account
    from app.core.security import verify_account_access
    if not verify_account_access(db, current_user, account_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this account"
        )
    
    # Verify account exists
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    client_id = os.getenv("ALLEGRO_CLIENT_ID") or ""
    client_secret = os.getenv("ALLEGRO_CLIENT_SECRET") or ""
    if (not client_id or not client_secret) or client_id == "DUMMY" or client_secret == "DUMMY":
        env_values = dotenv_values(Path(__file__).resolve().parents[4] / ".env")
        client_id = str(env_values.get("ALLEGRO_CLIENT_ID") or "")
        client_secret = str(env_values.get("ALLEGRO_CLIENT_SECRET") or "")
    if not client_id or not client_secret or client_id == "DUMMY" or client_secret == "DUMMY":
        raise HTTPException(
            status_code=400,
            detail="Brak konfiguracji Allegro. Ustaw ALLEGRO_CLIENT_ID i ALLEGRO_CLIENT_SECRET w pliku .env (dane z Allegro Developer)."
        )
    
    try:
        device_flow_data = allegro_auth.start_device_flow()

        if _should_use_local_tasks():
            task_id = str(uuid.uuid4())
            _set_local_task(task_id, "PENDING", None)
            thread = threading.Thread(
                target=_run_local_allegro_auth_task,
                kwargs={
                    "task_id": task_id,
                    "device_code": device_flow_data["device_code"],
                    "interval": int(device_flow_data["interval"]),
                    "user_id": int(current_user.id),
                    "account_id": int(account_id),
                },
                daemon=True,
            )
            thread.start()
            return {
                "user_code": device_flow_data["user_code"],
                "verification_uri": device_flow_data["verification_uri"],
                "task_id": task_id,
                "account_id": account_id,
                "account_name": account.nazwa_konta
            }

        task = allegro_auth_task.delay(
            device_code=device_flow_data["device_code"],
            interval=device_flow_data["interval"],
            user_id=current_user.id,
            account_id=account_id
        )

        return {
            "user_code": device_flow_data["user_code"],
            "verification_uri": device_flow_data["verification_uri"],
            "task_id": task.id,
            "account_id": account_id,
            "account_name": account.nazwa_konta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start re-authentication: {e}")

@router.get("/accounts/{account_id}/re-authenticate/status/{task_id}")
def get_reauth_task_status(
    account_id: int,
    task_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get status of account re-authentication task"""
    
    # Verify user has access to this account
    from app.core.security import verify_account_access
    if not verify_account_access(db, current_user, account_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this account"
        )
    
    task_result = AsyncResult(task_id, app=celery)
    return {
        "task_id": task_id,
        "account_id": account_id,
        "status": task_result.status,
        "result": task_result.result,
    }





@router.post("/refresh-token/{account_id}", response_model=schemas.Account)
async def refresh_allegro_token(
    account_id: int,
    current_user: User = Depends(require_vsprint_or_admin),
    db: Session = Depends(get_db)
):
    """Refresh Allegro access token for an account"""
    
    # Verify user has access to this account
    from app.core.security import verify_account_access
    if not verify_account_access(db, current_user, account_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this account"
        )
    
    account = AccountRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ALLEGRO_TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': account.refresh_token,
                    'client_id': settings.ALLEGRO_CLIENT_ID,
                    'client_secret': settings.ALLEGRO_CLIENT_SECRET,
                }
            )
            
            if response.status_code != 200:
                # Check if it's an invalid_grant error (expired/invalid refresh token)
                try:
                    error_data = response.json()
                    if error_data.get('error') == 'invalid_grant':
                        # Mark account as needing re-authentication
                        account.needs_reauth = True
                        db.commit()
                        raise HTTPException(
                            status_code=401,
                            detail={
                                "message": f"Konto Allegro '{account.nazwa_konta}' wymaga ponownej autoryzacji. Token został unieważniony.",
                                "needs_reauth": True,
                                "account_id": account_id,
                                "account_name": account.nazwa_konta
                            }
                        )
                except HTTPException:
                    raise
                except:
                    pass
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to refresh token: {response.text}"
                )
            
            tokens = response.json()
        
        # Update account with new tokens
        updated_account = AccountRepository.update_token(db, account_id, tokens)
        return updated_account
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing token: {str(e)}"
        )

@router.get("/shared-accounts", response_model=List[schemas.AccountWithOwnership])
async def get_shared_accounts(
    current_user: User = Depends(require_vsprint_or_admin),
    db: Session = Depends(get_db)
):
    """Get all accounts shared with the current vsprint employee"""
    
    # Get user's accessible accounts
    accounts = AccountRepository.get_user_accounts(db, current_user)
    
    # Add ownership information
    result = []
    for account in accounts:
        user_account_relation = db.query(models.UserMarketplaceAccount).filter(
            models.UserMarketplaceAccount.user_id == current_user.id,
            models.UserMarketplaceAccount.account_id == account.id
        ).first()
        
        account_data = schemas.AccountWithOwnership(
            **account.__dict__,
            is_owner=user_account_relation.is_owner if user_account_relation else False,
            shared_with_vsprint=user_account_relation.shared_with_vsprint if user_account_relation else False
        )
        result.append(account_data)
    
    return result 
