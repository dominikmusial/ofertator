from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_


class AnalyticsArchiveService:
    
    @staticmethod
    def archive_user_analytics(db: Session, user_id: int, admin_id: int, user_display_name: str):
        """Archive all analytics data for a user before deletion"""
        
        # Archive AI token usage
        ai_token_usages = db.query(models.AITokenUsage).filter(models.AITokenUsage.user_id == user_id).all()
        for usage in ai_token_usages:
            archive_entry = models.AITokenUsageArchive(
                original_id=usage.id,
                user_id=usage.user_id,
                account_id=usage.account_id,
                operation_type=usage.operation_type,
                ai_provider=usage.ai_provider,
                model_name=usage.model_name,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
                input_cost_usd=usage.input_cost_usd,
                output_cost_usd=usage.output_cost_usd,
                total_cost_usd=usage.total_cost_usd,
                pricing_version=usage.pricing_version,
                request_timestamp=usage.request_timestamp,
                offer_id=usage.offer_id,
                template_id=usage.template_id,
                batch_id=usage.batch_id,
                deleted_user_display_name=user_display_name,
                deleted_at=datetime.now(),
                deleted_by_admin_id=admin_id
            )
            db.add(archive_entry)
        
        # Delete original AI token usage records
        db.query(models.AITokenUsage).filter(models.AITokenUsage.user_id == user_id).delete(synchronize_session=False)
        
        # Archive AI usage daily stats
        ai_daily_stats = db.query(models.AIUsageDailyStats).filter(models.AIUsageDailyStats.user_id == user_id).all()
        for stats in ai_daily_stats:
            archive_entry = models.AIUsageDailyStatsArchive(
                original_id=stats.id,
                user_id=stats.user_id,
                date=stats.date,
                total_requests=stats.total_requests,
                total_input_tokens=stats.total_input_tokens,
                total_output_tokens=stats.total_output_tokens,
                total_cost_usd=stats.total_cost_usd,
                operations_breakdown=stats.operations_breakdown,
                created_at=stats.created_at,
                updated_at=stats.updated_at,
                deleted_user_display_name=user_display_name,
                deleted_at=datetime.now(),
                deleted_by_admin_id=admin_id
            )
            db.add(archive_entry)
        
        # Delete original AI daily stats records
        db.query(models.AIUsageDailyStats).filter(models.AIUsageDailyStats.user_id == user_id).delete(synchronize_session=False)
        
        # Archive User activity logs (if this table exists)
        try:
            user_activity_logs = db.query(models.UserActivityLog).filter(models.UserActivityLog.user_id == user_id).all()
            for log in user_activity_logs:
                archive_entry = models.UserActivityLogArchive(
                    original_id=log.id,
                    user_id=log.user_id,
                    action_type=log.action_type,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    details=log.details,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    session_id=log.session_id,
                    timestamp=log.timestamp,
                    account_id=log.account_id,
                    deleted_user_display_name=user_display_name,
                    deleted_at=datetime.now(),
                    deleted_by_admin_id=admin_id
                )
                db.add(archive_entry)
            
            # Delete original activity log records
            db.query(models.UserActivityLog).filter(models.UserActivityLog.user_id == user_id).delete(synchronize_session=False)
        except AttributeError:
            # UserActivityLog table might not exist yet
            pass
        
        db.flush()  # Flush to ensure IDs are generated before commit
    
    @staticmethod
    def get_all_archived_users(db: Session) -> List[Dict]:
        """Get list of all users with archived analytics data"""
        
        # Get unique deleted users from archive tables
        archived_users = db.query(
            models.AITokenUsageArchive.deleted_user_display_name,
            models.AITokenUsageArchive.deleted_at,
            models.AITokenUsageArchive.deleted_by_admin_id,
            func.count(models.AITokenUsageArchive.id).label('token_usage_count')
        ).group_by(
            models.AITokenUsageArchive.deleted_user_display_name,
            models.AITokenUsageArchive.deleted_at,
            models.AITokenUsageArchive.deleted_by_admin_id
        ).all()
        
        result = []
        for user in archived_users:
            # Get additional counts from other archive tables
            daily_stats_count = db.query(models.AIUsageDailyStatsArchive).filter(
                models.AIUsageDailyStatsArchive.deleted_user_display_name == user.deleted_user_display_name
            ).count()
            
            activity_logs_count = 0
            try:
                activity_logs_count = db.query(models.UserActivityLogArchive).filter(
                    models.UserActivityLogArchive.deleted_user_display_name == user.deleted_user_display_name
                ).count()
            except AttributeError:
                # UserActivityLogArchive table might not exist yet
                pass
            
            result.append({
                "display_name": user.deleted_user_display_name,
                "deleted_at": user.deleted_at,
                "deleted_by_admin_id": user.deleted_by_admin_id,
                "archive_counts": {
                    "token_usage": user.token_usage_count,
                    "daily_stats": daily_stats_count,
                    "activity_logs": activity_logs_count
                }
            })
        
        return result
    
    @staticmethod
    def get_archived_user_analytics(db: Session, user_display_name: str) -> Dict:
        """Get archived analytics data for a specific deleted user"""
        
        # Get token usage data
        token_usage = db.query(models.AITokenUsageArchive).filter(
            models.AITokenUsageArchive.deleted_user_display_name == user_display_name
        ).all()
        
        # Get daily stats data
        daily_stats = db.query(models.AIUsageDailyStatsArchive).filter(
            models.AIUsageDailyStatsArchive.deleted_user_display_name == user_display_name
        ).all()
        
        # Convert to dictionaries
        token_usage_data = []
        for usage in token_usage:
            token_usage_data.append({
                "id": usage.original_id,
                "account_id": usage.account_id,
                "operation_type": usage.operation_type,
                "ai_provider": usage.ai_provider.value if usage.ai_provider else None,
                "model_name": usage.model_name,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "input_cost_usd": usage.input_cost_usd,
                "output_cost_usd": usage.output_cost_usd,
                "total_cost_usd": usage.total_cost_usd,
                "pricing_version": usage.pricing_version,
                "request_timestamp": usage.request_timestamp.isoformat() if usage.request_timestamp else None,
                "offer_id": usage.offer_id,
                "template_id": usage.template_id,
                "batch_id": usage.batch_id
            })
        
        daily_stats_data = []
        for stats in daily_stats:
            daily_stats_data.append({
                "id": stats.original_id,
                "date": stats.date,
                "total_requests": stats.total_requests,
                "total_input_tokens": stats.total_input_tokens,
                "total_output_tokens": stats.total_output_tokens,
                "total_cost_usd": stats.total_cost_usd,
                "operations_breakdown": stats.operations_breakdown,
                "created_at": stats.created_at.isoformat() if stats.created_at else None,
                "updated_at": stats.updated_at.isoformat() if stats.updated_at else None
            })
        
        return {
            "user_display_name": user_display_name,
            "token_usage_records": len(token_usage_data),
            "daily_stats_records": len(daily_stats_data),
            "activity_log_records": 0,  # TODO: Add when UserActivityLogArchive is available
            "token_usage": token_usage_data,
            "daily_stats": daily_stats_data
        }
    
    @staticmethod
    def get_team_analytics_with_archived(
        db: Session, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict:
        """Get team analytics including archived user data"""
        
        # Build date filter conditions
        date_conditions = []
        if start_date:
            date_conditions.append(models.AITokenUsage.request_timestamp >= start_date)
            # For archived data
            date_conditions.append(models.AITokenUsageArchive.request_timestamp >= start_date)
        if end_date:
            date_conditions.append(models.AITokenUsage.request_timestamp <= end_date)
            # For archived data
            date_conditions.append(models.AITokenUsageArchive.request_timestamp <= end_date)
        
        # Get active users analytics
        active_query = db.query(
            models.User.id,
            models.User.email,
            models.User.first_name,
            models.User.last_name,
            func.count(models.AITokenUsage.id).label('total_requests'),
            func.sum(models.AITokenUsage.input_tokens).label('total_input_tokens'),
            func.sum(models.AITokenUsage.output_tokens).label('total_output_tokens'),
            func.sum(func.cast(models.AITokenUsage.total_cost_usd, db.bind.dialect.NUMERIC)).label('total_cost')
        ).outerjoin(models.AITokenUsage).group_by(
            models.User.id, models.User.email, models.User.first_name, models.User.last_name
        )
        
        if date_conditions:
            for condition in date_conditions:
                if 'AITokenUsage.' in str(condition):
                    active_query = active_query.filter(condition)
        
        active_users = active_query.all()
        
        # Get archived users analytics
        archived_query = db.query(
            models.AITokenUsageArchive.deleted_user_display_name,
            func.count(models.AITokenUsageArchive.id).label('total_requests'),
            func.sum(models.AITokenUsageArchive.input_tokens).label('total_input_tokens'),
            func.sum(models.AITokenUsageArchive.output_tokens).label('total_output_tokens'),
            func.sum(func.cast(models.AITokenUsageArchive.total_cost_usd, db.bind.dialect.NUMERIC)).label('total_cost')
        ).group_by(models.AITokenUsageArchive.deleted_user_display_name)
        
        if date_conditions:
            for condition in date_conditions:
                if 'AITokenUsageArchive.' in str(condition):
                    archived_query = archived_query.filter(condition)
        
        archived_users = archived_query.all()
        
        # Format active users data
        active_users_data = []
        total_cost = 0
        total_requests = 0
        
        for user in active_users:
            user_cost = float(user.total_cost or 0)
            user_requests = user.total_requests or 0
            
            total_cost += user_cost
            total_requests += user_requests
            
            active_users_data.append({
                "user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "total_requests": user_requests,
                "total_input_tokens": user.total_input_tokens or 0,
                "total_output_tokens": user.total_output_tokens or 0,
                "total_cost_usd": f"{user_cost:.4f}"
            })
        
        # Format archived users data
        archived_users_data = []
        for user in archived_users:
            user_cost = float(user.total_cost or 0)
            user_requests = user.total_requests or 0
            
            total_cost += user_cost
            total_requests += user_requests
            
            archived_users_data.append({
                "user_display_name": user.deleted_user_display_name,
                "total_requests": user_requests,
                "total_input_tokens": user.total_input_tokens or 0,
                "total_output_tokens": user.total_output_tokens or 0,
                "total_cost_usd": f"{user_cost:.4f}",
                "is_deleted": True
            })
        
        return {
            "active_users": active_users_data,
            "archived_users": archived_users_data,
            "total_cost": f"{total_cost:.4f}",
            "total_requests": total_requests
        }