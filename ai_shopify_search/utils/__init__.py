#!/usr/bin/env python3
"""
Utilities package for Findly AI Search.

Contains utility functions organized in subpackages:
- validation: Input validation and security
- search: Search-related utilities
- privacy: Privacy and data protection
- error_handling: Error handling utilities
"""

from .validation import *
from .search import *
from .privacy import *
from .error_handling import *

__all__ = [
    # Validation utilities
    'AISearchQuery',
    'AnalyticsQuery',
    'sanitize_search_query',
    'validate_price_range',
    'generate_secure_cache_key',
    'validate_rate_limit_identifier',
    'log_security_event',
    
    # Search utilities
    'FuzzySearch',
    
    # Privacy utilities
    'sanitize_log_data',
    'anonymize_ip',
    'sanitize_user_agent',
    'generate_session_id',
    'is_session_expired',
    'DataRetentionManager',
    'PRIVACY_CONFIG',
    
    # Error handling utilities
    'BaseError',
    'ValidationError',
    'DatabaseError',
    'handle_error'
] 