"""
Analytics API endpoints for AI token usage and user activity tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, distinct
from typing import Optional, List
from datetime import date, datetime
import csv
import io
from fastapi.responses import StreamingResponse

from app.db.session import get_db
from app.db import models, schemas
from app.core.auth import get_current_verified_user, require_vsprint_or_admin
from app.services.analytics_service import AnalyticsService
from app.services.token_cost_service import TokenCostService

router = APIRouter()

@router.get("/token-usage/my-usage", response_model=schemas.AIUsageSummary)
async def get_my_token_usage(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"), 
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get current user's AI token usage summary"""
    try:
        return AnalyticsService.get_user_usage_summary(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            operation_type=operation_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage data: {str(e)}")

@router.get("/token-usage/team-usage", response_model=schemas.AIUsageSummary) 
async def get_team_token_usage(
    employee_id: Optional[int] = Query(None, description="Specific employee ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    current_user: models.User = Depends(require_vsprint_or_admin),
    db: Session = Depends(get_db)
):
    """Get team AI token usage summary (vsprint managers only)"""
    try:
        # If no specific employee requested, aggregate all team usage
        if employee_id:
            # Verify the employee is part of vsprint team
            employee = db.query(models.User).filter(models.User.id == employee_id).first()
            if not employee or employee.role.value not in ["vsprint_employee", "admin"]:
                raise HTTPException(status_code=403, detail="Employee not found or not part of vsprint team")
            
            return AnalyticsService.get_user_usage_summary(
                db=db,
                user_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                operation_type=operation_type
            )
        else:
            # TODO: Implement team aggregate usage summary
            # For now, return current user's data
            return AnalyticsService.get_user_usage_summary(
                db=db,
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
                operation_type=operation_type
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team usage data: {str(e)}")

@router.get("/token-usage/detailed", response_model=List[schemas.AITokenUsageResponse])
async def get_detailed_token_usage(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    limit: int = Query(100, description="Maximum number of records"),
    offset: int = Query(0, description="Number of records to skip"),
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get detailed token usage records for current user"""
    try:
        from sqlalchemy import and_, func, desc
        
        query = db.query(models.AITokenUsage).filter(
            models.AITokenUsage.user_id == current_user.id
        )
        
        if start_date:
            query = query.filter(func.date(models.AITokenUsage.request_timestamp) >= start_date)
        if end_date:
            query = query.filter(func.date(models.AITokenUsage.request_timestamp) <= end_date)
        if operation_type:
            query = query.filter(models.AITokenUsage.operation_type == operation_type)
        
        usage_records = query.order_by(desc(models.AITokenUsage.request_timestamp)).offset(offset).limit(limit).all()
        
        return [schemas.AITokenUsageResponse.from_orm(record) for record in usage_records]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detailed usage data: {str(e)}")

@router.get("/activity/my-activity", response_model=List[schemas.UserActivityLogResponse])
async def get_my_activity(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, description="Maximum number of records"),
    offset: int = Query(0, description="Number of records to skip"),
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get current user's activity log"""
    try:
        return AnalyticsService.get_user_activities(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            action_type=action_type,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity data: {str(e)}")

@router.get("/activity/team-activity", response_model=schemas.TeamActivitySummary)
async def get_team_activity(
    employee_id: Optional[int] = Query(None, description="Specific employee ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Maximum number of activities to return"),
    offset: int = Query(0, description="Number of activities to skip"),
    role: Optional[str] = Query(None, description="Filter by role"),
    registration_source: Optional[str] = Query(None, description="Filter by registration source"),
    key_source: Optional[str] = Query(None, description="Filter by key source"),
    current_user: models.User = Depends(require_vsprint_or_admin),
    db: Session = Depends(get_db)
):
    """Get team activity summary (vsprint managers and admins)"""
    try:
        # Check if user is admin
        is_admin = current_user.role == models.UserRole.admin
        
        return AnalyticsService.get_team_activity_summary(
            db=db,
            manager_user_id=current_user.id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            role_filter=role,
            registration_source_filter=registration_source,
            key_source_filter=key_source,
            is_admin=is_admin
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team activity data: {str(e)}")

@router.get("/activity/live-feed", response_model=List[schemas.UserActivityLogResponse])
async def get_live_activity_feed(
    limit: int = Query(20, description="Maximum number of recent activities"),
    current_user: models.User = Depends(require_vsprint_or_admin),
    db: Session = Depends(get_db)
):
    """Get live activity feed for real-time monitoring (vsprint managers only)"""
    try:
        from sqlalchemy import desc, or_
        from datetime import timedelta
        
        # Get activities from last 24 hours for all vsprint users
        vsprint_users = db.query(models.User).filter(
            or_(
                models.User.role == 'vsprint_employee',
                models.User.role == 'admin'
            )
        ).all()
        
        user_ids = [user.id for user in vsprint_users]
        
        from sqlalchemy import and_
        
        recent_activities = db.query(models.UserActivityLog).filter(
            and_(
                models.UserActivityLog.user_id.in_(user_ids),
                models.UserActivityLog.timestamp >= datetime.now() - timedelta(hours=24)
            )
        ).order_by(desc(models.UserActivityLog.timestamp)).limit(limit).all()
        
        return [schemas.UserActivityLogResponse.from_orm(activity) for activity in recent_activities]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live activity feed: {str(e)}")

@router.get("/reports/usage-export")
async def export_usage_report(
    format: str = Query("csv", description="Export format: csv or json"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Export user's usage data"""
    try:
        from sqlalchemy import and_, func, desc
        
        query = db.query(models.AITokenUsage).filter(
            models.AITokenUsage.user_id == current_user.id
        )
        
        if start_date:
            query = query.filter(func.date(models.AITokenUsage.request_timestamp) >= start_date)
        if end_date:
            query = query.filter(func.date(models.AITokenUsage.request_timestamp) <= end_date)
        if operation_type:
            query = query.filter(models.AITokenUsage.operation_type == operation_type)
        
        usage_records = query.order_by(desc(models.AITokenUsage.request_timestamp)).all()
        
        if format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Timestamp", "Operation Type", "AI Provider", "Model", 
                "Input Tokens", "Output Tokens", "Total Tokens", 
                "Input Cost USD", "Output Cost USD", "Total Cost USD"
            ])
            
            # Write data
            for record in usage_records:
                writer.writerow([
                    record.request_timestamp.isoformat(),
                    record.operation_type,
                    record.ai_provider.value,
                    record.model_name,
                    record.input_tokens,
                    record.output_tokens,
                    record.total_tokens,
                    record.input_cost_usd,
                    record.output_cost_usd,
                    record.total_cost_usd
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=usage_report_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
        elif format.lower() == "json":
            import json
            
            data = []
            for record in usage_records:
                data.append({
                    "timestamp": record.request_timestamp.isoformat(),
                    "operation_type": record.operation_type,
                    "ai_provider": record.ai_provider.value,
                    "model_name": record.model_name,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "total_tokens": record.total_tokens,
                    "input_cost_usd": record.input_cost_usd,
                    "output_cost_usd": record.output_cost_usd,
                    "total_cost_usd": record.total_cost_usd
                })
            
            json_data = json.dumps(data, indent=2)
            
            return StreamingResponse(
                io.BytesIO(json_data.encode()),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=usage_report_{datetime.now().strftime('%Y%m%d')}.json"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export usage data: {str(e)}")

@router.get("/pricing/current")
async def get_current_pricing(
    current_user: models.User = Depends(get_current_verified_user)
):
    """Get current AI pricing information"""
    try:
        pricing_data = await TokenCostService.get_current_pricing_summary()
        return pricing_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing data: {str(e)}")

@router.post("/maintenance/cleanup-old-data")
async def cleanup_old_data(
    retention_months: int = Query(6, description="Number of months to retain data"),
    current_user: models.User = Depends(require_vsprint_or_admin),
    db: Session = Depends(get_db)
):
    """Cleanup old analytics data (admin only)"""
    try:
        if current_user.role.value != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        AnalyticsService.cleanup_old_data(db, retention_months)
        return {"message": f"Successfully cleaned up data older than {retention_months} months"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup data: {str(e)}")

@router.get("/stats/overview")
async def get_overview_stats(
    current_user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get overview statistics for current user"""
    try:
        from datetime import timedelta
        
        today = date.today()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        from decimal import Decimal
        
        # Get this month's stats
        this_month_usage = db.query(
            func.count(models.AITokenUsage.id).label('requests'),
            func.sum(models.AITokenUsage.input_tokens).label('input_tokens'),
            func.sum(models.AITokenUsage.output_tokens).label('output_tokens')
        ).filter(
            and_(
                models.AITokenUsage.user_id == current_user.id,
                func.date(models.AITokenUsage.request_timestamp) >= this_month_start
            )
        ).first()
        
        # Calculate total cost manually to avoid SQL type issues
        this_month_records = db.query(models.AITokenUsage).filter(
            and_(
                models.AITokenUsage.user_id == current_user.id,
                func.date(models.AITokenUsage.request_timestamp) >= this_month_start
            )
        ).all()
        
        this_month_cost = sum(Decimal(record.total_cost_usd) for record in this_month_records)
        
        # Get last month's stats for comparison
        last_month_usage = db.query(
            func.count(models.AITokenUsage.id).label('requests')
        ).filter(
            and_(
                models.AITokenUsage.user_id == current_user.id,
                func.date(models.AITokenUsage.request_timestamp) >= last_month_start,
                func.date(models.AITokenUsage.request_timestamp) < this_month_start
            )
        ).first()
        
        # Calculate last month cost manually
        last_month_records = db.query(models.AITokenUsage).filter(
            and_(
                models.AITokenUsage.user_id == current_user.id,
                func.date(models.AITokenUsage.request_timestamp) >= last_month_start,
                func.date(models.AITokenUsage.request_timestamp) < this_month_start
            )
        ).all()
        
        last_month_cost = sum(Decimal(record.total_cost_usd) for record in last_month_records)
        
        return {
            "this_month": {
                "requests": this_month_usage.requests or 0,
                "input_tokens": int(this_month_usage.input_tokens or 0),
                "output_tokens": int(this_month_usage.output_tokens or 0),
                "total_cost": str(this_month_cost)
            },
            "last_month": {
                "requests": last_month_usage.requests or 0,
                "total_cost": str(last_month_cost)
            },
            "comparison": {
                "requests_change": (this_month_usage.requests or 0) - (last_month_usage.requests or 0),
                "cost_change": float(this_month_cost) - float(last_month_cost)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overview stats: {str(e)}")
