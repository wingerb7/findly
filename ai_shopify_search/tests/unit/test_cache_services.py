#!/usr/bin/env python3
"""
Unit tests for cache services.
Tests cache_manager.py and services/cache_service.py functionality.
"""

import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache_manager import cache_manager
from services.cache_service import CacheService


class TestCacheManager:
    """Test cache manager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Mock Redis connection
        self.mock_redis = Mock()
        self.mock_redis.get.return_value = None
        self.mock_redis.set.return_value = True
        self.mock_redis.delete.return_value = 1
        self.mock_redis.exists.return_value = 0
        self.mock_redis.ttl.return_value = -1
        
        # Patch Redis connection
        self.redis_patcher = patch('cache_manager.redis_client', self.mock_redis)
        self.redis_patcher.start()
    
    def teardown_method(self):
        """Cleanup test environment."""
        self.redis_patcher.stop()
    
    def test_cache_get_miss(self):
        """Test cache get when key doesn't exist."""
        print("🧪 Testing Cache Get Miss")
        print("=" * 30)
        
        # Mock Redis to return None (cache miss)
        self.mock_redis.get.return_value = None
        
        result = cache_manager.get("test_key")
        
        assert result is None
        self.mock_redis.get.assert_called_once_with("test_key")
        print("✅ Cache get miss tests passed")
    
    def test_cache_get_hit(self):
        """Test cache get when key exists."""
        print("\n🧪 Testing Cache Get Hit")
        print("=" * 30)
        
        # Mock Redis to return cached data
        cached_data = {"test": "data", "count": 42}
        self.mock_redis.get.return_value = json.dumps(cached_data)
        
        result = cache_manager.get("test_key")
        
        assert result == cached_data
        self.mock_redis.get.assert_called_once_with("test_key")
        print("✅ Cache get hit tests passed")
    
    def test_cache_set(self):
        """Test cache set functionality."""
        print("\n🧪 Testing Cache Set")
        print("=" * 25)
        
        test_data = {"query": "test", "results": [1, 2, 3]}
        ttl = 300  # 5 minutes
        
        result = cache_manager.set("test_key", test_data, ttl)
        
        assert result is True
        self.mock_redis.set.assert_called_once_with(
            "test_key", 
            json.dumps(test_data), 
            ex=ttl
        )
        print("✅ Cache set tests passed")
    
    def test_cache_delete(self):
        """Test cache delete functionality."""
        print("\n🧪 Testing Cache Delete")
        print("=" * 30)
        
        result = cache_manager.delete("test_key")
        
        assert result == 1
        self.mock_redis.delete.assert_called_once_with("test_key")
        print("✅ Cache delete tests passed")
    
    def test_cache_exists(self):
        """Test cache exists functionality."""
        print("\n🧪 Testing Cache Exists")
        print("=" * 30)
        
        # Test key exists
        self.mock_redis.exists.return_value = 1
        exists = cache_manager.exists("test_key")
        assert exists is True
        
        # Test key doesn't exist
        self.mock_redis.exists.return_value = 0
        exists = cache_manager.exists("test_key")
        assert exists is False
        
        self.mock_redis.exists.assert_called_with("test_key")
        print("✅ Cache exists tests passed")
    
    def test_cache_ttl(self):
        """Test cache TTL functionality."""
        print("\n🧪 Testing Cache TTL")
        print("=" * 25)
        
        # Test key with TTL
        self.mock_redis.ttl.return_value = 150
        ttl = cache_manager.ttl("test_key")
        assert ttl == 150
        
        # Test key without TTL
        self.mock_redis.ttl.return_value = -1
        ttl = cache_manager.ttl("test_key")
        assert ttl == -1
        
        self.mock_redis.ttl.assert_called_with("test_key")
        print("✅ Cache TTL tests passed")
    
    def test_cache_clear(self):
        """Test cache clear functionality."""
        print("\n🧪 Testing Cache Clear")
        print("=" * 30)
        
        # Mock keys pattern
        self.mock_redis.keys.return_value = [b"cache:test1", b"cache:test2"]
        
        result = cache_manager.clear_cache()
        
        assert result == 2
        self.mock_redis.keys.assert_called_once_with("cache:*")
        self.mock_redis.delete.assert_called_once_with("cache:test1", "cache:test2")
        print("✅ Cache clear tests passed")
    
    def test_cache_stats(self):
        """Test cache statistics functionality."""
        print("\n🧪 Testing Cache Statistics")
        print("=" * 35)
        
        # Mock Redis info
        self.mock_redis.info.return_value = {
            "used_memory": 1024000,
            "used_memory_human": "1.0M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }
        
        # Mock keys count
        self.mock_redis.keys.return_value = [b"cache:key1", b"cache:key2", b"cache:key3"]
        
        stats = cache_manager.get_cache_stats()
        
        assert "memory_usage" in stats
        assert "connected_clients" in stats
        assert "total_commands" in stats
        assert "hit_rate" in stats
        assert "cache_keys" in stats
        
        # Calculate expected hit rate
        expected_hit_rate = 800 / (800 + 200) * 100
        assert abs(stats["hit_rate"] - expected_hit_rate) < 0.01
        
        print("✅ Cache statistics tests passed")
    
    def test_cache_error_handling(self):
        """Test cache error handling."""
        print("\n🧪 Testing Cache Error Handling")
        print("=" * 40)
        
        # Test Redis connection error
        self.mock_redis.get.side_effect = Exception("Redis connection failed")
        
        try:
            result = cache_manager.get("test_key")
            assert result is None  # Should return None on error
            print("✅ Cache error handling tests passed")
        except Exception:
            assert False, "Cache should handle Redis errors gracefully"


class TestCacheService:
    """Test cache service functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.cache_service = CacheService()
        
        # Mock Redis connection
        self.mock_redis = Mock()
        self.mock_redis.get.return_value = None
        self.mock_redis.set.return_value = True
        self.mock_redis.delete.return_value = 1
        
        # Patch Redis connection
        self.redis_patcher = patch('services.cache_service.redis_client', self.mock_redis)
        self.redis_patcher.start()
    
    def teardown_method(self):
        """Cleanup test environment."""
        self.redis_patcher.stop()
    
    async def test_async_cache_get(self):
        """Test async cache get functionality."""
        print("\n🧪 Testing Async Cache Get")
        print("=" * 35)
        
        # Test cache miss
        self.mock_redis.get.return_value = None
        result = await self.cache_service.get("test_key")
        assert result is None
        
        # Test cache hit
        cached_data = {"test": "async_data"}
        self.mock_redis.get.return_value = json.dumps(cached_data)
        result = await self.cache_service.get("test_key")
        assert result == cached_data
        
        print("✅ Async cache get tests passed")
    
    async def test_async_cache_set(self):
        """Test async cache set functionality."""
        print("\n🧪 Testing Async Cache Set")
        print("=" * 35)
        
        test_data = {"query": "async_test", "results": [1, 2, 3]}
        ttl = 600
        
        result = await self.cache_service.set("test_key", test_data, ttl)
        
        assert result is True
        self.mock_redis.set.assert_called_with(
            "test_key",
            json.dumps(test_data),
            ex=ttl
        )
        print("✅ Async cache set tests passed")
    
    async def test_async_cache_delete(self):
        """Test async cache delete functionality."""
        print("\n🧪 Testing Async Cache Delete")
        print("=" * 40)
        
        result = await self.cache_service.delete("test_key")
        
        assert result == 1
        self.mock_redis.delete.assert_called_once_with("test_key")
        print("✅ Async cache delete tests passed")
    
    async def test_cache_key_generation(self):
        """Test cache key generation."""
        print("\n🧪 Testing Cache Key Generation")
        print("=" * 40)
        
        # Test with different parameters
        key1 = self.cache_service.generate_key("search", query="test", page=1)
        key2 = self.cache_service.generate_key("search", query="test", page=2)
        key3 = self.cache_service.generate_key("search", query="test", page=1)
        
        assert key1 != key2  # Different pages should have different keys
        assert key1 == key3   # Same parameters should have same key
        assert "search" in key1
        assert "test" in key1
        assert "1" in key1
        
        print("✅ Cache key generation tests passed")
    
    async def test_cache_ttl_management(self):
        """Test cache TTL management."""
        print("\n🧪 Testing Cache TTL Management")
        print("=" * 40)
        
        # Test default TTL
        await self.cache_service.set("test_key", {"data": "test"})
        self.mock_redis.set.assert_called_with(
            "test_key",
            json.dumps({"data": "test"}),
            ex=900  # Default 15 minutes
        )
        
        # Test custom TTL
        await self.cache_service.set("test_key", {"data": "test"}, ttl=300)
        self.mock_redis.set.assert_called_with(
            "test_key",
            json.dumps({"data": "test"}),
            ex=300
        )
        
        print("✅ Cache TTL management tests passed")


class TestCachePerformance:
    """Test cache performance scenarios."""
    
    def test_cache_performance_bulk_operations(self):
        """Test cache performance with bulk operations."""
        print("\n🧪 Testing Cache Performance - Bulk Operations")
        print("=" * 55)
        
        cache_service = CacheService()
        
        # Mock Redis for performance testing
        with patch('services.cache_service.redis_client') as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = json.dumps({"test": "data"})
            
            # Test bulk set operations
            start_time = time.time()
            
            for i in range(100):
                cache_service.set(f"key_{i}", {"data": f"value_{i}"})
            
            end_time = time.time()
            operation_time = end_time - start_time
            
            assert operation_time < 1.0  # Should complete within 1 second
            assert mock_redis.set.call_count == 100
            
            print(f"✅ Bulk cache operations completed in {operation_time:.3f}s")
    
    def test_cache_memory_efficiency(self):
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
        with patch('services.cache_service.redis_client') as mock_redis:
            mock_redis.set.return_value = True
            
            # Should handle large data without issues
            result = cache_service.set("large_key", large_data)
            assert result is True
            
            # Verify data was serialized correctly
            call_args = mock_redis.set.call_args
            serialized_data = call_args[0][1]  # Second argument is the serialized data
            
            # Should be valid JSON
            parsed_data = json.loads(serialized_data)
            assert parsed_data["metadata"]["total"] == 1000
            assert len(parsed_data["results"]) == 1000
            
            print("✅ Cache memory efficiency tests passed")


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
    with patch('cache_manager.redis_client') as mock_redis:
        mock_redis.set.return_value = True
        mock_redis.get.return_value = json.dumps(search_results)
        
        # Test caching search results
        cache_manager.set("search:blue_shirt:1:25", search_results, 900)
        
        # Test retrieving cached results
        cached_results = cache_manager.get("search:blue_shirt:1:25")
        
        assert cached_results == search_results
        assert cached_results["query"] == "blue shirt"
        assert len(cached_results["results"]) == 2
        
        print("✅ Cache integration tests passed")


if __name__ == "__main__":
    # Run cache manager tests
    test_instance = TestCacheManager()
    test_instance.setup_method()
    
    test_instance.test_cache_get_miss()
    test_instance.test_cache_get_hit()
    test_instance.test_cache_set()
    test_instance.test_cache_delete()
    test_instance.test_cache_exists()
    test_instance.test_cache_ttl()
    test_instance.test_cache_clear()
    test_instance.test_cache_stats()
    test_instance.test_cache_error_handling()
    
    test_instance.teardown_method()
    
    # Run integration tests
    test_cache_integration()
    
    print("\n🎉 Cache services tests completed!") 