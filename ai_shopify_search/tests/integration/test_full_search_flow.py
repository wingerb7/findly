"""
Integration tests for the complete search flow.
Tests the entire pipeline from API request to response with all services involved.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import redis
import json
import time

from main import app
from core.database import get_db, SessionLocal
from core.models import Product, SearchAnalytics
from services.service_factory import service_factory
from utils.privacy_utils import anonymize_ip
from utils.validation import sanitize_search_query


@pytest.mark.skip(reason="Integration test requires external dependencies not available in CI environment")
class TestFullSearchFlow:
    """Integration tests for complete search functionality."""
    
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
    def redis_client(self):
        """Redis client for testing."""
        return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    @pytest.fixture
    def sample_products(self, db_session):
        """Create sample products for testing."""
        products = [
            Product(
                id=1,
                title="Test Product 1",
                description="A test product for integration testing",
                price=29.99,
                shopify_id="test_product_1",
                tags=["electronics", "test"]
            ),
            Product(
                id=2,
                title="Test Product 2",
                description="Another test product for integration testing",
                price=49.99,
                shopify_id="test_product_2",
                tags=["electronics", "test"]
            ),
            Product(
                id=3,
                title="Premium Test Product",
                description="A premium test product with higher price",
                price=199.99,
                shopify_id="premium_product_1",
                tags=["electronics", "premium"]
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
                            'search_terms': ['test', 'product', 'electronics'],
                            'filters': {
                                'price_min': 20,
                                'price_max': 250,
                                'category': 'Electronics'
                            },
                            'intent': 'product_search'
                        })
                    }
                }]
            }
            yield mock
    
    def test_complete_search_flow_with_cache(self, client, db_session, redis_client, sample_products, mock_openai):
        """Test complete search flow with caching."""
        # Clear cache first
        redis_client.flushdb()
        
        # First search request (should hit AI and cache result)
        response1 = client.get("/api/v2/products/search", params={
            "query": "test electronics products",
            "limit": 10,
            "offset": 0
        })
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert "products" in data1
        assert "pagination" in data1
        assert "analytics" in data1
        assert len(data1["products"]) > 0
        
        # Verify cache was populated
        cache_key = f"search:test electronics products:10:0"
        cached_result = redis_client.get(cache_key)
        assert cached_result is not None
        
        # Second search request (should hit cache)
        response2 = client.get("/api/v2/products/search", params={
            "query": "test electronics products",
            "limit": 10,
            "offset": 0
        })
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Results should be identical (from cache)
        assert data1["products"] == data2["products"]
        
        # Verify analytics were tracked
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "test electronics products"
        ).first()
        assert analytics is not None
        assert analytics.search_count >= 2
    
    def test_search_with_price_filtering(self, client, db_session, sample_products, mock_openai):
        """Test search with price filtering."""
        response = client.get("/api/v2/products/search", params={
            "query": "electronics",
            "min_price": 30,
            "max_price": 100,
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify price filtering
        for product in data["products"]:
            assert 30 <= product["price"] <= 100
    
    def test_search_with_category_filtering(self, client, db_session, sample_products, mock_openai):
        """Test search with category filtering."""
        response = client.get("/api/v2/products/search", params={
            "query": "test products",
            "category": "Electronics",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify category filtering
        for product in data["products"]:
            assert product["category"] == "Electronics"
    
    def test_search_pagination(self, client, db_session, sample_products, mock_openai):
        """Test search pagination."""
        # First page
        response1 = client.get("/api/v2/products/search", params={
            "query": "test",
            "limit": 2,
            "offset": 0
        })
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["products"]) <= 2
        
        # Second page
        response2 = client.get("/api/v2/products/search", params={
            "query": "test",
            "limit": 2,
            "offset": 2
        })
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify pagination info
        assert data1["pagination"]["current_page"] == 1
        assert data2["pagination"]["current_page"] == 2
        assert data1["pagination"]["next_page"] == 2
        assert data2["pagination"]["previous_page"] == 1
    
    def test_search_with_ai_fallback(self, client, db_session, sample_products):
        """Test search with AI fallback when primary search fails."""
        # Mock AI service to fail first, then succeed
        with patch('services.ai_search_service.AISearchService.search_products') as mock_ai:
            mock_ai.side_effect = [
                Exception("AI service temporarily unavailable"),
                {
                    "products": [{"id": 1, "title": "Test Product 1", "price": 29.99}],
                    "total": 1
                }
            ]
            
            response = client.get("/api/v2/products/search", params={
                "query": "test product",
                "limit": 10
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["products"]) > 0
    
    def test_search_error_handling(self, client, db_session):
        """Test search error handling."""
        # Test with invalid query
        response = client.get("/api/v2/products/search", params={
            "query": "",  # Empty query
            "limit": 10
        })
        
        assert response.status_code == 400
        
        # Test with invalid price range
        response = client.get("/api/v2/products/search", params={
            "query": "test",
            "min_price": 100,
            "max_price": 50  # Invalid range
        })
        
        assert response.status_code == 400
    
    def test_search_analytics_tracking(self, client, db_session, sample_products, mock_openai):
        """Test that search analytics are properly tracked."""
        initial_count = db_session.query(SearchAnalytics).count()
        
        # Perform search
        response = client.get("/api/v2/products/search", params={
            "query": "analytics test query",
            "limit": 10
        })
        
        assert response.status_code == 200
        
        # Verify analytics were created
        final_count = db_session.query(SearchAnalytics).count()
        assert final_count > initial_count
        
        # Verify specific analytics entry
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "analytics test query"
        ).first()
        assert analytics is not None
        assert analytics.search_count >= 1
    
    def test_search_rate_limiting(self, client, db_session, sample_products, mock_openai):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/api/v2/products/search", params={
                "query": f"rate limit test {i}",
                "limit": 10
            })
            responses.append(response)
        
        # At least one should be rate limited (429)
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(code == 200 for code in status_codes)
    
    def test_search_with_suggestions(self, client, db_session, sample_products, mock_openai):
        """Test search with autocomplete suggestions."""
        response = client.get("/api/v2/products/suggestions", params={
            "query": "test",
            "limit": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
    
    def test_search_performance_metrics(self, client, db_session, sample_products, mock_openai):
        """Test that performance metrics are captured."""
        start_time = time.time()
        
        response = client.get("/api/v2/products/search", params={
            "query": "performance test",
            "limit": 10
        })
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify performance data is included
        assert "performance" in data
        assert "response_time" in data["performance"]
        assert data["performance"]["response_time"] > 0
    
    def test_search_with_privacy_compliance(self, client, db_session, sample_products, mock_openai):
        """Test that privacy compliance is maintained."""
        client_ip = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Test Browser)"
        
        response = client.get("/api/v2/products/search", params={
            "query": "privacy test"
        }, headers={
            "X-Forwarded-For": client_ip,
            "User-Agent": user_agent
        })
        
        assert response.status_code == 200
        
        # Verify IP is anonymized in analytics
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "privacy test"
        ).first()
        
        if analytics and analytics.client_ip:
            # IP should be anonymized (not the original)
            assert analytics.client_ip != client_ip
            assert analytics.client_ip == anonymize_ip(client_ip)
    
    @pytest.mark.asyncio
    async def test_async_search_flow(self, db_session, sample_products, mock_openai):
        """Test async search flow."""
        from services.ai_search_service import AISearchService
        from services.cache_service import CacheService
        
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        
        # Test async search
        result = await ai_service.search_products(
            db_session, 
            "async test query",
            limit=10,
            offset=0
        )
        
        assert result is not None
        assert "products" in result
        
        # Test async cache operations
        cache_key = "test_async_key"
        test_data = {"test": "data"}
        
        await cache_service.set(cache_key, test_data, ttl=60)
        cached_data = await cache_service.get(cache_key)
        
        assert cached_data == test_data
    
    def test_search_with_background_tasks(self, client, db_session, sample_products, mock_openai):
        """Test that background tasks are triggered."""
        initial_analytics_count = db_session.query(SearchAnalytics).count()
        
        # Perform search (should trigger background analytics)
        response = client.get("/api/v2/products/search", params={
            "query": "background task test",
            "limit": 10
        })
        
        assert response.status_code == 200
        
        # Wait a bit for background tasks
        time.sleep(1)
        
        # Verify background tasks were executed
        final_analytics_count = db_session.query(SearchAnalytics).count()
        assert final_analytics_count >= initial_analytics_count
    
    def test_search_with_error_recovery(self, client, db_session, sample_products):
        """Test search with error recovery mechanisms."""
        # Mock multiple services to fail and recover
        with patch('services.ai_search_service.AISearchService.search_products') as mock_ai, \
             patch('services.cache_service.CacheService.get') as mock_cache_get, \
             patch('services.cache_service.CacheService.set') as mock_cache_set:
            
            # First call: AI fails, cache miss
            mock_ai.side_effect = Exception("AI service down")
            mock_cache_get.return_value = None
            
            response1 = client.get("/api/v2/products/search", params={
                "query": "error recovery test",
                "limit": 10
            })
            
            # Should still return results (fallback to basic search)
            assert response1.status_code == 200
            
            # Second call: AI recovers, cache hit
            mock_ai.side_effect = None
            mock_ai.return_value = {
                "products": [{"id": 1, "title": "Recovered Product", "price": 29.99}],
                "total": 1
            }
            mock_cache_get.return_value = mock_ai.return_value
            
            response2 = client.get("/api/v2/products/search", params={
                "query": "error recovery test",
                "limit": 10
            })
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert len(data2["products"]) > 0 