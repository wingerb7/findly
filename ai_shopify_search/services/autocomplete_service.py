"""
Autocomplete service for handling search autocomplete functionality.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from core.models import QuerySuggestion, PopularSearch, Product

logger = logging.getLogger(__name__)

class AutocompleteService:
    """Service for handling autocomplete functionality."""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
    
    async def get_autocomplete_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions for a query."""
        try:
            if len(query.strip()) < 2:
                return []
            
            # Check cache first
            cache_key = f"autocomplete:{query}:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            query_lower = query.lower().strip()
            
            # Get suggestions from database
            suggestions = db.query(QuerySuggestion).filter(
                QuerySuggestion.suggestion.ilike(f"{query_lower}%"),
                QuerySuggestion.is_active == True
            ).order_by(QuerySuggestion.search_count.desc()).limit(limit).all()
            
            result = []
            for suggestion in suggestions:
                result.append({
                    "suggestion": suggestion.suggestion,
                    "type": "autocomplete",
                    "search_count": suggestion.search_count,
                    "click_count": suggestion.click_count,
                    "relevance_score": suggestion.relevance_score,
                    "context": suggestion.context
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {e}")
            return []
    
    async def get_autocomplete_with_price_filter(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions with price filtering."""
        try:
            # Check cache
            cache_key = f"autocomplete_price:{query}:{limit}:{min_price}:{max_price}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Build base query
            base_query = db.query(QuerySuggestion).filter(
                QuerySuggestion.suggestion.ilike(f"%{query}%")
            )
            
            # Apply price filters if provided
            if min_price is not None:
                base_query = base_query.filter(QuerySuggestion.avg_price >= min_price)
            if max_price is not None:
                base_query = base_query.filter(QuerySuggestion.avg_price <= max_price)
            
            # Get suggestions
            suggestions = base_query.order_by(QuerySuggestion.search_count.desc()).limit(limit).all()
            
            result = []
            for suggestion in suggestions:
                result.append({
                    "suggestion": suggestion.suggestion,
                    "type": "autocomplete",
                    "search_count": suggestion.search_count,
                    "click_count": suggestion.click_count,
                    "relevance_score": suggestion.relevance_score,
                    "avg_price": getattr(suggestion, 'avg_price', None)
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            logger.info(f"💰 Autocomplete suggestions met prijsfilter: {len(result)} resultaten (min_price={min_price}, max_price={max_price})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions with price filter: {e}")
            return []
    
    async def get_popular_autocomplete(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get popular autocomplete suggestions."""
        try:
            # Check cache
            cache_key = f"popular_autocomplete:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            popular_searches = db.query(PopularSearch).order_by(
                PopularSearch.search_count.desc()
            ).limit(limit).all()
            
            result = []
            for search in popular_searches:
                result.append({
                    "suggestion": search.query,
                    "type": "popular",
                    "search_count": search.search_count,
                    "click_count": search.click_count,
                    "click_through_rate": search.click_count / search.search_count if search.search_count > 0 else 0
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=600)  # 10 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting popular autocomplete: {e}")
            return []
    
    async def get_popular_with_price_filter(
        self, 
        db: Session, 
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get popular suggestions with price filtering."""
        try:
            # Check cache
            cache_key = f"popular_price:{limit}:{min_price}:{max_price}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Build base query
            base_query = db.query(PopularSearch).filter(
                PopularSearch.search_count > 0
            )
            
            # Apply price filters if provided
            if min_price is not None:
                base_query = base_query.filter(PopularSearch.avg_price >= min_price)
            if max_price is not None:
                base_query = base_query.filter(PopularSearch.avg_price <= max_price)
            
            # Get suggestions
            suggestions = base_query.order_by(PopularSearch.search_count.desc()).limit(limit).all()
            
            result = []
            for suggestion in suggestions:
                result.append({
                    "suggestion": suggestion.query,
                    "type": "popular",
                    "search_count": suggestion.search_count,
                    "click_count": suggestion.click_count,
                    "relevance_score": 0.8,
                    "similarity_score": 0.9,
                    "avg_price": getattr(suggestion, 'avg_price', None)
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=600)  # 10 minutes
            
            logger.info(f"💰 Populaire suggestions met prijsfilter: {len(result)} resultaten (min_price={min_price}, max_price={max_price})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting popular suggestions with price filter: {e}")
            return []
    
    async def get_related_autocomplete(
        self, 
        db: Session, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get related autocomplete suggestions."""
        try:
            # Check cache
            cache_key = f"related_autocomplete:{query}:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Simple related suggestions based on product data
            search_term = f"%{query}%"
            
            # Build base query
            base_query = db.query(Product).filter(
                (Product.title.ilike(search_term)) |
                (Product.description.ilike(search_term))
            )
            
            # Get products
            products = base_query.limit(limit * 2).all()
            
            # Extract related terms
            related_terms = set()
            for product in products:
                # Extract words from title
                words = product.title.lower().split()
                related_terms.update(words)
                
                # Extract tags
                if product.tags:
                    related_terms.update([tag.lower() for tag in product.tags])
            
            # Filter and format
            filtered_terms = [term for term in related_terms if len(term) >= 3 and term != query.lower()]
            result = []
            for term in filtered_terms[:limit]:
                result.append({
                    "suggestion": term,
                    "type": "related",
                    "search_count": 0,
                    "click_count": 0,
                    "relevance_score": 0.6,
                    "similarity_score": 0.7
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting related autocomplete: {e}")
            return []
    
    async def get_related_with_price_filter(
        self, 
        db: Session, 
        query: str, 
        limit: int = 5,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get related suggestions with price filtering."""
        try:
            # Check cache
            cache_key = f"related_price:{query}:{limit}:{min_price}:{max_price}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Simple related suggestions based on product data
            search_term = f"%{query}%"
            
            # Build base query
            base_query = db.query(Product).filter(
                (Product.title.ilike(search_term)) |
                (Product.description.ilike(search_term))
            )
            
            # Apply price filters if provided
            if min_price is not None:
                base_query = base_query.filter(Product.price >= min_price)
            if max_price is not None:
                base_query = base_query.filter(Product.price <= max_price)
            
            # Get products
            products = base_query.limit(limit * 2).all()
            
            # Extract related terms
            related_terms = set()
            for product in products:
                # Extract words from title
                words = product.title.lower().split()
                related_terms.update(words)
                
                # Extract tags
                if product.tags:
                    related_terms.update([tag.lower() for tag in product.tags])
            
            # Filter and format
            filtered_terms = [term for term in related_terms if len(term) >= 3 and term != query.lower()]
            result = []
            for term in filtered_terms[:limit]:
                result.append({
                    "suggestion": term,
                    "type": "related",
                    "search_count": 0,
                    "click_count": 0,
                    "relevance_score": 0.6,
                    "similarity_score": 0.7
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            logger.info(f"💰 Gerelateerde suggestions met prijsfilter: {len(result)} resultaten (min_price={min_price}, max_price={max_price})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting related suggestions with price filter: {e}")
            return []
    
    async def get_cheapest_autocomplete(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions from the cheapest products."""
        try:
            # Check cache
            cache_key = f"cheapest_autocomplete:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Get cheapest products
            products = db.query(Product).filter(
                Product.price.isnot(None)
            ).order_by(Product.price.asc()).limit(limit).all()
            
            result = []
            for product in products:
                result.append({
                    "suggestion": product.title,
                    "type": "cheapest",
                    "search_count": 0,
                    "click_count": 0,
                    "relevance_score": 0.3,
                    "similarity_score": 0.4,
                    "price": product.price
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=600)  # 10 minutes
            
            logger.info(f"💰 Goedkoopste product autocomplete: {len(result)} resultaten")
            return result
            
        except Exception as e:
            logger.error(f"Error getting cheapest autocomplete: {e}")
            return [] 