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
from sqlalchemy import text, func
from ai_shopify_search.core.models import Product
from ai_shopify_search.core.embeddings import (
    generate_embedding, 
    get_embedding_model, 
    generate_image_embedding
)
from ai_shopify_search.utils.validation.validation import (
    validate_price_range, 
    generate_secure_cache_key, 
    sanitize_search_query
)
from ai_shopify_search.utils.privacy.privacy_utils import sanitize_log_data
from ai_shopify_search.utils.search.fuzzy_search import FuzzySearch
from ai_shopify_search.features.refinement_agent import ConversationalRefinementAgent
from ai_shopify_search.features.store_profile import StoreProfileGenerator
from ai_shopify_search.features.adaptive_filters import AdaptiveFilterEngine
from ai_shopify_search.api.schemas import ConversationalRefinements
import json

# ✅ Correcte import voor pgvector
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    VECTOR_AVAILABLE = False

logger = logging.getLogger(__name__)

class AISearchService:
    """Specialized service for AI-powered semantic search with vector embeddings."""
    
    def __init__(self, cache_service, analytics_service):
        self.cache_service = cache_service
        self.analytics_service = analytics_service
        self.max_retries = 3
        self.retry_delay = 1.0
        self.fuzzy_search = FuzzySearch()
        
        # Initialize AI features
        self._initialize_features()
    
    def _initialize_features(self):
        """Initialize all AI features with error handling."""
        try:
            self.refinement_agent = ConversationalRefinementAgent()
            logger.info("ConversationalRefinementAgent initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize ConversationalRefinementAgent: {e}")
            self.refinement_agent = None
        
        try:
            self.store_profile_generator = StoreProfileGenerator()
            logger.info("StoreProfileGenerator initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize StoreProfileGenerator: {e}")
            self.store_profile_generator = None
        
        try:
            self.adaptive_filters = AdaptiveFilterEngine()
            logger.info("AdaptiveFilterEngine initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize AdaptiveFilterEngine: {e}")
            self.adaptive_filters = None

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
        db: Session,
        embedding_str: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page: int = 1,
        limit: int = 25,
        similarity_threshold: float = 0.7,
        store_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Build and execute search query using combined_embedding_vector for AI search.
        
        Args:
            db: Database session
            embedding_str: Query embedding as string
            min_price: Minimum price filter
            max_price: Maximum price filter
            page: Page number
            limit: Results per page
            similarity_threshold: Minimum similarity score
            store_id: Store identifier
            
        Returns:
            Tuple of (results, total_count)
        """
        try:
            logger.info(f"🔍 [AI SEARCH] Building search query with combined_embedding_vector")
            
            # Parse embedding string to list
            try:
                embedding_list = json.loads(embedding_str.replace("'", '"'))
                if not isinstance(embedding_list, list):
                    logger.warning(f"⚠️ [AI SEARCH] Invalid embedding format, using empty list")
                    embedding_list = []
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"⚠️ [AI SEARCH] Failed to parse embedding string: {e}, using empty list")
                embedding_list = []
            
            # Build the base query using combined_embedding_vector
            base_query = db.query(Product).filter(
                Product.combined_embedding_vector.isnot(None)
            )
            
            # Add store filter if provided
            if store_id:
                base_query = base_query.filter(Product.store_id == store_id)
                logger.info(f"🔍 [AI SEARCH] Filtering by store_id: {store_id}")
            
            # Add price filters
            if min_price is not None:
                base_query = base_query.filter(Product.price >= min_price)
                logger.info(f"💰 [AI SEARCH] Applied min_price filter: {min_price}")
            
            if max_price is not None:
                base_query = base_query.filter(Product.price <= max_price)
                logger.info(f"💰 [AI SEARCH] Applied max_price filter: {max_price}")
            
            # Add similarity search using combined_embedding_vector
            if VECTOR_AVAILABLE and embedding_list:
                # Convert embedding list to vector format
                vector_str = '[' + ','.join(str(x) for x in embedding_list) + ']'
                
                # Use cosine similarity with combined_embedding_vector
                similarity_query = base_query.add_columns(
                    func.cosine_similarity(
                        Product.combined_embedding_vector,
                        func.cast(vector_str, Vector(1536))
                    ).label('similarity')
                ).filter(
                    func.cosine_similarity(
                        Product.combined_embedding_vector,
                        func.cast(vector_str, Vector(1536))
                    ) >= similarity_threshold
                ).order_by(
                    func.cosine_similarity(
                        Product.combined_embedding_vector,
                        func.cast(vector_str, Vector(1536))
                    ).desc()
                )
                
                logger.info(f"🎯 [AI SEARCH] Using combined_embedding_vector similarity search with threshold: {similarity_threshold}")
            else:
                # Fallback to basic query if no embedding or pgvector
                similarity_query = base_query.order_by(Product.id.desc())
                logger.warning(f"⚠️ [AI SEARCH] No embedding or pgvector available, using basic query")
            
            # Get total count
            total_count = similarity_query.count()
            logger.info(f"📊 [AI SEARCH] Total products matching criteria: {total_count}")
            
            # Apply pagination
            offset = (page - 1) * limit
            paginated_query = similarity_query.offset(offset).limit(limit)
            
            # Execute query
            results_with_similarity = paginated_query.all()
            
            # Convert to dictionary format
            results = []
            for result in results_with_similarity:
                if hasattr(result, 'similarity'):
                    # If similarity was calculated
                    product = result[0]  # First element is the Product object
                    similarity = result[1]  # Second element is the similarity score
                else:
                    # If no similarity was calculated (fallback)
                    product = result
                    similarity = 0.5  # Default similarity
                
                # Ensure image_url is always included, even if None
                image_url = getattr(product, 'image_url', None)
                if image_url is None:
                    logger.debug(f"⚠️ [AI SEARCH] No image_url found for product {product.shopify_id}")
                
                results.append({
                    "id": product.id,
                    "shopify_id": product.shopify_id,
                    "title": product.title,
                    "description": getattr(product, 'description', None),
                    "price": float(product.price) if product.price else None,
                    "image_url": image_url,  # Always include image_url, even if None
                    "vendor": getattr(product, 'vendor', None),
                    "product_type": getattr(product, 'product_type', None),
                    "tags": product.tags if product.tags else [],
                    "similarity": float(similarity) if similarity else 0.0,
                    "search_type": "ai"
                })
            
            logger.info(f"✅ [AI SEARCH] Found {len(results)} results with combined_embedding_vector")
            return results, total_count
            
        except Exception as e:
            logger.error(f"❌ [AI SEARCH] Error in _build_search_query: {e}")
            return [], 0

    async def search_products_by_image(
        self,
        db: Session,
        image_url: str,
        page: int = 1,
        limit: int = 25,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        similarity_threshold: float = 0.7,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform image-based product search using OpenCLIP embeddings.
        
        Args:
            db: Database session
            image_url: URL of the image to search for
            page: Page number
            limit: Results per page
            min_price: Minimum price filter
            max_price: Maximum price filter
            user_agent: User agent string
            ip_address: IP address
            similarity_threshold: Minimum similarity score (0.0-1.0)
            store_id: Store identifier
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not image_url or not image_url.strip():
                return self._create_empty_response("image_search", page, limit)
            
            # Generate image embedding
            logger.info(f"Generating image embedding for: {image_url}")
            image_embedding = generate_image_embedding(image_url)
            
            if not image_embedding:
                logger.error("Failed to generate image embedding")
                return self._create_error_response("image_search", "Failed to generate image embedding", page, limit)
            
            # Execute search with image embedding
            results, total_count = await self._execute_image_search(
                db=db,
                image_embedding=image_embedding,
                min_price=min_price,
                max_price=max_price,
                page=page,
                limit=limit,
                similarity_threshold=similarity_threshold,
                store_id=store_id
            )
            
            # Create response
            response = self._create_response(
                query=f"image_search:{image_url}",
                results=results,
                total_count=total_count,
                page=page,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                fallback_used=False,
                similarity_threshold=similarity_threshold
            )
            
            # Add image-specific metadata
            response["search_type"] = "image"
            response["image_url"] = image_url
            
            # Track analytics
            search_time = time.time() - start_time
            await self._track_search_analytics(
                query=f"image_search:{image_url}",
                result_count=len(results),
                total_count=total_count,
                search_time=search_time,
                user_agent=user_agent,
                ip_address=ip_address,
                fallback_used=False
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in image-based search: {e}")
            return self._create_error_response("image_search", str(e), page, limit)

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
        similarity_threshold: float = 0.7,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main AI search method for text-based product search.
        
        Args:
            db: Database session
            query: Search query
            page: Page number
            limit: Results per page
            min_price: Minimum price filter
            max_price: Maximum price filter
            user_agent: User agent string
            ip_address: IP address
            similarity_threshold: Minimum similarity score
            store_id: Store identifier
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Validate and sanitize query
            if not query or not query.strip():
                return self._create_empty_response(query, page, limit)
            
            query = sanitize_search_query(query)
            
            # Generate embedding for the query
            logger.info(f"🔍 [AI SEARCH] Generating embedding for query: '{query}'")
            embedding = await self._generate_embedding_with_retry(query)
            
            if not embedding:
                logger.error(f"❌ [AI SEARCH] Failed to generate embedding for query: '{query}'")
                return self._create_error_response(query, "Failed to generate embedding", page, limit)
            
            # Convert embedding to string for search
            embedding_str = str(embedding)
            
            # Execute search
            results, total_count = self._build_search_query(
                db=db,
                embedding_str=embedding_str,
                min_price=min_price,
                max_price=max_price,
                page=page,
                limit=limit,
                similarity_threshold=similarity_threshold,
                store_id=store_id
            )
            
            # Create response
            response = self._create_response(
                query=query,
                results=results,
                total_count=total_count,
                page=page,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                fallback_used=False,
                similarity_threshold=similarity_threshold
            )
            
            # Track analytics
            search_time = time.time() - start_time
            await self._track_search_analytics(
                query=query,
                result_count=len(results),
                total_count=total_count,
                search_time=search_time,
                user_agent=user_agent,
                ip_address=ip_address,
                fallback_used=False
            )
            
            logger.info(f"✅ [AI SEARCH COMPLETE] Query: '{query}', Results: {len(results)}, Time: {search_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ [AI SEARCH ERROR] Query: '{query}', Error: {e}")
            return self._create_error_response(query, str(e), page, limit)

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
        similarity_threshold: float = 0.7,
        store_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Execute fallback search without price filters using helper function."""
        from ai_shopify_search.utils.search import search_similar_products
        
        # Safely convert embedding string to list of floats
        try:
            embedding_list = [float(x) for x in embedding_str.strip('[]').split(',')]
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid embedding format in fallback search: {embedding_str[:100]}... Error: {e}")
            return [], 0
        
        # Use the helper function to get similar products (no price filters)
        try:
            similar_products = search_similar_products(
                session=db,
                embedding=embedding_list,
                min_score=similarity_threshold,
                limit=limit,
                store_id=store_id
            )
        except Exception as e:
            logger.error(f"Error in fallback search_similar_products: {e}")
            return [], 0
        
        # Convert to the expected format with safe image_url handling
        results = []
        for product in similar_products:
            # Ensure image_url is always included, even if None
            image_url = product.get('image_url')
            if image_url is None:
                logger.debug(f"No image_url found for product {product.get('shopify_id', 'unknown')} in fallback search")
            
            results.append({
                'id': product.get('shopify_id'),
                'title': product.get('title', ''),
                'price': product.get('price', 0.0),
                'tags': product.get('tags', []),
                'similarity': product.get('similarity', 0.0),
                'image_url': image_url,  # Always include image_url, even if None
                'description': product.get('description'),
                'vendor': product.get('vendor'),
                'product_type': product.get('product_type')
            })
        
        return results, len(results)

    async def _execute_image_search(
        self,
        db: Session,
        image_embedding: List[float],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page: int = 1,
        limit: int = 25,
        similarity_threshold: float = 0.7,
        store_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Execute image-based search using vector similarity.
        
        Args:
            db: Database session
            image_embedding: Image embedding vector
            min_price: Minimum price filter
            max_price: Maximum price filter
            page: Page number
            limit: Results per page
            similarity_threshold: Minimum similarity score
            store_id: Store identifier
            
        Returns:
            Tuple of (results, total_count)
        """
        try:
            # Build base query
            base_query = """
                SELECT 
                    p.id,
                    p.shopify_id,
                    p.title,
                    p.tags,
                    p.price,
                    p.embedding,
                    p.image_embedding,
                    p.created_at,
                    p.updated_at
                FROM products p
                WHERE 1=1
            """
            
            params = {}
            
            # Add store filter if specified
            if store_id:
                base_query += " AND p.store_id = :store_id"
                params["store_id"] = store_id
            
            # Add price filters
            if min_price is not None:
                base_query += " AND p.price >= :min_price"
                params["min_price"] = min_price
            
            if max_price is not None:
                base_query += " AND p.price <= :max_price"
                params["max_price"] = max_price
            
            # Add image embedding similarity search
            # Note: This assumes you have pgvector extension installed
            # If not, you'll need to implement a different similarity calculation
            base_query += """
                AND p.image_embedding IS NOT NULL
                ORDER BY p.image_embedding <-> :image_embedding::vector
            """
            params["image_embedding"] = str(image_embedding)
            
            # Add pagination
            offset = (page - 1) * limit
            base_query += f" LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            # Execute query
            result = db.execute(text(base_query), params)
            rows = result.fetchall()
            
            # Convert to dict format
            results = []
            for row in rows:
                product_dict = {
                    "id": row.id,
                    "shopify_id": row.shopify_id,
                    "title": row.title,
                    "tags": row.tags,
                    "price": row.price,
                    "embedding": row.embedding,
                    "image_embedding": row.image_embedding,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at
                }
                results.append(product_dict)
            
            # Get total count
            count_query = """
                SELECT COUNT(*) 
                FROM products p 
                WHERE p.image_embedding IS NOT NULL
            """
            
            if store_id:
                count_query += " AND p.store_id = :store_id"
            
            if min_price is not None:
                count_query += " AND p.price >= :min_price"
            
            if max_price is not None:
                count_query += " AND p.price <= :max_price"
            
            count_params = {k: v for k, v in params.items() if k in ["store_id", "min_price", "max_price"]}
            count_result = db.execute(text(count_query), count_params)
            total_count = count_result.scalar()
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error executing image search: {e}")
            return [], 0

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
            },
            "conversational_refinements": ConversationalRefinements()
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
            # Get database session for analytics
            from ai_shopify_search.core.database import get_db
            db = next(get_db())
            
            await self.analytics_service.track_search(
                db=db,
                query=sanitize_log_data(query, 50),
                search_type="ai_search",
                filters={"fallback_used": fallback_used},
                results_count=result_count,
                page=1,  # Default page
                limit=25,  # Default limit
                response_time_ms=search_time * 1000,  # Convert to milliseconds
                cache_hit=False,  # Default value
                user_agent=sanitize_log_data(user_agent, 100) if user_agent else None,
                ip_address=sanitize_log_data(ip_address, 15) if ip_address else None
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
        """Fallback to text-based search when AI search fails."""
        logger.info(f"🔄 [FUZZY SEARCH START] Query: '{query}', page: {page}, limit: {limit}")
        
        try:
            from ai_shopify_search.utils.search.fuzzy_search import fuzzy_search_products
            
            logger.info(f"🔍 [FUZZY SEARCH] Using fuzzy search for query: '{query}'")
            
            result = await fuzzy_search_products(
                session=db,
                query=query,
                limit=limit,
                page=page
            )
            
            logger.info(f"✅ [FUZZY SEARCH] Found {len(result.get('results', []))} results")
            
            # Add fallback indicator
            result["fallback_used"] = True
            result["search_type"] = "fuzzy_fallback"
            
            logger.info(f"✅ [FUZZY SEARCH COMPLETE] Query: '{query}', Results: {len(result.get('results', []))}")
            return result
            
        except Exception as e:
            logger.error(f"❌ [FUZZY SEARCH ERROR] Query: '{query}', Error: {e}")
            return {
                "results": [],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                },
                "search_type": "fuzzy_error",
                "query": query,
                "fallback_used": True,
                "error": str(e)
            }