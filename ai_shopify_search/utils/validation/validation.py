#!/usr/bin/env python3
"""
Input validation and security utilities for the search API.
"""

import re
import hashlib
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator, Field
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class SearchQuery(BaseModel):
    """Validated search query model."""
    
    query: str = Field(..., min_length=2, max_length=200, description="Search query")
    page: int = Field(1, ge=1, le=1000, description="Page number")
    limit: int = Field(25, ge=1, le=100, description="Results per page")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate and sanitize search query."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', v.strip())
        
        if len(sanitized) < 2:
            raise ValueError('Query must be at least 2 characters')
        
        if len(sanitized) > 200:
            raise ValueError('Query too long (max 200 characters)')
        
        return sanitized
    
    @field_validator('page')
    @classmethod
    def validate_page(cls, v):
        """Validate page number."""
        if v < 1:
            raise ValueError('Page must be >= 1')
        if v > 1000:
            raise ValueError('Page number too high (max 1000)')
        return v
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        """Validate limit parameter."""
        if v < 1:
            raise ValueError('Limit must be >= 1')
        if v > 100:
            raise ValueError('Limit too high (max 100)')
        return v

class AISearchQuery(SearchQuery):
    """Validated AI search query model."""
    
    source_language: Optional[str] = Field(None, max_length=10, description="Source language (ISO 639-1)")
    target_language: str = Field("en", max_length=10, description="Target language (ISO 639-1)")
    
    @field_validator('source_language')
    @classmethod
    def validate_source_language(cls, v):
        """Validate source language code."""
        if v is not None:
            if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
                raise ValueError('Invalid source language format (use ISO 639-1)')
        return v
    
    @field_validator('target_language')
    @classmethod
    def validate_target_language(cls, v):
        """Validate target language code."""
        if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
            raise ValueError('Invalid target language format (use ISO 639-1)')
        return v

class AnalyticsQuery(BaseModel):
    """Validated analytics query model."""
    
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    search_type: Optional[str] = Field(None, description="Search type filter")
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Invalid date format. Use YYYY-MM-DD')
        
        # Basic date validation
        try:
            from datetime import datetime
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Invalid date')
        
        return v
    
    @field_validator('search_type')
    @classmethod
    def validate_search_type(cls, v):
        """Validate search type."""
        if v is not None and v not in ['basic', 'ai', 'faceted']:
            raise ValueError('Invalid search type. Must be basic, ai, or faceted')
        return v

def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query to prevent injection attacks.
    
    Args:
        query: Raw search query
        
    Returns:
        Sanitized search query
        
    Raises:
        ValueError: If query is invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', query.strip())
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    # Ensure minimum length
    if len(sanitized) < 2:
        raise ValueError("Search query must be at least 2 characters")
    
    return sanitized

def validate_price_range(min_price: Optional[float], max_price: Optional[float]) -> None:
    """
    Validate price range parameters.
    
    Args:
        min_price: Minimum price
        max_price: Maximum price
        
    Raises:
        ValueError: If price range is invalid
    """
    if min_price is not None:
        if min_price < 0:
            raise ValueError("Minimum price cannot be negative")
        if min_price > 1000000:
            raise ValueError("Minimum price too high")
    
    if max_price is not None:
        if max_price < 0:
            raise ValueError("Maximum price cannot be negative")
        if max_price > 1000000:
            raise ValueError("Maximum price too high")
    
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise ValueError("Minimum price cannot be greater than maximum price")

def validate_cache_key(key: str) -> str:
    """
    Validate and sanitize cache key.
    
    Args:
        key: Raw cache key
        
    Returns:
        Sanitized cache key
        
    Raises:
        ValueError: If key is invalid
    """
    if not key or not key.strip():
        raise ValueError("Cache key cannot be empty")
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', key.strip())
    
    # Limit length
    if len(sanitized) > 500:
        sanitized = sanitized[:500]
    
    return sanitized

def generate_secure_cache_key(prefix: str, **kwargs) -> str:
    """
    Generate a secure cache key with hash.
    
    Args:
        prefix: Cache key prefix
        **kwargs: Key-value pairs to include in cache key
        
    Returns:
        Secure cache key
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

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or not api_key.strip():
        return False
    
    # Basic API key validation (adjust based on your key format)
    if len(api_key) < 10:
        return False
    
    # Check for common patterns
    if re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        return True
    
    return False

def validate_rate_limit_identifier(identifier: str) -> str:
    """
    Validate rate limit identifier.
    
    Args:
        identifier: Rate limit identifier (usually IP address)
        
    Returns:
        Sanitized identifier
        
    Raises:
        ValueError: If identifier is invalid
    """
    if not identifier or not identifier.strip():
        raise ValueError("Rate limit identifier cannot be empty")
    
    # Basic validation for IP addresses
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', identifier):
        # Validate IP octets
        parts = identifier.split('.')
        try:
            octets = [int(part) for part in parts]
            if all(0 <= octet <= 255 for octet in octets):
                return identifier
        except ValueError:
            pass
    
    # For other identifiers, just sanitize
    sanitized = re.sub(r'[<>"\']', '', identifier.strip())
    return sanitized[:100]  # Limit length

class SecurityConfig:
    """Security configuration settings."""
    
    # Rate limiting
    MAX_REQUESTS_PER_HOUR = 1000
    MAX_REQUESTS_PER_MINUTE = 100
    
    # Input validation
    MAX_QUERY_LENGTH = 200
    MAX_CACHE_KEY_LENGTH = 500
    MAX_API_KEY_LENGTH = 100
    
    # Price validation
    MIN_PRICE = 0.0
    MAX_PRICE = 1000000.0
    
    # Session security
    SESSION_EXPIRY_HOURS = 24
    MAX_SESSION_LENGTH = 1000

def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO") -> None:
    """
    Log security events for monitoring.
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Log severity level
    """
    log_message = f"SECURITY_EVENT: {event_type} - {details}"
    
    if severity == "WARNING":
        logger.warning(log_message)
    elif severity == "ERROR":
        logger.error(log_message)
    else:
        logger.info(log_message) 