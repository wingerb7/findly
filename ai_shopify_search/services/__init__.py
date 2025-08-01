#!/usr/bin/env python3
"""
Services Package

Contains service classes for integrating various AI learning features into the API.
"""

# Core services
from .service_factory import ServiceFactory, get_service_factory
from .ai_search_service import AISearchService
from .cache_service import CacheService
from .analytics_service import AnalyticsService
from .autocomplete_service import AutocompleteService
from .suggestion_service import SuggestionService

# AI feature services
from .transfer_learning_service import TransferLearningService
from .knowledge_base_service import KnowledgeBaseService
from .baseline_generator_service import BaselineGeneratorService
from .pattern_learning_service import PatternLearningService
from .facets_service import FacetsService
from .smart_autocomplete import SmartAutocompleteService

__all__ = [
    # Core services
    "ServiceFactory",
    "get_service_factory",
    "AISearchService",
    "CacheService", 
    "AnalyticsService",
    "AutocompleteService",
    "SuggestionService",
    
    # AI feature services
    "TransferLearningService",
    "KnowledgeBaseService",
    "BaselineGeneratorService",
    "PatternLearningService",
    "FacetsService",
    "SmartAutocompleteService"
] 