#!/usr/bin/env python3
"""
AI Search Service for semantic search with vector embeddings.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Product
from embeddings import generate_embedding
from validation import validate_price_range, generate_secure_cache_key
from privacy_utils import sanitize_log_data

logger = logging.getLogger(__name__)

class AISearchService:
    """Specialized service for AI-powered semantic search with vector embeddings."""
    
    def __init__(self, cache_service, analytics_service):
        self.cache_service = cache_service
        self.analytics_service = analytics_service
    
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
        Perform AI-powered product search with vector embeddings and price filtering.
        
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
                max_price=max_price
            )
            
            # Check cache
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for AI search: '{sanitize_log_data(query, 30)}'")
                return cached_result
            
            # Generate embedding
            query_embedding = generate_embedding(title=query)
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Build search query
            sql_query, params = self._build_search_query(
                embedding_str, min_price, max_price, page, limit
            )
            
            # Execute search
            results, total_count = await self._execute_search(db, sql_query, params)
            
            # Handle fallback if no results with price filter
            if len(results) == 0 and (min_price is not None or max_price is not None):
                logger.warning("No results with price filter, using fallback")
                results, total_count = await self._execute_fallback_search(
                    db, embedding_str, page, limit
                )
                fallback_used = True
            else:
                fallback_used = False
            
            # Create response
            response_data = self._create_response(
                query, results, total_count, page, limit, min_price, max_price, fallback_used
            )
            
            # Cache result
            await self.cache_service.set(cache_key, response_data, ttl=900)  # 15 minutes
            
            # Track analytics
            response_time_ms = (time.time() - start_time) * 1000
            await self.analytics_service.track_search(
                db, query, "ai", {"price_filter": {"min": min_price, "max": max_price}},
                len(results), page, limit, response_time_ms, False, user_agent, ip_address
            )
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error in AI search: {e}")
            raise
    
    def _build_search_query(
        self, 
        embedding_str: str, 
        min_price: Optional[float], 
        max_price: Optional[float],
        page: int,
        limit: int
    ) -> Tuple[str, Dict[str, Any]]:
        """Build SQL query for vector search with price filtering."""
        
        sql_query = """
        SELECT id, shopify_id, title, description, price, tags,
               1 - (embedding <=> :embedding) as similarity
        FROM products 
        WHERE embedding IS NOT NULL
        """
        params = {"embedding": embedding_str}
        
        # Add price filters
        if min_price is not None:
            sql_query += " AND price >= :min_price"
            params["min_price"] = min_price
        if max_price is not None:
            sql_query += " AND price <= :max_price"
            params["max_price"] = max_price
        
        # Add pagination
        offset = (page - 1) * limit
        sql_query += " ORDER BY similarity DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        return sql_query, params
    
    async def _execute_search(
        self, 
        db: Session, 
        sql_query: str, 
        params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute search query and return results with count."""
        
        # Execute main query
        result = db.execute(text(sql_query), params)
        rows = result.fetchall()
        
        # Count total results (without pagination)
        count_query = sql_query.split("ORDER BY")[0]  # Remove ORDER BY and LIMIT
        count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
        count_result = db.execute(text(f"SELECT COUNT(*) FROM ({count_query}) as subquery"), count_params)
        total_count = count_result.scalar()
        
        # Format results
        results = []
        for row in rows:
            results.append({
                "id": row.id,
                "shopify_id": row.shopify_id,
                "title": row.title,
                "description": row.description,
                "price": float(row.price) if row.price else None,
                "tags": row.tags if row.tags else [],
                "similarity": float(row.similarity) if row.similarity else 0.0
            })
        
        return results, total_count
    
    async def _execute_fallback_search(
        self, 
        db: Session, 
        embedding_str: str, 
        page: int, 
        limit: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute fallback search without price filters, sorted by price."""
        
        sql_query = """
        SELECT id, shopify_id, title, description, price, tags,
               1 - (embedding <=> :embedding) as similarity
        FROM products 
        WHERE embedding IS NOT NULL
        ORDER BY price ASC, similarity DESC
        LIMIT :limit OFFSET :offset
        """
        params = {
            "embedding": embedding_str,
            "limit": limit,
            "offset": (page - 1) * limit
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
        fallback_used: bool
    ) -> Dict[str, Any]:
        """Create standardized response with metadata."""
        
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        
        response_data = {
            "query": query,
            "results": results,
            "count": len(results),
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "cache_hit": False,
            "price_filter": {
                "min_price": min_price,
                "max_price": max_price,
                "applied": min_price is not None or max_price is not None,
                "fallback_used": fallback_used
            }
        }
        
        # Add fallback message if used
        if fallback_used:
            response_data["message"] = "Geen producten gevonden binnen de prijsklasse, hier zijn de goedkoopste alternatieven."
        
        return response_data
    
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