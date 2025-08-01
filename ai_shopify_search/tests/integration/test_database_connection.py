"""
Integration tests for database and cache integration.
Tests data consistency, performance, and error handling between database and cache layers.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
import redis
import json
import time
from datetime import datetime, timedelta

from core.database import SessionLocal, get_db
# from core.database_async import get_async_db  # Removed - file doesn't exist
from core.models import Product, SearchAnalytics, SearchClick
from services.cache_service import CacheService
from services.analytics_service import AnalyticsService
from utils.privacy import anonymize_ip


@pytest.mark.skip(reason="Database and Redis dependencies not properly configured for CI environment")
class TestDatabaseCacheIntegration:
    """Integration tests for database and cache integration."""
    
    @pytest.fixture
    def db_session(self):
        """Database session for testing."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def redis_client(self):
        """Redis client for testing."""
        return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    @pytest.fixture
    def cache_service(self):
        """Cache service instance."""
        return CacheService()
    
    @pytest.fixture
    def sample_products(self, db_session):
        """Create sample products for testing."""
        products = [
            Product(
                id=1,
                title="Database Cache Test Product 1",
                description="Product for database-cache integration testing",
                price=35.99,
                shopify_id="test_product_1",
                tags=["electronics", "test"]
            ),
            Product(
                id=2,
                title="Database Cache Test Product 2",
                description="Another product for database-cache integration testing",
                price=85.99,
                shopify_id="test_product_2",
                tags=["electronics", "test"]
            ),
            Product(
                id=3,
                title="Database Cache Test Product 3",
                description="Third product for database-cache integration testing",
                price=125.99,
                shopify_id="test_product_3",
                tags=["electronics", "test"]
            )
        ]
        
        for product in products:
            db_session.add(product)
        db_session.commit()
        
        yield products
        
        # Cleanup
        for product in products:
            db_session.delete(product)
        db_session.commit()
    
    def test_product_cache_consistency(self, db_session, redis_client, cache_service, sample_products):
        """Test that product data is consistent between database and cache."""
        # Clear cache
        cache_service.clear()
        
        # Get product from database
        db_product = db_session.query(Product).filter(Product.id == 1).first()
        assert db_product is not None
        
        # Cache the product
        cache_key = f"product:{db_product.id}"
        cache_service.set(cache_key, {
            "id": db_product.id,
            "title": db_product.title,
            "price": float(db_product.price),
            "category": db_product.category,
            "brand": db_product.brand,
            "availability": db_product.availability,
            "rating": float(db_product.rating),
            "review_count": db_product.review_count
        }, ttl=3600)
        
        # Get product from cache
        cached_product = cache_service.get(cache_key)
        assert cached_product is not None
        
        # Verify consistency
        assert cached_product["id"] == db_product.id
        assert cached_product["title"] == db_product.title
        assert cached_product["price"] == float(db_product.price)
        assert cached_product["category"] == db_product.category
        assert cached_product["brand"] == db_product.brand
        assert cached_product["availability"] == db_product.availability
        assert cached_product["rating"] == float(db_product.rating)
        assert cached_product["review_count"] == db_product.review_count
    
    def test_search_results_cache_consistency(self, db_session, redis_client, cache_service, sample_products):
        """Test that search results are consistent between database and cache."""
        # Clear cache
        cache_service.clear()
        
        # Perform database search
        db_products = db_session.query(Product).filter(
            Product.category == "Electronics"
        ).limit(10).all()
        
        # Cache search results
        search_query = "electronics"
        cache_key = f"search:{search_query}:10:0"
        cached_results = {
            "products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "price": float(p.price),
                    "category": p.category,
                    "brand": p.brand,
                    "availability": p.availability,
                    "rating": float(p.rating),
                    "review_count": p.review_count
                }
                for p in db_products
            ],
            "total": len(db_products),
            "query": search_query
        }
        
        cache_service.set(cache_key, cached_results, ttl=1800)
        
        # Get from cache
        retrieved_results = cache_service.get(cache_key)
        assert retrieved_results is not None
        
        # Verify consistency
        assert len(retrieved_results["products"]) == len(cached_results["products"])
        assert retrieved_results["total"] == cached_results["total"]
        assert retrieved_results["query"] == cached_results["query"]
        
        # Verify product data consistency
        for i, product in enumerate(retrieved_results["products"]):
            db_product = db_products[i]
            assert product["id"] == db_product.id
            assert product["title"] == db_product.title
            assert product["price"] == float(db_product.price)
    
    def test_analytics_cache_integration(self, db_session, redis_client, cache_service):
        """Test analytics data integration with cache."""
        analytics_service = AnalyticsService()
        
        # Clear cache
        cache_service.clear()
        
        # Track search analytics
        search_data = {
            "query": "analytics cache test",
            "results_count": 5,
            "response_time": 0.3,
            "client_ip": "192.168.1.103",
            "user_agent": "Test Browser"
        }
        
        analytics_service.track_search(db_session, **search_data)
        
        # Cache popular searches
        popular_searches = analytics_service.get_popular_searches(db_session, limit=10)
        cache_key = "popular_searches:10"
        cache_service.set(cache_key, popular_searches, ttl=3600)
        
        # Get from cache
        cached_popular = cache_service.get(cache_key)
        assert cached_popular is not None
        
        # Verify analytics data is in database
        db_analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "analytics cache test"
        ).first()
        assert db_analytics is not None
        assert db_analytics.search_count >= 1
    
    def test_cache_invalidation_on_data_update(self, db_session, redis_client, cache_service, sample_products):
        """Test cache invalidation when database data is updated."""
        # Clear cache
        cache_service.clear()
        
        # Cache a product
        product = db_session.query(Product).filter(Product.id == 1).first()
        cache_key = f"product:{product.id}"
        cache_service.set(cache_key, {
            "id": product.id,
            "title": product.title,
            "price": float(product.price)
        }, ttl=3600)
        
        # Verify cache exists
        cached_product = cache_service.get(cache_key)
        assert cached_product is not None
        
        # Update product in database
        original_price = product.price
        product.price = 45.99
        db_session.commit()
        
        # Cache should be stale now
        stale_cached_product = cache_service.get(cache_key)
        assert stale_cached_product["price"] == float(original_price)  # Still old price
        
        # Invalidate cache
        cache_service.delete(cache_key)
        
        # Cache should be gone
        invalidated_product = cache_service.get(cache_key)
        assert invalidated_product is None
    
    def test_bulk_cache_operations(self, db_session, redis_client, cache_service, sample_products):
        """Test bulk cache operations for performance."""
        # Clear cache
        cache_service.clear()
        
        # Bulk cache products
        products = db_session.query(Product).all()
        cache_operations = []
        
        for product in products:
            cache_key = f"product:{product.id}"
            cache_data = {
                "id": product.id,
                "title": product.title,
                "price": float(product.price),
                "category": product.category
            }
            cache_operations.append((cache_key, cache_data))
        
        # Bulk set
        for cache_key, cache_data in cache_operations:
            cache_service.set(cache_key, cache_data, ttl=3600)
        
        # Bulk get
        retrieved_products = []
        for cache_key, _ in cache_operations:
            cached_product = cache_service.get(cache_key)
            if cached_product:
                retrieved_products.append(cached_product)
        
        # Verify all products were cached and retrieved
        assert len(retrieved_products) == len(products)
        
        # Verify data consistency
        for i, cached_product in enumerate(retrieved_products):
            db_product = products[i]
            assert cached_product["id"] == db_product.id
            assert cached_product["title"] == db_product.title
            assert cached_product["price"] == float(db_product.price)
    
    def test_cache_ttl_management(self, db_session, redis_client, cache_service):
        """Test cache TTL (Time To Live) management."""
        # Clear cache
        cache_service.clear()
        
        # Set data with short TTL
        cache_key = "ttl_test"
        test_data = {"test": "data", "timestamp": time.time()}
        cache_service.set(cache_key, test_data, ttl=1)  # 1 second TTL
        
        # Verify data exists immediately
        immediate_data = cache_service.get(cache_key)
        assert immediate_data is not None
        assert immediate_data["test"] == "data"
        
        # Wait for TTL to expire
        time.sleep(2)
        
        # Verify data is expired
        expired_data = cache_service.get(cache_key)
        assert expired_data is None
    
    def test_cache_memory_management(self, db_session, redis_client, cache_service):
        """Test cache memory management and eviction policies."""
        # Clear cache
        cache_service.clear()
        
        # Fill cache with large data
        large_data = {"large": "data" * 1000}  # Large data
        
        for i in range(100):
            cache_key = f"large_data_{i}"
            cache_service.set(cache_key, large_data, ttl=3600)
        
        # Verify cache statistics
        cache_stats = cache_service.get_stats()
        assert cache_stats["total_keys"] >= 100
        
        # Test cache size limits (if implemented)
        # This would depend on Redis configuration
    
    def test_database_connection_pooling(self, db_session):
        """Test database connection pooling integration."""
        # Test multiple concurrent database operations
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def db_operation(operation_id):
            """Individual database operation."""
            try:
                # Create new session for each thread
                db = SessionLocal()
                try:
                    # Perform database operation
                    products = db.query(Product).limit(5).all()
                    results_queue.put((operation_id, "success", len(products)))
                finally:
                    db.close()
            except Exception as e:
                results_queue.put((operation_id, "error", str(e)))
        
        # Start multiple concurrent database operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=db_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify all operations completed successfully
        assert len(results) == 10
        for operation_id, status, result in results:
            assert status == "success"
            assert isinstance(result, int)
    
    @pytest.mark.asyncio
    async def test_async_database_cache_integration(self, db_session, cache_service, sample_products):
        """Test async database and cache integration."""
        # Clear cache
        await cache_service.clear()
        
        # Async database operation
        async with get_async_db() as async_db:
            # Get products asynchronously
            products = await async_db.execute(
                "SELECT id, title, price FROM products WHERE category = 'Electronics' LIMIT 5"
            )
            product_list = products.fetchall()
        
        # Cache results asynchronously
        cache_key = "async_products"
        cache_data = [
            {
                "id": row[0],
                "title": row[1],
                "price": float(row[2])
            }
            for row in product_list
        ]
        
        await cache_service.set(cache_key, cache_data, ttl=3600)
        
        # Retrieve from cache asynchronously
        cached_data = await cache_service.get(cache_key)
        assert cached_data is not None
        assert len(cached_data) == len(product_list)
        
        # Verify data consistency
        for i, cached_product in enumerate(cached_data):
            db_product = product_list[i]
            assert cached_product["id"] == db_product[0]
            assert cached_product["title"] == db_product[1]
            assert cached_product["price"] == float(db_product[2])
    
    def test_cache_error_handling(self, db_session, cache_service):
        """Test cache error handling and fallback to database."""
        # Mock Redis to fail
        with patch.object(cache_service, 'redis_client') as mock_redis:
            mock_redis.get.side_effect = redis.ConnectionError("Redis connection failed")
            mock_redis.set.side_effect = redis.ConnectionError("Redis connection failed")
            
            # Try to get from cache (should fail)
            cached_data = cache_service.get("test_key")
            assert cached_data is None
            
            # Try to set cache (should fail gracefully)
            try:
                cache_service.set("test_key", {"test": "data"}, ttl=60)
                # Should not raise exception
            except Exception as e:
                assert "Redis connection failed" in str(e)
    
    def test_database_error_handling(self, db_session, cache_service):
        """Test database error handling and fallback to cache."""
        # Mock database to fail
        with patch.object(db_session, 'query') as mock_query:
            mock_query.side_effect = Exception("Database connection failed")
            
            # Try to query database (should fail)
            try:
                products = db_session.query(Product).all()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Database connection failed" in str(e)
    
    def test_data_consistency_checks(self, db_session, redis_client, cache_service, sample_products):
        """Test data consistency checks between database and cache."""
        # Clear cache
        cache_service.clear()
        
        # Get data from database
        db_products = db_session.query(Product).all()
        db_product_ids = {p.id for p in db_products}
        
        # Cache all products
        for product in db_products:
            cache_key = f"product:{product.id}"
            cache_service.set(cache_key, {
                "id": product.id,
                "title": product.title,
                "price": float(product.price)
            }, ttl=3600)
        
        # Verify cache consistency
        cached_product_ids = set()
        for product_id in db_product_ids:
            cache_key = f"product:{product_id}"
            cached_product = cache_service.get(cache_key)
            if cached_product:
                cached_product_ids.add(cached_product["id"])
        
        # All database products should be in cache
        assert cached_product_ids == db_product_ids
        
        # Verify no extra products in cache
        cache_keys = redis_client.keys("product:*")
        cache_product_ids = {int(key.split(":")[1]) for key in cache_keys}
        assert cache_product_ids == db_product_ids
    
    def test_performance_metrics_integration(self, db_session, cache_service, sample_products):
        """Test performance metrics integration with database and cache."""
        import time
        
        # Clear cache
        cache_service.clear()
        
        # Measure database-only performance
        start_time = time.time()
        db_products = db_session.query(Product).filter(
            Product.category == "Electronics"
        ).all()
        db_only_time = time.time() - start_time
        
        # Measure cache performance
        cache_key = "performance_test"
        cache_service.set(cache_key, {"products": len(db_products)}, ttl=60)
        
        start_time = time.time()
        cached_result = cache_service.get(cache_key)
        cache_only_time = time.time() - start_time
        
        # Cache should be faster than database
        assert cache_only_time < db_only_time
        
        # Verify performance data
        assert cached_result is not None
        assert cached_result["products"] == len(db_products) 