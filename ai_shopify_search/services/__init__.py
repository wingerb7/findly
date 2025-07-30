#!/usr/bin/env python3
"""
Service factory for managing all search-related services.
"""

from .ai_search_service import AISearchService
from .suggestion_service import SuggestionService
from .cache_service import CacheService
from .analytics_service import AnalyticsService
from .autocomplete_service import AutocompleteService

class ServiceFactory:
    """Factory for creating and managing service instances."""
    
    def __init__(self):
        self._services = {}
    
    def get_ai_search_service(self) -> AISearchService:
        """Get AI search service instance."""
        if 'ai_search' not in self._services:
            cache_service = self.get_cache_service()
            analytics_service = self.get_analytics_service()
            self._services['ai_search'] = AISearchService(cache_service, analytics_service)
        return self._services['ai_search']
    
    def get_suggestion_service(self) -> SuggestionService:
        """Get suggestion service instance."""
        if 'suggestion' not in self._services:
            cache_service = self.get_cache_service()
            self._services['suggestion'] = SuggestionService(cache_service)
        return self._services['suggestion']
    
    def get_cache_service(self) -> CacheService:
        """Get cache service instance."""
        if 'cache' not in self._services:
            self._services['cache'] = CacheService()
        return self._services['cache']
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get analytics service instance."""
        if 'analytics' not in self._services:
            self._services['analytics'] = AnalyticsService()
        return self._services['analytics']
    
    def get_autocomplete_service(self) -> AutocompleteService:
        """Get autocomplete service instance."""
        if 'autocomplete' not in self._services:
            cache_service = self.get_cache_service()
            self._services['autocomplete'] = AutocompleteService(cache_service)
        return self._services['autocomplete']

# Global service factory instance
service_factory = ServiceFactory() 