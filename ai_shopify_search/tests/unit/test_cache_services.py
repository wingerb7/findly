#!/usr/bin/env python3
"""
Unit tests for cache services.
Tests cache_manager.py and services/cache_service.py functionality.
"""

import sys
import os
import json
import time
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_shopify_search.core.cache_manager import cache_manager
from ai_shopify_search.services.cache_service import CacheService


class TestCacheManager:
    """Test cache manager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_redis = Mock()
        self.mock_redis.get.return_value = None
        self.mock_redis.setex.return_value = True
        self.mock_redis.keys.return_value = []
        self.mock_redis.delete.return_value = 1
        # Patch Redis connection op het juiste pad
        patcher = patch.object(cache_manager, 'redis_client', self.mock_redis)
        self.redis_patcher = patcher
        self.redis_patcher.start()
    
    def teardown_method(self):
        self.redis_patcher.stop()
    
    def test_cache_get_miss(self):
        print("🧪 Testing Cache Get Miss")
        print("=" * 30)
        self.mock_redis.get.return_value = None
        result = cache_manager.get_cached_result("test_key")
        assert result is None
        self.mock_redis.get.assert_called_once_with("test_key")
        print("✅ Cache get miss tests passed")
    
    def test_cache_get_hit(self):
        print("\n🧪 Testing Cache Get Hit")
        print("=" * 30)
        cached_data = {"test": "data", "count": 42}
        self.mock_redis.get.return_value = json.dumps(cached_data)
        result = cache_manager.get_cached_result("test_key")
        assert result == cached_data
        self.mock_redis.get.assert_called_once_with("test_key")
        print("✅ Cache get hit tests passed")
    
    def test_cache_set(self):
        print("\n🧪 Testing Cache Set")
        print("=" * 25)
        test_data = {"query": "test", "results": [1, 2, 3]}
        ttl_val = 300
        cache_manager.set_cached_result("test_key", test_data, ttl_val)
        self.mock_redis.setex.assert_called_once_with(
            "test_key", ttl_val, json.dumps(test_data)
        )
        print("✅ Cache set tests passed")
    
    def test_cache_invalidate(self):
        print("\n🧪 Testing Cache Invalidate")
        print("=" * 35)
        self.mock_redis.keys.return_value = [b"product:1", b"product:2"]
        cache_manager.invalidate_product_cache()
        self.mock_redis.keys.assert_called_once_with("product:*")
        self.mock_redis.delete.assert_called_once_with(b"product:1", b"product:2")
        print("✅ Cache invalidate tests passed")
    
    def test_cache_clear(self):
        print("\n🧪 Testing Cache Clear")
        print("=" * 25)
        self.mock_redis.keys.return_value = [b"product:1", b"product:2"]
        cache_manager.clear_cache()
        self.mock_redis.keys.assert_called_with("product:*")
        print("✅ Cache clear tests passed")
    
    def test_cache_stats(self):
        print("\n🧪 Testing Cache Stats")
        print("=" * 25)
        self.mock_redis.keys.side_effect = [
            [b"product:1", b"product:2"],  # product keys
            [b"search:1"],                 # search keys  
            [b"ai_search:1"]               # ai_search keys
        ]
        result = cache_manager.get_cache_stats()
        assert "total_cache_keys" in result
        assert "search_cache_keys" in result
        assert "ai_search_cache_keys" in result
        assert "cache_info" in result
        print("✅ Cache stats tests passed")
    
    def test_cache_error_handling(self):
        print("\n🧪 Testing Cache Error Handling")
        print("=" * 40)
        self.mock_redis.get.side_effect = Exception("Redis connection failed")
        result = cache_manager.get_cached_result("test_key")
        assert result is None
        print("✅ Cache error handling tests passed")


class TestCacheService:
    """Test CacheService class functionality."""
    
    def setup_method(self):
        self.mock_redis = Mock()
        self.mock_redis.setex.return_value = True
        self.mock_redis.get.return_value = None
        self.mock_redis.delete.return_value = 1
        self.cache_service = CacheService()
        patcher = patch.object(self.cache_service, 'redis_client', self.mock_redis)
        self.redis_patcher = patcher
        self.redis_patcher.start()
    
    def teardown_method(self):
        self.redis_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_async_cache_get(self):
        """Test async cache get functionality."""
        print("\n🧪 Testing Async Cache Get")
        print("=" * 30)
        
        # Mock Redis response
        cached_data = {"test": "data"}
        self.mock_redis.get.return_value = json.dumps(cached_data)
        
        result = await self.cache_service.get("test_key")
        assert result == cached_data
        self.mock_redis.get.assert_called_once_with("test_key")
        print("✅ Async cache get tests passed")
    
    @pytest.mark.asyncio
    async def test_async_cache_set(self):
        """Test async cache set functionality."""
        print("\n🧪 Testing Async Cache Set")
        print("=" * 30)
        
        test_data = {"query": "test", "results": [1, 2, 3]}
        ttl = 300
        
        result = await self.cache_service.set("test_key", test_data, ttl)
        assert result is True
        self.mock_redis.setex.assert_called_once_with(
            "test_key", ttl, json.dumps(test_data, default=str)
        )
        print("✅ Async cache set tests passed")
    
    @pytest.mark.asyncio
    async def test_async_cache_delete(self):
        """Test async cache delete functionality."""
        print("\n🧪 Testing Async Cache Delete")
        print("=" * 35)
        
        self.mock_redis.delete.return_value = 1
        
        result = await self.cache_service.delete("test_key")
        assert result is True
        self.mock_redis.delete.assert_called_once_with("test_key")
        print("✅ Async cache delete tests passed")
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation."""
        print("\n🧪 Testing Cache Key Generation")
        print("=" * 35)
        
        # Test key generation with parameters
        key = self.cache_service.generate_key("search", query="test", page=1)
        assert "search" in key
        assert len(key) > 10  # Should be a hash
        
        print("✅ Cache key generation tests passed")
    
    @pytest.mark.asyncio
    async def test_cache_ttl_management(self):
        """Test cache TTL management."""
        print("\n🧪 Testing Cache TTL Management")
        print("=" * 35)
        
        # Test setting different TTL values
        await self.cache_service.set("short_ttl", {"data": "test"}, 60)
        await self.cache_service.set("long_ttl", {"data": "test"}, 3600)
        
        # Verify different TTL values were set
        assert self.mock_redis.setex.call_count == 2
        calls = self.mock_redis.setex.call_args_list
        assert calls[0][0][1] == 60   # short TTL
        assert calls[1][0][1] == 3600 # long TTL
        
        print("✅ Cache TTL management tests passed")


