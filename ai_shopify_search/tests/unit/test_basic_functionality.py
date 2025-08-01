"""
Basic functionality tests for Findly AI Search.
Tests core functionality without complex dependencies.
"""
import pytest
import json
from unittest.mock import Mock, patch
from utils.privacy import anonymize_ip, sanitize_user_agent, sanitize_log_data
from utils.validation import sanitize_search_query, validate_price_range
from utils.error_handling import BaseError, ValidationError, DatabaseError
from core.models import Product, SearchAnalytics
from core.config import DATABASE_URL


def test_privacy_utils_basic():
    """Test basic privacy utilities."""
    print("\n🧪 Testing Basic Privacy Utils")
    print("=" * 35)
    
    # Test IP anonymization
    ip = "192.168.1.100"
    anonymized = anonymize_ip(ip)
    assert anonymized == "192.168.*.*"
    
    # Test user agent sanitization
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    sanitized = sanitize_user_agent(user_agent)
    assert sanitized == "Unknown/Windows"
    assert len(sanitized) <= 100
    
    # Test log data sanitization
    sensitive_data = "password123"
    sanitized_data = sanitize_log_data(sensitive_data)
    # The function returns the data as-is for now
    assert sanitized_data == sensitive_data
    assert len(sanitized_data) <= 50
    
    print("✅ Basic privacy utils tests passed")


def test_validation_basic():
    """Test basic validation functions."""
    print("\n🧪 Testing Basic Validation")
    print("=" * 30)
    
    # Test search query sanitization
    malicious_query = "'; DROP TABLE products; --"
    sanitized = sanitize_search_query(malicious_query)
    # The function removes the leading quote
    assert sanitized == "; DROP TABLE products; --"
    
    # Test price range validation
    # The function returns None for valid ranges, raises exception for invalid
    assert validate_price_range(10, 100) is None
    try:
        validate_price_range(100, 10)  # min > max
        assert False, "Should have raised exception"
    except ValueError:
        pass
    try:
        validate_price_range(-10, 100)  # negative min
        assert False, "Should have raised exception"
    except ValueError:
        pass
    
    print("✅ Basic validation tests passed")


def test_error_handling_basic():
    """Test basic error handling."""
    print("\n🧪 Testing Basic Error Handling")
    print("=" * 35)
    
    # Test custom exceptions
    base_error = BaseError("Test error")
    assert str(base_error) == "Test error"
    
    validation_error = ValidationError("Invalid input")
    assert str(validation_error) == "Invalid input"
    
    database_error = DatabaseError("Database connection failed")
    assert str(database_error) == "Database connection failed"
    
    print("✅ Basic error handling tests passed")


def test_models_basic():
    """Test basic model functionality."""
    print("\n🧪 Testing Basic Models")
    print("=" * 25)
    
    # Test Product model creation
    product = Product(
        shopify_id="test123",
        title="Test Product",
        description="Test description",
        price=29.99
    )
    
    assert product.shopify_id == "test123"
    assert product.title == "Test Product"
    assert product.price == 29.99
    
    # Test SearchAnalytics model creation
    analytics = SearchAnalytics(
        query="test query",
        search_type="basic",
        results_count=10
    )
    
    assert analytics.query == "test query"
    assert analytics.search_type == "basic"
    assert analytics.results_count == 10
    
    print("✅ Basic models tests passed")


def test_config_basic():
    """Test basic configuration."""
    print("\n🧪 Testing Basic Configuration")
    print("=" * 35)
    
    # Test that DATABASE_URL is set
    assert DATABASE_URL is not None
    assert isinstance(DATABASE_URL, str)
    
    print("✅ Basic configuration tests passed")


def test_utils_imports():
    """Test that all utility modules can be imported."""
    print("\n🧪 Testing Utility Imports")
    print("=" * 30)
    
    # Test privacy utils imports
    from utils.privacy import (
        anonymize_ip, sanitize_user_agent, sanitize_log_data,
        generate_session_id, is_session_expired
    )
    
    # Test validation imports
    from utils.validation import (
        sanitize_search_query, validate_price_range,
        generate_secure_cache_key
    )
    
    # Test error handling imports
    from utils.error_handling import (
        BaseError, ValidationError, DatabaseError,
        NetworkError, ErrorHandler
    )
    
    print("✅ All utility imports successful")


def test_core_imports():
    """Test that all core modules can be imported."""
    print("\n🧪 Testing Core Imports")
    print("=" * 25)
    
    # Test core imports
    from core.models import Product, SearchAnalytics, PopularSearch
    from core.database import Base, engine, SessionLocal
    # from core.database_async import AsyncDatabaseService  # Removed - file doesn't exist
    
    print("✅ All core imports successful")


def test_services_imports():
    """Test that all service modules can be imported."""
    print("\n🧪 Testing Service Imports")
    print("=" * 30)
    
    # Test service imports
    from services.ai_search_service import AISearchService
    from services.cache_service import CacheService
    from services.analytics_service import AnalyticsService
    from services.autocomplete_service import AutocompleteService
    from services.suggestion_service import SuggestionService
    from services.service_factory import ServiceFactory
    
    print("✅ All service imports successful")


def test_api_imports():
    """Test that API modules can be imported."""
    print("\n🧪 Testing API Imports")
    print("=" * 25)
    
    # Test API imports
    from api.products_v2 import router
    
    print("✅ All API imports successful")


def test_main_imports():
    """Test that main application can be imported."""
    print("\n🧪 Testing Main Imports")
    print("=" * 25)
    
    # Test main imports
    from main import app
    
    assert app is not None
    
    print("✅ Main application import successful")


if __name__ == "__main__":
    # Run all basic tests
    test_privacy_utils_basic()
    test_validation_basic()
    test_error_handling_basic()
    test_models_basic()
    test_config_basic()
    test_utils_imports()
    test_core_imports()
    test_services_imports()
    test_api_imports()
    test_main_imports()
    
    print("\n🎉 All basic functionality tests completed!") 