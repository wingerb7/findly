#!/usr/bin/env python3
"""
API package for Findly AI Search.

Contains API-related components:
- Error handlers
- Shopify client
- API routes and endpoints
"""

from .error_handlers import error_handler_middleware

__all__ = [
    'error_handler_middleware'
] 