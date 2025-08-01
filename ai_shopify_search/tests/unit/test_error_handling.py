#!/usr/bin/env python3
"""
Simple tests for utils/error_handling.py - only testing what actually exists.
"""

import pytest
import asyncio
from utils.error_handling import (
    BaseError, ValidationError, DatabaseError, NetworkError,
    AuthenticationError, AuthorizationError, RateLimitError,
    CacheError, ExternalAPIError, SystemError,
    ErrorHandler, ErrorMonitor, ErrorSeverity, ErrorCategory,
    handle_errors, retry_on_error, validate_input
)

class TestBaseError:
    """Test BaseError class."""
    
    def test_base_error_creation(self):
        """Test creating a base error."""
        error = BaseError("Test error message")
        assert error.message == "Test error message"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.retryable is False
        assert error.timestamp is not None
        assert error.traceback is not None
    
    def test_base_error_with_details(self):
        """Test creating a base error with details."""
        details = {"key": "value", "number": 123}
        error = BaseError(
            "Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            retryable=True
        )
        assert error.message == "Test error"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == details
        assert error.retryable is True

class TestValidationError:
    """Test ValidationError class."""
    
    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError("Invalid input", field="email", value="invalid@")
        assert error.message == "Invalid input"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert error.retryable is False
        assert error.details["field"] == "email"
        assert error.details["value"] == "invalid@"

class TestDatabaseError:
    """Test DatabaseError class."""
    
    def test_database_error_creation(self):
        """Test creating a database error."""
        error = DatabaseError("Connection failed", operation="SELECT", table="users")
        assert error.message == "Connection failed"
        assert error.category == ErrorCategory.DATABASE
        assert error.severity == ErrorSeverity.HIGH
        assert error.retryable is True
        assert error.details["operation"] == "SELECT"
        assert error.details["table"] == "users"
    
    def test_database_error_not_retryable(self):
        """Test creating a non-retryable database error."""
        error = DatabaseError("Schema error", retryable=False)
        assert error.retryable is False

class TestNetworkError:
    """Test NetworkError class."""
    
    def test_network_error_creation(self):
        """Test creating a network error."""
        error = NetworkError("Connection timeout", url="https://api.example.com", status_code=408)
        assert error.message == "Connection timeout"
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.retryable is True
        assert error.details["url"] == "https://api.example.com"
        assert error.details["status_code"] == 408

class TestAuthenticationError:
    """Test AuthenticationError class."""
    
    def test_authentication_error_creation(self):
        """Test creating an authentication error."""
        error = AuthenticationError("Invalid credentials", user_id="user123")
        assert error.message == "Invalid credentials"
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.retryable is False
        assert error.details["user_id"] == "user123"

class TestAuthorizationError:
    """Test AuthorizationError class."""
    
    def test_authorization_error_creation(self):
        """Test creating an authorization error."""
        error = AuthorizationError("Access denied", user_id="user123", resource="/admin")
        assert error.message == "Access denied"
        assert error.category == ErrorCategory.AUTHORIZATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.retryable is False
        assert error.details["user_id"] == "user123"
        assert error.details["resource"] == "/admin"

