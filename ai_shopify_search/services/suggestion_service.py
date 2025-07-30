"""
Suggestion service for handling query suggestions, corrections, and related searches.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import QuerySuggestion, SearchCorrection, PopularSearch, Product

logger = logging.getLogger(__name__)

class SuggestionService:
    """Service for handling search suggestions and corrections."""
    
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
            
            # Search for exact matches
            exact_matches = db.query(QuerySuggestion).filter(
                QuerySuggestion.suggestion.ilike(f"{query_lower}%"),
                QuerySuggestion.is_active == True
            ).order_by(QuerySuggestion.search_count.desc()).limit(limit).all()
            
            # Search for fuzzy matches
            fuzzy_matches = db.query(QuerySuggestion).filter(
                QuerySuggestion.suggestion.ilike(f"%{query_lower}%"),
                QuerySuggestion.is_active == True
            ).order_by(QuerySuggestion.search_count.desc()).limit(limit).all()
            
            # Combine and sort by relevance
            all_matches = list(set(exact_matches + fuzzy_matches))
            
            suggestions = []
            for match in all_matches:
                # Calculate similarity score
                similarity = SequenceMatcher(None, query_lower, match.suggestion.lower()).ratio()
                
                suggestions.append({
                    "suggestion": match.suggestion,
                    "type": match.suggestion_type,
                    "search_count": match.search_count,
                    "click_count": match.click_count,
                    "relevance_score": match.relevance_score,
                    "similarity_score": similarity,
                    "context": match.context
                })
            
            # Sort by combination of similarity and relevance
            suggestions.sort(key=lambda x: (x["similarity_score"] * 0.7 + x["relevance_score"] * 0.3), reverse=True)
            
            result = suggestions[:limit]
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {e}")
            return []
    
    async def get_popular_suggestions(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get popular search suggestions."""
        try:
            # Check cache
            cache_key = f"popular_suggestions:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            popular_searches = db.query(PopularSearch).order_by(
                PopularSearch.search_count.desc()
            ).limit(limit).all()
            
            suggestions = []
            for search in popular_searches:
                suggestions.append({
                    "suggestion": search.query,
                    "type": "popular",
                    "search_count": search.search_count,
                    "click_count": search.click_count,
                    "click_through_rate": search.click_count / search.search_count if search.search_count > 0 else 0
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, suggestions, ttl=600)  # 10 minutes
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting popular suggestions: {e}")
            return []
    
    async def get_related_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get related search suggestions."""
        try:
            # Check cache
            cache_key = f"related_suggestions:{query}:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Search for suggestions with similar words
            query_words = query.lower().split()
            
            related_suggestions = db.query(QuerySuggestion).filter(
                QuerySuggestion.is_active == True
            ).all()
            
            scored_suggestions = []
            for suggestion in related_suggestions:
                suggestion_words = suggestion.suggestion.lower().split()
                
                # Calculate overlap score
                common_words = set(query_words) & set(suggestion_words)
                overlap_score = len(common_words) / max(len(query_words), len(suggestion_words))
                
                if overlap_score > 0.3:  # Only suggestions with sufficient overlap
                    scored_suggestions.append({
                        "suggestion": suggestion.suggestion,
                        "type": "related",
                        "overlap_score": overlap_score,
                        "search_count": suggestion.search_count,
                        "relevance_score": suggestion.relevance_score
                    })
            
            # Sort by overlap score and relevance
            scored_suggestions.sort(key=lambda x: (x["overlap_score"] * 0.6 + x["relevance_score"] * 0.4), reverse=True)
            
            result = scored_suggestions[:limit]
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting related suggestions: {e}")
            return []
    
    async def get_query_corrections(
        self, 
        db: Session, 
        query: str
    ) -> List[Dict[str, Any]]:
        """Get query corrections for possible spelling errors."""
        try:
            # Check cache
            cache_key = f"query_corrections:{query}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Search for existing corrections
            corrections = db.query(SearchCorrection).filter(
                SearchCorrection.original_query.ilike(f"%{query}%")
            ).order_by(SearchCorrection.confidence_score.desc()).limit(5).all()
            
            suggestions = []
            for correction in corrections:
                suggestions.append({
                    "original": correction.original_query,
                    "corrected": correction.corrected_query,
                    "type": correction.correction_type,
                    "confidence": correction.confidence_score,
                    "usage_count": correction.usage_count
                })
            
            # Cache the result
            await self.cache_service.set(cache_key, suggestions, ttl=600)  # 10 minutes
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting query corrections: {e}")
            return []
    
    async def generate_suggestions_from_products(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10
    ) -> List[str]:
        """Generate suggestions based on product data."""
        try:
            # Check cache
            cache_key = f"product_suggestions:{query}:{limit}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            query_lower = query.lower().strip()
            
            # Search in product titles
            products = db.query(Product).filter(
                Product.title.ilike(f"%{query_lower}%")
            ).limit(50).all()
            
            suggestions = set()
            
            for product in products:
                # Extract words from title
                title_words = re.findall(r'\b\w+\b', product.title.lower())
                
                # Add relevant words
                for word in title_words:
                    if len(word) >= 3 and word.startswith(query_lower):
                        suggestions.add(word)
                
                # Add full title as suggestion
                if product.title.lower().startswith(query_lower):
                    suggestions.add(product.title)
            
            # Search in tags
            tag_products = db.query(Product).filter(
                func.array_to_string(Product.tags, ',').ilike(f"%{query_lower}%")
            ).limit(20).all()
            
            for product in tag_products:
                for tag in product.tags:
                    if tag.lower().startswith(query_lower):
                        suggestions.add(tag)
            
            result = list(suggestions)[:limit]
            
            # Cache the result
            await self.cache_service.set(cache_key, result, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating suggestions from products: {e}")
            return []
    
    async def get_suggestions_with_price_filter(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get suggestions with price filtering."""
        try:
            # Build base query
            base_query = db.query(QuerySuggestion).filter(
                QuerySuggestion.query.ilike(f"%{query}%")
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
                    "suggestion": suggestion.query,
                    "type": "autocomplete",
                    "search_count": suggestion.search_count,
                    "click_count": suggestion.click_count,
                    "relevance_score": suggestion.relevance_score,
                    "similarity_score": suggestion.similarity_score,
                    "avg_price": getattr(suggestion, 'avg_price', None)
                })
            
            logger.info(f"💰 Suggestions met prijsfilter: {len(result)} resultaten (min_price={min_price}, max_price={max_price})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting suggestions with price filter: {e}")
            return []
    
    async def get_cheapest_product_suggestions(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get suggestions from the cheapest products when no products found in price range."""
        try:
            # Check cache
            cache_key = f"cheapest_suggestions:{limit}"
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
            
            logger.info(f"💰 Goedkoopste product suggestions: {len(result)} resultaten")
            return result
            
        except Exception as e:
            logger.error(f"Error getting cheapest product suggestions: {e}")
            return [] 