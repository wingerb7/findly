#!/usr/bin/env python3
"""
Feedback API Router

Handles user feedback collection and processing.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ai_shopify_search.core.database import get_db
from ai_shopify_search.services.service_factory import get_analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class SearchFeedback(BaseModel):
    query: str
    result_count: int
    clicked_product_id: Optional[str] = None
    search_time_ms: Optional[int] = None
    user_satisfaction: Optional[int] = None  # 1-5 scale
    feedback_text: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class AutocompleteFeedback(BaseModel):
    query: str
    selected_suggestion: str
    suggestion_position: int
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class GeneralFeedback(BaseModel):
    feedback_type: str  # bug_report, feature_request, general
    title: str
    description: str
    severity: Optional[str] = None  # low, medium, high, critical
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

@router.post("/search")
async def submit_search_feedback(
    feedback: SearchFeedback,
    db: Session = Depends(get_db)
):
    """Submit feedback for search results."""
    try:
        analytics_service = await get_analytics_service()
        
        # Track search feedback using existing method
        await analytics_service.track_search(
            db=db,
            query=feedback.query,
            search_type="feedback",
            filters={},
            results_count=feedback.result_count,
            page=1,
            limit=feedback.result_count,
            response_time_ms=feedback.search_time_ms or 0,
            cache_hit=False,
            user_agent=feedback.user_agent,
            ip_address=feedback.ip_address
        )
        
        return {
            "status": "success",
            "message": "Search feedback recorded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/autocomplete")
async def submit_autocomplete_feedback(
    feedback: AutocompleteFeedback,
    db: Session = Depends(get_db)
):
    """Submit feedback for autocomplete suggestions."""
    try:
        analytics_service = await get_analytics_service()
        
        # Track autocomplete feedback using existing method
        await analytics_service.track_search(
            db=db,
            query=feedback.query,
            search_type="autocomplete_feedback",
            filters={"selected_suggestion": feedback.selected_suggestion, "position": feedback.suggestion_position},
            results_count=1,
            page=1,
            limit=1,
            response_time_ms=0,
            cache_hit=False,
            user_agent=feedback.user_agent,
            ip_address=feedback.ip_address
        )
        
        return {
            "status": "success",
            "message": "Autocomplete feedback recorded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Autocomplete feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/general")
async def submit_general_feedback(
    feedback: GeneralFeedback,
    db: Session = Depends(get_db)
):
    """Submit general feedback."""
    try:
        analytics_service = await get_analytics_service()
        
        # Track general feedback using existing method
        await analytics_service.track_search(
            db=db,
            query=f"{feedback.feedback_type}: {feedback.title}",
            search_type="general_feedback",
            filters={"feedback_type": feedback.feedback_type, "severity": feedback.severity},
            results_count=1,
            page=1,
            limit=1,
            response_time_ms=0,
            cache_hit=False,
            user_agent=feedback.user_agent,
            ip_address=feedback.ip_address
        )
        
        return {
            "status": "success",
            "message": "General feedback recorded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"General feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/search")
async def get_search_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get search analytics data."""
    try:
        analytics_service = await get_analytics_service()
        
        analytics = await analytics_service.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            store_id=store_id
        )
        
        return {
            "analytics": analytics,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "store_id": store_id
        }
        
    except Exception as e:
        logger.error(f"Search analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/autocomplete")
async def get_autocomplete_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get autocomplete analytics data."""
    try:
        analytics_service = await get_analytics_service()
        
        analytics = await analytics_service.get_autocomplete_analytics(
            start_date=start_date,
            end_date=end_date,
            store_id=store_id
        )
        
        return {
            "analytics": analytics,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "store_id": store_id
        }
        
    except Exception as e:
        logger.error(f"Autocomplete analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/feedback")
async def get_feedback_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    feedback_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get feedback analytics data."""
    try:
        analytics_service = await get_analytics_service()
        
        analytics = await analytics_service.get_feedback_analytics(
            start_date=start_date,
            end_date=end_date,
            feedback_type=feedback_type
        )
        
        return {
            "analytics": analytics,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "feedback_type": feedback_type
        }
        
    except Exception as e:
        logger.error(f"Feedback analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def feedback_health():
    """Health check for feedback service."""
    try:
        analytics_service = await get_analytics_service()
        
        return {
            "status": "healthy",
            "service": "feedback",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "feedback",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 