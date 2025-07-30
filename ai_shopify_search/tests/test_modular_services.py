"""
Comprehensive tests for modular search services.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from search_service_modular import ModularSearchService
from services.ai_search_service import AISearchService
from services.suggestion_service import SuggestionService
from services.autocomplete_service import AutocompleteService
from services.cache_service import CacheService
from services.analytics_service import AnalyticsService
from database_async import AsyncDatabaseService


class TestModularSearchService:
    """Test cases for ModularSearchService."""
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        cache_service = Mock(spec=CacheService)
        cache_service.get = AsyncMock(return_value=None)
        cache_service.set = AsyncMock()
        return cache_service
    
    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service."""
        analytics_service = Mock(spec=AnalyticsService)
        analytics_service.track_search = AsyncMock(return_value="test_analytics_id")
        return analytics_service
    
    @pytest.fixture
    def mock_ai_search_service(self, mock_cache_service, mock_analytics_service):
        """Mock AI search service."""
        ai_service = Mock(spec=AISearchService)
        ai_service.search_products = AsyncMock(return_value={
            "query": "test query",
            "results": [{"id": 1, "title": "Test Product"}],
            "count": 1,
            "total_count": 1,
            "page": 1,
            "total_pages": 1,
            "limit": 25
        })
        ai_service.search_with_fallback = AsyncMock(return_value={
            "query": "test query",
            "results": [{"id": 1, "title": "Test Product"}],
            "count": 1,
            "search_type": "ai"
        })
        return ai_service
    
    @pytest.fixture
    def mock_suggestion_service(self, mock_cache_service):
        """Mock suggestion service."""
        suggestion_service = Mock(spec=SuggestionService)
        suggestion_service.get_popular_suggestions = AsyncMock(return_value=[
            {"suggestion": "popular1", "type": "popular", "search_count": 10}
        ])
        suggestion_service.get_related_suggestions = AsyncMock(return_value=[
            {"suggestion": "related1", "type": "related", "overlap_score": 0.8}
        ])
        suggestion_service.generate_suggestions_from_products = AsyncMock(return_value=[
            "product1", "product2"
        ])
        suggestion_service.get_query_corrections = AsyncMock(return_value=[
            {"original": "test", "corrected": "test", "confidence": 0.9}
        ])
        suggestion_service.get_cheapest_product_suggestions = AsyncMock(return_value=[
            {"suggestion": "cheap1", "type": "cheapest", "price": 10.0}
        ])
        return suggestion_service
    
    @pytest.fixture
    def mock_autocomplete_service(self, mock_cache_service):
        """Mock autocomplete service."""
        autocomplete_service = Mock(spec=AutocompleteService)
        autocomplete_service.get_autocomplete_suggestions = AsyncMock(return_value=[
            {"suggestion": "auto1", "type": "autocomplete", "relevance_score": 0.8}
        ])
        autocomplete_service.get_autocomplete_with_price_filter = AsyncMock(return_value=[
            {"suggestion": "auto_price1", "type": "autocomplete", "avg_price": 50.0}
        ])
        autocomplete_service.get_popular_with_price_filter = AsyncMock(return_value=[
            {"suggestion": "popular_price1", "type": "popular", "avg_price": 75.0}
        ])
        autocomplete_service.get_related_with_price_filter = AsyncMock(return_value=[
            {"suggestion": "related_price1", "type": "related", "relevance_score": 0.7}
        ])
        return autocomplete_service
    
    @pytest.fixture
    def modular_search_service(
        self,
        mock_ai_search_service,
        mock_suggestion_service,
        mock_autocomplete_service,
        mock_cache_service,
        mock_analytics_service
    ):
        """Create ModularSearchService with mocked dependencies."""
        service = ModularSearchService()
        service.ai_search_service = mock_ai_search_service
        service.suggestion_service = mock_suggestion_service
        service.autocomplete_service = mock_autocomplete_service
        service.cache_service = mock_cache_service
        service.analytics_service = mock_analytics_service
        return service
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, modular_search_service, mock_db_session):
        """Test successful product search."""
        query = "test query"
        page = 1
        limit = 25
        
        result = await modular_search_service.search_products(
            db=mock_db_session,
            query=query,
            page=page,
            limit=limit
        )
        
        assert result["query"] == query
        assert "results" in result
        assert "service_type" in result
        assert result["service_type"] == "modular"
        assert "response_time_ms" in result
        assert result["count"] == 1
        
        # Verify AI search service was called
        modular_search_service.ai_search_service.search_products.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_products_with_price_filter(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test product search with price filtering."""
        query = "test query"
        min_price = 10.0
        max_price = 100.0
        
        result = await modular_search_service.search_products(
            db=mock_db_session,
            query=query,
            min_price=min_price,
            max_price=max_price
        )
        
        assert result["query"] == query
        
        # Verify AI search service was called with price filters
        call_args = modular_search_service.ai_search_service.search_products.call_args
        assert call_args[1]["min_price"] == min_price
        assert call_args[1]["max_price"] == max_price
    
    @pytest.mark.asyncio
    async def test_get_suggestions_comprehensive(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test comprehensive suggestions retrieval."""
        query = "test"
        limit = 10
        
        result = await modular_search_service.get_suggestions(
            db=mock_db_session,
            query=query,
            limit=limit
        )
        
        assert result["query"] == query
        assert "suggestions" in result
        assert "count" in result
        assert "price_filter" in result
        assert len(result["suggestions"]) > 0
        
        # Verify services were called
        modular_search_service.autocomplete_service.get_autocomplete_suggestions.assert_called_once()
        modular_search_service.suggestion_service.get_popular_suggestions.assert_called_once()
        modular_search_service.suggestion_service.get_related_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_suggestions_with_price_filter(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test suggestions with price filtering."""
        query = "test"
        limit = 10
        min_price = 10.0
        max_price = 100.0
        
        result = await modular_search_service.get_suggestions(
            db=mock_db_session,
            query=query,
            limit=limit,
            min_price=min_price,
            max_price=max_price
        )
        
        assert result["price_filter"]["min_price"] == min_price
        assert result["price_filter"]["max_price"] == max_price
        assert result["price_filter"]["applied"] is True
    
    @pytest.mark.asyncio
    async def test_get_autocomplete_basic(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test basic autocomplete functionality."""
        query = "test"
        limit = 5
        
        result = await modular_search_service.get_autocomplete(
            db=mock_db_session,
            query=query,
            limit=limit
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        
        # Verify autocomplete service was called
        modular_search_service.autocomplete_service.get_autocomplete_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_autocomplete_with_price_filter(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test autocomplete with price filtering."""
        query = "test"
        limit = 5
        min_price = 10.0
        max_price = 100.0
        
        result = await modular_search_service.get_autocomplete(
            db=mock_db_session,
            query=query,
            limit=limit,
            min_price=min_price,
            max_price=max_price
        )
        
        assert isinstance(result, list)
        
        # Verify price filter service was called
        modular_search_service.autocomplete_service.get_autocomplete_with_price_filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_popular_suggestions(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test popular suggestions retrieval."""
        limit = 5
        
        result = await modular_search_service.get_popular_suggestions(
            db=mock_db_session,
            limit=limit
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        
        # Verify suggestion service was called
        modular_search_service.suggestion_service.get_popular_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_popular_suggestions_with_price_filter(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test popular suggestions with price filtering."""
        limit = 5
        min_price = 10.0
        max_price = 100.0
        
        result = await modular_search_service.get_popular_suggestions(
            db=mock_db_session,
            limit=limit,
            min_price=min_price,
            max_price=max_price
        )
        
        assert isinstance(result, list)
        
        # Verify price filter service was called
        modular_search_service.autocomplete_service.get_popular_with_price_filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_related_suggestions(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test related suggestions retrieval."""
        query = "test"
        limit = 5
        
        result = await modular_search_service.get_related_suggestions(
            db=mock_db_session,
            query=query,
            limit=limit
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        
        # Verify suggestion service was called
        modular_search_service.suggestion_service.get_related_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_related_suggestions_with_price_filter(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test related suggestions with price filtering."""
        query = "test"
        limit = 5
        min_price = 10.0
        max_price = 100.0
        
        result = await modular_search_service.get_related_suggestions(
            db=mock_db_session,
            query=query,
            limit=limit,
            min_price=min_price,
            max_price=max_price
        )
        
        assert isinstance(result, list)
        
        # Verify price filter service was called
        modular_search_service.autocomplete_service.get_related_with_price_filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_query_corrections(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test query corrections retrieval."""
        query = "test"
        
        result = await modular_search_service.get_query_corrections(
            db=mock_db_session,
            query=query
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("original" in item for item in result)
        assert all("corrected" in item for item in result)
        
        # Verify suggestion service was called
        modular_search_service.suggestion_service.get_query_corrections.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cheapest_suggestions(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test cheapest suggestions retrieval."""
        limit = 5
        
        result = await modular_search_service.get_cheapest_suggestions(
            db=mock_db_session,
            limit=limit
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        assert all("price" in item for item in result)
        
        # Verify suggestion service was called
        modular_search_service.suggestion_service.get_cheapest_product_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_fallback(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test search with fallback functionality."""
        query = "test query"
        page = 1
        limit = 25
        
        result = await modular_search_service.search_with_fallback(
            db=mock_db_session,
            query=query,
            page=page,
            limit=limit
        )
        
        assert result["query"] == query
        assert "results" in result
        assert "search_type" in result
        
        # Verify AI search service was called
        modular_search_service.ai_search_service.search_with_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_search_products(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test error handling in search products."""
        # Make AI search service raise an exception
        modular_search_service.ai_search_service.search_products.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            await modular_search_service.search_products(
                db=mock_db_session,
                query="test"
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_suggestions(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test error handling in suggestions."""
        # Make autocomplete service raise an exception
        modular_search_service.autocomplete_service.get_autocomplete_suggestions.side_effect = Exception("Test error")
        
        result = await modular_search_service.get_suggestions(
            db=mock_db_session,
            query="test"
        )
        
        assert result["error"] == "Test error"
        assert result["count"] == 0
        assert result["suggestions"] == []
    
    @pytest.mark.asyncio
    async def test_short_query_handling(
        self,
        modular_search_service,
        mock_db_session
    ):
        """Test handling of short queries."""
        query = "a"  # Too short for autocomplete
        
        result = await modular_search_service.get_suggestions(
            db=mock_db_session,
            query=query,
            limit=10
        )
        
        # Should still get popular and related suggestions
        assert result["query"] == query
        assert "suggestions" in result
        
        # Autocomplete service should not be called for short queries
        modular_search_service.autocomplete_service.get_autocomplete_suggestions.assert_not_called()


class TestAsyncDatabaseService:
    """Test cases for AsyncDatabaseService."""
    
    @pytest.fixture
    def async_db_service(self):
        """Create AsyncDatabaseService instance."""
        return AsyncDatabaseService()
    
    @pytest.mark.asyncio
    async def test_initialization(self, async_db_service):
        """Test database service initialization."""
        await async_db_service.initialize()
        
        assert async_db_service.engine is not None
        assert async_db_service.async_session_maker is not None
    
    @pytest.mark.asyncio
    async def test_get_session(self, async_db_service):
        """Test getting database session."""
        await async_db_service.initialize()
        
        async with async_db_service.get_session() as session:
            assert session is not None
            # Session should be committed automatically
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_db_service):
        """Test database health check."""
        await async_db_service.initialize()
        
        is_healthy = await async_db_service.health_check()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_pool_status(self, async_db_service):
        """Test connection pool status."""
        await async_db_service.initialize()
        
        status = await async_db_service.get_pool_status()
        assert isinstance(status, dict)
        assert "pool_size" in status
        assert "checked_in" in status
        assert "checked_out" in status
    
    @pytest.mark.asyncio
    async def test_close(self, async_db_service):
        """Test closing database service."""
        await async_db_service.initialize()
        await async_db_service.close()
        
        # Engine should be disposed
        assert async_db_service.engine is None


class TestServiceFactory:
    """Test cases for ServiceFactory."""
    
    @pytest.fixture
    def service_factory(self):
        """Create ServiceFactory instance."""
        from services import ServiceFactory
        return ServiceFactory()
    
    def test_get_ai_search_service(self, service_factory):
        """Test getting AI search service."""
        service = service_factory.get_ai_search_service()
        assert isinstance(service, AISearchService)
    
    def test_get_suggestion_service(self, service_factory):
        """Test getting suggestion service."""
        service = service_factory.get_suggestion_service()
        assert isinstance(service, SuggestionService)
    
    def test_get_autocomplete_service(self, service_factory):
        """Test getting autocomplete service."""
        service = service_factory.get_autocomplete_service()
        assert isinstance(service, AutocompleteService)
    
    def test_get_cache_service(self, service_factory):
        """Test getting cache service."""
        service = service_factory.get_cache_service()
        assert isinstance(service, CacheService)
    
    def test_get_analytics_service(self, service_factory):
        """Test getting analytics service."""
        service = service_factory.get_analytics_service()
        assert isinstance(service, AnalyticsService)
    
    def test_service_singleton_behavior(self, service_factory):
        """Test that services are singleton instances."""
        service1 = service_factory.get_ai_search_service()
        service2 = service_factory.get_ai_search_service()
        assert service1 is service2
    
    def test_service_dependencies(self, service_factory):
        """Test that services have proper dependencies."""
        ai_service = service_factory.get_ai_search_service()
        cache_service = service_factory.get_cache_service()
        analytics_service = service_factory.get_analytics_service()
        
        assert ai_service.cache_service is cache_service
        assert ai_service.analytics_service is analytics_service 