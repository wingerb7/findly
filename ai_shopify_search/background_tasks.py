import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from concurrent.futures import ThreadPoolExecutor
import threading

from ai_shopify_search.embeddings import generate_embedding
from ai_shopify_search.models import Product, SearchAnalytics, PopularSearch
from ai_shopify_search.analytics_manager import analytics_manager
from ai_shopify_search.error_handlers import safe_embedding_operation, safe_database_operation

logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

class BackgroundTaskManager:
    """Manager for background tasks."""
    
    def __init__(self):
        self.executor = executor
        self._lock = threading.Lock()
    
    async def generate_product_embeddings_async(
        self, 
        products: List[Dict[str, Any]], 
        db: Session
    ) -> None:
        """Generate embeddings for products asynchronously."""
        try:
            logger.info(f"Starting background embedding generation for {len(products)} products")
            
            # Process products in batches
            batch_size = 10
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                
                # Run embedding generation in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    self._generate_embeddings_batch,
                    batch,
                    db
                )
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
            
            logger.info("Background embedding generation completed")
            
        except Exception as e:
            logger.error(f"Error in background embedding generation: {e}")
            raise
    
    def _generate_embeddings_batch(self, products: List[Dict[str, Any]], db: Session) -> None:
        """Generate embeddings for a batch of products."""
        try:
            for product_data in products:
                try:
                    # Generate embedding
                    embedding = safe_embedding_operation(
                        lambda: generate_embedding(
                            title=product_data.get('title', ''),
                            description=product_data.get('description', ''),
                            tags=product_data.get('tags', []),
                            price=product_data.get('price')
                        ),
                        {"product_id": product_data.get('shopify_id')}
                    )
                    
                    if embedding and len(embedding) == 1536:
                        # Update product in database
                        safe_database_operation(
                            lambda: self._update_product_embedding(
                                db, 
                                product_data.get('shopify_id'), 
                                embedding
                            ),
                            {"product_id": product_data.get('shopify_id')}
                        )
                    
                except Exception as e:
                    logger.error(f"Error processing product {product_data.get('shopify_id')}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in embedding batch generation: {e}")
            raise
    
    def _update_product_embedding(self, db: Session, shopify_id: str, embedding: List[float]) -> None:
        """Update product embedding in database."""
        try:
            product = db.query(Product).filter_by(shopify_id=shopify_id).first()
            if product:
                product.embedding = embedding
                product.updated_at = datetime.now()
                db.commit()
                logger.debug(f"Updated embedding for product {shopify_id}")
        except Exception as e:
            logger.error(f"Error updating product embedding: {e}")
            db.rollback()
            raise
    
    async def log_analytics_async(
        self,
        query: str,
        search_type: str,
        filters: Dict[str, Any],
        results_count: int,
        page: int,
        limit: int,
        response_time_ms: float,
        cache_hit: bool,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        db: Session = None
    ) -> None:
        """Log analytics asynchronously."""
        try:
            logger.debug(f"Logging analytics for query: {query}")
            
            # Run analytics logging in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._log_analytics_sync,
                query, search_type, filters, results_count,
                page, limit, response_time_ms, cache_hit,
                user_agent, ip_address, db
            )
            
        except Exception as e:
            logger.error(f"Error in background analytics logging: {e}")
            # Don't raise - analytics logging should not break the main flow
    
    def _log_analytics_sync(
        self,
        query: str,
        search_type: str,
        filters: Dict[str, Any],
        results_count: int,
        page: int,
        limit: int,
        response_time_ms: float,
        cache_hit: bool,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        db: Session = None
    ) -> None:
        """Synchronous analytics logging."""
        try:
            if db:
                analytics_manager.track_search_analytics(
                    db=db,
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
        except Exception as e:
            logger.error(f"Error in synchronous analytics logging: {e}")
    
    async def update_popular_searches_async(self, query: str, db: Session) -> None:
        """Update popular searches asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._update_popular_searches_sync,
                query,
                db
            )
        except Exception as e:
            logger.error(f"Error updating popular searches: {e}")
    
    def _update_popular_searches_sync(self, query: str, db: Session) -> None:
        """Synchronous popular searches update."""
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
            logger.error(f"Error in synchronous popular searches update: {e}")
            db.rollback()
    
    async def precompute_embeddings_async(self, queries: List[str]) -> Dict[str, List[float]]:
        """Precompute embeddings for common queries."""
        try:
            logger.info(f"Precomputing embeddings for {len(queries)} queries")
            
            embeddings = {}
            tasks = []
            
            for query in queries:
                task = asyncio.create_task(
                    self._precompute_single_embedding(query)
                )
                tasks.append(task)
            
            # Wait for all embeddings to be computed
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error precomputing embedding for '{queries[i]}': {result}")
                else:
                    embeddings[queries[i]] = result
            
            logger.info(f"Precomputed {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in precompute embeddings: {e}")
            return {}
    
    async def _precompute_single_embedding(self, query: str) -> List[float]:
        """Precompute embedding for a single query."""
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                safe_embedding_operation,
                lambda: generate_embedding(title=query),
                {"query": query}
            )
            return embedding
        except Exception as e:
            logger.error(f"Error precomputing embedding for '{query}': {e}")
            raise

# Global background task manager
background_task_manager = BackgroundTaskManager()

def add_background_tasks(background_tasks: BackgroundTasks, *tasks) -> None:
    """Add multiple background tasks."""
    for task in tasks:
        if task:
            background_tasks.add_task(task)

async def generate_embeddings_task(products: List[Dict[str, Any]], db: Session) -> None:
    """Background task for generating embeddings."""
    await background_task_manager.generate_product_embeddings_async(products, db)

async def log_analytics_task(
    query: str,
    search_type: str,
    filters: Dict[str, Any],
    results_count: int,
    page: int,
    limit: int,
    response_time_ms: float,
    cache_hit: bool,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    db: Session = None
) -> None:
    """Background task for logging analytics."""
    await background_task_manager.log_analytics_async(
        query, search_type, filters, results_count,
        page, limit, response_time_ms, cache_hit,
        user_agent, ip_address, db
    )

async def update_popular_searches_task(query: str, db: Session) -> None:
    """Background task for updating popular searches."""
    await background_task_manager.update_popular_searches_async(query, db)

async def precompute_embeddings_task(queries: List[str]) -> Dict[str, List[float]]:
    """Background task for precomputing embeddings."""
    return await background_task_manager.precompute_embeddings_async(queries) 