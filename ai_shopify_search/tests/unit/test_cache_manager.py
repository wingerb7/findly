#!/usr/bin/env python3
"""
Simple tests for cache_manager.py - only testing what actually exists.
"""

import pytest
import json
import hashlib
from unittest.mock import Mock, patch, MagicMock
from ai_shopify_search.core.cache_manager import CacheManager, cache_manager

class TestCacheManager:
    """Test CacheManager class."""
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            assert manager.redis_client is not None
            mock_redis.assert_called_once()
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        with patch('ai_shopify_search.cache_manager.redis.Redis'):
            manager = CacheManager()
            
            # Test with simple parameters
            key = manager.get_cache_key("product", id=123, category="electronics")
            assert key.startswith("product:")
            assert len(key) == 32 + 8  # md5 hash + prefix
            
            # Test with complex parameters
            key2 = manager.get_cache_key("search", query="test", filters={"price": {"min": 10, "max": 100}})
            assert key2.startswith("search:")
            
            # Test that different parameters generate different keys
            key3 = manager.get_cache_key("product", id=124, category="electronics")
            assert key != key3
    
    def test_get_cached_result_success(self):
        """Test successful cache retrieval."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock cached data
            cached_data = {"result": "test data", "count": 5}
            mock_redis_instance.get.return_value = json.dumps(cached_data)
            
            result = manager.get_cached_result("test_key")
            
            assert result == cached_data
            mock_redis_instance.get.assert_called_once_with("test_key")
    
    def test_get_cached_result_not_found(self):
        """Test cache retrieval when key doesn't exist."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock no cached data
            mock_redis_instance.get.return_value = None
            
            result = manager.get_cached_result("test_key")
            
            assert result is None
            mock_redis_instance.get.assert_called_once_with("test_key")
    
    def test_get_cached_result_error(self):
        """Test cache retrieval with error."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock Redis error
            mock_redis_instance.get.side_effect = Exception("Redis error")
            
            result = manager.get_cached_result("test_key")
            
            assert result is None
    
    def test_set_cached_result_success(self):
        """Test successful cache storage."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            data = {"result": "test data", "count": 5}
            
            manager.set_cached_result("test_key", data, ttl=300)
            
            mock_redis_instance.setex.assert_called_once_with(
                "test_key", 300, json.dumps(data)
            )
    
    def test_set_cached_result_with_default_ttl(self):
        """Test cache storage with default TTL."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            data = {"result": "test data"}
            
            # The actual default TTL is 3600, so we test with that
            manager.set_cached_result("test_key", data)
            
            mock_redis_instance.setex.assert_called_once_with(
                "test_key", 3600, json.dumps(data)
            )
    
    def test_set_cached_result_error(self):
        """Test cache storage with error."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock Redis error
            mock_redis_instance.setex.side_effect = Exception("Redis error")
            
            data = {"result": "test data"}
            
            # Should not raise exception
            manager.set_cached_result("test_key", data)
    
    def test_invalidate_product_cache_success(self):
        """Test successful product cache invalidation."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock keys to delete
            mock_redis_instance.keys.return_value = ["product:1", "product:2", "product:3"]
            mock_redis_instance.delete.return_value = 3
            
            manager.invalidate_product_cache()
            
            mock_redis_instance.keys.assert_called_once_with("product:*")
            mock_redis_instance.delete.assert_called_once_with("product:1", "product:2", "product:3")
    
    def test_invalidate_product_cache_no_keys(self):
        """Test product cache invalidation with no keys."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock no keys to delete
            mock_redis_instance.keys.return_value = []
            
            manager.invalidate_product_cache()
            
            mock_redis_instance.keys.assert_called_once_with("product:*")
            mock_redis_instance.delete.assert_not_called()
    
    def test_invalidate_product_cache_error(self):
        """Test product cache invalidation with error."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock Redis error
            mock_redis_instance.keys.side_effect = Exception("Redis error")
            
            # Should not raise exception
            manager.invalidate_product_cache()
    
    def test_get_cache_stats_success(self):
        """Test successful cache statistics retrieval."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock different key types
            mock_redis_instance.keys.side_effect = [
                ["product:1", "product:2"],  # product keys
                ["search:1", "search:2", "search:3"],  # search keys
                ["ai_search:1"]  # ai_search keys
            ]
            
            with patch('ai_shopify_search.ai_shopify_search.cache_manager.SEARCH_CACHE_TTL', 300):
                with patch('ai_shopify_search.ai_shopify_search.cache_manager.AI_SEARCH_CACHE_TTL', 600):
                    with patch('ai_shopify_search.ai_shopify_search.cache_manager.CACHE_TTL', 900):
                        stats = manager.get_cache_stats()
            
            assert stats["total_cache_keys"] == 2
            assert stats["search_cache_keys"] == 3
            assert stats["ai_search_cache_keys"] == 1
            assert stats["cache_info"]["search_ttl"] == 300
            assert stats["cache_info"]["ai_search_ttl"] == 600
            assert stats["cache_info"]["default_ttl"] == 900
    
    def test_get_cache_stats_error(self):
        """Test cache statistics retrieval with error."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock Redis error
            mock_redis_instance.keys.side_effect = Exception("Redis error")
            
            stats = manager.get_cache_stats()
            
            assert stats == {}
    
    def test_clear_cache_success(self):
        """Test successful cache clearing."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock keys to delete
            mock_redis_instance.keys.return_value = ["product:1", "product:2"]
            mock_redis_instance.delete.return_value = 2
            
            manager.clear_cache()
            
            # Should call invalidate_product_cache
            mock_redis_instance.keys.assert_called_once_with("product:*")
            mock_redis_instance.delete.assert_called_once_with("product:1", "product:2")
    
    def test_clear_cache_error(self):
        """Test cache clearing with error."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Mock Redis error
            mock_redis_instance.keys.side_effect = Exception("Redis error")
            
            # Should not raise exception
            manager.clear_cache()

class TestGlobalCacheManager:
    """Test global cache manager instance."""
    
    def test_global_cache_manager_exists(self):
        """Test that global cache manager instance exists."""
        assert cache_manager is not None
        assert isinstance(cache_manager, CacheManager)
    
    def test_global_cache_manager_methods(self):
        """Test that global cache manager has required methods."""
        assert hasattr(cache_manager, 'get_cache_key')
        assert hasattr(cache_manager, 'get_cached_result')
        assert hasattr(cache_manager, 'set_cached_result')
        assert hasattr(cache_manager, 'invalidate_product_cache')
        assert hasattr(cache_manager, 'get_cache_stats')
        assert hasattr(cache_manager, 'clear_cache')

class TestCacheManagerIntegration:
    """Test integration scenarios for CacheManager."""
    
    def test_complete_cache_workflow(self):
        """Test complete cache workflow."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Test data
            search_params = {"query": "test", "filters": {"category": "electronics"}}
            cache_key = manager.get_cache_key("search", **search_params)
            
            # Initially no cached data
            mock_redis_instance.get.return_value = None
            result = manager.get_cached_result(cache_key)
            assert result is None
            
            # Store data in cache
            data = {"results": ["product1", "product2"], "count": 2}
            manager.set_cached_result(cache_key, data, ttl=300)
            mock_redis_instance.setex.assert_called_once_with(
                cache_key, 300, json.dumps(data)
            )
            
            # Retrieve cached data
            mock_redis_instance.get.return_value = json.dumps(data)
            result = manager.get_cached_result(cache_key)
            assert result == data
    
    def test_cache_key_uniqueness(self):
        """Test that cache keys are unique for different parameters."""
        with patch('ai_shopify_search.cache_manager.redis.Redis'):
            manager = CacheManager()
            
            # Different parameters should generate different keys
            key1 = manager.get_cache_key("product", id=1, category="electronics")
            key2 = manager.get_cache_key("product", id=2, category="electronics")
            key3 = manager.get_cache_key("product", id=1, category="clothing")
            
            assert key1 != key2
            assert key1 != key3
            assert key2 != key3
            
            # Same parameters should generate same key
            key4 = manager.get_cache_key("product", id=1, category="electronics")
            assert key1 == key4
    
    def test_cache_with_complex_data(self):
        """Test cache with complex data structures."""
        with patch('ai_shopify_search.cache_manager.redis.Redis') as mock_redis:
            manager = CacheManager()
            mock_redis_instance = Mock()
            manager.redis_client = mock_redis_instance
            
            # Complex data structure
            complex_data = {
                "results": [
                    {"id": 1, "name": "Product 1", "price": 99.99},
                    {"id": 2, "name": "Product 2", "price": 149.99}
                ],
                "filters": {
                    "category": ["electronics", "computers"],
                    "price_range": {"min": 50, "max": 200}
                },
                "pagination": {
                    "page": 1,
                    "limit": 25,
                    "total": 150
                },
                "metadata": {
                    "search_time_ms": 45.2,
                    "cache_hit": False
                }
            }
            
            # Store complex data
            manager.set_cached_result("complex_key", complex_data)
            
            # Verify JSON serialization
            mock_redis_instance.setex.assert_called_once()
            call_args = mock_redis_instance.setex.call_args
            stored_json = call_args[0][2]  # The JSON string
            
            # Should be valid JSON
            parsed_data = json.loads(stored_json)
            assert parsed_data == complex_data 