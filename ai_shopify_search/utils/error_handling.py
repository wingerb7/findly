#!/usr/bin/env python3
"""
Comprehensive error handling system with custom exceptions and error recovery.
"""

import logging
import traceback
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories."""
    VALIDATION = "validation"
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class BaseError(Exception):
    """Base error class for all custom exceptions."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.retryable = retryable
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()

class ValidationError(BaseError):
    """Validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details={"field": field, "value": value},
            retryable=False
        )

class DatabaseError(BaseError):
    """Database error."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        retryable: bool = True
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details={"operation": operation, "table": table},
            retryable=retryable
        )

class NetworkError(BaseError):
    """Network error."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            details={"url": url, "status_code": status_code},
            retryable=True
        )

class AuthenticationError(BaseError):
    """Authentication error."""
    
    def __init__(self, message: str, user_id: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details={"user_id": user_id},
            retryable=False
        )

class AuthorizationError(BaseError):
    """Authorization error."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, resource: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            details={"user_id": user_id, "resource": resource},
            retryable=False
        )

class RateLimitError(BaseError):
    """Rate limit error."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details={"retry_after": retry_after},
            retryable=True
        )

class CacheError(BaseError):
    """Cache error."""
    
    def __init__(self, message: str, operation: Optional[str] = None, key: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CACHE,
            severity=ErrorSeverity.LOW,
            details={"operation": operation, "key": key},
            retryable=True
        )

class ExternalAPIError(BaseError):
    """External API error."""
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            details={"api_name": api_name, "endpoint": endpoint, "status_code": status_code},
            retryable=True
        )

class SystemError(BaseError):
    """System error."""
    
    def __init__(self, message: str, component: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            details={"component": component},
            retryable=False
        )

class ErrorHandler:
    """Centralized error handler with recovery strategies."""
    
    def __init__(self):
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.error_stats: Dict[str, int] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default error recovery strategies."""
        
        # Database errors - retry with exponential backoff
        self.recovery_strategies[ErrorCategory.DATABASE] = self._retry_with_backoff
        
        # Network errors - retry with exponential backoff
        self.recovery_strategies[ErrorCategory.NETWORK] = self._retry_with_backoff
        
        # Cache errors - fallback to database
        self.recovery_strategies[ErrorCategory.CACHE] = self._fallback_to_database
        
        # Rate limit errors - wait and retry
        self.recovery_strategies[ErrorCategory.RATE_LIMIT] = self._wait_and_retry
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """Register a callback for specific error categories."""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def handle_error(self, error: BaseError) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging and recovery.
        
        Args:
            error: The error to handle
            
        Returns:
            Error handling result
        """
        try:
            # Log error
            self._log_error(error)
            
            # Update statistics
            self._update_error_stats(error)
            
            # Execute callbacks
            self._execute_callbacks(error)
            
            # Attempt recovery
            recovery_result = self._attempt_recovery(error)
            
            return {
                "error_id": id(error),
                "category": error.category.value,
                "severity": error.severity.value,
                "retryable": error.retryable,
                "recovery_attempted": recovery_result["attempted"],
                "recovery_successful": recovery_result["successful"],
                "timestamp": error.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return {"error": "Error handler failed"}
    
    def _log_error(self, error: BaseError):
        """Log error with appropriate level."""
        log_message = f"{error.category.value.upper()} ERROR: {error.message}"
        
        if error.details:
            log_message += f" | Details: {error.details}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _update_error_stats(self, error: BaseError):
        """Update error statistics."""
        category_key = f"{error.category.value}_{error.severity.value}"
        self.error_stats[category_key] = self.error_stats.get(category_key, 0) + 1
    
    def _execute_callbacks(self, error: BaseError):
        """Execute registered callbacks for the error category."""
        if error.category in self.error_callbacks:
            for callback in self.error_callbacks[error.category]:
                try:
                    callback(error)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
    
    def _attempt_recovery(self, error: BaseError) -> Dict[str, bool]:
        """Attempt error recovery using registered strategies."""
        if not error.retryable or error.category not in self.recovery_strategies:
            return {"attempted": False, "successful": False}
        
        try:
            strategy = self.recovery_strategies[error.category]
            result = strategy(error)
            return {"attempted": True, "successful": result}
        except Exception as e:
            logger.error(f"Recovery strategy failed: {e}")
            return {"attempted": True, "successful": False}
    
    async def _retry_with_backoff(self, error: BaseError) -> bool:
        """Retry operation with exponential backoff."""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(base_delay * (2 ** attempt))
                # Here you would retry the original operation
                # For now, we'll just return True to simulate success
                return True
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
        
        return False
    
    async def _fallback_to_database(self, error: BaseError) -> bool:
        """Fallback to database when cache fails."""
        try:
            # Simulate fallback to database
            logger.info("Falling back to database due to cache error")
            return True
        except Exception as e:
            logger.error(f"Database fallback failed: {e}")
            return False
    
    async def _wait_and_retry(self, error: BaseError) -> bool:
        """Wait and retry for rate limit errors."""
        try:
            retry_after = error.details.get("retry_after", 60)
            await asyncio.sleep(retry_after)
            return True
        except Exception as e:
            logger.error(f"Wait and retry failed: {e}")
            return False
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "error_counts": self.error_stats,
            "total_errors": sum(self.error_stats.values()),
            "categories": list(set(key.split("_")[0] for key in self.error_stats.keys())),
            "severities": list(set(key.split("_")[1] for key in self.error_stats.keys()))
        }

# Global error handler instance
error_handler = ErrorHandler()

def handle_errors(func):
    """Decorator to automatically handle errors in functions."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseError as e:
            error_handler.handle_error(e)
            raise
        except Exception as e:
            # Convert generic exceptions to BaseError
            base_error = BaseError(
                message=str(e),
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                details={"function": func.__name__},
                retryable=False
            )
            error_handler.handle_error(base_error)
            raise base_error
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseError as e:
            error_handler.handle_error(e)
            raise
        except Exception as e:
            # Convert generic exceptions to BaseError
            base_error = BaseError(
                message=str(e),
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                details={"function": func.__name__},
                retryable=False
            )
            error_handler.handle_error(base_error)
            raise base_error
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry operations on specific errors."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except BaseError as e:
                    last_exception = e
                    if e.retryable and attempt < max_retries - 1:
                        logger.warning(f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries}): {e.message}")
                        await asyncio.sleep(delay * (2 ** attempt))
                    else:
                        break
                except Exception as e:
                    # Don't retry on non-BaseError exceptions
                    raise e
            
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except BaseError as e:
                    last_exception = e
                    if e.retryable and attempt < max_retries - 1:
                        logger.warning(f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries}): {e.message}")
                        import time
                        time.sleep(delay * (2 ** attempt))
                    else:
                        break
                except Exception as e:
                    # Don't retry on non-BaseError exceptions
                    raise e
            
            if last_exception:
                raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def validate_input(validation_func: Callable):
    """Decorator to validate function inputs."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                validation_func(*args, **kwargs)
                return await func(*args, **kwargs)
            except Exception as e:
                raise ValidationError(f"Input validation failed: {e}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                validation_func(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                raise ValidationError(f"Input validation failed: {e}")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Error monitoring and alerting
class ErrorMonitor:
    """Monitor errors and send alerts for critical issues."""
    
    def __init__(self):
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.MEDIUM: 10
        }
        self.error_counts = {}
    
    def check_alerts(self, error: BaseError):
        """Check if an alert should be sent for this error."""
        severity_key = f"{error.category.value}_{error.severity.value}"
        current_count = self.error_counts.get(severity_key, 0) + 1
        self.error_counts[severity_key] = current_count
        
        threshold = self.alert_thresholds.get(error.severity, float('inf'))
        
        if current_count >= threshold:
            self._send_alert(error, current_count)
    
    def _send_alert(self, error: BaseError, count: int):
        """Send alert for critical error."""
        alert_message = f"ALERT: {count} {error.severity.value} {error.category.value} errors detected"
        logger.critical(alert_message)
        # Here you would integrate with your alerting system (email, Slack, etc.)

# Global error monitor instance
error_monitor = ErrorMonitor()

# Register error monitor with error handler
error_handler.register_error_callback(ErrorCategory.SYSTEM, error_monitor.check_alerts)
error_handler.register_error_callback(ErrorCategory.DATABASE, error_monitor.check_alerts) 