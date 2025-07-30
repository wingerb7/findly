import pytest
from unittest.mock import patch, MagicMock
from ai_shopify_search.search_service import SearchService
from ai_shopify_search.models import Product, QuerySuggestion, PopularSearch

class TestSearchService:
    """Test cases for SearchService."""
    
    @pytest.fixture
    def search_service(self):
        return SearchService()
    
    @pytest.mark.asyncio
    async def test_ai_search_products_success(self, search_service, db_session, sample_products, mock_embedding):
        """Test successful AI search."""
        query = "blue shirt"
        page = 1
        limit = 25
        
        result = await search_service.ai_search_products(
            db=db_session,
            query=query,
            page=page,
            limit=limit
        )
        
        assert result["query"] == query
        assert "results" in result
        assert "pagination" in result
        assert len(result["results"]) > 0
        assert result["pagination"]["page"] == page
        assert result["pagination"]["limit"] == limit
    
    @pytest.mark.asyncio
    async def test_ai_search_products_no_results(self, search_service, db_session, mock_embedding):
        """Test AI search with no results."""
        query = "nonexistent product"
        page = 1
        limit = 25
        
        result = await search_service.ai_search_products(
            db=db_session,
            query=query,
            page=page,
            limit=limit
        )
        
        assert result["query"] == query
        assert len(result["results"]) == 0
        assert result["count"] == 0
    
    @pytest.mark.asyncio
    async def test_ai_search_products_pagination(self, search_service, db_session, sample_products, mock_embedding):
        """Test AI search pagination."""
        query = "shirt"
        page = 1
        limit = 2
        
        result = await search_service.ai_search_products(
            db=db_session,
            query=query,
            page=page,
            limit=limit
        )
        
        assert len(result["results"]) <= limit
        assert result["pagination"]["page"] == page
        assert result["pagination"]["limit"] == limit
    
    def test_get_autocomplete_suggestions(self, search_service, db_session):
        """Test autocomplete suggestions."""
        # Add test suggestions
        suggestions = [
            QuerySuggestion(
                query="blue",
                suggestion="blue shirt",
                suggestion_type="autocomplete",
                search_count=5,
                click_count=2,
                relevance_score=0.8,
                is_active=True
            ),
            QuerySuggestion(
                query="blue",
                suggestion="blue jeans",
                suggestion_type="autocomplete",
                search_count=3,
                click_count=1,
                relevance_score=0.7,
                is_active=True
            )
        ]
        
        for suggestion in suggestions:
            db_session.add(suggestion)
        db_session.commit()
        
        result = search_service.get_autocomplete_suggestions(db_session, "blue", limit=5)
        
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        assert all("similarity_score" in item for item in result)
    
    def test_get_popular_suggestions(self, search_service, db_session, sample_popular_searches):
        """Test popular suggestions."""
        result = search_service.get_popular_suggestions(db_session, limit=5)
        
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        assert all("search_count" in item for item in result)
        assert all("click_count" in item for item in result)
    
    def test_get_related_suggestions(self, search_service, db_session):
        """Test related suggestions."""
        # Add test suggestions
        suggestions = [
            QuerySuggestion(
                query="shirt",
                suggestion="blue shirt",
                suggestion_type="related",
                search_count=5,
                relevance_score=0.8,
                is_active=True
            ),
            QuerySuggestion(
                query="shirt",
                suggestion="white shirt",
                suggestion_type="related",
                search_count=3,
                relevance_score=0.7,
                is_active=True
            )
        ]
        
        for suggestion in suggestions:
            db_session.add(suggestion)
        db_session.commit()
        
        result = search_service.get_related_suggestions(db_session, "blue shirt", limit=5)
        
        assert len(result) > 0
        assert all("suggestion" in item for item in result)
        assert all("overlap_score" in item for item in result)
    
    def test_generate_suggestions_from_products(self, search_service, db_session, sample_products):
        """Test generating suggestions from products."""
        result = search_service.generate_suggestions_from_products(db_session, "blue", limit=5)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("blue" in suggestion.lower() for suggestion in result)
    
    @pytest.mark.asyncio
    async def test_fallback_text_search(self, search_service, db_session, sample_products):
        """Test fallback text search."""
        query = "blue"
        page = 1
        limit = 5
        
        result = await search_service._fallback_text_search(db_session, query, page, limit)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("title" in product for product in result)
        assert all("similarity" in product for product in result)
    
    def test_create_pagination_metadata(self, search_service):
        """Test pagination metadata creation."""
        page = 2
        limit = 25
        total_count = 100
        total_pages = 4
        
        result = search_service._create_pagination_metadata(page, limit, total_count, total_pages)
        
        assert "pagination" in result
        pagination = result["pagination"]
        assert pagination["page"] == page
        assert pagination["limit"] == limit
        assert pagination["total_count"] == total_count
        assert pagination["total_pages"] == total_pages
        assert pagination["has_next"] == True
        assert pagination["has_previous"] == True
        assert pagination["next_page"] == 3
        assert pagination["previous_page"] == 1 