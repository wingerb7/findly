import time
import logging
from typing import Dict, Tuple, Optional
from cache_manager import cache_manager

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API endpoints using Redis."""
    
    def __init__(self):
        self.cache_manager = cache_manager
    
    def check_rate_limit(
        self, 
        identifier: str, 
        max_requests: int = 100, 
        window_seconds: int = 3600
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            (is_allowed, rate_limit_info)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Create rate limit key
            rate_limit_key = f"rate_limit:{identifier}:{window_start // window_seconds}"
            
            # Get current request count
            current_count = self.cache_manager.redis_client.get(rate_limit_key)
            current_count = int(current_count) if current_count else 0
            
            # Check if limit exceeded
            is_allowed = current_count < max_requests
            
            if is_allowed:
                # Increment counter
                self.cache_manager.redis_client.incr(rate_limit_key)
                # Set expiry to window_seconds
                self.cache_manager.redis_client.expire(rate_limit_key, window_seconds)
            
            # Calculate remaining requests and reset time
            remaining_requests = max(0, max_requests - current_count - (1 if is_allowed else 0))
            reset_time = window_start + window_seconds
            
            rate_limit_info = {
                "limit": max_requests,
                "remaining": remaining_requests,
                "reset": reset_time,
                "window_seconds": window_seconds
            }
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True, {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": int(time.time()) + window_seconds,
                "window_seconds": window_seconds,
                "error": "Rate limiting temporarily unavailable"
            }
    
    def get_rate_limit_headers(self, rate_limit_info: Dict[str, any]) -> Dict[str, str]:
        """Generate rate limit headers for response."""
        return {
            "X-RateLimit-Limit": str(rate_limit_info["limit"]),
            "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
            "X-RateLimit-Reset": str(rate_limit_info["reset"]),
            "X-RateLimit-Window": str(rate_limit_info["window_seconds"])
        }

# Global rate limiter instance
rate_limiter = RateLimiter() 