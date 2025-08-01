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
from .transfer_learning_service import TransferLearningService
from .knowledge_base_service import KnowledgeBaseService
from .baseline_generator_service import BaselineGeneratorService
from .pattern_learning_service import PatternLearningService
from .facets_service import FacetsService
from .smart_autocomplete import SmartAutocompleteService

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
            
            # Initialize AI feature services
            transfer_learning_service = TransferLearningService()
            knowledge_base_service = KnowledgeBaseService()
            baseline_generator_service = BaselineGeneratorService()
            pattern_learning_service = PatternLearningService()
            facets_service = FacetsService()
            smart_autocomplete_service = SmartAutocompleteService()
            
            # Store services
            self._services = {
                "cache": cache_service,
                "analytics": analytics_service,
                "ai_search": ai_search_service,
                "autocomplete": autocomplete_service,
                "suggestion": suggestion_service,
                "transfer_learning": transfer_learning_service,
                "knowledge_base": knowledge_base_service,
                "baseline_generator": baseline_generator_service,
                "pattern_learning": pattern_learning_service,
                "facets": facets_service,
                "smart_autocomplete": smart_autocomplete_service
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
    
    def get_transfer_learning_service(self) -> TransferLearningService:
        """Get transfer learning service."""
        return self.get_service("transfer_learning")
    
    def get_knowledge_base_service(self) -> KnowledgeBaseService:
        """Get knowledge base service."""
        return self.get_service("knowledge_base")
    
    def get_baseline_generator_service(self) -> BaselineGeneratorService:
        """Get baseline generator service."""
        return self.get_service("baseline_generator")
    
    def get_pattern_learning_service(self) -> PatternLearningService:
        """Get pattern learning service."""
        return self.get_service("pattern_learning")
    
    def get_facets_service(self) -> FacetsService:
        """Get facets service."""
        return self.get_service("facets")
    
    def get_smart_autocomplete_service(self) -> SmartAutocompleteService:
        """Get smart autocomplete service."""
        return self.get_service("smart_autocomplete")
    
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

async def get_transfer_learning_service() -> TransferLearningService:
    """Get transfer learning service."""
    factory = await get_service_factory()
    return factory.get_transfer_learning_service()

async def get_knowledge_base_service() -> KnowledgeBaseService:
    """Get knowledge base service."""
    factory = await get_service_factory()
    return factory.get_knowledge_base_service()

async def get_baseline_generator_service() -> BaselineGeneratorService:
    """Get baseline generator service."""
    factory = await get_service_factory()
    return factory.get_baseline_generator_service()

async def get_pattern_learning_service() -> PatternLearningService:
    """Get pattern learning service."""
    factory = await get_service_factory()
    return factory.get_pattern_learning_service()

async def get_facets_service() -> FacetsService:
    """Get facets service."""
    factory = await get_service_factory()
    return factory.get_facets_service()

async def get_smart_autocomplete_service() -> SmartAutocompleteService:
    """Get smart autocomplete service."""
    factory = await get_service_factory()
    return factory.get_smart_autocomplete_service() 