class TestRateLimitError:
    """Test RateLimitError class."""
    
    def test_rate_limit_error_creation(self):
        """Test creating a rate limit error."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert error.message == "Rate limit exceeded"
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.retryable is True
        assert error.details["retry_after"] == 60

class TestCacheError:
    """Test CacheError class."""
    
    def test_cache_error_creation(self):
        """Test creating a cache error."""
        error = CacheError("Redis connection failed", operation="GET", key="user:123")
        assert error.message == "Redis connection failed"
        assert error.category == ErrorCategory.CACHE
        assert error.severity == ErrorSeverity.LOW  # Implementation uses LOW severity
        assert error.retryable is True
        assert error.details["operation"] == "GET"
        assert error.details["key"] == "user:123"

class TestExternalAPIError:
    """Test ExternalAPIError class."""
    
    def test_external_api_error_creation(self):
        """Test creating an external API error."""
        error = ExternalAPIError(
            "API call failed",
            api_name="shopify",
            endpoint="/products",
            status_code=500
        )
        assert error.message == "API call failed"
        assert error.category == ErrorCategory.EXTERNAL_API
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.retryable is True
        assert error.details["api_name"] == "shopify"
        assert error.details["endpoint"] == "/products"
        assert error.details["status_code"] == 500

class TestSystemError:
    """Test SystemError class."""
    
    def test_system_error_creation(self):
        """Test creating a system error."""
        error = SystemError("Memory allocation failed", component="cache_manager")
        assert error.message == "Memory allocation failed"
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.retryable is False
        assert error.details["component"] == "cache_manager"

class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler()
        assert handler.error_stats is not None
        assert handler.error_callbacks is not None
        assert handler.recovery_strategies is not None
    
    def test_handle_error(self):
        """Test error handling."""
        handler = ErrorHandler()
        error = ValidationError("Test error")
        
        result = handler.handle_error(error)
        assert "error_id" in result
        assert "category" in result
        assert "recovery_attempted" in result
        assert result["category"] == "validation"
    
    def test_register_error_callback(self):
        """Test registering error callbacks."""
        handler = ErrorHandler()
        
        def test_callback(error):
            return {"custom": "handled"}
        
        handler.register_error_callback(ErrorCategory.VALIDATION, test_callback)
        assert ErrorCategory.VALIDATION in handler.error_callbacks
    
    def test_get_error_stats(self):
        """Test getting error statistics."""
        handler = ErrorHandler()
        
        # Handle some errors
        handler.handle_error(ValidationError("Error 1"))
        handler.handle_error(DatabaseError("Error 2"))
        handler.handle_error(ValidationError("Error 3"))
        
        stats = handler.get_error_stats()
        assert "total_errors" in stats
        assert "categories" in stats
        assert "severities" in stats
        assert stats["total_errors"] == 3

class TestErrorMonitor:
    """Test ErrorMonitor class."""
    
    def test_error_monitor_initialization(self):
        """Test error monitor initialization."""
        monitor = ErrorMonitor()
        assert monitor.error_counts is not None
        assert monitor.alert_thresholds is not None
    
    def test_check_alerts(self):
        """Test alert checking."""
        monitor = ErrorMonitor()
        error = ValidationError("Test error")
        
        # Should not raise any exceptions
        monitor.check_alerts(error)

class TestDecorators:
    """Test error handling decorators."""
    
    @pytest.mark.asyncio
    async def test_handle_errors_decorator_async(self):
        """Test @handle_errors decorator with async function."""
        @handle_errors
        async def test_async_func():
            raise ValidationError("Test error")
        
        # The decorator should catch the exception and return error info
        with pytest.raises(ValidationError):
            await test_async_func()
    
    def test_handle_errors_decorator_sync(self):
        """Test @handle_errors decorator with sync function."""
        @handle_errors
        def test_sync_func():
            raise ValidationError("Test error")
        
        # The decorator should catch the exception and return error info
        with pytest.raises(ValidationError):
            test_sync_func()
    
    @pytest.mark.asyncio
    async def test_retry_on_error_decorator_async(self):
        """Test @retry_on_error decorator with async function."""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay=0.1)
        async def test_async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseError("Temporary error")
            return "success"
        
        # The decorator should retry and eventually fail
        with pytest.raises(DatabaseError):
            await test_async_func()
        assert call_count == 2  # Should have tried 2 times (max_retries=2 means 2 attempts total)
    
    def test_retry_on_error_decorator_sync(self):
        """Test @retry_on_error decorator with sync function."""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay=0.1)
        def test_sync_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseError("Temporary error")
            return "success"
        
        # The decorator should retry and eventually fail
        with pytest.raises(DatabaseError):
            test_sync_func()
        assert call_count == 2  # Should have tried 2 times (max_retries=2 means 2 attempts total)
    
    @pytest.mark.asyncio
    async def test_validate_input_decorator_async(self):
        """Test @validate_input decorator with async function."""
        def validation_func(value):
            if value < 0:
                raise ValidationError("Value must be positive")
            return True
        
        @validate_input(validation_func)
        async def test_async_func(value):
            return value * 2
        
        # Valid input
        result = await test_async_func(5)
        assert result == 10
        
        # Invalid input
        with pytest.raises(ValidationError):
            await test_async_func(-5)
    
    def test_validate_input_decorator_sync(self):
        """Test @validate_input decorator with sync function."""
        def validation_func(value):
            if value < 0:
                raise ValidationError("Value must be positive")
            return True
        
        @validate_input(validation_func)
        def test_sync_func(value):
            return value * 2
        
        # Valid input
        result = test_sync_func(5)
        assert result == 10
        
        # Invalid input
        with pytest.raises(ValidationError):
            test_sync_func(-5)

class TestErrorSeverity:
    """Test ErrorSeverity enum."""
    
    def test_error_severity_values(self):
        """Test error severity enum values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

class TestErrorCategory:
    """Test ErrorCategory enum."""
    
    def test_error_category_values(self):
        """Test error category enum values."""
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.AUTHORIZATION.value == "authorization"
        assert ErrorCategory.RATE_LIMIT.value == "rate_limit"
        assert ErrorCategory.CACHE.value == "cache"
        assert ErrorCategory.EXTERNAL_API.value == "external_api"
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.UNKNOWN.value == "unknown" 