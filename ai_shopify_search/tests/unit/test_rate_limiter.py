#!/usr/bin/env python3
"""
Simple tests for rate_limiter.py - only testing what actually exists.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from rate_limiter import RateLimiter, rate_limiter

class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            assert limiter.cache_manager is not None
    
    def test_check_rate_limit_allowed(self):
        """Test rate limit check when request is allowed."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock current count below limit
            mock_redis.get.return_value = "50"  # Current count
            mock_redis.incr.return_value = 51
            mock_redis.expire.return_value = True
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=100, window_seconds=3600)
            
            assert is_allowed is True
            assert info["limit"] == 100
            assert info["remaining"] == 49  # 100 - 50 - 1
            assert "reset" in info
            assert info["window_seconds"] == 3600
            assert "error" not in info
            
            # Verify Redis calls
            mock_redis.get.assert_called_once()
            mock_redis.incr.assert_called_once()
            mock_redis.expire.assert_called_once()
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit is exceeded."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock current count at limit
            mock_redis.get.return_value = "100"  # Current count at limit
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=100, window_seconds=3600)
            
            assert is_allowed is False
            assert info["limit"] == 100
            assert info["remaining"] == 0  # 100 - 100 - 0
            assert "reset" in info
            assert info["window_seconds"] == 3600
            assert "error" not in info
            
            # Verify Redis calls
            mock_redis.get.assert_called_once()
            mock_redis.incr.assert_not_called()
            mock_redis.expire.assert_not_called()
    
    def test_check_rate_limit_no_existing_count(self):
        """Test rate limit check when no existing count."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock no existing count
            mock_redis.get.return_value = None
            mock_redis.incr.return_value = 1
            mock_redis.expire.return_value = True
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=100, window_seconds=3600)
            
            assert is_allowed is True
            assert info["limit"] == 100
            assert info["remaining"] == 99  # 100 - 0 - 1
            assert "reset" in info
            assert info["window_seconds"] == 3600
            assert "error" not in info
    
    def test_check_rate_limit_redis_error(self):
        """Test rate limit check when Redis has error."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock Redis error
            mock_redis.get.side_effect = Exception("Redis connection failed")
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=100, window_seconds=3600)
            
            # Should allow request when rate limiting fails
            assert is_allowed is True
            assert info["limit"] == 100
            assert info["remaining"] == 100
            assert "reset" in info
            assert info["window_seconds"] == 3600
            assert info["error"] == "Rate limiting temporarily unavailable"
    
    def test_check_rate_limit_different_parameters(self):
        """Test rate limit check with different parameters."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock current count
            mock_redis.get.return_value = "25"
            mock_redis.incr.return_value = 26
            mock_redis.expire.return_value = True
            
            is_allowed, info = limiter.check_rate_limit(
                "ip_192.168.1.1", 
                max_requests=50, 
                window_seconds=1800
            )
            
            assert is_allowed is True
            assert info["limit"] == 50
            assert info["remaining"] == 24  # 50 - 25 - 1
            assert info["window_seconds"] == 1800
            assert "error" not in info
    
    def test_get_rate_limit_headers(self):
        """Test rate limit headers generation."""
        limiter = RateLimiter()
        
        rate_limit_info = {
            "limit": 100,
            "remaining": 75,
            "reset": 1640995200,
            "window_seconds": 3600
        }
        
        headers = limiter.get_rate_limit_headers(rate_limit_info)
        
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "75"
        assert headers["X-RateLimit-Reset"] == "1640995200"
        assert headers["X-RateLimit-Window"] == "3600"
    
    def test_get_rate_limit_headers_with_error(self):
        """Test rate limit headers with error info."""
        limiter = RateLimiter()
        
        rate_limit_info = {
            "limit": 100,
            "remaining": 100,
            "reset": 1640995200,
            "window_seconds": 3600,
            "error": "Rate limiting temporarily unavailable"
        }
        
        headers = limiter.get_rate_limit_headers(rate_limit_info)
        
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "100"
        assert headers["X-RateLimit-Reset"] == "1640995200"
        assert headers["X-RateLimit-Window"] == "3600"

class TestGlobalRateLimiter:
    """Test global rate limiter instance."""
    
    def test_global_rate_limiter_exists(self):
        """Test that global rate limiter instance exists."""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)
    
    def test_global_rate_limiter_methods(self):
        """Test that global rate limiter has required methods."""
        assert hasattr(rate_limiter, 'check_rate_limit')
        assert hasattr(rate_limiter, 'get_rate_limit_headers')

class TestRateLimiterIntegration:
    """Test integration scenarios for RateLimiter."""
    
    def test_complete_rate_limit_workflow(self):
        """Test complete rate limit workflow."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # First request - no existing count
            mock_redis.get.return_value = None
            mock_redis.incr.return_value = 1
            mock_redis.expire.return_value = True
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=10, window_seconds=3600)
            
            assert is_allowed is True
            assert info["remaining"] == 9
            
            # Second request - increment count
            mock_redis.get.return_value = "1"
            mock_redis.incr.return_value = 2
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=10, window_seconds=3600)
            
            assert is_allowed is True
            assert info["remaining"] == 8
            
            # Tenth request - at limit
            mock_redis.get.return_value = "9"
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=10, window_seconds=3600)
            
            assert is_allowed is True
            assert info["remaining"] == 0
            
            # Eleventh request - exceeded limit
            mock_redis.get.return_value = "10"
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=10, window_seconds=3600)
            
            assert is_allowed is False
            assert info["remaining"] == 0
    
    def test_rate_limit_with_different_identifiers(self):
        """Test rate limiting with different identifiers."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock for first identifier
            mock_redis.get.return_value = "5"
            mock_redis.incr.return_value = 6
            mock_redis.expire.return_value = True
            
            is_allowed1, info1 = limiter.check_rate_limit("user_123", max_requests=10)
            
            # Mock for second identifier
            mock_redis.get.return_value = "3"
            mock_redis.incr.return_value = 4
            
            is_allowed2, info2 = limiter.check_rate_limit("ip_192.168.1.1", max_requests=10)
            
            assert is_allowed1 is True
            assert is_allowed2 is True
            assert info1["remaining"] == 4  # 10 - 5 - 1
            assert info2["remaining"] == 6  # 10 - 3 - 1
    
    def test_rate_limit_window_calculation(self):
        """Test rate limit window calculation."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Mock current time
            current_time = 1640995200  # Fixed timestamp
            with patch('time.time', return_value=current_time):
                mock_redis.get.return_value = "5"
                mock_redis.incr.return_value = 6
                mock_redis.expire.return_value = True
                
                is_allowed, info = limiter.check_rate_limit("user123", max_requests=10, window_seconds=3600)
                
                # Calculate expected reset time
                window_start = current_time - 3600
                expected_reset = window_start + 3600
                
                assert info["reset"] == expected_reset
                assert info["window_seconds"] == 3600
    
    def test_rate_limit_edge_cases(self):
        """Test rate limit edge cases."""
        with patch('rate_limiter.cache_manager') as mock_cache_manager:
            limiter = RateLimiter()
            mock_redis = Mock()
            mock_cache_manager.redis_client = mock_redis
            
            # Test with very small window
            mock_redis.get.return_value = "0"
            mock_redis.incr.return_value = 1
            mock_redis.expire.return_value = True
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=1, window_seconds=1)
            
            assert is_allowed is True
            assert info["limit"] == 1
            assert info["remaining"] == 0
            
            # Test with very large window
            mock_redis.get.return_value = "999"
            mock_redis.incr.return_value = 1000
            
            is_allowed, info = limiter.check_rate_limit("user123", max_requests=1000, window_seconds=86400)
            
            assert is_allowed is True
            assert info["limit"] == 1000
            assert info["remaining"] == 0
            assert info["window_seconds"] == 86400 