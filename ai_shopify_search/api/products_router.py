#!/usr/bin/env python3
"""
Products API Router

Handles all product-related endpoints with AI-powered search and features.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from services.service_factory import (
    get_ai_search_service, get_autocomplete_service, get_suggestion_service,
    get_facets_service, get_smart_autocomplete_service
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 25
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    similarity_threshold: float = 0.7

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    search_suggestions: Optional[Dict[str, Any]] = None
    conversational_refinements: Optional[List[Dict[str, Any]]] = None
    store_insights: Optional[Dict[str, Any]] = None
    facets: Optional[Dict[str, Any]] = None

@router.post("/search", response_model=SearchResponse)
async def search_products(
    request: SearchRequest,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None)
):
    """AI-powered product search with all features."""
    try:
        ai_search_service = await get_ai_search_service()
        
        result = await ai_search_service.search_products(
            db=db,
            query=request.query,
            page=request.page,
            limit=request.limit,
            min_price=request.min_price,
            max_price=request.max_price,
            user_agent=user_agent,
            ip_address=ip_address,
            similarity_threshold=request.similarity_threshold
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/autocomplete")
async def get_autocomplete(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get autocomplete suggestions."""
    try:
        autocomplete_service = await get_autocomplete_service()
        
        suggestions = await autocomplete_service.get_suggestions(
            query=query,
            limit=limit,
            db=db
        )
        
        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/smart-autocomplete")
async def get_smart_autocomplete(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get AI-powered smart autocomplete suggestions."""
    try:
        smart_autocomplete_service = await get_smart_autocomplete_service()
        
        suggestions = await smart_autocomplete_service.get_smart_suggestions(
            query=query,
            limit=limit,
            db=db
        )
        
        return {
            "query": query,
            "smart_suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Smart autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on query."""
    try:
        suggestion_service = await get_suggestion_service()
        
        suggestions = await suggestion_service.get_suggestions(
            query=query,
            limit=limit,
            db=db
        )
        
        return {
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facets")
async def get_product_facets(
    query: Optional[str] = Query(None),
    product_ids: Optional[str] = Query(None),  # Comma-separated
    db: Session = Depends(get_db)
):
    """Get product facets for filtering."""
    try:
        facets_service = await get_facets_service()
        
        # Parse product IDs if provided
        parsed_product_ids = None
        if product_ids:
            parsed_product_ids = [int(pid.strip()) for pid in product_ids.split(",") if pid.strip().isdigit()]
        
        facets = await facets_service.get_facets(
            query=query,
            product_ids=parsed_product_ids,
            db=db
        )
        
        return {
            "facets": facets,
            "query": query,
            "product_count": len(parsed_product_ids) if parsed_product_ids else None
        }
        
    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/fallback")
async def search_with_fallback(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search with fallback mechanisms."""
    try:
        ai_search_service = await get_ai_search_service()
        
        result = await ai_search_service.search_with_fallback(
            db=db,
            query=query,
            page=page,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Fallback search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 