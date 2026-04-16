"""Configuration API - Feature flags and system configuration."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict

from app.db.session import get_db
from app.services.feature_flag_service import FeatureFlagService

router = APIRouter()


@router.get("/feature-flags", response_model=Dict)
async def get_feature_flags(
    db: Session = Depends(get_db)
):
    """
    Get all feature flags for the frontend.
    
    Returns feature flags in a structured format that can be consumed
    by the frontend FeatureFlagContext.
    """
    flags = FeatureFlagService.get_all_feature_flags(db)
    return flags
