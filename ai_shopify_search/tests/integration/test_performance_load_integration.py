"""
Integration tests for performance and load testing.
Tests system performance, scalability, and load handling capabilities.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime

from main import app
from core.database import SessionLocal
from core.models import Product, SearchAnalytics
from services.service_factory import service_factory
from performance_monitor import PerformanceMonitor


class TestPerformanceLoadIntegration:
    """Integration tests for performance and load testing."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        """Database session for testing."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def sample_products(self, db_session):
        """Create sample products for performance testing."""
        products = []
        for i in range(100):  # Create 100 products for load testing
            product = Product(
                id=i + 1,
                title=f"Performance Test Product {i + 1}",
                description=f"Product {i + 1} for performance and load testing",
                price=float(10 + (i % 90)),  # Prices from 10 to 99
                category=f"Category {i % 5}",  # 5 different categories
                brand=f"Brand {i % 10}",  # 10 different brands
                image_url=f"https://example.com/image{i + 1}.jpg",
                product_url=f"https://example.com/product{i + 1}",
                availability=True,
                rating=float(3.0 + (i % 20) / 10),  # Ratings from 3.0 to 4.9
                review_count=i * 10
            )
            products.append(product)
            db_session.add(product)
        
        db_session.commit()
        yield products
        
        # Cleanup
        for product in products:
            db_session.delete(product)
        db_session.commit()
    
    def test_single_request_performance(self, client, db_session, sample_products):
        """Test performance of single requests."""
        # Test search performance
        start_time = time.time()
        response = client.get("/api/v2/products/search", params={
            "query": "performance test",
            "limit": 10
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should complete within 1 second
        
        # Test suggestions performance
        start_time = time.time()
        response = client.get("/api/v2/products/suggestions", params={
            "query": "perf",
            "limit": 5
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Suggestions should be faster
    
    def test_concurrent_requests_performance(self, client, db_session, sample_products):
        """Test performance under concurrent load."""
        def make_request(request_id):
            """Make a single request."""
            start_time = time.time()
            response = client.get("/api/v2/products/search", params={
                "query": f"concurrent test {request_id}",
                "limit": 10
            })
            end_time = time.time()
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }
        
        # Test with 10 concurrent requests
        num_requests = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]
        
        assert len(successful_requests) >= num_requests * 0.9  # 90% success rate
        assert statistics.mean(response_times) < 2.0  # Average response time < 2s
        assert max(response_times) < 5.0  # Max response time < 5s
    
    def test_database_performance_under_load(self, db_session, sample_products):
        """Test database performance under load."""
        def database_operation(operation_id):
            """Perform database operation."""
            db = SessionLocal()
            try:
                start_time = time.time()
                
                # Complex query with joins and filters
                products = db.query(Product).filter(
                    Product.category == f"Category {operation_id % 5}",
                    Product.price >= 20,
                    Product.price <= 80,
                    Product.rating >= 4.0
                ).limit(20).all()
                
                end_time = time.time()
                return {
                    "operation_id": operation_id,
                    "response_time": end_time - start_time,
                    "result_count": len(products)
                }
            finally:
                db.close()
        
        # Test with 20 concurrent database operations
        num_operations = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_operations) as executor:
            futures = [executor.submit(database_operation, i) for i in range(num_operations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze database performance
        response_times = [r["response_time"] for r in results]
        result_counts = [r["result_count"] for r in results]
        
        assert statistics.mean(response_times) < 0.5  # Average DB query < 0.5s
        assert max(response_times) < 2.0  # Max DB query < 2s
        assert all(count > 0 for count in result_counts)  # All queries returned results
    
    def test_cache_performance_under_load(self, db_session, sample_products):
        """Test cache performance under load."""
        cache_service = service_factory.get_cache_service()
        
        # Clear cache
        cache_service.clear()
        
        def cache_operation(operation_id):
            """Perform cache operation."""
            cache_key = f"load_test_{operation_id}"
            cache_data = {
                "id": operation_id,
                "data": f"test_data_{operation_id}",
                "timestamp": time.time()
            }
            
            # Set cache
            start_time = time.time()
            cache_service.set(cache_key, cache_data, ttl=60)
            set_time = time.time() - start_time
            
            # Get cache
            start_time = time.time()
            retrieved_data = cache_service.get(cache_key)
            get_time = time.time() - start_time
            
            return {
                "operation_id": operation_id,
                "set_time": set_time,
                "get_time": get_time,
                "success": retrieved_data == cache_data
            }
        
        # Test with 50 concurrent cache operations
        num_operations = 50
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_operations) as executor:
            futures = [executor.submit(cache_operation, i) for i in range(num_operations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze cache performance
        set_times = [r["set_time"] for r in results]
        get_times = [r["get_time"] for r in results]
        successful_operations = [r for r in results if r["success"]]
        
        assert len(successful_operations) >= num_operations * 0.95  # 95% success rate
        assert statistics.mean(set_times) < 0.1  # Average set time < 0.1s
        assert statistics.mean(get_times) < 0.05  # Average get time < 0.05s
    
    def test_memory_usage_under_load(self, client, db_session, sample_products):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple requests to simulate load
        for i in range(100):
            response = client.get("/api/v2/products/search", params={
                "query": f"memory test {i}",
                "limit": 10
            })
            assert response.status_code == 200
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100
    
    def test_response_time_distribution(self, client, db_session, sample_products):
        """Test response time distribution under load."""
        response_times = []
        
        # Make 50 requests
        for i in range(50):
            start_time = time.time()
            response = client.get("/api/v2/products/search", params={
                "query": f"distribution test {i}",
                "limit": 10
            })
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Analyze response time distribution
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Performance requirements
        assert mean_time < 1.0  # Average < 1s
        assert median_time < 0.8  # Median < 0.8s
        assert p95_time < 2.0  # 95th percentile < 2s
        assert p99_time < 3.0  # 99th percentile < 3s
    
    def test_concurrent_user_simulation(self, client, db_session, sample_products):
        """Simulate multiple concurrent users."""
        def user_session(user_id):
            """Simulate a user session with multiple requests."""
            session_results = []
            
            # User performs multiple searches
            for search_id in range(5):
                start_time = time.time()
                response = client.get("/api/v2/products/search", params={
                    "query": f"user {user_id} search {search_id}",
                    "limit": 10
                })
                end_time = time.time()
                
                session_results.append({
                    "user_id": user_id,
                    "search_id": search_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
                
                # Small delay between requests
                time.sleep(0.1)
            
            return session_results
        
        # Simulate 20 concurrent users
        num_users = 20
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_session, i) for i in range(num_users)]
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        # Analyze user session performance
        successful_requests = [r for r in all_results if r["status_code"] == 200]
        response_times = [r["response_time"] for r in successful_requests]
        
        assert len(successful_requests) >= num_users * 5 * 0.9  # 90% success rate
        assert statistics.mean(response_times) < 1.5  # Average response time < 1.5s
        assert max(response_times) < 5.0  # Max response time < 5s
    
    def test_database_connection_pool_performance(self, db_session, sample_products):
        """Test database connection pool performance under load."""
        def database_operation(operation_id):
            """Perform database operation with connection pooling."""
            db = SessionLocal()
            try:
                start_time = time.time()
                
                # Multiple queries to test connection reuse
                for i in range(5):
                    products = db.query(Product).filter(
                        Product.category == f"Category {operation_id % 5}"
                    ).limit(10).all()
                
                end_time = time.time()
                return {
                    "operation_id": operation_id,
                    "response_time": end_time - start_time,
                    "success": True
                }
            except Exception as e:
                return {
                    "operation_id": operation_id,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
            finally:
                db.close()
        
        # Test with 30 concurrent operations
        num_operations = 30
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_operations) as executor:
            futures = [executor.submit(database_operation, i) for i in range(num_operations)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze connection pool performance
        successful_operations = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_operations]
        
        assert len(successful_operations) >= num_operations * 0.95  # 95% success rate
        assert statistics.mean(response_times) < 1.0  # Average operation < 1s
    
    def test_cache_hit_rate_performance(self, client, db_session, sample_products):
        """Test cache hit rate performance."""
        cache_service = service_factory.get_cache_service()
        
        # Clear cache
        cache_service.clear()
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get("/api/v2/products/search", params={
            "query": "cache hit rate test",
            "limit": 10
        })
        cache_miss_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = client.get("/api/v2/products/search", params={
            "query": "cache hit rate test",
            "limit": 10
        })
        cache_hit_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Cache hit should be significantly faster
        assert cache_hit_time < cache_miss_time * 0.5  # At least 50% faster
        
        # Verify cache hit rate
        cache_stats = cache_service.get_stats()
        assert cache_stats["hits"] > 0
        assert cache_stats["misses"] > 0
    
    def test_background_task_performance(self, client, db_session, sample_products):
        """Test background task performance under load."""
        initial_analytics_count = db_session.query(SearchAnalytics).count()
        
        # Make multiple requests to trigger background tasks
        for i in range(20):
            response = client.get("/api/v2/products/search", params={
                "query": f"background task test {i}",
                "limit": 10
            })
            assert response.status_code == 200
        
        # Wait for background tasks to complete
        time.sleep(2)
        
        # Verify background tasks were processed
        final_analytics_count = db_session.query(SearchAnalytics).count()
        assert final_analytics_count >= initial_analytics_count + 15  # Most tasks processed
    
    def test_error_recovery_performance(self, client, db_session, sample_products):
        """Test performance during error recovery scenarios."""
        # Mock services to fail intermittently
        with patch('services.ai_search_service.AISearchService.search_products') as mock_ai:
            # Make some requests fail, some succeed
            mock_ai.side_effect = [
                Exception("AI service error"),  # First request fails
                {"products": [{"id": 1, "title": "Test Product", "price": 29.99}], "total": 1},  # Second succeeds
                Exception("AI service error"),  # Third fails
                {"products": [{"id": 2, "title": "Test Product 2", "price": 39.99}], "total": 1}  # Fourth succeeds
            ]
            
            response_times = []
            successful_requests = 0
            
            for i in range(4):
                start_time = time.time()
                response = client.get("/api/v2/products/search", params={
                    "query": f"error recovery test {i}",
                    "limit": 10
                })
                end_time = time.time()
                
                response_times.append(end_time - start_time)
                if response.status_code == 200:
                    successful_requests += 1
            
            # Should handle errors gracefully
            assert successful_requests >= 2  # At least half should succeed
            assert all(time < 3.0 for time in response_times)  # All responses < 3s
    
    def test_scalability_test(self, client, db_session, sample_products):
        """Test system scalability with increasing load."""
        load_levels = [5, 10, 20, 30]  # Concurrent requests
        performance_results = {}
        
        for load in load_levels:
            def make_request(request_id):
                start_time = time.time()
                response = client.get("/api/v2/products/search", params={
                    "query": f"scalability test {load} {request_id}",
                    "limit": 10
                })
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                }
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=load) as executor:
                futures = [executor.submit(make_request, i) for i in range(load)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            successful_requests = [r for r in results if r["status_code"] == 200]
            avg_response_time = statistics.mean([r["response_time"] for r in successful_requests])
            
            performance_results[load] = {
                "success_rate": len(successful_requests) / load,
                "avg_response_time": avg_response_time
            }
        
        # Verify scalability characteristics
        for load, metrics in performance_results.items():
            assert metrics["success_rate"] >= 0.8  # At least 80% success rate
            assert metrics["avg_response_time"] < 3.0  # Average response time < 3s
        
        # Performance should degrade gracefully (not exponentially)
        response_times = [metrics["avg_response_time"] for metrics in performance_results.values()]
        assert response_times[-1] < response_times[0] * 3  # Max 3x degradation 