import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from redis.exceptions import RedisError
import psycopg2

logger = logging.getLogger(__name__)

class SearchAPIException(HTTPException):
    """Custom exception for search API errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}

class DatabaseConnectionError(SearchAPIException):
    """Database connection error."""
    def __init__(self, detail: str = "Database connection failed"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="DB_CONNECTION_ERROR"
        )

class EmbeddingGenerationError(SearchAPIException):
    """Embedding generation error."""
    def __init__(self, detail: str = "Failed to generate embedding"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="EMBEDDING_ERROR"
        )

class CacheError(SearchAPIException):
    """Cache operation error."""
    def __init__(self, detail: str = "Cache operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="CACHE_ERROR"
        )

class RateLimitExceededError(SearchAPIException):
    """Rate limit exceeded error."""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED"
        )

class ValidationError(SearchAPIException):
    """Validation error."""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context."""
    error_context = context or {}
    error_context.update({
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    })
    
    logger.error(f"API Error: {error_context}")

def handle_database_error(error: SQLAlchemyError, context: Dict[str, Any] = None) -> JSONResponse:
    """Handle database errors."""
    log_error(error, context)
    
    if isinstance(error, OperationalError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Database connection error",
                "error_code": "DB_CONNECTION_ERROR",
                "detail": "Database is temporarily unavailable",
                "context": context
            }
        )
    elif isinstance(error, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Data integrity error",
                "error_code": "DB_INTEGRITY_ERROR",
                "detail": "Invalid data provided",
                "context": context
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database error",
                "error_code": "DB_ERROR",
                "detail": "An unexpected database error occurred",
                "context": context
            }
        )

def handle_redis_error(error: RedisError, context: Dict[str, Any] = None) -> JSONResponse:
    """Handle Redis errors."""
    log_error(error, context)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Cache error",
            "error_code": "CACHE_ERROR",
            "detail": "Cache service is temporarily unavailable",
            "context": context
        }
    )

def handle_embedding_error(error: Exception, context: Dict[str, Any] = None) -> JSONResponse:
    """Handle embedding generation errors."""
    log_error(error, context)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Embedding generation error",
            "error_code": "EMBEDDING_ERROR",
            "detail": "Failed to generate search embeddings",
            "context": context
        }
    )

def handle_validation_error(error: Exception, context: Dict[str, Any] = None) -> JSONResponse:
    """Handle validation errors."""
    log_error(error, context)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "detail": str(error),
            "context": context
        }
    )

def handle_rate_limit_error(error: RateLimitExceededError, context: Dict[str, Any] = None) -> JSONResponse:
    """Handle rate limit errors."""
    log_error(error, context)
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "detail": error.detail,
            "context": context
        }
    )

def handle_generic_error(error: Exception, context: Dict[str, Any] = None) -> JSONResponse:
    """Handle generic errors."""
    log_error(error, context)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "detail": "An unexpected error occurred",
            "context": context
        }
    )

async def error_handler_middleware(request: Request, call_next):
    """Middleware for handling errors."""
    try:
        response = await call_next(request)
        return response
    except SearchAPIException as e:
        # Handle custom exceptions
        if isinstance(e, RateLimitExceededError):
            return handle_rate_limit_error(e, {"endpoint": request.url.path})
        elif isinstance(e, ValidationError):
            return handle_validation_error(e, {"endpoint": request.url.path})
        else:
            return handle_generic_error(e, {"endpoint": request.url.path})
    except SQLAlchemyError as e:
        return handle_database_error(e, {"endpoint": request.url.path})
    except RedisError as e:
        return handle_redis_error(e, {"endpoint": request.url.path})
    except Exception as e:
        return handle_generic_error(e, {"endpoint": request.url.path})

def validate_search_parameters(query: str, page: int, limit: int) -> None:
    """Validate search parameters."""
    if not query or not query.strip():
        raise ValidationError("Search query cannot be empty")
    
    if len(query.strip()) < 2:
        raise ValidationError("Search query must be at least 2 characters long")
    
    if page < 1:
        raise ValidationError("Page number must be greater than 0")
    
    if limit < 1 or limit > 100:
        raise ValidationError("Limit must be between 1 and 100")

def validate_analytics_parameters(start_date: str, end_date: str) -> None:
    """Validate analytics parameters."""
    try:
        from datetime import datetime
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")

def safe_database_operation(operation, context: Dict[str, Any] = None):
    """Safely execute database operations with error handling."""
    try:
        return operation()
    except SQLAlchemyError as e:
        log_error(e, context)
        raise DatabaseConnectionError(f"Database operation failed: {str(e)}")

def safe_cache_operation(operation, context: Dict[str, Any] = None):
    """Safely execute cache operations with error handling."""
    try:
        return operation()
    except RedisError as e:
        log_error(e, context)
        raise CacheError(f"Cache operation failed: {str(e)}")

def safe_embedding_operation(operation, context: Dict[str, Any] = None):
    """Safely execute embedding operations with error handling."""
    try:
        return operation()
    except Exception as e:
        log_error(e, context)
        raise EmbeddingGenerationError(f"Embedding operation failed: {str(e)}") 