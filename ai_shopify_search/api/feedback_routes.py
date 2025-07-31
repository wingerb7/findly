"""
Feedback API Routes - FastAPI endpoints for feedback collection
Provides REST API endpoints for collecting and analyzing user feedback.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# Import feedback collector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from feedback.feedback_collector import (
    FeedbackCollector, FeedbackData, FeedbackType, 
    FeedbackCategory, FeedbackAnalysis
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Initialize feedback collector
feedback_collector = FeedbackCollector()

# Pydantic models for API requests/responses
class FeedbackRequest(BaseModel):
    """Request model for feedback submission"""
    query_id: str = Field(..., description="ID of the search query")
    search_query: str = Field(..., description="Original search query")
    feedback_type: str = Field(..., description="Type of feedback (positive/negative/neutral/suggestion/bug_report)")
    feedback_category: str = Field(..., description="Category of feedback (price/relevance/speed/ui_ux/content/other)")
    feedback_text: str = Field(..., description="Detailed feedback text")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5)")
    suggested_improvement: Optional[str] = Field(None, description="User's suggested improvement")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    success: bool
    feedback_id: str
    message: str
    timestamp: datetime

class FeedbackAnalysisResponse(BaseModel):
    """Response model for feedback analysis"""
    total_feedback: int
    positive_ratio: float
    negative_ratio: float
    avg_rating: float
    satisfaction_score: float
    top_categories: List[Dict[str, Any]]
    trending_issues: List[str]
    improvement_suggestions: List[str]
    recommendations: List[str]

class FeedbackQueryResponse(BaseModel):
    """Response model for query-specific feedback"""
    query_id: str
    feedback_count: int
    feedback_list: List[Dict[str, Any]]

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_request: FeedbackRequest,
    request: Request
):
    """
    Submit user feedback for a search query
    
    - **query_id**: ID of the search query
    - **search_query**: Original search query
    - **feedback_type**: Type of feedback (positive/negative/neutral/suggestion/bug_report)
    - **feedback_category**: Category of feedback (price/relevance/speed/ui_ux/content/other)
    - **feedback_text**: Detailed feedback text
    - **user_rating**: Optional user rating (1-5)
    - **suggested_improvement**: Optional improvement suggestion
    - **metadata**: Optional additional metadata
    """
    try:
        # Validate feedback type
        try:
            feedback_type = FeedbackType(feedback_request.feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid feedback_type. Must be one of: {[t.value for t in FeedbackType]}"
            )
        
        # Validate feedback category
        try:
            feedback_category = FeedbackCategory(feedback_request.feedback_category)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid feedback_category. Must be one of: {[c.value for c in FeedbackCategory]}"
            )
        
        # Create feedback data
        feedback_data = FeedbackData(
            feedback_id="",  # Will be generated
            query_id=feedback_request.query_id,
            search_query=feedback_request.search_query,
            feedback_type=feedback_type,
            feedback_category=feedback_category,
            feedback_text=feedback_request.feedback_text,
            user_rating=feedback_request.user_rating,
            suggested_improvement=feedback_request.suggested_improvement,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            metadata=feedback_request.metadata
        )
        
        # Collect feedback
        success = feedback_collector.collect_feedback(feedback_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store feedback")
        
        logger.info(f"Feedback submitted successfully: {feedback_data.feedback_id}")
        
        return FeedbackResponse(
            success=True,
            feedback_id=feedback_data.feedback_id,
            message="Feedback submitted successfully",
            timestamp=feedback_data.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analysis", response_model=FeedbackAnalysisResponse)
async def get_feedback_analysis(days: int = 30):
    """
    Get feedback analysis for the specified period
    
    - **days**: Number of days to analyze (default: 30)
    """
    try:
        if days <= 0 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        # Get analysis
        analysis = feedback_collector.analyze_feedback(days=days)
        
        # Get recommendations
        recommendations = feedback_collector.get_improvement_recommendations()
        
        # Store analysis for historical tracking
        feedback_collector.store_analysis(analysis)
        
        return FeedbackAnalysisResponse(
            total_feedback=analysis.total_feedback,
            positive_ratio=analysis.positive_ratio,
            negative_ratio=analysis.negative_ratio,
            avg_rating=analysis.avg_rating,
            satisfaction_score=analysis.satisfaction_score,
            top_categories=analysis.top_categories,
            trending_issues=analysis.trending_issues,
            improvement_suggestions=analysis.improvement_suggestions,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/query/{query_id}", response_model=FeedbackQueryResponse)
async def get_feedback_by_query(query_id: str):
    """
    Get all feedback for a specific query
    
    - **query_id**: ID of the search query
    """
    try:
        # Get feedback for query
        feedback_list = feedback_collector.get_feedback_by_query(query_id)
        
        # Convert to dict for response
        feedback_dicts = []
        for feedback in feedback_list:
            feedback_dict = {
                "feedback_id": feedback.feedback_id,
                "feedback_type": feedback.feedback_type.value,
                "feedback_category": feedback.feedback_category.value,
                "feedback_text": feedback.feedback_text,
                "user_rating": feedback.user_rating,
                "suggested_improvement": feedback.suggested_improvement,
                "timestamp": feedback.timestamp.isoformat() if feedback.timestamp else None,
                "metadata": feedback.metadata
            }
            feedback_dicts.append(feedback_dict)
        
        return FeedbackQueryResponse(
            query_id=query_id,
            feedback_count=len(feedback_list),
            feedback_list=feedback_dicts
        )
        
    except Exception as e:
        logger.error(f"Error getting feedback for query {query_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/report")
async def get_feedback_report(days: int = 30):
    """
    Get comprehensive feedback report
    
    - **days**: Number of days to include in report (default: 30)
    """
    try:
        if days <= 0 or days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        # Export report
        report = feedback_collector.export_feedback_report(days=days)
        
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        
        return JSONResponse(content=report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feedback report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def feedback_health_check():
    """Health check endpoint for feedback system"""
    try:
        # Test database connection
        analysis = feedback_collector.analyze_feedback(days=1)
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_feedback": analysis.total_feedback,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback health check failed: {e}")
        raise HTTPException(status_code=503, detail="Feedback system unhealthy")

# Additional utility endpoints
@router.get("/categories")
async def get_feedback_categories():
    """Get available feedback categories"""
    return {
        "feedback_types": [t.value for t in FeedbackType],
        "feedback_categories": [c.value for c in FeedbackCategory]
    }

@router.get("/stats")
async def get_feedback_stats():
    """Get basic feedback statistics"""
    try:
        analysis = feedback_collector.analyze_feedback(days=30)
        
        return {
            "last_30_days": {
                "total_feedback": analysis.total_feedback,
                "satisfaction_score": analysis.satisfaction_score,
                "positive_ratio": analysis.positive_ratio,
                "negative_ratio": analysis.negative_ratio,
                "avg_rating": analysis.avg_rating
            },
            "top_categories": analysis.top_categories[:3],
            "trending_issues": analysis.trending_issues[:5],
            "recommendations": feedback_collector.get_improvement_recommendations()[:3]
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 