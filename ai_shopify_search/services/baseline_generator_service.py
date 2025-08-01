#!/usr/bin/env python3
"""
Baseline Generator Service

Integrates baseline generator functionality into the production API.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    # Try multiple import paths
    try:
        from analysis.baseline_generator import BaselineGenerator
    except ImportError:
        # Try relative import from project root
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from analysis.baseline_generator import BaselineGenerator
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Baseline Generator not available - feature disabled")
    BaselineGenerator = None

logger = logging.getLogger(__name__)

class BaselineGeneratorService:
    """Service for integrating baseline generator into the API."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path from project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, "data", "databases", "findly_consolidated.db")
        else:
            self.db_path = db_path
        self.baseline_generator = None
        
        try:
            if BaselineGenerator is not None:
                self.baseline_generator = BaselineGenerator(self.db_path)
                logger.info("Baseline Generator Service initialized successfully")
            else:
                logger.warning("Baseline Generator not available - feature disabled")
        except Exception as e:
            logger.warning(f"Baseline Generator Service initialization failed: {e}")
    
    async def generate_store_baselines_async(self, store_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive baselines for a store."""
        if not self.baseline_generator:
            return {"error": "Baseline generator not available"}
        
        try:
            loop = asyncio.get_event_loop()
            benchmark = await loop.run_in_executor(
                None,
                self.baseline_generator.generate_store_baselines,
                store_id,
                days_back
            )
            
            # Convert to dict for JSON serialization
            return {
                "store_id": benchmark.store_id,
                "overall_baseline": benchmark.overall_baseline,
                "performance_grade": benchmark.performance_grade,
                "improvement_opportunities": benchmark.improvement_opportunities,
                "generated_at": benchmark.generated_at.isoformat(),
                "category_baselines": {
                    category: {
                        "avg_score": baseline.avg_score,
                        "avg_response_time": baseline.avg_response_time,
                        "avg_price_coherence": baseline.avg_price_coherence,
                        "avg_diversity_score": baseline.avg_diversity_score,
                        "avg_conversion_potential": baseline.avg_conversion_potential,
                        "total_queries": baseline.total_queries,
                        "successful_queries": baseline.successful_queries,
                        "success_rate": baseline.success_rate,
                        "confidence": baseline.confidence,
                        "trend": baseline.trend,
                        "last_updated": baseline.last_updated.isoformat()
                    }
                    for category, baseline in benchmark.category_baselines.items()
                },
                "intent_baselines": {
                    intent_type: {
                        "avg_score": baseline.avg_score,
                        "avg_response_time": baseline.avg_response_time,
                        "price_filter_usage_rate": baseline.price_filter_usage_rate,
                        "fallback_usage_rate": baseline.fallback_usage_rate,
                        "cache_hit_rate": baseline.cache_hit_rate,
                        "total_queries": baseline.total_queries,
                        "successful_queries": baseline.successful_queries,
                        "success_rate": baseline.success_rate,
                        "confidence": baseline.confidence,
                        "category_distribution": baseline.category_distribution,
                        "last_updated": baseline.last_updated.isoformat()
                    }
                    for intent_type, baseline in benchmark.intent_baselines.items()
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate store baselines: {e}")
            return {"error": str(e)}
    
    async def get_latest_baseline_async(self, store_id: str) -> Dict[str, Any]:
        """Get the latest baseline for a store."""
        if not self.baseline_generator:
            return {"error": "Baseline generator not available"}
        
        try:
            loop = asyncio.get_event_loop()
            benchmark = await loop.run_in_executor(
                None,
                self.baseline_generator.get_latest_baseline,
                store_id
            )
            
            if not benchmark:
                return {"error": "No baseline found for store"}
            
            # Convert to dict (same as above)
            return {
                "store_id": benchmark.store_id,
                "overall_baseline": benchmark.overall_baseline,
                "performance_grade": benchmark.performance_grade,
                "improvement_opportunities": benchmark.improvement_opportunities,
                "generated_at": benchmark.generated_at.isoformat(),
                "category_baselines": {
                    category: {
                        "avg_score": baseline.avg_score,
                        "avg_response_time": baseline.avg_response_time,
                        "avg_price_coherence": baseline.avg_price_coherence,
                        "avg_diversity_score": baseline.avg_diversity_score,
                        "avg_conversion_potential": baseline.avg_conversion_potential,
                        "total_queries": baseline.total_queries,
                        "successful_queries": baseline.successful_queries,
                        "success_rate": baseline.success_rate,
                        "confidence": baseline.confidence,
                        "trend": baseline.trend,
                        "last_updated": baseline.last_updated.isoformat()
                    }
                    for category, baseline in benchmark.category_baselines.items()
                },
                "intent_baselines": {
                    intent_type: {
                        "avg_score": baseline.avg_score,
                        "avg_response_time": baseline.avg_response_time,
                        "price_filter_usage_rate": baseline.price_filter_usage_rate,
                        "fallback_usage_rate": baseline.fallback_usage_rate,
                        "cache_hit_rate": baseline.cache_hit_rate,
                        "total_queries": baseline.total_queries,
                        "successful_queries": baseline.successful_queries,
                        "success_rate": baseline.success_rate,
                        "confidence": baseline.confidence,
                        "category_distribution": baseline.category_distribution,
                        "last_updated": baseline.last_updated.isoformat()
                    }
                    for intent_type, baseline in benchmark.intent_baselines.items()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get latest baseline: {e}")
            return {"error": str(e)}
    
    def is_available(self) -> bool:
        """Check if baseline generator is available."""
        return self.baseline_generator is not None 