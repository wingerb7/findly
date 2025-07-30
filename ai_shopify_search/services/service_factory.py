#!/usr/bin/env python3
"""
Service Factory for dependency injection and service management.
"""

import logging
from typing import Dict, Any, Optional
from .cache_service import CacheService
from .analytics_service import AnalyticsService
from .ai_search_service import AISearchService
from .autocomplete_service import AutocompleteService
from .suggestion_service import SuggestionService

logger = logging.getLogger(__name__)

class ServiceFactory:
    """Factory for creating and managing service instances."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all services."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing services...")
            
            # Initialize core services first
            cache_service = CacheService()
            analytics_service = AnalyticsService()
            
            # Initialize dependent services
            ai_search_service = AISearchService(cache_service, analytics_service)
            autocomplete_service = AutocompleteService(cache_service, analytics_service)
            suggestion_service = SuggestionService(cache_service)
            
            # Store services
            self._services = {
                "cache": cache_service,
                "analytics": analytics_service,
                "ai_search": ai_search_service,
                "autocomplete": autocomplete_service,
                "suggestion": suggestion_service
            }
            
            # Health check
            await self._health_check()
            
            self._initialized = True
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def _health_check(self) -> None:
        """Perform health checks on services."""
        try:
            # Check cache service
            cache_healthy = await self._services["cache"].health_check()
            if not cache_healthy:
                logger.warning("Cache service health check failed")
            
            logger.info("Service health checks completed")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to get
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service not found or not initialized
        """
        if not self._initialized:
            raise ValueError("Services not initialized. Call initialize() first.")
        
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        
        return self._services[service_name]
    
    def get_cache_service(self) -> CacheService:
        """Get cache service."""
        return self.get_service("cache")
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get analytics service."""
        return self.get_service("analytics")
    
    def get_ai_search_service(self) -> AISearchService:
        """Get AI search service."""
        return self.get_service("ai_search")
    
    def get_autocomplete_service(self) -> AutocompleteService:
        """Get autocomplete service."""
        return self.get_service("autocomplete")
    
    def get_suggestion_service(self) -> SuggestionService:
        """Get suggestion service."""
        return self.get_service("suggestion")
    
    async def shutdown(self) -> None:
        """Shutdown all services."""
        try:
            logger.info("Shutting down services...")
            
            # Clear cache
            cache_service = self.get_cache_service()
            await cache_service.clear_all()
            
            self._services.clear()
            self._initialized = False
            
            logger.info("Services shut down successfully")
            
        except Exception as e:
            logger.error(f"Error shutting down services: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all services.
        
        Returns:
            Dictionary with service statistics
        """
        try:
            stats = {
                "initialized": self._initialized,
                "services": list(self._services.keys())
            }
            
            # Get cache stats
            if "cache" in self._services:
                cache_stats = self._services["cache"].get_stats()
                stats["cache"] = cache_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {"error": str(e)}
    
    def is_initialized(self) -> bool:
        """Check if services are initialized."""
        return self._initialized

# Global service factory instance
service_factory = ServiceFactory()

async def get_service_factory() -> ServiceFactory:
    """
    Get the global service factory instance.
    
    Returns:
        ServiceFactory instance
    """
    if not service_factory.is_initialized():
        await service_factory.initialize()
    return service_factory

# Convenience functions for getting services
async def get_cache_service() -> CacheService:
    """Get cache service."""
    factory = await get_service_factory()
    return factory.get_cache_service()

async def get_analytics_service() -> AnalyticsService:
    """Get analytics service."""
    factory = await get_service_factory()
    return factory.get_analytics_service()

async def get_ai_search_service() -> AISearchService:
    """Get AI search service."""
    factory = await get_service_factory()
    return factory.get_ai_search_service()

async def get_autocomplete_service() -> AutocompleteService:
    """Get autocomplete service."""
    factory = await get_service_factory()
    return factory.get_autocomplete_service()

async def get_suggestion_service() -> SuggestionService:
    """Get suggestion service."""
    factory = await get_service_factory()
    return factory.get_suggestion_service() 