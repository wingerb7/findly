import logging
import json
import hashlib
import redis
from typing import Optional, Dict, Any
from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, CACHE_TTL, SEARCH_CACHE_TTL, AI_SEARCH_CACHE_TTL

logger = logging.getLogger(__name__)

class CacheManager:
    """Centralized cache management for Redis operations."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB, 
            password=REDIS_PASSWORD,
            decode_responses=True
        )
    
    def get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key based on parameters."""
        params_str = json.dumps(kwargs, sort_keys=True)
        return f"{prefix}:{hashlib.md5(params_str.encode()).hexdigest()}"
    
    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve result from cache."""
        try:
            cached = self.redis_client.get(cache_key)
            return json.loads(cached) if cached else None
        except Exception as e:
            logger.warning(f"Cache error: {e}")
            return None
    
    def set_cached_result(self, cache_key: str, data: Dict[str, Any], ttl: int = CACHE_TTL) -> None:
        """Store result in cache."""
        try:
            self.redis_client.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def invalidate_product_cache(self) -> None:
        """Invalidate all product-related cache."""
        try:
            keys = self.redis_client.keys("product:*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            keys = self.redis_client.keys("product:*")
            search_keys = self.redis_client.keys("search:*")
            ai_search_keys = self.redis_client.keys("ai_search:*")
            
            return {
                "total_cache_keys": len(keys),
                "search_cache_keys": len(search_keys),
                "ai_search_cache_keys": len(ai_search_keys),
                "cache_info": {
                    "search_ttl": SEARCH_CACHE_TTL,
                    "ai_search_ttl": AI_SEARCH_CACHE_TTL,
                    "default_ttl": CACHE_TTL
                }
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_cache(self) -> None:
        """Clear all cache."""
        try:
            self.invalidate_product_cache()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# Global cache manager instance
cache_manager = CacheManager() 