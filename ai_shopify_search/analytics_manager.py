import logging
import uuid
import time
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from ai_shopify_search.models import (
    SearchAnalytics, SearchClick, SearchPerformance, 
    PopularSearch, FacetUsage, QuerySuggestion, SearchCorrection
)

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Centralized analytics management for search tracking and insights."""
    
    def __init__(self):
        self.session_id_generator = self._generate_session_id
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def track_search_analytics(
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
    ) -> int:
        """Track search analytics and return search_analytics_id."""
        try:
            session_id = self.session_id_generator()
            
            analytics = SearchAnalytics(
                session_id=session_id,
                query=query,
                search_type=search_type,
                filters=filters,
                results_count=results_count,
                page=page,
                limit=limit,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            db.add(analytics)
            db.commit()
            db.refresh(analytics)
            
            # Update related analytics
            self._update_popular_search(db, query)
            self._update_facet_usage(db, filters)
            self._update_daily_performance(db, search_type, response_time_ms, cache_hit, results_count)
            
            return analytics.id
            
        except Exception as e:
            logger.error(f"Error tracking search analytics: {e}")
            db.rollback()
            return None
    
    def track_product_click(
        self,
        db: Session,
        search_analytics_id: int,
        product_id: int,
        position: int,
        click_time_ms: float
    ):
        """Track product click."""
        try:
            click = SearchClick(
                search_analytics_id=search_analytics_id,
                product_id=product_id,
                position=position,
                click_time_ms=click_time_ms
            )
            
            db.add(click)
            db.commit()
            
            # Update popular search click stats
            self._update_popular_search_click(db, search_analytics_id, position)
            
        except Exception as e:
            logger.error(f"Error tracking product click: {e}")
            db.rollback()
    
    def _update_popular_search(self, db: Session, query: str):
        """Update popular search statistics."""
        try:
            popular_search = db.query(PopularSearch).filter_by(query=query.lower()).first()
            
            if popular_search:
                popular_search.search_count += 1
                popular_search.last_searched = datetime.now()
            else:
                popular_search = PopularSearch(
                    query=query.lower(),
                    search_count=1
                )
                db.add(popular_search)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating popular search: {e}")
            db.rollback()
    
    def _update_popular_search_click(self, db: Session, search_analytics_id: int, position: int):
        """Update popular search click statistics."""
        try:
            # Get search analytics
            search_analytics = db.query(SearchAnalytics).filter_by(id=search_analytics_id).first()
            if not search_analytics:
                return
            
            # Update popular search
            popular_search = db.query(PopularSearch).filter_by(query=search_analytics.query.lower()).first()
            if popular_search:
                popular_search.click_count += 1
                
                # Update average position
                total_clicks = popular_search.click_count
                current_avg = popular_search.avg_position_clicked
                new_avg = ((current_avg * (total_clicks - 1)) + position) / total_clicks
                popular_search.avg_position_clicked = new_avg
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating popular search click: {e}")
            db.rollback()
    
    def _update_facet_usage(self, db: Session, filters: Dict[str, Any]):
        """Update facet usage statistics."""
        try:
            for facet_type, facet_value in filters.items():
                if facet_value and facet_type not in ['min_price', 'max_price', 'page', 'limit']:
                    facet_usage = db.query(FacetUsage).filter_by(
                        facet_type=facet_type,
                        facet_value=str(facet_value).lower()
                    ).first()
                    
                    if facet_usage:
                        facet_usage.usage_count += 1
                        facet_usage.last_used = datetime.now()
                    else:
                        facet_usage = FacetUsage(
                            facet_type=facet_type,
                            facet_value=str(facet_value).lower(),
                            usage_count=1
                        )
                        db.add(facet_usage)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating facet usage: {e}")
            db.rollback()
    
    def _update_daily_performance(
        self,
        db: Session,
        search_type: str,
        response_time_ms: float,
        cache_hit: bool,
        results_count: int
    ):
        """Update daily performance statistics."""
        try:
            today = date.today().isoformat()
            
            performance = db.query(SearchPerformance).filter_by(
                date=today,
                search_type=search_type
            ).first()
            
            if performance:
                # Update existing statistics
                total_searches = performance.total_searches + 1
                total_clicks = performance.total_clicks  # Updated separately
                
                # Average response time
                current_avg_time = performance.avg_response_time_ms
                new_avg_time = ((current_avg_time * (total_searches - 1)) + response_time_ms) / total_searches
                
                # Cache hit rate
                current_cache_hits = performance.cache_hit_rate * (total_searches - 1)
                new_cache_hits = current_cache_hits + (1 if cache_hit else 0)
                new_cache_hit_rate = new_cache_hits / total_searches
                
                # Average results count
                current_avg_results = performance.avg_results_count
                new_avg_results = ((current_avg_results * (total_searches - 1)) + results_count) / total_searches
                
                performance.total_searches = total_searches
                performance.avg_response_time_ms = new_avg_time
                performance.cache_hit_rate = new_cache_hit_rate
                performance.avg_results_count = new_avg_results
                
            else:
                # New daily entry
                performance = SearchPerformance(
                    date=today,
                    search_type=search_type,
                    total_searches=1,
                    avg_response_time_ms=response_time_ms,
                    cache_hit_rate=1.0 if cache_hit else 0.0,
                    avg_results_count=results_count
                )
                db.add(performance)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating daily performance: {e}")
            db.rollback()
    
    def get_performance_analytics(
        self,
        db: Session,
        start_date: str,
        end_date: str,
        search_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance analytics for a specific period."""
        try:
            query = db.query(SearchPerformance).filter(
                SearchPerformance.date >= start_date,
                SearchPerformance.date <= end_date
            )
            
            if search_type:
                query = query.filter(SearchPerformance.search_type == search_type)
            
            results = query.all()
            
            analytics = []
            for result in results:
                analytics.append({
                    "date": result.date,
                    "search_type": result.search_type,
                    "total_searches": result.total_searches,
                    "total_clicks": result.total_clicks,
                    "avg_response_time_ms": result.avg_response_time_ms,
                    "cache_hit_rate": result.cache_hit_rate,
                    "avg_results_count": result.avg_results_count,
                    "click_through_rate": result.total_clicks / result.total_searches if result.total_searches > 0 else 0
                })
            
            return {
                "period": {"start_date": start_date, "end_date": end_date},
                "search_type_filter": search_type,
                "analytics": analytics,
                "summary": {
                    "total_searches": sum(a["total_searches"] for a in analytics),
                    "total_clicks": sum(a["total_clicks"] for a in analytics),
                    "avg_response_time_ms": sum(a["avg_response_time_ms"] for a in analytics) / len(analytics) if analytics else 0,
                    "avg_cache_hit_rate": sum(a["cache_hit_rate"] for a in analytics) / len(analytics) if analytics else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {}
    
    def get_popular_searches_analytics(
        self,
        db: Session,
        limit: int = 20,
        min_searches: int = 1
    ) -> Dict[str, Any]:
        """Get popular searches analytics."""
        try:
            popular_searches = db.query(PopularSearch).filter(
                PopularSearch.search_count >= min_searches
            ).order_by(PopularSearch.search_count.desc()).limit(limit).all()
            
            results = []
            for search in popular_searches:
                results.append({
                    "query": search.query,
                    "search_count": search.search_count,
                    "click_count": search.click_count,
                    "avg_position_clicked": search.avg_position_clicked,
                    "click_through_rate": search.click_count / search.search_count if search.search_count > 0 else 0,
                    "last_searched": search.last_searched.isoformat() if search.last_searched else None
                })
            
            return {
                "popular_searches": results,
                "total_searches": sum(r["search_count"] for r in results),
                "total_clicks": sum(r["click_count"] for r in results)
            }
            
        except Exception as e:
            logger.error(f"Error getting popular searches analytics: {e}")
            return {}

# Global analytics manager instance
analytics_manager = AnalyticsManager() 