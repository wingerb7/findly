"""
Tests for ModularSearchService
Tests the modular search service with proper mocking and async support
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.orm import Session
import time

from search_service_modular import ModularSearchService


class TestModularSearchService:
    """Test suite for ModularSearchService"""
    
    @pytest.fixture
    def search_service(self):
        """Create a ModularSearchService instance with mocked dependencies"""
        with patch('search_service_modular.service_factory') as mock_factory:
            # Mock all service dependencies
            mock_factory.get_ai_search_service.return_value = AsyncMock()
            mock_factory.get_suggestion_service.return_value = AsyncMock()
            mock_factory.get_autocomplete_service.return_value = AsyncMock()
            mock_factory.get_cache_service.return_value = AsyncMock()
            mock_factory.get_analytics_service.return_value = AsyncMock()
            
            service = ModularSearchService()
            return service
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    # Happy Path Tests
    @pytest.mark.asyncio
    async def test_search_products_success(self, search_service, mock_db):
        """Test successful product search"""
        # Arrange
        expected_result = {
            "products": [{"id": 1, "title": "Test Product"}],
            "total": 1,
            "page": 1,
            "limit": 25
        }
        search_service.ai_search_service.search_products.return_value = expected_result
        
        # Act
        result = await search_service.search_products(
            db=mock_db,
            query="test query",
            page=1,
            limit=25
        )
        
        # Assert
        assert result["products"] == expected_result["products"]
        assert result["total"] == expected_result["total"]
        assert result["service_type"] == "modular"
        assert "response_time_ms" in result
        assert result["response_time_ms"] > 0
        
        search_service.ai_search_service.search_products.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_products_with_price_filters(self, search_service, mock_db):
        """Test search with price filters"""
        # Arrange
        expected_result = {"products": [], "total": 0}
        search_service.ai_search_service.search_products.return_value = expected_result
        
        # Act
        result = await search_service.search_products(
            db=mock_db,
            query="shirt",
            min_price=10.0,
            max_price=50.0
        )
        
        # Assert
        call_args = search_service.ai_search_service.search_products.call_args
        assert call_args[1]["min_price"] == 10.0
        assert call_args[1]["max_price"] == 50.0
    
    @pytest.mark.asyncio
    async def test_get_suggestions_success(self, search_service, mock_db):
        """Test successful suggestions retrieval"""
        # Arrange
        mock_suggestions = {
            "autocomplete": ["shirt", "shirts"],
            "popular": ["blue shirt", "white shirt"],
            "related": ["t-shirt", "polo shirt"]
        }
        search_service.suggestion_service.get_suggestions.return_value = mock_suggestions
        
        # Act
        result = await search_service.get_suggestions(
            db=mock_db,
            query="shirt"
        )
        
        # Assert
        # The actual result includes additional metadata, so we check for the expected keys
        assert "suggestions" in result
        assert "query" in result
        assert "count" in result
        assert result["query"] == "shirt"
        search_service.suggestion_service.get_popular_suggestions.assert_called()
    
    # Edge Cases Tests
    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_service, mock_db):
        """Test search with empty query"""
        # Arrange
        expected_result = {"products": [], "total": 0, "error": "Empty query"}
        search_service.ai_search_service.search_products.return_value = expected_result
        
        # Act
        result = await search_service.search_products(
            db=mock_db,
            query=""
        )
        
        # Assert
        assert result["products"] == []
        assert result["total"] == 0
    
    @pytest.mark.asyncio
    async def test_search_very_long_query(self, search_service, mock_db):
        """Test search with very long query (>200 chars)"""
        # Arrange
        long_query = "a" * 250
        expected_result = {"products": [], "total": 0, "error": "Query too long"}
        search_service.ai_search_service.search_products.return_value = expected_result
        
        # Act
        result = await search_service.search_products(
            db=mock_db,
            query=long_query
        )
        
        # Assert
        assert result["products"] == []
        assert result["total"] == 0
    
    @pytest.mark.asyncio
    async def test_search_with_unsupported_filters(self, search_service, mock_db):
        """Test search with unsupported filters"""
        # Arrange
        expected_result = {"products": [], "total": 0, "error": "Unsupported filter"}
        search_service.ai_search_service.search_products.return_value = expected_result
        
        # Act
        result = await search_service.search_products(
            db=mock_db,
            query="shirt",
            min_price=-10.0,  # Invalid negative price
            max_price=1000000.0  # Unrealistic high price
        )
        
        # Assert
        assert result["products"] == []
        assert result["total"] == 0
    
    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_search_database_error(self, search_service, mock_db):
        """Test search when database throws an error"""
        # Arrange
        search_service.ai_search_service.search_products.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await search_service.search_products(
                db=mock_db,
                query="shirt"
            )
        
        assert "Database connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_cache_timeout(self, search_service, mock_db):
        """Test search when cache times out"""
        # Arrange
        search_service.ai_search_service.search_products.side_effect = TimeoutError("Cache timeout")
        
        # Act & Assert
        with pytest.raises(TimeoutError) as exc_info:
            await search_service.search_products(
                db=mock_db,
                query="shirt"
            )
        
        assert "Cache timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_embedding_service_failure(self, search_service, mock_db):
        """Test search when embedding service fails"""
        # Arrange
        search_service.ai_search_service.search_products.side_effect = Exception("Embedding service unavailable")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await search_service.search_products(
                db=mock_db,
                query="shirt"
            )
        
        assert "Embedding service unavailable" in str(exc_info.value)
    
    # Performance Tests
    @pytest.mark.asyncio
    async def test_search_response_time(self, search_service, mock_db):
        """Test that response time is measured correctly"""
        # Arrange
        expected_result = {"products": [], "total": 0}
        search_service.ai_search_service.search_products.return_value = expected_result
        
        # Act
        start_time = time.time()
        result = await search_service.search_products(
            db=mock_db,
            query="shirt"
        )
        end_time = time.time()
        
        # Assert
        actual_time = (end_time - start_time) * 1000
        assert result["response_time_ms"] > 0
        assert result["response_time_ms"] >= actual_time * 0.9  # Allow some tolerance
    
    # Integration Tests
    @pytest.mark.asyncio
    async def test_full_search_flow(self, search_service, mock_db):
        """Test complete search flow with all components"""
        # Arrange
        search_result = {"products": [{"id": 1, "title": "Product"}], "total": 1}
        suggestions_result = {"autocomplete": ["product"], "popular": ["test"]}
        
        search_service.ai_search_service.search_products.return_value = search_result
        search_service.suggestion_service.get_suggestions.return_value = suggestions_result
        
        # Act
        search_response = await search_service.search_products(
            db=mock_db,
            query="test",
            user_agent="TestBot/1.0",
            ip_address="192.168.1.1"
        )
        
        suggestions_response = await search_service.get_suggestions(
            db=mock_db,
            query="test"
        )
        
        # Assert
        assert search_response["products"] == search_result["products"]
        assert "suggestions" in suggestions_response
        assert suggestions_response["query"] == "test"
    
    # Additional Method Tests
    @pytest.mark.asyncio
    async def test_get_autocomplete_success(self, search_service, mock_db):
        """Test successful autocomplete"""
        # Arrange
        expected_suggestions = ["shirt", "shirts", "shirtless"]
        search_service.autocomplete_service.get_autocomplete_suggestions.return_value = expected_suggestions
        
        # Act
        result = await search_service.get_autocomplete(
            db=mock_db,
            query="shi"
        )
        
        # Assert
        assert result == expected_suggestions
        search_service.autocomplete_service.get_autocomplete_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_popular_suggestions(self, search_service, mock_db):
        """Test popular suggestions retrieval"""
        # Arrange
        expected_suggestions = ["blue shirt", "white shirt", "black shirt"]
        search_service.suggestion_service.get_popular_suggestions.return_value = expected_suggestions
        
        # Act
        result = await search_service.get_popular_suggestions(
            db=mock_db,
            limit=5
        )
        
        # Assert
        assert result == expected_suggestions
        search_service.suggestion_service.get_popular_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_related_suggestions(self, search_service, mock_db):
        """Test related suggestions retrieval"""
        # Arrange
        expected_suggestions = ["t-shirt", "polo shirt", "dress shirt"]
        search_service.suggestion_service.get_related_suggestions.return_value = expected_suggestions
        
        # Act
        result = await search_service.get_related_suggestions(
            db=mock_db,
            query="shirt"
        )
        
        # Assert
        assert result == expected_suggestions
        search_service.suggestion_service.get_related_suggestions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_query_corrections(self, search_service, mock_db):
        """Test query corrections"""
        # Arrange
        expected_corrections = ["shirt", "shirts"]
        search_service.suggestion_service.get_query_corrections.return_value = expected_corrections
        
        # Act
        result = await search_service.get_query_corrections(
            db=mock_db,
            query="shrt"  # Misspelled
        )
        
        # Assert
        assert result == expected_corrections
        search_service.suggestion_service.get_query_corrections.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cheapest_suggestions(self, search_service, mock_db):
        """Test cheapest suggestions retrieval"""
        # Arrange
        expected_suggestions = [
            {"title": "Cheap Shirt", "price": 9.99},
            {"title": "Budget Shirt", "price": 12.99}
        ]
        search_service.suggestion_service.get_cheapest_product_suggestions.return_value = expected_suggestions
        
        # Act
        result = await search_service.get_cheapest_suggestions(
            db=mock_db,
            limit=5
        )
        
        # Assert
        assert result == expected_suggestions
        search_service.suggestion_service.get_cheapest_product_suggestions.assert_called_once() 