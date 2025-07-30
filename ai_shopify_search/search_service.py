import logging
import time
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from difflib import SequenceMatcher
from ai_shopify_search.models import Product, QuerySuggestion, SearchCorrection, PopularSearch
from ai_shopify_search.embeddings import generate_embedding
from ai_shopify_search.cache_manager import cache_manager
from ai_shopify_search.analytics_manager import analytics_manager
from ai_shopify_search.config import AI_SEARCH_CACHE_TTL

logger = logging.getLogger(__name__)

class SearchService:
    """Centralized search service for AI-powered product search."""
    
    def __init__(self):
        self.cache_manager = cache_manager
        self.analytics_manager = analytics_manager
    
    async def ai_search_products(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 25,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        source_language: Optional[str] = None,
        target_language: str = "en"
    ) -> Dict[str, Any]:
        """Perform AI-powered product search with vector embeddings."""
        start_time = time.time()
        
        try:
            # Language detection and translation
            search_query = query
            detected_language = source_language
            
            if not source_language:
                # Auto-detect language (simplified for now)
                detected_language = "en"
            
            # Check cache first
            cache_key = self.cache_manager.get_cache_key(
                "ai_search", 
                query=search_query, 
                page=page, 
                limit=limit, 
                target_language=target_language
            )
            cached_result = self.cache_manager.get_cached_result(cache_key)
            cache_hit = cached_result is not None
            
            if cache_hit:
                logger.info(f"Cache hit for AI search: '{search_query}' (page {page})")
                # Track analytics for cache hit
                response_time_ms = (time.time() - start_time) * 1000
                self.analytics_manager.track_search_analytics(
                    db, query, "ai", {}, len(cached_result.get("results", [])),
                    page, limit, response_time_ms, cache_hit, user_agent, ip_address
                )
                return cached_result
            
            # Generate embedding for search query
            query_embedding = generate_embedding(title=search_query)
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Build vector search query
            sql_query = """
            SELECT id, shopify_id, title, description, price, tags,
                   1 - (embedding <=> :embedding) as similarity
            FROM products 
            WHERE embedding IS NOT NULL
            """
            params = {"embedding": embedding_str}
            
            # Count total results for pagination
            count_sql = """
            SELECT COUNT(*)
            FROM products 
            WHERE embedding IS NOT NULL
            """
            count_result = db.execute(text(count_sql), params)
            total_count = count_result.scalar()
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
            
            # Apply pagination
            offset = (page - 1) * limit
            sql_query += " ORDER BY similarity DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            logger.info(f"Executing vector search (page {page}/{total_pages}, total: {total_count})")
            
            # Execute search
            result = db.execute(text(sql_query), params)
            rows = result.fetchall()
            
            # Process results
            if len(rows) == 0:
                # Fallback to text search
                logger.warning("No embeddings found, falling back to text search.")
                products = await self._fallback_text_search(db, query, page, limit)
                total_count = len(products)
                total_pages = 1
            else:
                products = []
                for row in rows:
                    # Convert tags to list if it's a PostgreSQL array
                    tags = row[5] if row[5] else []
                    if hasattr(tags, '__iter__') and not isinstance(tags, str):
                        tags = list(tags)
                    else:
                        tags = []
                    
                    products.append({
                        "id": row[0],
                        "shopify_id": row[1],
                        "title": row[2],
                        "description": row[3],
                        "price": float(row[4]),
                        "tags": tags,
                        "similarity": float(row[6]) if row[6] else 0.0
                    })
            
            # Create pagination metadata
            pagination_meta = self._create_pagination_metadata(page, limit, total_count, total_pages)
            
            result_data = {
                "query": query,
                "results": products,
                "count": len(products),
                **pagination_meta
            }
            
            # Track analytics
            response_time_ms = (time.time() - start_time) * 1000
            search_analytics_id = self.analytics_manager.track_search_analytics(
                db, query, "ai", {}, len(products),
                page, limit, response_time_ms, cache_hit, user_agent, ip_address
            )
            
            # Add analytics ID to response for click tracking
            if search_analytics_id:
                result_data["analytics_id"] = search_analytics_id
            
            # Cache the result
            self.cache_manager.set_cached_result(cache_key, result_data, AI_SEARCH_CACHE_TTL)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error in ai_search_products: {e}")
            raise
    
    async def _fallback_text_search(
        self, 
        db: Session, 
        query: str, 
        page: int, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback text search when no embeddings are found."""
        try:
            logger.info(f"Fallback text search for: '{query}'")
            
            # Simple text search in title
            search_query = db.query(Product).filter(Product.title.ilike(f"%{query}%"))
            
            # Apply pagination
            offset = (page - 1) * limit
            results = search_query.offset(offset).limit(limit).all()
            
            # Convert to JSON format
            products = []
            for product in results:
                products.append({
                    "id": product.id,
                    "shopify_id": product.shopify_id,
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "tags": product.tags,
                    "similarity": 0.8  # Fallback similarity
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Error in fallback text search: {e}")
            return []
    
    def _create_pagination_metadata(
        self, 
        page: int, 
        limit: int, 
        total_count: int, 
        total_pages: int
    ) -> Dict[str, Any]:
        """Create pagination metadata for API responses."""
        return {
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            }
        }
    
    def get_autocomplete_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions for a query."""
        try:
            if len(query.strip()) < 2:
                return []
            
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
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {e}")
            return []
    
    def get_popular_suggestions(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get popular search suggestions."""
        try:
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
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting popular suggestions: {e}")
            return []
    
    def get_related_suggestions(
        self, 
        db: Session, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get related search suggestions."""
        try:
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
            
            return scored_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting related suggestions: {e}")
            return []
    
    def get_query_corrections(
        self, 
        db: Session, 
        query: str
    ) -> List[Dict[str, Any]]:
        """Get query corrections for possible spelling errors."""
        try:
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
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting query corrections: {e}")
            return []
    
    def generate_suggestions_from_products(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10
    ) -> List[str]:
        """Generate suggestions based on product data."""
        try:
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
            
            return list(suggestions)[:limit]
            
        except Exception as e:
            logger.error(f"Error generating suggestions from products: {e}")
            return []

# Global search service instance
search_service = SearchService() 