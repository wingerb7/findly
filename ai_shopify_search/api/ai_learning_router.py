#!/usr/bin/env python3
"""
AI Learning API Router

Handles all AI learning and analytics endpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ai_shopify_search.core.database import get_db
from ai_shopify_search.services.service_factory import (
    get_transfer_learning_service, get_knowledge_base_service,
    get_baseline_generator_service, get_pattern_learning_service
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class TransferLearningRequest(BaseModel):
    target_store_id: str
    limit: int = 5

class KnowledgeBaseRequest(BaseModel):
    store_id: Optional[str] = None
    action: str = "build"  # build, update, insights

class BaselineGeneratorRequest(BaseModel):
    store_id: Optional[str] = None
    benchmark_type: str = "search_performance"

class PatternLearningRequest(BaseModel):
    store_id: Optional[str] = None
    pattern_type: str = "search_patterns"

# Transfer Learning Endpoints
@router.post("/transfer-learning/similar-stores")
async def find_similar_stores(
    request: TransferLearningRequest,
    db: Session = Depends(get_db)
):
    """Find stores similar to target store using transfer learning."""
    try:
        transfer_service = await get_transfer_learning_service()
        
        if not transfer_service.is_available():
            raise HTTPException(status_code=503, detail="Transfer learning service not available")
        
        similar_stores = await transfer_service.find_similar_stores_async(
            target_store_id=request.target_store_id,
            limit=request.limit
        )
        
        return {
            "target_store_id": request.target_store_id,
            "similar_stores": similar_stores,
            "count": len(similar_stores)
        }
        
    except Exception as e:
        logger.error(f"Transfer learning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transfer-learning/recommendations")
async def generate_transfer_recommendations(
    request: TransferLearningRequest,
    db: Session = Depends(get_db)
):
    """Generate transfer learning recommendations for a store."""
    try:
        transfer_service = await get_transfer_learning_service()
        
        if not transfer_service.is_available():
            raise HTTPException(status_code=503, detail="Transfer learning service not available")
        
        recommendations = await transfer_service.generate_transfer_recommendations_async(
            target_store_id=request.target_store_id
        )
        
        return {
            "target_store_id": request.target_store_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Transfer recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transfer-learning/apply")
async def apply_transfer_recommendations(
    target_store_id: str,
    recommendations: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Apply transfer learning recommendations to a store."""
    try:
        transfer_service = await get_transfer_learning_service()
        
        if not transfer_service.is_available():
            raise HTTPException(status_code=503, detail="Transfer learning service not available")
        
        result = await transfer_service.apply_transfer_recommendations_async(
            target_store_id=target_store_id,
            recommendations=recommendations
        )
        
        return {
            "target_store_id": target_store_id,
            "result": result,
            "recommendations_applied": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Apply recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Base Endpoints
@router.post("/knowledge-base/build")
async def build_knowledge_base(
    request: KnowledgeBaseRequest,
    db: Session = Depends(get_db)
):
    """Build knowledge base for store(s)."""
    try:
        kb_service = await get_knowledge_base_service()
        
        if not kb_service.is_available():
            raise HTTPException(status_code=503, detail="Knowledge base service not available")
        
        result = await kb_service.build_knowledge_base_async(
            store_id=request.store_id
        )
        
        return {
            "action": "build",
            "store_id": request.store_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Knowledge base build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/insights/{store_id}")
async def get_store_insights(
    store_id: str,
    db: Session = Depends(get_db)
):
    """Get insights for a specific store."""
    try:
        kb_service = await get_knowledge_base_service()
        
        if not kb_service.is_available():
            raise HTTPException(status_code=503, detail="Knowledge base service not available")
        
        insights = await kb_service.get_store_insights_async(store_id=store_id)
        
        return {
            "store_id": store_id,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Store insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/update")
async def update_knowledge_base(
    request: KnowledgeBaseRequest,
    db: Session = Depends(get_db)
):
    """Update knowledge base with new data."""
    try:
        kb_service = await get_knowledge_base_service()
        
        if not kb_service.is_available():
            raise HTTPException(status_code=503, detail="Knowledge base service not available")
        
        result = await kb_service.update_knowledge_base_async(
            store_id=request.store_id
        )
        
        return {
            "action": "update",
            "store_id": request.store_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Knowledge base update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Baseline Generator Endpoints
@router.post("/baseline-generator/generate")
async def generate_baseline(
    request: BaselineGeneratorRequest,
    db: Session = Depends(get_db)
):
    """Generate baseline metrics for store(s)."""
    try:
        baseline_service = await get_baseline_generator_service()
        
        result = await baseline_service.generate_baseline_async(
            store_id=request.store_id,
            benchmark_type=request.benchmark_type
        )
        
        return {
            "store_id": request.store_id,
            "benchmark_type": request.benchmark_type,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Baseline generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Pattern Learning Endpoints
@router.post("/pattern-learning/analyze")
async def analyze_patterns(
    request: PatternLearningRequest,
    db: Session = Depends(get_db)
):
    """Analyze search patterns for store(s)."""
    try:
        pattern_service = await get_pattern_learning_service()
        
        result = await pattern_service.analyze_patterns_async(
            store_id=request.store_id,
            pattern_type=request.pattern_type
        )
        
        return {
            "store_id": request.store_id,
            "pattern_type": request.pattern_type,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pattern-learning/patterns/{store_id}")
async def get_learned_patterns(
    store_id: str,
    pattern_type: str = Query("search_patterns"),
    db: Session = Depends(get_db)
):
    """Get learned patterns for a store."""
    try:
        pattern_service = await get_pattern_learning_service()
        
        patterns = await pattern_service.get_patterns_async(
            store_id=store_id,
            pattern_type=pattern_type
        )
        
        return {
            "store_id": store_id,
            "pattern_type": pattern_type,
            "patterns": patterns
        }
        
    except Exception as e:
        logger.error(f"Get patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check for AI learning services
@router.get("/health")
async def ai_learning_health():
    """Health check for AI learning services."""
    try:
        transfer_service = await get_transfer_learning_service()
        kb_service = await get_knowledge_base_service()
        baseline_service = await get_baseline_generator_service()
        pattern_service = await get_pattern_learning_service()
        
        return {
            "status": "healthy",
            "services": {
                "transfer_learning": transfer_service.is_available() if transfer_service else False,
                "knowledge_base": kb_service.is_available() if kb_service else False,
                "baseline_generator": True,  # Always available
                "pattern_learning": True     # Always available
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 