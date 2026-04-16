"""
Analytics service for tracking AI token usage and user activity.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
import uuid

from app.db.models import (
    AITokenUsage, AIUsageDailyStats, UserActivityLog, UserSession, 
    User, Account, Template, UserAIConfig
)
from app.db.schemas import (
    AITokenUsageResponse, AIUsageDailyStatsResponse, AIUsageSummary,
    UserActivityLogResponse, TeamActivitySummary, UserSummaryExtended
)
from app.services.token_cost_service import TokenCostService

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for AI usage and activity analytics"""
    
    @staticmethod
    def log_ai_usage(
        db: Session,
        user_id: int,
        operation_type: str,
        ai_provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        account_id: Optional[int] = None,
        offer_id: Optional[str] = None,
        template_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        key_source: Optional[str] = None
    ) -> AITokenUsage:
        """Log AI token usage and calculate costs"""
        try:
            # Calculate costs using fallback pricing for simplicity
            cost_data = AnalyticsService._calculate_cost_fallback(
                provider=ai_provider,
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Create usage record
            usage_record = AITokenUsage(
                user_id=user_id,
                account_id=account_id,
                operation_type=operation_type,
                ai_provider=ai_provider,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost_usd=cost_data['input_cost_usd'],
                output_cost_usd=cost_data['output_cost_usd'],
                total_cost_usd=cost_data['total_cost_usd'],
                pricing_version=cost_data['pricing_version'],
                offer_id=offer_id,
                template_id=template_id,
                batch_id=batch_id,
                key_source=key_source
            )
            
            db.add(usage_record)
            db.commit()
            db.refresh(usage_record)
            
            # Update daily stats
            AnalyticsService._update_daily_stats(
                db, user_id, operation_type, input_tokens, output_tokens, cost_data['total_cost_usd']
            )
            
            logger.info(f"Logged AI usage for user {user_id}: {input_tokens}+{output_tokens} tokens, ${cost_data['total_cost_usd']}")
            return usage_record
            
        except Exception as e:
            logger.error(f"Failed to log AI usage: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def _update_daily_stats(
        db: Session,
        user_id: int,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        total_cost: str
    ):
        """Update daily aggregated statistics"""
        try:
            today = date.today().strftime('%Y-%m-%d')
            
            # Get or create daily stats record
            daily_stats = db.query(AIUsageDailyStats).filter(
                and_(
                    AIUsageDailyStats.user_id == user_id,
                    AIUsageDailyStats.date == today
                )
            ).first()
            
            if not daily_stats:
                daily_stats = AIUsageDailyStats(
                    user_id=user_id,
                    date=today,
                    total_requests=0,
                    total_input_tokens=0,
                    total_output_tokens=0,
                    total_cost_usd='0.000000',
                    operations_breakdown={}
                )
                db.add(daily_stats)
            
            # Update stats
            daily_stats.total_requests += 1
            daily_stats.total_input_tokens += input_tokens
            daily_stats.total_output_tokens += output_tokens
            
            # Add costs using Decimal for precision
            current_cost = Decimal(daily_stats.total_cost_usd)
            new_cost = current_cost + Decimal(total_cost)
            daily_stats.total_cost_usd = str(new_cost)
            
            # Update operations breakdown
            breakdown = daily_stats.operations_breakdown or {}
            breakdown[operation_type] = breakdown.get(operation_type, 0) + 1
            daily_stats.operations_breakdown = breakdown
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update daily stats: {e}")
            db.rollback()
    
    @staticmethod
    def get_user_usage_summary(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        operation_type: Optional[str] = None
    ) -> AIUsageSummary:
        """Get usage summary for a user within date range"""
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query
        query = db.query(AITokenUsage).filter(
            and_(
                AITokenUsage.user_id == user_id,
                func.date(AITokenUsage.request_timestamp) >= start_date,
                func.date(AITokenUsage.request_timestamp) <= end_date
            )
        )
        
        if operation_type:
            query = query.filter(AITokenUsage.operation_type == operation_type)
        
        usage_records = query.all()
        
        # Calculate totals
        total_requests = len(usage_records)
        total_input_tokens = sum(r.input_tokens for r in usage_records)
        total_output_tokens = sum(r.output_tokens for r in usage_records)
        total_cost = sum(Decimal(r.total_cost_usd) for r in usage_records)
        
        # Operation breakdown
        operation_breakdown = {}
        for record in usage_records:
            op_type = record.operation_type
            if op_type not in operation_breakdown:
                operation_breakdown[op_type] = {
                    'count': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'total_cost': Decimal('0')
                }
            operation_breakdown[op_type]['count'] += 1
            operation_breakdown[op_type]['input_tokens'] += record.input_tokens
            operation_breakdown[op_type]['output_tokens'] += record.output_tokens
            operation_breakdown[op_type]['total_cost'] += Decimal(record.total_cost_usd)
        
        # Convert Decimal to string for response
        for op_data in operation_breakdown.values():
            op_data['total_cost'] = str(op_data['total_cost'])
        
        # Get daily stats
        daily_stats = db.query(AIUsageDailyStats).filter(
            and_(
                AIUsageDailyStats.user_id == user_id,
                AIUsageDailyStats.date >= start_date.strftime('%Y-%m-%d'),
                AIUsageDailyStats.date <= end_date.strftime('%Y-%m-%d')
            )
        ).order_by(AIUsageDailyStats.date).all()
        
        return AIUsageSummary(
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost_usd=str(total_cost),
            date_range=f"{start_date} to {end_date}",
            operation_breakdown=operation_breakdown,
            daily_stats=[AIUsageDailyStatsResponse.from_orm(stat) for stat in daily_stats]
        )
    
    @staticmethod
    def log_user_activity(
        db: Session,
        user_id: int,
        action_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        account_id: Optional[int] = None
    ) -> UserActivityLog:
        """Log user activity"""
        try:
            activity_log = UserActivityLog(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                account_id=account_id
            )
            
            db.add(activity_log)
            db.commit()
            db.refresh(activity_log)
            
            # Update session activity count if session_id provided
            if session_id:
                AnalyticsService._update_session_activity(db, session_id)
            
            logger.debug(f"Logged activity for user {user_id}: {action_type}")
            return activity_log
            
        except Exception as e:
            logger.error(f"Failed to log user activity: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def _update_session_activity(db: Session, session_id: str):
        """Update session activity count and last activity time"""
        try:
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                session.activity_count += 1
                session.last_activity = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            db.rollback()
    
    @staticmethod
    def get_user_activities(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserActivityLogResponse]:
        """Get user activities with filtering"""
        
        query = db.query(UserActivityLog).filter(UserActivityLog.user_id == user_id)
        
        if start_date:
            query = query.filter(func.date(UserActivityLog.timestamp) >= start_date)
        if end_date:
            query = query.filter(func.date(UserActivityLog.timestamp) <= end_date)
        if action_type:
            query = query.filter(UserActivityLog.action_type == action_type)
        
        activities = query.order_by(desc(UserActivityLog.timestamp)).offset(offset).limit(limit).all()
        
        return [UserActivityLogResponse.from_orm(activity) for activity in activities]
    
    @staticmethod
    def get_team_activity_summary(
        db: Session,
        manager_user_id: int,
        employee_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
        role_filter: Optional[str] = None,
        registration_source_filter: Optional[str] = None,
        key_source_filter: Optional[str] = None,
        is_admin: bool = False
    ) -> TeamActivitySummary:
        """Get team activity summary for managers/admins"""
        
        # Build user query based on access level
        if is_admin:
            # Admin sees all users
            users_query = db.query(User).filter(User.admin_approved == True, User.is_active == True)
        else:
            # Vsprint managers see only vsprint team
            users_query = db.query(User).filter(
                or_(
                    User.role == 'vsprint_employee',
                    User.role == 'admin'
                )
            )
        
        # Apply role filter
        if role_filter:
            users_query = users_query.filter(User.role == role_filter)
        
        # Apply registration source filter
        if registration_source_filter:
            users_query = users_query.filter(User.registration_source == registration_source_filter)
        
        all_users = users_query.all()
        user_ids = [user.id for user in all_users]
        
        # Filter by specific employee if requested
        if employee_id:
            user_ids = [employee_id] if employee_id in user_ids else []
        
        # Default to current month if no dates provided
        if not start_date:
            now = date.today()
            start_date = now.replace(day=1)
        if not end_date:
            end_date = date.today()
        
        # Get activities in date range
        activities_query = db.query(UserActivityLog).filter(
            and_(
                UserActivityLog.user_id.in_(user_ids),
                func.date(UserActivityLog.timestamp) >= start_date,
                func.date(UserActivityLog.timestamp) <= end_date
            )
        )
        
        period_activities = activities_query.all()
        
        # Get AI usage stats in date range
        usage_query = db.query(AITokenUsage).filter(
            and_(
                AITokenUsage.user_id.in_(user_ids),
                func.date(AITokenUsage.request_timestamp) >= start_date,
                func.date(AITokenUsage.request_timestamp) <= end_date
            )
        )
        
        period_usage = usage_query.all()
        total_cost_period = sum(Decimal(usage.total_cost_usd) for usage in period_usage)
        
        # Get paginated activities for the detailed list
        detailed_activities = activities_query.order_by(
            desc(UserActivityLog.timestamp)
        ).offset(offset).limit(limit).all()
        
        # Count total activities for pagination
        total_activities_count = activities_query.count()
        
        # Calculate active users in period
        active_user_ids = set(activity.user_id for activity in period_activities)
        
        # Get AI configs for key_source determination
        configs_query = db.query(UserAIConfig).filter(UserAIConfig.user_id.in_(user_ids)).all()
        configs_by_user = {config.user_id: config for config in configs_query}
        
        # Create user summaries
        user_summaries = []
        for user in all_users:
            if user.id in user_ids:
                user_activities = [a for a in period_activities if a.user_id == user.id]
                user_usage = [u for u in period_usage if u.user_id == user.id]
                user_cost = sum(Decimal(u.total_cost_usd) for u in user_usage)
                
                # Determine key_source
                config = configs_by_user.get(user.id)
                if config and config.is_active:
                    key_source = 'user_custom'
                elif user.role in ['vsprint_employee', 'admin'] or user.registration_source == 'asystenciai' or user.role == 'user':
                    key_source = 'company_default'
                else:
                    key_source = 'none'
                
                # Apply key_source filter
                if key_source_filter and key_source != key_source_filter:
                    continue
                
                from app.db.schemas import UserSummaryExtended
                user_summaries.append(UserSummaryExtended(
                    user_id=user.id,
                    user_name=f"{user.first_name} {user.last_name}",
                    user_email=user.email,
                    role=user.role.value if hasattr(user.role, 'value') else str(user.role),
                    registration_source=user.registration_source.value if hasattr(user.registration_source, 'value') else str(user.registration_source),
                    key_source=key_source,
                    activity_count=len(user_activities),
                    ai_requests=len(user_usage),
                    cost=str(user_cost),
                    last_activity=max([a.timestamp for a in user_activities]) if user_activities else None
                ))
        
        return TeamActivitySummary(
            total_active_users=len(active_user_ids),
            total_operations_today=len(period_activities),
            total_cost_today=str(total_cost_period),
            recent_activities=[UserActivityLogResponse.from_orm(activity) for activity in detailed_activities],
            activities=[UserActivityLogResponse.from_orm(activity) for activity in detailed_activities],
            user_summaries=user_summaries,
            total_activities=total_activities_count
        )
    
    @staticmethod
    def create_or_update_session(
        db: Session,
        user_id: int,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        login_method: Optional[str] = None
    ) -> UserSession:
        """Create or update user session"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Check if session already exists
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                # Update existing session
                session.last_activity = datetime.utcnow()
                if ip_address:
                    session.ip_address = ip_address
                if user_agent:
                    session.user_agent = user_agent
            else:
                # Create new session
                session = UserSession(
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    login_method=login_method
                )
                db.add(session)
            
            db.commit()
            db.refresh(session)
            return session
            
        except Exception as e:
            logger.error(f"Failed to create/update session: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def end_session(db: Session, session_id: str):
        """End a user session"""
        try:
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).first()
            
            if session:
                session.session_end = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            db.rollback()
    
    @staticmethod
    def cleanup_old_data(db: Session, retention_months: int = 6):
        """Clean up old analytics data based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_months * 30)
            
            # Delete old AI usage records
            old_usage_count = db.query(AITokenUsage).filter(
                AITokenUsage.request_timestamp < cutoff_date
            ).count()
            
            db.query(AITokenUsage).filter(
                AITokenUsage.request_timestamp < cutoff_date
            ).delete()
            
            # Delete old activity logs
            old_activity_count = db.query(UserActivityLog).filter(
                UserActivityLog.timestamp < cutoff_date
            ).count()
            
            db.query(UserActivityLog).filter(
                UserActivityLog.timestamp < cutoff_date
            ).delete()
            
            # Delete old daily stats
            cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')
            old_stats_count = db.query(AIUsageDailyStats).filter(
                AIUsageDailyStats.date < cutoff_date_str
            ).count()
            
            db.query(AIUsageDailyStats).filter(
                AIUsageDailyStats.date < cutoff_date_str
            ).delete()
            
            # Delete old sessions
            old_sessions_count = db.query(UserSession).filter(
                UserSession.session_start < cutoff_date
            ).count()
            
            db.query(UserSession).filter(
                UserSession.session_start < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up old data: {old_usage_count} usage records, "
                       f"{old_activity_count} activity logs, {old_stats_count} daily stats, "
                       f"{old_sessions_count} sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def _calculate_cost_fallback(provider: str, model: str, input_tokens: int, output_tokens: int) -> dict:
        """Calculate cost using fallback pricing (synchronous)"""
        from decimal import Decimal
        
        # Simplified fallback pricing
        fallback_pricing = {
            'anthropic': {
                'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
                'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
                'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            },
            'google': {
                'gemini-1.5-flash': {'input': 0.000075, 'output': 0.0003},
                'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
                'gemini-1.0-pro': {'input': 0.0005, 'output': 0.0015},
            }
        }
        
        try:
            # Get model pricing or use default
            model_pricing = fallback_pricing.get(provider, {}).get(model)
            if not model_pricing:
                # Use first available model as fallback
                available_models = fallback_pricing.get(provider, {})
                if available_models:
                    model_pricing = list(available_models.values())[0]
                else:
                    # Ultimate fallback
                    model_pricing = {'input': 0.001, 'output': 0.002}
            
            # Calculate costs
            input_cost = Decimal(str(input_tokens)) * Decimal(str(model_pricing['input'])) / Decimal('1000')
            output_cost = Decimal(str(output_tokens)) * Decimal(str(model_pricing['output'])) / Decimal('1000')
            total_cost = input_cost + output_cost
            
            return {
                'input_cost_usd': str(input_cost),
                'output_cost_usd': str(output_cost),
                'total_cost_usd': str(total_cost),
                'pricing_version': 'fallback_v1'
            }
            
        except Exception as e:
            logger.error(f"Error calculating fallback cost: {e}")
            return {
                'input_cost_usd': '0.00',
                'output_cost_usd': '0.00',
                'total_cost_usd': '0.00',
                'pricing_version': 'error_fallback'
            }