class TestCachePerformance:
    """Test cache performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_cache_performance_bulk_operations(self):
        """Test cache performance with bulk operations."""
        print("\n🧪 Testing Cache Performance - Bulk Operations")
        print("=" * 55)
        
        cache_service = CacheService()
        
        # Mock Redis for performance testing
        with patch.object(cache_service, 'redis_client') as mock_redis:
            mock_redis.setex.return_value = True
            mock_redis.get.return_value = json.dumps({"test": "data"})
            
            # Test bulk set operations
            start_time = time.time()
            for i in range(100):
                await cache_service.set(f"key_{i}", {"data": f"value_{i}"}, 300)
            
            set_time = time.time() - start_time
            assert set_time < 1.0  # Should complete within 1 second
            
            # Test bulk get operations
            start_time = time.time()
            for i in range(100):
                await cache_service.get(f"key_{i}")
            
            get_time = time.time() - start_time
            assert get_time < 1.0  # Should complete within 1 second
            
            print(f"✅ Bulk operations: set={set_time:.3f}s, get={get_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self):
        """Test cache memory efficiency."""
        print("\n🧪 Testing Cache Memory Efficiency")
        print("=" * 45)
        
        cache_service = CacheService()
        
        # Test with large data
        large_data = {
            "results": [{"id": i, "title": f"Product {i}", "price": i * 10} for i in range(1000)],
            "metadata": {"total": 1000, "page": 1, "limit": 1000}
        }
        
        # Mock Redis
        with patch.object(cache_service, 'redis_client') as mock_redis:
            mock_redis.setex.return_value = True
            
            # Test storing large data
            await cache_service.set("large_data", large_data, 300)
            
            # Verify data was stored
            mock_redis.setex.assert_called_once()
            stored_data = mock_redis.setex.call_args[0][2]  # The JSON string
            parsed_data = json.loads(stored_data)
            assert len(parsed_data["results"]) == 1000
            
            print("✅ Memory efficiency tests passed")


def test_cache_integration():
    """Test cache integration with real scenarios."""
    print("\n🧪 Testing Cache Integration")
    print("=" * 35)
    
    # Test search result caching
    search_results = {
        "query": "blue shirt",
        "results": [
            {"id": 1, "title": "Blue Cotton Shirt", "price": 29.99},
            {"id": 2, "title": "Blue Denim Shirt", "price": 49.99}
        ],
        "count": 2,
        "page": 1,
        "limit": 25
    }
    
    # Mock Redis
    with patch.object(cache_manager, 'redis_client') as mock_redis:
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = json.dumps(search_results)
        
        # Test caching search results
        cache_manager.set_cached_result("search:blue_shirt:1:25", search_results, 900)
        
        # Test retrieving cached results
        cached_results = cache_manager.get_cached_result("search:blue_shirt:1:25")
        
        assert cached_results == search_results
        print("✅ Cache integration tests passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 