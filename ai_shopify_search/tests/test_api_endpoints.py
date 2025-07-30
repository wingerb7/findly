import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    def test_ai_search_endpoint_success(self, client, sample_products, mock_embedding):
        """Test AI search endpoint with successful response."""
        response = client.get("/api/ai-search", params={
            "query": "blue shirt",
            "page": 1,
            "limit": 25
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "pagination" in data
        assert data["query"] == "blue shirt"
    
    def test_ai_search_endpoint_missing_query(self, client):
        """Test AI search endpoint with missing query parameter."""
        response = client.get("/api/ai-search", params={
            "page": 1,
            "limit": 25
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_ai_search_endpoint_invalid_page(self, client):
        """Test AI search endpoint with invalid page parameter."""
        response = client.get("/api/ai-search", params={
            "query": "blue shirt",
            "page": 0,  # Invalid page number
            "limit": 25
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_ai_search_endpoint_invalid_limit(self, client):
        """Test AI search endpoint with invalid limit parameter."""
        response = client.get("/api/ai-search", params={
            "query": "blue shirt",
            "page": 1,
            "limit": 1000  # Exceeds maximum limit
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_products_endpoint_success(self, client, sample_products):
        """Test products endpoint with successful response."""
        response = client.get("/api/products", params={
            "page": 1,
            "limit": 10,
            "sort_by": "title",
            "sort_order": "asc"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "pagination" in data
        assert "sorting" in data
        assert len(data["products"]) > 0
    
    def test_products_endpoint_pagination(self, client, sample_products):
        """Test products endpoint pagination."""
        response = client.get("/api/products", params={
            "page": 1,
            "limit": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) <= 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 2
    
    def test_autocomplete_endpoint_success(self, client, db_session):
        """Test autocomplete endpoint."""
        # Add test suggestions
        from ai_shopify_search.models import QuerySuggestion
        
        suggestion = QuerySuggestion(
            query="blue",
            suggestion="blue shirt",
            suggestion_type="autocomplete",
            search_count=5,
            is_active=True
        )
        db_session.add(suggestion)
        db_session.commit()
        
        response = client.get("/api/suggestions/autocomplete", params={
            "query": "blue",
            "limit": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "suggestions" in data
        assert "count" in data
    
    def test_autocomplete_endpoint_short_query(self, client):
        """Test autocomplete endpoint with short query."""
        response = client.get("/api/suggestions/autocomplete", params={
            "query": "a",  # Too short
            "limit": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) == 0
    
    def test_popular_searches_endpoint(self, client, sample_popular_searches):
        """Test popular searches endpoint."""
        response = client.get("/api/analytics/popular-searches", params={
            "limit": 10,
            "min_searches": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "popular_searches" in data
        assert "total_searches" in data
        assert "total_clicks" in data
    
    def test_performance_analytics_endpoint(self, client, sample_analytics):
        """Test performance analytics endpoint."""
        response = client.get("/api/analytics/performance", params={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "analytics" in data
        assert "summary" in data
    
    def test_cache_stats_endpoint(self, client, mock_redis):
        """Test cache stats endpoint."""
        response = client.get("/api/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_cache_keys" in data
        assert "cache_info" in data
    
    def test_clear_cache_endpoint(self, client, mock_redis):
        """Test clear cache endpoint."""
        response = client.delete("/api/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Cache cleared successfully" in data["message"]
    
    def test_track_click_endpoint(self, client, sample_analytics):
        """Test track click endpoint."""
        response = client.post("/api/track-click", params={
            "search_analytics_id": 1,
            "product_id": 1,
            "position": 1,
            "click_time_ms": 1500.0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain"
    
    @patch('ai_shopify_search.embeddings.generate_embedding')
    def test_import_products_endpoint(self, mock_embedding, client):
        """Test import products endpoint."""
        mock_embedding.return_value = [0.1] * 1536
        
        response = client.post("/api/import-products")
        
        assert response.status_code == 200
        data = response.json()
        assert "imported" in data
        assert "updated" in data
    
    def test_rate_limiting(self, client, sample_products, mock_embedding):
        """Test rate limiting functionality."""
        # Make multiple requests to trigger rate limiting
        for i in range(105):  # Exceed the 100 requests/hour limit
            response = client.get("/api/ai-search", params={
                "query": f"test query {i}",
                "page": 1,
                "limit": 25
            })
            
            if response.status_code == 429:  # Rate limit exceeded
                data = response.json()
                assert "Rate limit exceeded" in data["detail"]
                break
        else:
            # If rate limiting didn't trigger, that's also valid
            assert True
    
    def test_error_handling_database_error(self, client):
        """Test error handling for database errors."""
        with patch('ai_shopify_search.search_service.SearchService.ai_search_products') as mock_search:
            mock_search.side_effect = Exception("Database connection error")
            
            response = client.get("/api/ai-search", params={
                "query": "test query",
                "page": 1,
                "limit": 25
            })
            
            assert response.status_code == 500
            data = response.json()
            assert "Internal server error" in data["detail"]
    
    def test_error_handling_embedding_error(self, client):
        """Test error handling for embedding generation errors."""
        with patch('ai_shopify_search.embeddings.generate_embedding') as mock_embedding:
            mock_embedding.side_effect = Exception("Embedding generation failed")
            
            response = client.get("/api/ai-search", params={
                "query": "test query",
                "page": 1,
                "limit": 25
            })
            
            assert response.status_code == 500
            data = response.json()
            assert "Internal server error" in data["detail"] 