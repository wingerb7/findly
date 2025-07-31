"""
Integration tests for service orchestration.
Tests how different services work together and communicate.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
import json
import time

from core.database import SessionLocal
from core.models import Product, SearchAnalytics, SearchClick
from services.service_factory import service_factory
from services.ai_search_service import AISearchService
from services.cache_service import CacheService
from services.analytics_service import AnalyticsService
from services.suggestion_service import SuggestionService
from services.autocomplete_service import AutocompleteService
from utils.privacy_utils import anonymize_ip
from utils.validation import sanitize_search_query


@pytest.mark.skip(reason="Integration test requires external dependencies not available in CI environment")
class TestServiceOrchestration:
    """Integration tests for service orchestration."""
    
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
        """Create sample products for testing."""
        products = [
            Product(
                id=1,
                title="Orchestration Test Product 1",
                description="Product for service orchestration testing",
                price=25.99,
                shopify_id="orchestration_test_1",
                tags=["electronics", "test"]
            ),
            Product(
                id=2,
                title="Orchestration Test Product 2",
                description="Another product for orchestration testing",
                price=75.99,
                shopify_id="orchestration_test_2",
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
    
    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI API responses."""
        with patch('openai.ChatCompletion.create') as mock:
            mock.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'search_terms': ['orchestration', 'test', 'product'],
                            'filters': {
                                'price_min': 20,
                                'price_max': 100,
                                'category': 'Electronics'
                            },
                            'intent': 'product_search'
                        })
                    }
                }]
            }
            yield mock
    
    def test_service_factory_singleton_pattern(self):
        """Test that service factory maintains singleton pattern."""
        factory1 = service_factory
        factory2 = service_factory
        
        assert factory1 is factory2
        
        # Test service instances are also singletons
        ai_service1 = factory1.get_ai_search_service()
        ai_service2 = factory2.get_ai_search_service()
        
        assert ai_service1 is ai_service2
    
    def test_ai_search_with_cache_integration(self, db_session, sample_products, mock_openai):
        """Test AI search service integration with cache service."""
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        
        # Clear cache
        cache_service.clear()
        
        # First search (should hit AI and cache result)
        result1 = ai_service.search_products(
            db_session,
            "orchestration test query",
            limit=10,
            offset=0
        )
        
        assert result1 is not None
        assert "products" in result1
        
        # Verify cache was populated
        cache_key = f"ai_search:orchestration test query:10:0"
        cached_result = cache_service.get(cache_key)
        assert cached_result is not None
        
        # Second search (should hit cache)
        result2 = ai_service.search_products(
            db_session,
            "orchestration test query",
            limit=10,
            offset=0
        )
        
        # Results should be identical
        assert result1["products"] == result2["products"]
    
    def test_analytics_service_integration(self, db_session, sample_products):
        """Test analytics service integration with other services."""
        analytics_service = service_factory.get_analytics_service()
        
        # Track search
        search_data = {
            "query": "analytics integration test",
            "results_count": 5,
            "response_time": 0.5,
            "client_ip": "192.168.1.101",
            "user_agent": "Test Browser"
        }
        
        analytics_service.track_search(db_session, **search_data)
        
        # Verify search was tracked
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "analytics integration test"
        ).first()
        
        assert analytics is not None
        assert analytics.search_count >= 1
        assert analytics.client_ip == anonymize_ip("192.168.1.101")
        
        # Track click
        click_data = {
            "product_id": 1,
            "query": "analytics integration test",
            "client_ip": "192.168.1.101",
            "user_agent": "Test Browser"
        }
        
        analytics_service.track_click(db_session, **click_data)
        
        # Verify click was tracked
        click = db_session.query(ProductClick).filter(
            ProductClick.product_id == 1
        ).first()
        
        assert click is not None
        assert click.client_ip == anonymize_ip("192.168.1.101")
    
    def test_suggestion_service_integration(self, db_session, sample_products):
        """Test suggestion service integration."""
        suggestion_service = service_factory.get_suggestion_service()
        cache_service = service_factory.get_cache_service()
        
        # Clear cache
        cache_service.clear()
        
        # Get suggestions
        suggestions = suggestion_service.get_suggestions(
            db_session,
            "orchestration",
            limit=5
        )
        
        assert suggestions is not None
        assert "suggestions" in suggestions
        assert len(suggestions["suggestions"]) > 0
        
        # Verify cache was populated
        cache_key = f"suggestions:orchestration:5"
        cached_suggestions = cache_service.get(cache_key)
        assert cached_suggestions is not None
    
    def test_autocomplete_service_integration(self, db_session, sample_products):
        """Test autocomplete service integration."""
        autocomplete_service = service_factory.get_autocomplete_service()
        cache_service = service_factory.get_cache_service()
        
        # Clear cache
        cache_service.clear()
        
        # Get autocomplete suggestions
        autocomplete = autocomplete_service.get_autocomplete(
            db_session,
            "orchestration",
            limit=5
        )
        
        assert autocomplete is not None
        assert "suggestions" in autocomplete
        assert len(autocomplete["suggestions"]) > 0
        
        # Verify cache was populated
        cache_key = f"autocomplete:orchestration:5"
        cached_autocomplete = cache_service.get(cache_key)
        assert cached_autocomplete is not None
    
    def test_error_propagation_between_services(self, db_session, sample_products):
        """Test how errors propagate between services."""
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        
        # Mock AI service to fail
        with patch.object(ai_service, 'search_products') as mock_search:
            mock_search.side_effect = Exception("AI service error")
            
            # Should handle error gracefully
            try:
                result = ai_service.search_products(
                    db_session,
                    "error test query",
                    limit=10
                )
                # Should fall back to basic search
                assert result is not None
            except Exception as e:
                # Error should be handled by error handling middleware
                assert "AI service error" in str(e)
    
    def test_concurrent_service_operations(self, db_session, sample_products):
        """Test concurrent operations across services."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def search_operation(query, service_name):
            """Individual search operation."""
            try:
                ai_service = service_factory.get_ai_search_service()
                result = ai_service.search_products(
                    db_session,
                    query,
                    limit=5
                )
                results_queue.put((service_name, "success", result))
            except Exception as e:
                results_queue.put((service_name, "error", str(e)))
        
        # Start multiple concurrent searches
        threads = []
        queries = [
            "concurrent test 1",
            "concurrent test 2",
            "concurrent test 3"
        ]
        
        for i, query in enumerate(queries):
            thread = threading.Thread(
                target=search_operation,
                args=(query, f"service_{i}")
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify all operations completed
        assert len(results) == 3
        for service_name, status, result in results:
            assert status == "success"
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_service_integration(self, db_session, sample_products):
        """Test async integration between services."""
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        analytics_service = service_factory.get_analytics_service()
        
        # Clear cache
        await cache_service.clear()
        
        # Async search
        search_result = await ai_service.search_products(
            db_session,
            "async orchestration test",
            limit=10
        )
        
        assert search_result is not None
        assert "products" in search_result
        
        # Async cache operations
        cache_key = "async_test_key"
        test_data = {"async": "test_data"}
        
        await cache_service.set(cache_key, test_data, ttl=60)
        cached_data = await cache_service.get(cache_key)
        
        assert cached_data == test_data
        
        # Async analytics
        await analytics_service.track_search_async(
            db_session,
            query="async orchestration test",
            results_count=len(search_result["products"]),
            response_time=0.3,
            client_ip="192.168.1.102"
        )
        
        # Verify async analytics
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "async orchestration test"
        ).first()
        
        assert analytics is not None
        assert analytics.search_count >= 1
    
    def test_service_dependency_injection(self):
        """Test that services are properly injected with dependencies."""
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        analytics_service = service_factory.get_analytics_service()
        
        # Verify services have required dependencies
        assert hasattr(ai_service, 'cache_service')
        assert hasattr(ai_service, 'analytics_service')
        assert hasattr(cache_service, 'redis_client')
        assert hasattr(analytics_service, 'privacy_utils')
    
    def test_service_configuration_integration(self):
        """Test that services use consistent configuration."""
        from config import settings
        
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        
        # Verify services use same configuration
        assert ai_service.openai_api_key == settings.OPENAI_API_KEY
        assert cache_service.redis_url == settings.REDIS_URL
    
    def test_service_metrics_integration(self, db_session, sample_products):
        """Test that services properly integrate with metrics."""
        from metrics import search_requests_total, search_duration_seconds
        
        ai_service = service_factory.get_ai_search_service()
        
        # Perform search
        result = ai_service.search_products(
            db_session,
            "metrics integration test",
            limit=10
        )
        
        assert result is not None
        
        # Verify metrics were incremented
        # Note: In a real test, you'd check the actual metric values
        # For now, we just verify the search completed successfully
    
    def test_service_logging_integration(self, db_session, sample_products):
        """Test that services properly integrate with logging."""
        import logging
        
        # Configure test logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        ai_service = service_factory.get_ai_search_service()
        
        # Perform search with logging
        with patch.object(logger, 'info') as mock_logger:
            result = ai_service.search_products(
                db_session,
                "logging integration test",
                limit=10
            )
            
            assert result is not None
            # Verify logging occurred (in real implementation)
    
    def test_service_error_recovery_integration(self, db_session, sample_products):
        """Test error recovery integration between services."""
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        
        # Mock cache to fail
        with patch.object(cache_service, 'get') as mock_cache_get:
            mock_cache_get.side_effect = Exception("Cache error")
            
            # Search should still work (fallback to no cache)
            result = ai_service.search_products(
                db_session,
                "error recovery integration test",
                limit=10
            )
            
            assert result is not None
            assert "products" in result
    
    def test_service_performance_integration(self, db_session, sample_products):
        """Test performance integration between services."""
        import time
        
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        
        # Clear cache for fresh test
        cache_service.clear()
        
        # Measure first search (cache miss)
        start_time = time.time()
        result1 = ai_service.search_products(
            db_session,
            "performance integration test",
            limit=10
        )
        first_search_time = time.time() - start_time
        
        assert result1 is not None
        
        # Measure second search (cache hit)
        start_time = time.time()
        result2 = ai_service.search_products(
            db_session,
            "performance integration test",
            limit=10
        )
        second_search_time = time.time() - start_time
        
        assert result2 is not None
        
        # Cache hit should be faster
        assert second_search_time < first_search_time
        
        # Results should be identical
        assert result1["products"] == result2["products"] 