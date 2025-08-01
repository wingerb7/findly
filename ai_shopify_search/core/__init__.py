#!/usr/bin/env python3
"""
Core package for Findly AI Search.

Contains essential components:
- Configuration
- Database connections
- Cache management
- Analytics
- Rate limiting
- Metrics
- Embeddings
"""

from .config import *
from .database import get_db, engine, SessionLocal
from .models import Base, Product, SearchAnalytics, QuerySuggestion, PopularSearch, SearchCorrection, SearchClick, FacetUsage, SearchPerformance
from .cache_manager import cache_manager
from .analytics_manager import analytics_manager
from .rate_limiter import rate_limiter
from .metrics import metrics_collector
from .embeddings import generate_embedding

__all__ = [
    'get_db',
    'engine', 
    'SessionLocal',
    'Base',
    'Product',
    'SearchAnalytics',
    'QuerySuggestion',
    'PopularSearch',
    'SearchCorrection',
    'SearchClick',
    'FacetUsage',
    'SearchPerformance',
    'cache_manager',
    'analytics_manager', 
    'rate_limiter',
    'metrics_collector',
    'generate_embedding'
] 