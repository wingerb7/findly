import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch
import redis

from main import app
from database import Base, get_db
from models import Product, SearchAnalytics, PopularSearch
from cache_manager import cache_manager
from analytics_manager import analytics_manager

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis for testing."""
    with patch('ai_shopify_search.cache_manager.redis_client') as mock_redis:
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = 0
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        yield mock_redis

@pytest.fixture(scope="function")
def mock_embedding():
    """Mock embedding generation."""
    with patch('ai_shopify_search.embeddings.generate_embedding') as mock_embed:
        mock_embed.return_value = [0.1] * 1536  # Mock 1536-dimensional embedding
        yield mock_embed

@pytest.fixture(scope="function")
def sample_products(db_session):
    """Create sample products for testing."""
    products = [
        Product(
            shopify_id="gid://shopify/Product/1",
            title="Blue Cotton Shirt",
            description="Comfortable blue cotton shirt",
            price=29.99,
            tags=["shirt", "blue", "cotton", "comfortable"],
            embedding=[0.1] * 1536
        ),
        Product(
            shopify_id="gid://shopify/Product/2",
            title="Black Jeans",
            description="Stylish black jeans",
            price=59.99,
            tags=["jeans", "black", "denim", "stylish"],
            embedding=[0.2] * 1536
        ),
        Product(
            shopify_id="gid://shopify/Product/3",
            title="Red Sneakers",
            description="Comfortable red sneakers",
            price=89.99,
            tags=["sneakers", "red", "comfortable", "sport"],
            embedding=[0.3] * 1536
        )
    ]
    
    for product in products:
        db_session.add(product)
    db_session.commit()
    
    return products

@pytest.fixture(scope="function")
def sample_analytics(db_session):
    """Create sample analytics data for testing."""
    analytics = [
        SearchAnalytics(
            session_id="test-session-1",
            query="blue shirt",
            search_type="ai",
            filters={},
            results_count=2,
            page=1,
            limit=25,
            response_time_ms=150.0,
            cache_hit=False,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        ),
        SearchAnalytics(
            session_id="test-session-2",
            query="black jeans",
            search_type="ai",
            filters={},
            results_count=1,
            page=1,
            limit=25,
            response_time_ms=120.0,
            cache_hit=True,
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )
    ]
    
    for analytic in analytics:
        db_session.add(analytic)
    db_session.commit()
    
    return analytics

@pytest.fixture(scope="function")
def sample_popular_searches(db_session):
    """Create sample popular searches for testing."""
    popular_searches = [
        PopularSearch(
            query="blue shirt",
            search_count=10,
            click_count=5,
            avg_position_clicked=2.5
        ),
        PopularSearch(
            query="black jeans",
            search_count=8,
            click_count=3,
            avg_position_clicked=1.8
        )
    ]
    
    for search in popular_searches:
        db_session.add(search)
    db_session.commit()
    
    return popular_searches 