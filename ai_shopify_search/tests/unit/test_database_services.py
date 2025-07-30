#!/usr/bin/env python3
"""
Unit tests for database services.
Tests core/database.py and core/database_async.py functionality.
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, engine, SessionLocal, get_db
from core.database_async import AsyncDatabaseService, get_async_db
from core.models import Product, SearchAnalytics


class TestDatabaseServices:
    """Test database services functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create in-memory SQLite database for testing
        self.test_engine = create_engine("sqlite:///:memory:")
        self.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.test_engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.test_engine)
    
    def teardown_method(self):
        """Cleanup test environment."""
        Base.metadata.drop_all(bind=self.test_engine)
    
    def test_database_connection(self):
        """Test database connection and session creation."""
        print("🧪 Testing Database Connection")
        print("=" * 40)
        
        # Test session creation
        session = self.TestSessionLocal()
        assert session is not None
        assert session.is_active
        
        # Test session closure
        session.close()
        assert not session.is_active
        
        print("✅ Database connection tests passed")
    
    def test_get_db_generator(self):
        """Test get_db dependency generator."""
        print("\n🧪 Testing get_db Generator")
        print("=" * 35)
        
        # Mock the database session
        mock_session = Mock()
        mock_session.is_active = True
        
        with patch('core.database.SessionLocal', return_value=mock_session):
            db_gen = get_db()
            db = next(db_gen)
            
            assert db == mock_session
            
            # Test cleanup
            try:
                next(db_gen)
            except StopIteration:
                pass
            
            mock_session.close.assert_called_once()
            print("✅ get_db generator tests passed")
    
    def test_product_model_operations(self):
        """Test Product model operations."""
        print("\n🧪 Testing Product Model Operations")
        print("=" * 40)
        
        session = self.TestSessionLocal()
        
        # Create test product
        test_product = Product(
            title="Test Product",
            description="Test Description",
            price=99.99,
            shopify_id="test_123",
            tags=["test", "product"],
            embedding=[0.1, 0.2, 0.3] * 512  # 1536 dimensions
        )
        
        # Test creation
        session.add(test_product)
        session.commit()
        session.refresh(test_product)
        
        assert test_product.id is not None
        assert test_product.title == "Test Product"
        assert test_product.price == 99.99
        
        # Test retrieval
        retrieved_product = session.query(Product).filter_by(shopify_id="test_123").first()
        assert retrieved_product is not None
        assert retrieved_product.title == "Test Product"
        
        # Test update
        retrieved_product.price = 149.99
        session.commit()
        
        updated_product = session.query(Product).filter_by(shopify_id="test_123").first()
        assert updated_product.price == 149.99
        
        # Test deletion
        session.delete(updated_product)
        session.commit()
        
        deleted_product = session.query(Product).filter_by(shopify_id="test_123").first()
        assert deleted_product is None
        
        session.close()
        print("✅ Product model operations tests passed")
    
    def test_search_analytics_model(self):
        """Test SearchAnalytics model operations."""
        print("\n🧪 Testing SearchAnalytics Model")
        print("=" * 35)
        
        session = self.TestSessionLocal()
        
        # Create test analytics
        test_analytics = SearchAnalytics(
            session_id="test_session_123",
            query="test query",
            search_type="ai",
            filters={"price_range": "10-100"},
            results_count=5,
            page=1,
            limit=25,
            response_time_ms=150.5,
            cache_hit=False,
            user_agent="test-agent",
            ip_address="192.168.1.1"
        )
        
        # Test creation
        session.add(test_analytics)
        session.commit()
        session.refresh(test_analytics)
        
        assert test_analytics.id is not None
        assert test_analytics.query == "test query"
        assert test_analytics.search_type == "ai"
        assert test_analytics.results_count == 5
        
        session.close()
        print("✅ SearchAnalytics model tests passed")


