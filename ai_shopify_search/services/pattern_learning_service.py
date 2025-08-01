#!/usr/bin/env python3
"""
Pattern Learning Service

Integrates pattern learning functionality into the production API.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from analysis.pattern_learning import PatternLearningSystem
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Pattern Learning System not available - feature disabled")

logger = logging.getLogger(__name__)

class PatternLearningService:
    """Service for integrating pattern learning into the API."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path from project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, "data", "databases", "findly_consolidated.db")
        else:
            self.db_path = db_path
        self.pattern_system = None
        
        try:
            self.pattern_system = PatternLearningSystem(self.db_path)
            logger.info("Pattern Learning Service initialized successfully")
        except Exception as e:
            logger.warning(f"Pattern Learning Service initialization failed: {e}")
    
    async def analyze_and_learn_async(self, store_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Asynchronously analyze and learn patterns."""
        if not self.pattern_system:
            return []
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            suggestions = await loop.run_in_executor(
                None, 
                self.pattern_system.analyze_and_learn_patterns, 
                store_id, 
                days_back
            )
            
            # Convert to dict for JSON serialization
            return [
                {
                    "suggestion_type": s.suggestion_type,
                    "description": s.description,
                    "target_category": s.target_category,
                    "expected_improvement": s.expected_improvement,
                    "confidence": s.confidence,
                    "implementation_steps": s.implementation_steps,
                    "priority": s.priority,
                    "estimated_effort": s.estimated_effort,
                    "last_updated": s.last_updated.isoformat()
                }
                for s in suggestions
            ]
        except Exception as e:
            logger.error(f"Pattern learning analysis failed: {e}")
            return []
    
    async def get_learned_patterns_async(self, store_id: str) -> List[Dict[str, Any]]:
        """Get learned patterns for a store."""
        if not self.pattern_system:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            patterns = await loop.run_in_executor(
                None,
                self.pattern_system._get_learned_patterns,
                store_id
            )
            
            return [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "success_rate": p.success_rate,
                    "usage_count": p.usage_count,
                    "performance_trend": p.performance_trend,
                    "confidence": p.confidence,
                    "last_used": p.last_used.isoformat(),
                    "created_at": p.created_at.isoformat()
                }
                for p in patterns
            ]
        except Exception as e:
            logger.error(f"Failed to get learned patterns: {e}")
            return []
    
    async def cleanup_old_data_async(self) -> Dict[str, int]:
        """Clean up old data asynchronously."""
        if not self.pattern_system:
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.pattern_system.cleanup_old_data
            )
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if pattern learning is available."""
        return self.pattern_system is not None 