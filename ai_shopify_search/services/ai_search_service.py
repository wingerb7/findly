#!/usr/bin/env python3
"""
AI Search Service for semantic search with vector embeddings.
Fase 1 Optimalisaties: Performance, Error Handling, Enhanced Search
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.models import Product
from embeddings import generate_embedding, generate_batch_embeddings, calculate_similarity, get_embedding_model
from utils.validation import validate_price_range, generate_secure_cache_key
from utils.privacy_utils import sanitize_log_data
from utils.fuzzy_search import FuzzySearch

logger = logging.getLogger(__name__)

class AISearchService:
    """Specialized service for AI-powered semantic search with vector embeddings."""
    
    def __init__(self, cache_service, analytics_service):
        self.cache_service = cache_service
        self.analytics_service = analytics_service
        self.max_retries = 3
        self.retry_delay = 1.0
        self.fuzzy_search = FuzzySearch()
    
    def log_search_event(
        self,
        query: str,
        user_ip: str = None,
        user_agent: str = None,
        price_intent: dict = None,
        min_price: float = None,
        max_price: float = None,
        fallback_used: bool = False,
        filtered_count: int = None,
        total_count: int = None,
        similarity_scores: list = None,
        engine_mode: str = "AI",
        engine_model: str = None,
        cache_status: str = None,
        cache_ttl: int = None,
        result_count: int = None,
        response_time: float = None
    ):
        """
        Print a multi-line, structured log block for a search event.
        """
        # Price intent
        if price_intent and price_intent.get("max_price") is not None:
            price_line = f"💰 [PRICE INTENT] max_price={price_intent['max_price']} (pattern: {price_intent.get('pattern_type','-')}, confidence: {price_intent.get('confidence','-'):.2f})"
        else:
            price_line = "💰 [PRICE INTENT] None detected"
        # Filters
        filters_line = f"🔗 [FILTERS] min_price={min_price} | max_price={max_price} | Fallback: {'YES' if fallback_used else 'NO'} | Filtered: {filtered_count}/{total_count}"
        # Similarity
        if similarity_scores:
            top = max(similarity_scores) if similarity_scores else 0
            avg = sum(similarity_scores)/len(similarity_scores) if similarity_scores else 0
            minv = min(similarity_scores) if similarity_scores else 0
            sim_line = f"📈 [SIMILARITY] Top: {top:.2f} | Avg: {avg:.2f} | Min: {minv:.2f}"
        else:
            sim_line = "📈 [SIMILARITY] -"
        # Engine
        engine_line = f"⚙️ [ENGINE] Mode: {engine_mode} | Model: {engine_model or '-'}"
        # Cache
        cache_line = f"🔄 [CACHE] {cache_status or '-'}" + (f" (TTL: {cache_ttl}s)" if cache_status == 'HIT' and cache_ttl is not None else "")
        # Result
        result_line = f"⚡ [RESULT] {result_count} hits | {response_time:.2f}s"
        # User
        user_line = f"    User: {user_ip or '-'} | UA: {user_agent or '-'}"
        # Print block
        logger.info(f"\n"
            f"🔎 [SEARCH] \"{query}\"\n"
            f"{user_line}\n"
            f"{price_line}\n"
            f"{filters_line}\n"
            f"{sim_line}\n"
            f"{engine_line}\n"
            f"{cache_line}\n"
            f"{result_line}\n"
        )

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
        target_language: str = "en",
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Perform AI-powered product search with vector embeddings and price filtering.
        Fase 1: Enhanced with better error handling, performance, and similarity threshold.
        
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
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not query or not query.strip():
                return self._create_empty_response(query, page, limit)
            
            # Apply fuzzy search corrections
            corrected_query, suggestions = self.fuzzy_search.correct_query(query)
            original_query = query
            query = corrected_query
            
            # Validate price range
            validate_price_range(min_price, max_price)
            
            # Generate cache key
            cache_key = generate_secure_cache_key(
                "ai_search",
                query=query,
                page=page,
                limit=limit,
                target_language=target_language,
                min_price=min_price,
                max_price=max_price,
                similarity_threshold=similarity_threshold
            )
            
            # Check cache
            cached_result = await self.cache_service.get(cache_key)
            cache_status = 'HIT' if cached_result else 'MISS'
            cache_ttl = None
            if hasattr(self.cache_service, 'get_ttl') and cache_status == 'HIT':
                try:
                    cache_ttl = await self.cache_service.get_ttl(cache_key)
                except Exception:
                    cache_ttl = None
            if cached_result:
                # Log block for cache hit
                self.log_search_event(
                    query=query,
                    user_ip=ip_address,
                    user_agent=user_agent,
                    price_intent=None,
                    min_price=min_price,
                    max_price=max_price,
                    fallback_used=False,
                    filtered_count=len(cached_result.get('results', [])),
                    total_count=cached_result.get('pagination', {}).get('total', 0),
                    similarity_scores=[r.get('similarity', 0) for r in cached_result.get('results', [])],
                    engine_mode="AI",
                    engine_model=self._get_current_model(),
                    cache_status=cache_status,
                    cache_ttl=cache_ttl,
                    result_count=len(cached_result.get('results', [])),
                    response_time=time.time() - start_time
                )
                logger.info(f"Cache hit for AI search: '{sanitize_log_data(query, 30)}'")
                return cached_result
            
            # Generate embedding with retry logic
            query_embedding = await self._generate_embedding_with_retry(query)
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Build search query with similarity threshold
            sql_query, params = self._build_search_query(
                embedding_str, min_price, max_price, page, limit, similarity_threshold
            )
            
            # Execute search with timeout
            results, total_count = await asyncio.wait_for(
                self._execute_search(db, sql_query, params),
                timeout=30.0
            )
            
            # Handle fallback if no results with price filter
            fallback_used = False
            if len(results) == 0 and (min_price is not None or max_price is not None):
                logger.warning("No results with price filter, using fallback")
                results, total_count = await self._execute_fallback_search(
                    db, embedding_str, page, limit, similarity_threshold
                )
                fallback_used = True
            
            # Create response
            response = self._create_response(
                query, results, total_count, page, limit,
                min_price, max_price, fallback_used, similarity_threshold
            )
            
            # Add search suggestions if query was corrected
            if corrected_query != original_query:
                response["search_suggestions"] = {
                    "original_query": original_query,
                    "corrected_query": corrected_query,
                    "suggestions": suggestions[:5],  # Top 5 suggestions
                    "correction_applied": True
                }
            
            # Cache results
            await self.cache_service.set(cache_key, response, ttl=3600)  # 1 hour
            
            # Track analytics
            await self._track_search_analytics(
                query, len(results), total_count, time.time() - start_time,
                user_agent, ip_address, fallback_used
            )
            
            # After search, before return:
            similarity_scores = [r.get('similarity', 0) for r in results]
            self.log_search_event(
                query=query,
                user_ip=ip_address,
                user_agent=user_agent,
                price_intent={"max_price": max_price, "pattern_type": "budget" if max_price == 75 else None, "confidence": 0.85 if max_price == 75 else 0.0} if max_price is not None else None,
                min_price=min_price,
                max_price=max_price,
                fallback_used=fallback_used,
                filtered_count=len(results),
                total_count=total_count,
                similarity_scores=similarity_scores,
                engine_mode="AI",
                engine_model=self._get_current_model(),
                cache_status=cache_status,
                cache_ttl=cache_ttl,
                result_count=len(results),
                response_time=time.time() - start_time
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Search timeout for query: '{sanitize_log_data(query, 30)}'")
            return self._create_error_response(query, "Search timeout", page, limit)
        except Exception as e:
            logger.error(f"Search error for query '{sanitize_log_data(query, 30)}': {str(e)}")
            return self._create_error_response(query, str(e), page, limit)
    
    async def _generate_embedding_with_retry(self, query: str) -> List[float]:
        """Generate embedding with retry logic for reliability."""
        for attempt in range(self.max_retries):
            try:
                return generate_embedding(title=query, use_case="query")
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to generate embedding after {self.max_retries} attempts: {e}")
                    raise
                logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    def _get_current_model(self) -> str:
        """Get the current embedding model being used."""
        return get_embedding_model("query")
    
    def _build_search_query(
        self, 
        embedding_str: str, 
        min_price: Optional[float], 
        max_price: Optional[float],
        page: int,
        limit: int,
        similarity_threshold: float = 0.7
    ) -> Tuple[str, Dict[str, Any]]:
        """Build search query with similarity threshold."""
        offset = (page - 1) * limit
        
        # Base query with similarity threshold
        sql_query = """
            SELECT 
                p.*,
                (p.embedding <=> :embedding) as similarity
            FROM products p
            WHERE (p.embedding <=> :embedding) <= :similarity_threshold
        """
        
        params = {
            "embedding": embedding_str,
            "similarity_threshold": 1.0 - similarity_threshold  # Convert to distance
        }
        
        # Add price filters
        if min_price is not None:
            sql_query += " AND p.price >= :min_price"
            params["min_price"] = min_price
        
        if max_price is not None:
            sql_query += " AND p.price <= :max_price"
            params["max_price"] = max_price
        
        # Add ordering and pagination
        sql_query += """
            ORDER BY similarity ASC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = limit
        params["offset"] = offset
        
        return sql_query, params
    
    async def _execute_search(
        self, 
        db: Session, 
        sql_query: str, 
        params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute search with better error handling."""
        try:
            # Execute main query
            result = db.execute(text(sql_query), params)
            results = [dict(row._mapping) for row in result.fetchall()]
            
            # Get total count
            count_query = sql_query.replace("SELECT p.*,", "SELECT COUNT(*) as count,")
            count_query = count_query.split("ORDER BY")[0]  # Remove ordering and pagination
            count_result = db.execute(text(count_query), params)
            total_count = count_result.fetchone()[0]
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            raise
    
    async def _execute_fallback_search(
        self, 
        db: Session, 
        embedding_str: str, 
        page: int, 
        limit: int,
        similarity_threshold: float = 0.7
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute fallback search without price filters."""
        offset = (page - 1) * limit
        
        sql_query = """
            SELECT 
                p.*,
                (p.embedding <=> :embedding) as similarity
            FROM products p
            WHERE (p.embedding <=> :embedding) <= :similarity_threshold
            ORDER BY similarity ASC
            LIMIT :limit OFFSET :offset
        """
        
        params = {
            "embedding": embedding_str,
            "similarity_threshold": 1.0 - similarity_threshold,
            "limit": limit,
            "offset": offset
        }
        
        return await self._execute_search(db, sql_query, params)
    
    def _create_response(
        self,
        query: str,
        results: List[Dict[str, Any]],
        total_count: int,
        page: int,
        limit: int,
        min_price: Optional[float],
        max_price: Optional[float],
        fallback_used: bool,
        similarity_threshold: float
    ) -> Dict[str, Any]:
        """Create enhanced response with metadata."""
        return {
            "query": query,
            "results": results,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            },
            "filters": {
                "min_price": min_price,
                "max_price": max_price,
                "similarity_threshold": similarity_threshold
            },
            "metadata": {
                "fallback_used": fallback_used,
                "result_count": len(results),
                "search_type": "ai_semantic"
            }
        }
    
    def _create_empty_response(self, query: str, page: int, limit: int) -> Dict[str, Any]:
        """Create response for empty query."""
        return {
            "query": query,
            "results": [],
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
            "filters": {},
            "metadata": {"error": "Empty query", "result_count": 0}
        }
    
    def _create_error_response(self, query: str, error: str, page: int, limit: int) -> Dict[str, Any]:
        """Create error response."""
        return {
            "query": query,
            "results": [],
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
            "filters": {},
            "metadata": {"error": error, "result_count": 0}
        }
    
    async def _track_search_analytics(
        self,
        query: str,
        result_count: int,
        total_count: int,
        search_time: float,
        user_agent: Optional[str],
        ip_address: Optional[str],
        fallback_used: bool
    ):
        """Track search analytics with privacy protection."""
        try:
            await self.analytics_service.track_search(
                query=sanitize_log_data(query, 50),
                result_count=result_count,
                total_count=total_count,
                search_time=search_time,
                user_agent=sanitize_log_data(user_agent, 100) if user_agent else None,
                ip_address=sanitize_log_data(ip_address, 15) if ip_address else None,
                fallback_used=fallback_used
            )
        except Exception as e:
            logger.warning(f"Failed to track analytics: {e}")
    
    async def search_with_fallback(
        self,
        db: Session,
        query: str,
        page: int = 1,
        limit: int = 25,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search with fallback to text search if no embeddings found.
        
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
            # Try AI search first
            return await self.search_products(db, query, page, limit, **kwargs)
        except Exception as e:
            logger.warning(f"AI search failed, falling back to text search: {e}")
            return await self._fallback_text_search(db, query, page, limit, **kwargs)
    
    async def _fallback_text_search(
        self,
        db: Session,
        query: str,
        page: int,
        limit: int,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Fallback to simple text search when embeddings fail."""
        
        try:
            # Simple text search in title
            search_query = db.query(Product).filter(Product.title.ilike(f"%{query}%"))
            
            # Apply price filters
            if min_price is not None:
                search_query = search_query.filter(Product.price >= min_price)
            if max_price is not None:
                search_query = search_query.filter(Product.price <= max_price)
            
            # Apply pagination
            offset = (page - 1) * limit
            results = search_query.offset(offset).limit(limit).all()
            
            # Format results
            formatted_results = []
            for product in results:
                formatted_results.append({
                    "id": product.id,
                    "shopify_id": product.shopify_id,
                    "title": product.title,
                    "description": product.description,
                    "price": float(product.price) if product.price else None,
                    "tags": product.tags if product.tags else [],
                    "similarity": 0.5  # Default similarity for text search
                })
            
            return {
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results),
                "total_count": len(formatted_results),
                "page": page,
                "total_pages": 1,
                "limit": limit,
                "cache_hit": False,
                "search_type": "text_fallback",
                "price_filter": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "applied": min_price is not None or max_price is not None,
                    "fallback_used": False
                }
            }
            
        except Exception as e:
            logger.error(f"Fallback text search failed: {e}")
            raise 