class TestAsyncDatabaseService:
    """Test async database service functionality."""
    
    @pytest.mark.asyncio
    async def test_async_database_initialization(self):
        """Test async database service initialization."""
        print("\n🧪 Testing Async Database Initialization")
        print("=" * 45)
        
        async_db_service = AsyncDatabaseService()
        
        # Test initialization with mock engine
        with patch('core.database_async.create_async_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            await async_db_service.initialize()
            
            assert async_db_service.engine == mock_engine
            assert async_db_service.async_session_maker is not None
            
            print("✅ Async database initialization tests passed")
    
    @pytest.mark.asyncio
    async def test_async_session_context_manager(self):
        """Test async session context manager."""
        print("\n🧪 Testing Async Session Context Manager")
        print("=" * 45)
        
        async_db_service = AsyncDatabaseService()
        
        # Mock session maker and session
        mock_session = Mock()
        mock_session_maker = Mock()
        mock_session_maker.return_value = mock_session
        
        async_db_service.async_session_maker = mock_session_maker
        
        # Test context manager
        async with async_db_service.get_session() as session:
            assert session == mock_session
        
        # Verify session was closed
        mock_session.close.assert_called_once()
        print("✅ Async session context manager tests passed")
    
    @pytest.mark.asyncio
    async def test_get_async_db_generator(self):
        """Test get_async_db dependency generator."""
        print("\n🧪 Testing get_async_db Generator")
        print("=" * 40)
        
        # Mock async database service
        mock_session = Mock()
        
        with patch('core.database_async.async_db_service.get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_get_session.return_value.__aexit__.return_value = None
            
            async_gen = get_async_db()
            session = await async_gen.__anext__()
            
            assert session == mock_session
            
            # Test cleanup
            try:
                await async_gen.__anext__()
            except StopAsyncIteration:
                pass
            
            print("✅ get_async_db generator tests passed")


class TestDatabaseErrorHandling:
    """Test database error handling scenarios."""
    
    def test_database_connection_error(self):
        """Test database connection error handling."""
        print("\n🧪 Testing Database Connection Error Handling")
        print("=" * 50)
        
        # Test with invalid database URL
        with patch('core.database.create_engine') as mock_create_engine:
            mock_create_engine.side_effect = Exception("Connection failed")
            
            try:
                # This should raise an exception
                from core.database import engine
                assert False, "Should have raised an exception"
            except Exception as e:
                assert "Connection failed" in str(e)
                print("✅ Database connection error handling tests passed")
    
    def test_session_rollback_on_error(self):
        """Test session rollback on error."""
        print("\n🧪 Testing Session Rollback on Error")
        print("=" * 45)
        
        session = self.TestSessionLocal()
        
        # Create a product
        test_product = Product(
            title="Test Product",
            description="Test Description",
            price=99.99,
            shopify_id="test_123",
            tags=["test"],
            embedding=[0.1] * 1536
        )
        
        session.add(test_product)
        session.commit()
        
        # Verify product exists
        assert session.query(Product).filter_by(shopify_id="test_123").first() is not None
        
        # Simulate error and rollback
        try:
            # Try to add invalid product (should fail)
            invalid_product = Product(
                title=None,  # This should cause an error
                shopify_id="invalid_123"
            )
            session.add(invalid_product)
            session.commit()
        except Exception:
            session.rollback()
        
        # Verify rollback worked (invalid product should not exist)
        invalid_product = session.query(Product).filter_by(shopify_id="invalid_123").first()
        assert invalid_product is None
        
        # Verify original product still exists
        original_product = session.query(Product).filter_by(shopify_id="test_123").first()
        assert original_product is not None
        
        session.close()
        print("✅ Session rollback tests passed")


def test_database_performance():
    """Test database performance with bulk operations."""
    print("\n🧪 Testing Database Performance")
    print("=" * 35)
    
    # Create test engine
    test_engine = create_engine("sqlite:///:memory:")
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    session = TestSessionLocal()
    
    # Test bulk insert performance
    products = []
    for i in range(100):
        product = Product(
            title=f"Product {i}",
            description=f"Description {i}",
            price=float(i * 10),
            shopify_id=f"shopify_{i}",
            tags=[f"tag_{i}"],
            embedding=[0.1] * 1536
        )
        products.append(product)
    
    # Bulk insert
    session.bulk_save_objects(products)
    session.commit()
    
    # Verify all products were inserted
    count = session.query(Product).count()
    assert count == 100
    
    # Test query performance
    results = session.query(Product).filter(Product.price > 500).all()
    assert len(results) == 50  # Products 51-100 have price > 500
    
    session.close()
    print("✅ Database performance tests passed")


if __name__ == "__main__":
    # Run tests
    test_database_performance()
    
    # Create test instance and run tests
    test_instance = TestDatabaseServices()
    test_instance.setup_method()
    
    test_instance.test_database_connection()
    test_instance.test_get_db_generator()
    test_instance.test_product_model_operations()
    test_instance.test_search_analytics_model()
    
    test_instance.teardown_method()
    
    print("\n🎉 Database services tests completed!") 