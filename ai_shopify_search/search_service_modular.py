"""
Modular search service that orchestrates different specialized services.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from services import service_factory
from core.database_async import get_async_db

logger = logging.getLogger(__name__)


class ModularSearchService:
    """Modular search service that orchestrates specialized services."""
    
    def __init__(self):
        """Initialize the modular search service."""
        self.ai_search_service = service_factory.get_ai_search_service()
        self.suggestion_service = service_factory.get_suggestion_service()
        self.autocomplete_service = service_factory.get_autocomplete_service()
        self.cache_service = service_factory.get_cache_service()
        self.analytics_service = service_factory.get_analytics_service()
    
    async def search_products(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 25,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        source_language: Optional[str] = None,
        target_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Perform AI-powered product search with vector embeddings.
        
        Args:
            db: Database session
            query: Search query
            page: Page number
            limit: Results per page
            min_price: Minimum price filter
            max_price: Maximum price filter
            user_agent: User agent string
            ip_address: IP address
            source_language: Source language
            target_language: Target language
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Use AI search service for the main search
            result = await self.ai_search_service.search_products(
                db=db,
                query=query,
                page=page,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                user_agent=user_agent,
                ip_address=ip_address,
                source_language=source_language,
                target_language=target_language
            )
            
            # Add service metadata
            result["service_type"] = "modular"
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            logger.error(f"Error in modular search: {e}")
            raise
    
    async def get_suggestions(
        self,
        db: Session,
        query: str,
        limit: int = 10,
        include_autocomplete: bool = True,
        include_popular: bool = True,
        include_related: bool = True,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive search suggestions.
        
        Args:
            db: Database session
            query: Search query
            limit: Maximum number of suggestions
            include_autocomplete: Include autocomplete suggestions
            include_popular: Include popular suggestions
            include_related: Include related suggestions
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            Suggestions with metadata
        """
        try:
            suggestions = []
            
            # Get autocomplete suggestions
            if include_autocomplete and len(query.strip()) >= 2:
                autocomplete_suggestions = await self.autocomplete_service.get_autocomplete_suggestions(
                    db, query, limit // 3
                )
                suggestions.extend(autocomplete_suggestions)
            
            # Get popular suggestions
            if include_popular and len(suggestions) < limit:
                popular_suggestions = await self.suggestion_service.get_popular_suggestions(
                    db, limit - len(suggestions)
                )
                suggestions.extend(popular_suggestions)
            
            # Get related suggestions
            if include_related and len(suggestions) < limit:
                related_suggestions = await self.suggestion_service.get_related_suggestions(
                    db, query, limit - len(suggestions)
                )
                suggestions.extend(related_suggestions)
            
            # Generate from products if needed
            if len(suggestions) < limit:
                product_suggestions = await self.suggestion_service.generate_suggestions_from_products(
                    db, query, limit - len(suggestions)
                )
                for suggestion in product_suggestions:
                    suggestions.append({
                        "suggestion": suggestion,
                        "type": "product",
                        "search_count": 0,
                        "click_count": 0,
                        "relevance_score": 0.5
                    })
            
            return {
                "query": query,
                "suggestions": suggestions[:limit],
                "count": len(suggestions[:limit]),
                "price_filter": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "applied": min_price is not None or max_price is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return {
                "query": query,
                "suggestions": [],
                "count": 0,
                "error": str(e)
            }
    
    async def get_autocomplete(
        self,
        db: Session,
        query: str,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions with price filtering.
        
        Args:
            db: Database session
            query: Search query
            limit: Maximum number of suggestions
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of autocomplete suggestions
        """
        try:
            if min_price is not None or max_price is not None:
                return await self.autocomplete_service.get_autocomplete_with_price_filter(
                    db, query, limit, min_price, max_price
                )
            else:
                return await self.autocomplete_service.get_autocomplete_suggestions(
                    db, query, limit
                )
                
        except Exception as e:
            logger.error(f"Error getting autocomplete: {e}")
            return []
    
    async def get_popular_suggestions(
        self,
        db: Session,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get popular suggestions with price filtering.
        
        Args:
            db: Database session
            limit: Maximum number of suggestions
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of popular suggestions
        """
        try:
            if min_price is not None or max_price is not None:
                return await self.autocomplete_service.get_popular_with_price_filter(
                    db, limit, min_price, max_price
                )
            else:
                return await self.suggestion_service.get_popular_suggestions(db, limit)
                
        except Exception as e:
            logger.error(f"Error getting popular suggestions: {e}")
            return []
    
    async def get_related_suggestions(
        self,
        db: Session,
        query: str,
        limit: int = 5,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get related suggestions with price filtering.
        
        Args:
            db: Database session
            query: Search query
            limit: Maximum number of suggestions
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of related suggestions
        """
        try:
            if min_price is not None or max_price is not None:
                return await self.autocomplete_service.get_related_with_price_filter(
                    db, query, limit, min_price, max_price
                )
            else:
                return await self.suggestion_service.get_related_suggestions(db, query, limit)
                
        except Exception as e:
            logger.error(f"Error getting related suggestions: {e}")
            return []
    
    async def get_query_corrections(
        self,
        db: Session,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Get query corrections for possible spelling errors.
        
        Args:
            db: Database session
            query: Search query
            
        Returns:
            List of query corrections
        """
        try:
            return await self.suggestion_service.get_query_corrections(db, query)
        except Exception as e:
            logger.error(f"Error getting query corrections: {e}")
            return []
    
    async def get_cheapest_suggestions(
        self,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions from the cheapest products.
        
        Args:
            db: Database session
            limit: Maximum number of suggestions
            
        Returns:
            List of cheapest product suggestions
        """
        try:
            return await self.suggestion_service.get_cheapest_product_suggestions(db, limit)
        except Exception as e:
            logger.error(f"Error getting cheapest suggestions: {e}")
            return []
    
    async def search_with_fallback(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 25,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search with fallback to text search if AI search fails.
        
        Args:
            db: Database session
            query: Search query
            page: Page number
            limit: Results per page
            **kwargs: Additional search parameters
            
        Returns:
            Search results with fallback if needed
        """
        try:
            return await self.ai_search_service.search_with_fallback(
                db, query, page, limit, **kwargs
            )
        except Exception as e:
            logger.error(f"Error in search with fallback: {e}")
            raise


# Global modular search service instance
modular_search_service = ModularSearchService() 