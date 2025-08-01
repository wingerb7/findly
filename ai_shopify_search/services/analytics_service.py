#!/usr/bin/env python3
"""
Analytics Service for tracking search analytics and insights.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from core.models import (
    SearchAnalytics, SearchClick, SearchPerformance, 
    PopularSearch, FacetUsage, QuerySuggestion, SearchCorrection
)
from utils.privacy import (
    anonymize_ip, sanitize_user_agent, generate_session_id, 
    is_session_expired, sanitize_log_data, DataRetentionManager, PRIVACY_CONFIG
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Specialized service for analytics tracking and insights."""
    
    def __init__(self):
        self.session_id_generator = generate_session_id
        self.data_retention_manager = DataRetentionManager(
            default_retention_days=PRIVACY_CONFIG["search_analytics_retention_days"]
        )
    
    async def track_search(
        self,
        db: Session,
        query: str,
        search_type: str,
        filters: Dict[str, Any],
        results_count: int,
        page: int,
        limit: int,
        response_time_ms: float,
        cache_hit: bool,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[int]:
        """
        Track search analytics with GDPR compliance.
        
        Args:
            db: Database session
            query: Search query
            search_type: Type of search (basic, ai, faceted)
            filters: Applied filters
            results_count: Number of results returned
            page: Page number
            limit: Results per page
            response_time_ms: Response time in milliseconds
            cache_hit: Whether result was from cache
            user_agent: User agent string
            ip_address: IP address
            
        Returns:
            Search analytics ID or None if tracking failed
        """
        try:
            # Generate GDPR-compliant session ID
            session_id = self.session_id_generator()
            
            # Anonymize IP address for GDPR compliance
            anonymized_ip = anonymize_ip(ip_address) if ip_address else None
            
            # Sanitize user agent for privacy
            sanitized_user_agent = sanitize_user_agent(user_agent) if user_agent else None
            
            # Sanitize query for logging
            sanitized_query = sanitize_log_data(query, max_length=100)
            
            analytics = SearchAnalytics(
                session_id=session_id,
                query=query,  # Store original query for functionality
                search_type=search_type,
                filters=filters,
                results_count=results_count,
                page=page,
                limit=limit,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                user_agent=sanitized_user_agent,
                ip_address=anonymized_ip
            )
            
            db.add(analytics)
            db.commit()
            db.refresh(analytics)
            
            # Update related analytics
            await self._update_popular_search(db, query)
            await self._update_facet_usage(db, filters)
            await self._update_daily_performance(db, search_type, response_time_ms, cache_hit, results_count)
            
            # Log with sanitized data
            logger.info(
                f"Search analytics tracked: {sanitized_query} ({search_type}) - "
                f"{results_count} results, {response_time_ms:.2f}ms, "
                f"cache_hit={cache_hit}, ip={anonymized_ip}, ua={sanitized_user_agent}"
            )
            
            return analytics.id
            
        except Exception as e:
            logger.error(f"Error tracking search analytics: {e}")
            db.rollback()
            return None
    
    async def track_click(
        self,
        db: Session,
        search_analytics_id: int,
        product_id: int,
        position: int,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Track product click analytics.
        
        Args:
            db: Database session
            search_analytics_id: ID of the search analytics record
            product_id: ID of the clicked product
            position: Position of the product in search results
            user_agent: User agent string
            ip_address: IP address
            
        Returns:
            True if tracking successful, False otherwise
        """
        try:
            # Anonymize IP address
            anonymized_ip = anonymize_ip(ip_address) if ip_address else None
            
            # Sanitize user agent
            sanitized_user_agent = sanitize_user_agent(user_agent) if user_agent else None
            
            click = SearchClick(
                search_analytics_id=search_analytics_id,
                product_id=product_id,
                position=position,
                user_agent=sanitized_user_agent,
                ip_address=anonymized_ip
            )
            
            db.add(click)
            db.commit()
            
            # Update popular search click count
            await self._update_popular_search_clicks(db, search_analytics_id)
            
            logger.info(f"Click tracked: product_id={product_id}, position={position}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking click: {e}")
            db.rollback()
            return False
    
    async def get_popular_searches(
        self,
        db: Session,
        limit: int = 20,
        min_searches: int = 1,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get popular searches analytics.
        
        Args:
            db: Database session
            limit: Maximum number of results
            min_searches: Minimum search count
            days: Number of days to look back
            
        Returns:
            Popular searches with metadata
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            popular_searches = db.query(PopularSearch).filter(
                PopularSearch.search_count >= min_searches,
                PopularSearch.last_searched >= cutoff_date
            ).order_by(PopularSearch.search_count.desc()).limit(limit).all()
            
            return {
                "popular_searches": [
                    {
                        "query": search.query,
                        "search_count": search.search_count,
                        "click_count": search.click_count,
                        "avg_position_clicked": search.avg_position_clicked,
                        "last_searched": search.last_searched.isoformat() if search.last_searched else None
                    }
                    for search in popular_searches
                ],
                "count": len(popular_searches),
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return {"popular_searches": [], "count": 0, "period_days": days}
    
    async def get_search_performance(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        search_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get search performance analytics.
        
        Args:
            db: Session
            start_date: Start date
            end_date: End date
            search_type: Filter by search type
            
        Returns:
            Performance analytics
        """
        try:
            query = db.query(SearchPerformance).filter(
                SearchPerformance.date >= start_date,
                SearchPerformance.date <= end_date
            )
            
            if search_type:
                query = query.filter(SearchPerformance.search_type == search_type)
            
            performance_data = query.order_by(SearchPerformance.date.desc()).all()
            
            return {
                "performance_data": [
                    {
                        "date": perf.date.isoformat(),
                        "search_type": perf.search_type,
                        "total_searches": perf.total_searches,
                        "avg_response_time": perf.avg_response_time,
                        "cache_hit_rate": perf.cache_hit_rate,
                        "avg_results_count": perf.avg_results_count
                    }
                    for perf in performance_data
                ],
                "count": len(performance_data),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting search performance: {e}")
            return {"performance_data": [], "count": 0}
    
    async def cleanup_expired_data(self, db: Session) -> Dict[str, int]:
        """
        Clean up expired analytics data based on retention policies.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cleanup_stats = {}
            
            # Clean up expired search analytics
            cutoff_date = self.data_retention_manager.get_retention_date()
            expired_analytics = db.query(SearchAnalytics).filter(
                SearchAnalytics.created_at < cutoff_date
            ).delete()
            cleanup_stats["search_analytics"] = expired_analytics
            
            # Clean up expired search clicks (older than 1 year)
            clicks_cutoff = datetime.now() - timedelta(days=365)
            expired_clicks = db.query(SearchClick).filter(
                SearchClick.created_at < clicks_cutoff
            ).delete()
            cleanup_stats["search_clicks"] = expired_clicks
            
            # Clean up expired search performance data (older than 2 years)
            performance_cutoff = datetime.now() - timedelta(days=730)
            expired_performance = db.query(SearchPerformance).filter(
                SearchPerformance.created_at < performance_cutoff
            ).delete()
            cleanup_stats["search_performance"] = expired_performance
            
            db.commit()
            
            logger.info(f"Data cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            db.rollback()
            return {}
    
    async def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Clean up expired session data.
        
        Args:
            db: Database session
            
        Returns:
            Number of expired sessions cleaned up
        """
        try:
            # Get all session IDs
            sessions = db.query(SearchAnalytics.session_id).distinct().all()
            expired_count = 0
            
            for (session_id,) in sessions:
                if is_session_expired(session_id, PRIVACY_CONFIG["session_expiry_hours"]):
                    # Delete all analytics for this session
                    deleted = db.query(SearchAnalytics).filter(
                        SearchAnalytics.session_id == session_id
                    ).delete()
                    expired_count += deleted
            
            db.commit()
            logger.info(f"Cleaned up {expired_count} expired session records")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            db.rollback()
            return 0
    
    async def _update_popular_search(self, db: Session, query: str) -> None:
        """Update popular search statistics."""
        try:
            popular_search = db.query(PopularSearch).filter(
                PopularSearch.query == query
            ).first()
            
            if popular_search:
                popular_search.search_count += 1
                popular_search.last_searched = datetime.now()
            else:
                popular_search = PopularSearch(
                    query=query,
                    search_count=1,
                    click_count=0,
                    last_searched=datetime.now()
                )
                db.add(popular_search)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error updating popular search: {e}")
            db.rollback()
    
    async def _update_popular_search_clicks(self, db: Session, search_analytics_id: int) -> None:
        """Update popular search click statistics."""
        try:
            # Get the search analytics record
            search_analytics = db.query(SearchAnalytics).filter(
                SearchAnalytics.id == search_analytics_id
            ).first()
            
            if search_analytics:
                popular_search = db.query(PopularSearch).filter(
                    PopularSearch.query == search_analytics.query
                ).first()
                
                if popular_search:
                    popular_search.click_count += 1
                    db.commit()
        except Exception as e:
            logger.error(f"Error updating popular search clicks: {e}")
            db.rollback()
    
    async def _update_facet_usage(self, db: Session, filters: Dict[str, Any]) -> None:
        """Update facet usage statistics."""
        try:
            for facet_name, facet_value in filters.items():
                facet_usage = db.query(FacetUsage).filter(
                    FacetUsage.facet_name == facet_name,
                    FacetUsage.facet_value == str(facet_value)
                ).first()
                
                if facet_usage:
                    facet_usage.usage_count += 1
                else:
                    facet_usage = FacetUsage(
                        facet_name=facet_name,
                        facet_value=str(facet_value),
                        usage_count=1
                    )
                    db.add(facet_usage)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error updating facet usage: {e}")
            db.rollback()
    
    async def _update_daily_performance(
        self,
        db: Session,
        search_type: str,
        response_time_ms: float,
        cache_hit: bool,
        results_count: int
    ) -> None:
        """Update daily performance statistics."""
        try:
            today = date.today()
            
            performance = db.query(SearchPerformance).filter(
                SearchPerformance.date == today,
                SearchPerformance.search_type == search_type
            ).first()
            
            if performance:
                # Update existing record
                total_searches = performance.total_searches + 1
                total_response_time = performance.avg_response_time * performance.total_searches + response_time_ms
                total_cache_hits = performance.cache_hit_rate * performance.total_searches + (1 if cache_hit else 0)
                total_results = performance.avg_results_count * performance.total_searches + results_count
                
                performance.total_searches = total_searches
                performance.avg_response_time = total_response_time / total_searches
                performance.cache_hit_rate = total_cache_hits / total_searches
                performance.avg_results_count = total_results / total_searches
            else:
                # Create new record
                performance = SearchPerformance(
                    date=today,
                    search_type=search_type,
                    total_searches=1,
                    avg_response_time=response_time_ms,
                    cache_hit_rate=1.0 if cache_hit else 0.0,
                    avg_results_count=results_count
                )
                db.add(performance)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error updating daily performance: {e}")
            db.rollback() 