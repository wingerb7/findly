"""
Smart autocomplete service with context-aware suggestions and fuzzy search.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from core.models import Product, QuerySuggestion, PopularSearch, SearchCorrection
from utils.fuzzy_search import FuzzySearch

logger = logging.getLogger(__name__)

class SmartAutocompleteService:
    """Smart autocomplete service with context-aware suggestions."""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        self.fuzzy_search = FuzzySearch()
    
    def get_smart_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get smart autocomplete suggestions with context awareness.
        
        Args:
            db: Database session
            query: Partial query
            limit: Maximum number of suggestions
            context: Search context (e.g., 'price_filter', 'category')
            
        Returns:
            List of suggestion dictionaries
        """
        try:
            if len(query.strip()) < 2:
                return self._get_popular_suggestions(db, limit)
            
            # Check cache
            cache_key = f"smart_autocomplete:{query}:{limit}:{context}"
            cached_result = self.cache_service.get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Get corrected query and suggestions
            corrected_query, fuzzy_suggestions = self.fuzzy_search.correct_query(query)
            
            # Get database suggestions
            db_suggestions = self._get_database_suggestions(db, query, limit)
            
            # Get product-based suggestions
            product_suggestions = self._get_product_suggestions(db, query, limit)
            
            # Get context-aware suggestions
            context_suggestions = self._get_context_suggestions(db, query, context, limit)
            
            # Combine and rank suggestions
            all_suggestions = self._combine_and_rank_suggestions(
                db_suggestions, 
                product_suggestions, 
                context_suggestions, 
                fuzzy_suggestions,
                query
            )
            
            # Format results
            result = []
            for suggestion in all_suggestions[:limit]:
                result.append({
                    "suggestion": suggestion["text"],
                    "type": suggestion["type"],
                    "confidence": suggestion["confidence"],
                    "search_count": suggestion.get("search_count", 0),
                    "click_count": suggestion.get("click_count", 0),
                    "context": suggestion.get("context", ""),
                    "is_correction": suggestion.get("is_correction", False)
                })
            
            # Cache results
            self.cache_service.set_cached_result(cache_key, result, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting smart suggestions: {e}")
            return []
    
    def _get_database_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get suggestions from database."""
        try:
            query_lower = query.lower().strip()
            
            # Exact matches
            exact_matches = db.query(QuerySuggestion).filter(
                QuerySuggestion.suggestion.ilike(f"{query_lower}%"),
                QuerySuggestion.is_active == True
            ).order_by(desc(QuerySuggestion.search_count)).limit(limit).all()
            
            # Partial matches
            partial_matches = db.query(QuerySuggestion).filter(
                QuerySuggestion.suggestion.ilike(f"%{query_lower}%"),
                QuerySuggestion.is_active == True
            ).order_by(desc(QuerySuggestion.search_count)).limit(limit).all()
            
            # If no database suggestions, create some basic ones
            if not exact_matches and not partial_matches:
                # Create basic suggestions based on query
                basic_suggestions = self._create_basic_suggestions(query_lower)
                return basic_suggestions
            
            suggestions = []
            for match in exact_matches + partial_matches:
                suggestions.append({
                    "text": match.suggestion,
                    "type": "database",
                    "confidence": 0.9,
                    "search_count": match.search_count,
                    "click_count": match.click_count,
                    "context": match.context
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting database suggestions: {e}")
            return []
    
    def _get_product_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get suggestions based on product data."""
        try:
            query_lower = query.lower().strip()
            
            # Get product titles that match
            products = db.query(Product).filter(
                Product.title.ilike(f"%{query_lower}%")
            ).limit(limit * 2).all()
            
            suggestions = []
            for product in products:
                # Extract relevant terms from title
                title_words = product.title.lower().split()
                matching_words = [word for word in title_words if query_lower in word]
                
                for word in matching_words:
                    suggestions.append({
                        "text": word,
                        "type": "product",
                        "confidence": 0.7,
                        "search_count": 0,
                        "click_count": 0,
                        "context": "product_title"
                    })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting product suggestions: {e}")
            return []
    
    def _get_context_suggestions(
        self, 
        db: Session, 
        query: str, 
        context: Optional[str], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get context-aware suggestions."""
        try:
            suggestions = []
            query_lower = query.lower().strip()
            
            # Price context
            if "goedkoop" in query_lower or "goedkope" in query_lower:
                suggestions.extend([
                    {"text": "goedkope schoenen", "type": "context", "confidence": 0.8},
                    {"text": "goedkope jas", "type": "context", "confidence": 0.8},
                    {"text": "goedkope shirt", "type": "context", "confidence": 0.8},
                    {"text": "goedkope broek", "type": "context", "confidence": 0.8},
                    {"text": "goedkope accessoires", "type": "context", "confidence": 0.8}
                ])
            
            # Season context
            if "winter" in query_lower:
                suggestions.extend([
                    {"text": "winter jas", "type": "context", "confidence": 0.8},
                    {"text": "winter schoenen", "type": "context", "confidence": 0.8},
                    {"text": "winter accessoires", "type": "context", "confidence": 0.8}
                ])
            
            if "zomer" in query_lower:
                suggestions.extend([
                    {"text": "zomer kleding", "type": "context", "confidence": 0.8},
                    {"text": "zomer schoenen", "type": "context", "confidence": 0.8},
                    {"text": "zomer jas", "type": "context", "confidence": 0.8}
                ])
            
            # Color context
            colors = ["zwart", "wit", "blauw", "rood", "groen", "geel", "paars", "grijs", "bruin", "beige", "roze", "oranje"]
            for color in colors:
                if color in query_lower:
                    suggestions.extend([
                        {"text": f"{color} schoenen", "type": "context", "confidence": 0.7},
                        {"text": f"{color} jas", "type": "context", "confidence": 0.7},
                        {"text": f"{color} shirt", "type": "context", "confidence": 0.7}
                    ])
                    break
            
            # Material context
            materials = ["leder", "katoen", "wol", "zijde", "denim", "polyester", "linnen", "synthetisch"]
            for material in materials:
                if material in query_lower:
                    suggestions.extend([
                        {"text": f"{material} schoenen", "type": "context", "confidence": 0.7},
                        {"text": f"{material} jas", "type": "context", "confidence": 0.7},
                        {"text": f"{material} shirt", "type": "context", "confidence": 0.7}
                    ])
                    break
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting context suggestions: {e}")
            return []
    
    def _create_basic_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Create basic suggestions when no database suggestions exist."""
        suggestions = []
        
        # Common fashion terms
        fashion_terms = [
            "schoenen", "jas", "jassen", "shirt", "shirts", "broek", "broeken",
            "jurk", "jurken", "accessoire", "accessoires", "tassen", "schoenen"
        ]
        
        # Price terms
        price_terms = ["goedkoop", "goedkope", "duur", "dure", "betaalbaar", "betaalbare"]
        
        # Colors
        colors = ["zwart", "wit", "blauw", "rood", "groen", "geel", "paars", "grijs", "bruin"]
        
        # Materials
        materials = ["leder", "katoen", "wol", "zijde", "denim", "polyester"]
        
        # Generate suggestions based on query
        for term in fashion_terms:
            if query in term or term in query:
                suggestions.append({
                    "text": term,
                    "type": "basic",
                    "confidence": 0.8,
                    "search_count": 0,
                    "click_count": 0,
                    "context": "fashion_term"
                })
        
        # Add price-based suggestions
        for price_term in price_terms:
            if price_term in query:
                for fashion_term in fashion_terms[:3]:  # Top 3 fashion terms
                    suggestions.append({
                        "text": f"{price_term} {fashion_term}",
                        "type": "basic",
                        "confidence": 0.7,
                        "search_count": 0,
                        "click_count": 0,
                        "context": "price_fashion"
                    })
        
        # Add color-based suggestions
        for color in colors:
            if color in query:
                for fashion_term in fashion_terms[:3]:  # Top 3 fashion terms
                    suggestions.append({
                        "text": f"{color} {fashion_term}",
                        "type": "basic",
                        "confidence": 0.7,
                        "search_count": 0,
                        "click_count": 0,
                        "context": "color_fashion"
                    })
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def _get_popular_suggestions(
        self, 
        db: Session, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get popular search suggestions."""
        try:
            # Check cache
            cache_key = f"popular_suggestions:{limit}"
            cached_result = self.cache_service.get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            popular_searches = db.query(PopularSearch).order_by(
                desc(PopularSearch.search_count)
            ).limit(limit).all()
            
            result = []
            for search in popular_searches:
                result.append({
                    "suggestion": search.query,
                    "type": "popular",
                    "confidence": 0.6,
                    "search_count": search.search_count,
                    "click_count": search.click_count,
                    "context": "popular"
                })
            
            # Cache results
            self.cache_service.set_cached_result(cache_key, result, ttl=600)  # 10 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting popular suggestions: {e}")
            return []
    
    def _combine_and_rank_suggestions(
        self,
        db_suggestions: List[Dict[str, Any]],
        product_suggestions: List[Dict[str, Any]],
        context_suggestions: List[Dict[str, Any]],
        fuzzy_suggestions: List[str],
        original_query: str
    ) -> List[Dict[str, Any]]:
        """Combine and rank all suggestions."""
        all_suggestions = []
        
        # Add database suggestions
        for suggestion in db_suggestions:
            suggestion["is_correction"] = False
            all_suggestions.append(suggestion)
        
        # Add product suggestions
        for suggestion in product_suggestions:
            suggestion["is_correction"] = False
            all_suggestions.append(suggestion)
        
        # Add context suggestions
        for suggestion in context_suggestions:
            suggestion["is_correction"] = False
            all_suggestions.append(suggestion)
        
        # Add fuzzy suggestions as corrections
        for suggestion_text in fuzzy_suggestions:
            if suggestion_text != original_query:
                all_suggestions.append({
                    "text": suggestion_text,
                    "type": "correction",
                    "confidence": 0.8,
                    "search_count": 0,
                    "click_count": 0,
                    "context": "fuzzy_match",
                    "is_correction": True
                })
        
        # Remove duplicates
        seen = set()
        unique_suggestions = []
        for suggestion in all_suggestions:
            if suggestion["text"] not in seen:
                seen.add(suggestion["text"])
                unique_suggestions.append(suggestion)
        
        # Sort by confidence and search count
        unique_suggestions.sort(
            key=lambda x: (x["confidence"], x.get("search_count", 0)), 
            reverse=True
        )
        
        return unique_suggestions
    
    def get_related_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get related search suggestions."""
        try:
            # Check cache
            cache_key = f"related_suggestions:{query}:{limit}"
            cached_result = self.cache_service.get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Get synonyms for query words
            words = query.lower().split()
            related_queries = []
            
            for word in words:
                synonyms = self.fuzzy_search.get_synonyms(word)
                for synonym in synonyms[:2]:  # Top 2 synonyms
                    # Replace word with synonym
                    new_words = [synonym if w == word else w for w in words]
                    related_queries.append(" ".join(new_words))
            
            # Get context-based related queries
            if "goedkoop" in query or "goedkope" in query:
                related_queries.extend([
                    "betaalbare schoenen",
                    "voordelige jas",
                    "economische shirt"
                ])
            
            if "duur" in query or "dure" in query:
                related_queries.extend([
                    "exclusieve schoenen",
                    "premium jas",
                    "luxe accessoires"
                ])
            
            result = []
            for related_query in related_queries[:limit]:
                result.append({
                    "suggestion": related_query,
                    "type": "related",
                    "confidence": 0.7,
                    "context": "related_search"
                })
            
            # Cache results
            self.cache_service.set_cached_result(cache_key, result, ttl=300)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting related suggestions: {e}")
            return [] 