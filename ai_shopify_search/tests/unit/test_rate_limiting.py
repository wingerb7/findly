#!/usr/bin/env python3
"""
Test script for rate limiting functionality in the enhanced benchmark.
"""

import asyncio
import time
from ai_shopify_search.features.enhanced_benchmark_search import BenchmarkRateLimiter, BenchmarkCache, BENCHMARK_CONFIG

async def test_rate_limiter():
    """Test the rate limiter functionality."""
    print("🧪 Testing Rate Limiter...")
    
    # Create rate limiter with small window for testing
    rate_limiter = BenchmarkRateLimiter(max_requests=3, window_seconds=5)
    
    print(f"Rate limit: 3 requests per 5 seconds")
    
    # Test normal requests
    for i in range(5):
        can_proceed, wait_time = await rate_limiter.check_rate_limit()
        print(f"Request {i+1}: {'✅ Allowed' if can_proceed else f'❌ Blocked (wait {wait_time:.1f}s)'}")
        
        if not can_proceed:
            print(f"   Waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
            can_proceed, _ = await rate_limiter.check_rate_limit()
            print(f"   After wait: {'✅ Allowed' if can_proceed else '❌ Still blocked'}")
        
        # Small delay between requests
        await asyncio.sleep(0.1)

async def test_cache():
    """Test the cache functionality."""
    print("\n🧪 Testing Cache...")
    
    cache = BenchmarkCache(ttl_seconds=5)
    
    # Test cache set/get
    test_data = {"results": ["test1", "test2"], "count": 2}
    cache.set("test_query", "/api/test", test_data)
    
    # Should get cached data
    cached_data = cache.get("test_query", "/api/test")
    print(f"Cache hit: {'✅ Yes' if cached_data else '❌ No'}")
    print(f"Cached data: {cached_data}")
    
    # Test cache miss with different query
    cached_data = cache.get("different_query", "/api/test")
    print(f"Cache miss: {'✅ Yes' if not cached_data else '❌ No'}")
    
    # Test cache expiration
    print("Waiting 6 seconds for cache to expire...")
    await asyncio.sleep(6)
    cached_data = cache.get("test_query", "/api/test")
    print(f"Cache expired: {'✅ Yes' if not cached_data else '❌ No'}")

async def test_configuration():
    """Test the configuration system."""
    print("\n🧪 Testing Configuration...")
    
    print("Default configuration:")
    for key, value in BENCHMARK_CONFIG.items():
        print(f"  {key}: {value}")
    
    # Test custom configuration
    custom_config = BENCHMARK_CONFIG.copy()
    custom_config.update({
        "max_queries": 50,
        "request_delay": 1.0,
        "batch_size": 3
    })
    
    print("\nCustom configuration:")
    for key, value in custom_config.items():
        print(f"  {key}: {value}")

async def main():
    """Run all tests."""
    print("🚀 Starting Rate Limiting Tests\n")
    
    await test_rate_limiter()
    await test_cache()
    await test_configuration()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 