#!/usr/bin/env python3
"""
Transfer Learning Service

Integrates transfer learning functionality into the production API.
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
    from features.transfer_learning import TransferLearningEngine, TransferRecommendation
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Transfer Learning Engine not available - feature disabled")
    TransferLearningEngine = None
    TransferRecommendation = None

logger = logging.getLogger(__name__)

class TransferLearningService:
    """Service for integrating transfer learning into the API."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path from project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, "data", "databases", "findly_consolidated.db")
        else:
            self.db_path = db_path
        self.transfer_engine = None
        
        try:
            if TransferLearningEngine is not None:
                self.transfer_engine = TransferLearningEngine(self.db_path)
                logger.info("Transfer Learning Service initialized successfully")
            else:
                logger.warning("Transfer Learning Engine not available - feature disabled")
        except Exception as e:
            logger.warning(f"Transfer Learning Service initialization failed: {e}")
    
    async def find_similar_stores_async(self, target_store_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find stores similar to the target store."""
        if not self.transfer_engine:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            similar_stores = await loop.run_in_executor(
                None,
                self.transfer_engine.find_similar_stores,
                target_store_id,
                limit
            )
            
            return [
                {
                    "store_id_1": s.store_id_1,
                    "store_id_2": s.store_id_2,
                    "similarity_score": s.similarity_score,
                    "similarity_factors": s.similarity_factors,
                    "confidence": s.confidence
                }
                for s in similar_stores
            ]
        except Exception as e:
            logger.error(f"Failed to find similar stores: {e}")
            return []
    
    async def generate_transfer_recommendations_async(self, target_store_id: str) -> List[Dict[str, Any]]:
        """Generate transfer recommendations for a store."""
        if not self.transfer_engine:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            recommendations = await loop.run_in_executor(
                None,
                self.transfer_engine.generate_transfer_recommendations,
                target_store_id
            )
            
            return [
                {
                    "pattern_type": r.pattern_type,
                    "pattern_description": r.pattern_description,
                    "source_stores": r.source_stores,
                    "expected_improvement": r.expected_improvement,
                    "confidence": r.confidence,
                    "implementation_steps": r.implementation_steps,
                    "risk_level": r.risk_level
                }
                for r in recommendations
            ]
        except Exception as e:
            logger.error(f"Failed to generate transfer recommendations: {e}")
            return []
    
    async def apply_transfer_recommendations_async(self, target_store_id: str, 
                                                 recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply transfer recommendations to a store."""
        if not self.transfer_engine:
            return {"success": False, "error": "Transfer learning not available"}
        
        try:
            # Convert dict back to TransferRecommendation objects
            transfer_recommendations = []
            for rec_dict in recommendations:
                rec = TransferRecommendation(
                    pattern_type=rec_dict["pattern_type"],
                    pattern_description=rec_dict["pattern_description"],
                    source_stores=rec_dict["source_stores"],
                    expected_improvement=rec_dict["expected_improvement"],
                    confidence=rec_dict["confidence"],
                    implementation_steps=rec_dict["implementation_steps"],
                    risk_level=rec_dict["risk_level"]
                )
                transfer_recommendations.append(rec)
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.transfer_engine.apply_transfer_recommendations,
                target_store_id,
                transfer_recommendations
            )
            
            return result
        except Exception as e:
            logger.error(f"Failed to apply transfer recommendations: {e}")
            return {"success": False, "error": str(e)}
    
    def is_available(self) -> bool:
        """Check if transfer learning is available."""
        return self.transfer_engine is not None 