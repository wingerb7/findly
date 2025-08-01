#!/usr/bin/env python3
"""
Cache Service for managing Redis caching operations.
"""

import logging
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta
import redis
from core.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

logger = logging.getLogger(__name__)

class CacheService:
    """Specialized service for Redis caching operations."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.default_ttl = 3600  # 1 hour default
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key '{key}': {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except (redis.RedisError, TypeError) as e:
            logger.warning(f"Cache set error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError as e:
            logger.warning(f"Cache delete error for key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError as e:
            logger.warning(f"Cache exists error for key '{key}': {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.expire(key, ttl))
        except redis.RedisError as e:
            logger.warning(f"Cache expire error for key '{key}': {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "ai_search:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.warning(f"Cache clear pattern error for '{pattern}': {e}")
            return 0
    
    async def clear_all(self) -> int:
        """
        Clear all cache data.
        
        Returns:
            Number of keys deleted
        """
        try:
            return self.redis_client.flushdb()
        except redis.RedisError as e:
            logger.warning(f"Cache clear all error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            info = self.redis_client.info()
            return {
                "total_keys": info.get("db0", {}).get("keys", 0),
                "memory_usage": info.get("used_memory_human", "Unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_misses", 1), 1)
            }
        except redis.RedisError as e:
            logger.warning(f"Cache stats error: {e}")
            return {
                "error": str(e),
                "total_keys": 0,
                "memory_usage": "Unknown",
                "connected_clients": 0,
                "uptime": 0,
                "hit_rate": 0
            }
    
    async def health_check(self) -> bool:
        """
        Check if Redis is healthy.
        
        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            self.redis_client.ping()
            return True
        except redis.RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a cache key from prefix and parameters.
        
        Args:
            prefix: Key prefix
            **kwargs: Key-value pairs to include in key
            
        Returns:
            Generated cache key
        """
        # Sort kwargs for consistent ordering
        sorted_items = sorted(kwargs.items())
        
        # Create key string
        key_parts = [prefix]
        for key, value in sorted_items:
            if value is not None:
                key_parts.append(f"{key}:{value}")
        
        key_string = "|".join(key_parts)
        
        # Generate hash for long keys
        if len(key_string) > 100:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
            return f"{prefix}:{key_hash}"
        
        return key_string
    
    async def get_or_set(
        self, 
        key: str, 
        getter_func, 
        ttl: Optional[int] = None,
        *args, 
        **kwargs
    ) -> Any:
        """
        Get from cache or set using getter function.
        
        Args:
            key: Cache key
            getter_func: Function to call if cache miss
            ttl: Time to live in seconds
            *args: Arguments for getter function
            **kwargs: Keyword arguments for getter function
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss, compute value
        try:
            value = getter_func(*args, **kwargs)
            await self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Error in get_or_set for key '{key}': {e}")
            raise
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Redis pattern to match
            
        Returns:
            Number of keys invalidated
        """
        return await self.clear_pattern(pattern)
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get detailed memory usage information.
        
        Returns:
            Dictionary with memory usage details
        """
        try:
            info = self.redis_client.info("memory")
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "Unknown"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "Unknown"),
                "used_memory_rss": info.get("used_memory_rss", 0),
                "used_memory_rss_human": info.get("used_memory_rss_human", "Unknown")
            }
        except redis.RedisError as e:
            logger.warning(f"Memory usage error: {e}")
            return {"error": str(e)} 