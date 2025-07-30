import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from core.models import Product, FacetUsage
from shopify_client import get_products
from embeddings import generate_embedding
from core.database import get_db
from cache_manager import cache_manager
from analytics_manager import analytics_manager
from search_service import search_service
from rate_limiter import rate_limiter
from metrics import metrics_collector
from price_intent import extract_price_intent, clean_query_from_price_intent, format_price_message
from utils.validation import (
    AISearchQuery, AnalyticsQuery, sanitize_search_query, 
    validate_price_range, generate_secure_cache_key, validate_rate_limit_identifier,
    log_security_event
)
from utils.privacy_utils import sanitize_log_data
from utils.error_handling import (
    validate_search_parameters, 
    validate_analytics_parameters,
    safe_database_operation,
    safe_cache_operation,
    safe_embedding_operation
)
from background_tasks import (
    log_analytics_task,
    update_popular_searches_task
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting configuration
AI_SEARCH_RATE_LIMIT = 100  # requests per hour
AI_SEARCH_RATE_WINDOW = 3600  # seconds

@router.post("/import-products")
async def import_products(db: Session = Depends(get_db)):
    """Import products from Shopify with embeddings."""
    try:
        logger.info("Starting product import...")
        products = get_products()
        logger.info(f"Retrieved {len(products)} products from Shopify")

        imported_count = 0
        updated_count = 0

        for p in products:
            try:
                import re
                # Clean description
                clean_description = re.sub(r"<[^>]+>", "", p.get("description") or p.get("body_html") or "").strip()

                # Clean tags
                raw_tags = p.get("tags") or []
                if isinstance(raw_tags, str):
                    clean_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                elif isinstance(raw_tags, list):
                    clean_tags = [str(t).strip() for t in raw_tags if t]
                else:
                    clean_tags = []

                # Clean price
                raw_price = p.get("price") or (p["variants"][0]["price"] if p.get("variants") else None)
                try:
                    clean_price = float(raw_price) if raw_price is not None else None
                except:
                    logger.warning(f"Price could not be converted for product {p.get('title', 'Unknown')}")
                    clean_price = None

                # Shopify ID
                clean_shopify_id = str(p.get("shopify_id") or p.get("id") or "")
                if not clean_shopify_id:
                    logger.warning(f"Product {p.get('title', 'Unknown')} has no valid ID. Skipped.")
                    continue

                # Generate embedding
                embedding = generate_embedding(
                    title=p.get('title', 'Unknown'),
                    description=clean_description,
                    tags=clean_tags,
                    price=clean_price
                )
                if not embedding or len(embedding) != 1536:
                    logger.error(f"Invalid embedding for product {p.get('title', 'Unknown')}. Skipped.")
                    continue
                clean_embedding = list(map(float, embedding))

                # Upsert: check if product exists
                existing = db.query(Product).filter_by(shopify_id=clean_shopify_id).first()
                if existing:
                    existing.title = p.get("title", "Unknown")
                    existing.description = clean_description
                    existing.price = clean_price
                    existing.tags = clean_tags
                    existing.embedding = clean_embedding
                    updated_count += 1
                    logger.info(f"Product updated: {p.get('title')} (ID: {clean_shopify_id})")
                else:
                    new_product = Product(
                        shopify_id=clean_shopify_id,
                        title=p.get("title", "Unknown"),
                        description=clean_description,
                        price=clean_price,
                        tags=clean_tags,
                        embedding=clean_embedding
                    )
                    db.add(new_product)
                    imported_count += 1
                    logger.info(f"New product added: {p.get('title')} (ID: {clean_shopify_id})")

            except Exception as e:
                logger.error(f"Error processing product {p.get('title', 'Unknown')}: {e}")
                continue

        db.commit()
        
        # Invalidate cache after product updates
        cache_manager.invalidate_product_cache()
        
        logger.info(f"Successfully imported {imported_count} new products, updated {updated_count} existing products.")
        return {"imported": imported_count, "updated": updated_count}

    except Exception as e:
        logger.error(f"Error in import_products: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-search")
async def ai_search_products(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    query: str = Query(..., description="Natural search term"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(25, ge=1, le=100, description="Number of results per page (max 100)"),
    user_agent: Optional[str] = Query(None, description="User agent for analytics"),
    ip_address: Optional[str] = Query(None, description="IP address for analytics"),
    source_language: Optional[str] = Query(None, description="Source language (ISO 639-1)"),
    target_language: str = Query("en", description="Target language (ISO 639-1)"),
    db: Session = Depends(get_db)
):
    """
    AI-powered product search with price intent filtering and rate limiting.
    
    This endpoint performs semantic search with automatic price filtering based on
    natural language queries. It includes GDPR-compliant analytics tracking and
    comprehensive input validation.
    """
    try:
        # Validate and sanitize input parameters
        search_query = AISearchQuery(
            query=query,
            page=page,
            limit=limit,
            source_language=source_language,
            target_language=target_language
        )
        
        # Validate price range (will be extracted from query)
        min_price, max_price = extract_price_intent(search_query.query)
        validate_price_range(min_price, max_price)
        
        # Sanitize and validate rate limit identifier
        client_ip = validate_rate_limit_identifier(ip_address or request.client.host)
        
        # Log security event
        log_security_event(
            "ai_search_request",
            {
                "query_length": len(search_query.query),
                "has_price_intent": min_price is not None or max_price is not None,
                "client_ip": client_ip
            }
        )
    
    start_time = time.time()
    
    try:
        # Get client IP for rate limiting
        client_ip = ip_address or request.client.host
        
        # Check rate limit
        is_allowed, rate_limit_info = rate_limiter.check_rate_limit(
            identifier=client_ip,
            max_requests=AI_SEARCH_RATE_LIMIT,
            window_seconds=AI_SEARCH_RATE_WINDOW
        )
        
        if not is_allowed:
            log_security_event("rate_limit_exceeded", {"client_ip": client_ip}, "WARNING")
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please try again later.",
                headers=rate_limiter.get_rate_limit_headers(rate_limit_info)
            )
        
        # Add rate limit headers to response
        for key, value in rate_limiter.get_rate_limit_headers(rate_limit_info).items():
            response.headers[key] = value
        
        # Extract price intent from query
        min_price, max_price = extract_price_intent(search_query.query)
        cleaned_query = clean_query_from_price_intent(search_query.query)
        
        # Log price intent information with sanitized data
        if min_price is not None or max_price is not None:
            sanitized_original = sanitize_log_data(search_query.query, 50)
            sanitized_cleaned = sanitize_log_data(cleaned_query, 50)
            logger.info(f"💰 Prijsfilter toegepast op AI search: min_price={min_price}, max_price={max_price}")
            logger.info(f"🧹 Opgeschoonde query: '{sanitized_cleaned}' (origineel: '{sanitized_original}')")
        
        # Perform AI search with price filtering
        result = await search_service.ai_search_products_with_price_filter(
            db=db,
            query=cleaned_query,
            page=search_query.page,
            limit=search_query.limit,
            min_price=min_price,
            max_price=max_price,
            user_agent=user_agent,
            ip_address=client_ip,
            source_language=search_query.source_language,
            target_language=search_query.target_language
        )
        
        # Record metrics
        response_time = time.time() - start_time
        metrics_collector.record_search_request(
            search_type="ai",
            cache_hit=result.get("cache_hit", False),
            response_time=response_time,
            results_count=result.get("count", 0)
        )
        
        # Add background tasks for analytics
        background_tasks.add_task(
            log_analytics_task,
            query=query,
            search_type="ai",
            filters={},
            results_count=result.get("count", 0),
            page=page,
            limit=limit,
            response_time_ms=response_time * 1000,
            cache_hit=result.get("cache_hit", False),
            user_agent=user_agent,
            ip_address=client_ip,
            db=db
        )
        
        background_tasks.add_task(
            update_popular_searches_task,
            query=query,
            db=db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ai_search_products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/products")
async def get_products_paginated(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(50, ge=1, le=250, description="Number of results per page (max 250)"),
    sort_by: str = Query("id", description="Sort by field (id, title, price, created_at)"),
    sort_order: str = Query("asc", description="Sort order (asc, desc)"),
    db: Session = Depends(get_db)
):
    """Get all products with pagination and sorting."""
    try:
        # Check cache first
        cache_key = cache_manager.get_cache_key("products", page=page, limit=limit, sort_by=sort_by, sort_order=sort_order)
        cached_result = cache_manager.get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Cache hit for products (page {page})")
            return cached_result
            
        logger.info(f"Fetching products (page {page}, limit {limit}, sort: {sort_by} {sort_order})")
        
        # Base query
        query = db.query(Product)
        
        # Apply sorting
        if hasattr(Product, sort_by):
            sort_column = getattr(Product, sort_by)
            if sort_order.lower() == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        
        # Count total results
        total_count = query.count()
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        
        # Apply pagination
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()
        
        # Convert to JSON
        products = [
            {
                "id": product.id,
                "shopify_id": product.shopify_id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "tags": product.tags
            }
            for product in results
        ]
        
        # Create pagination metadata
        pagination_meta = {
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            }
        }
        
        result = {
            "products": products,
            "count": len(products),
            "sorting": {
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            **pagination_meta
        }
        
        # Cache the result
        cache_manager.set_cached_result(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_products_paginated: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving products")

@router.get("/suggestions/autocomplete")
async def get_autocomplete_suggestions_endpoint(
    query: str = Query(..., description="Query for autocomplete"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    include_popular: bool = Query(True, description="Include popular suggestions"),
    include_related: bool = Query(True, description="Include related suggestions"),
    db: Session = Depends(get_db)
):
    """Get autocomplete suggestions for a query with price intent filtering."""
    try:
        # Log de originele query
        original_query = query
        
        # Check of query leeg is en gebruik fallback
        if not query or not query.strip():
            logger.warning("🔍 Autocomplete aangeroepen met lege query, gebruik fallback")
            query = "popular"  # Fallback waarde
            logger.info(f"🔄 Query overschreven door fallback: '{query}'")
        
        # Extract price intent from query
        min_price, max_price = extract_price_intent(query)
        cleaned_query = clean_query_from_price_intent(query)
        
        # Log price intent information
        if min_price is not None or max_price is not None:
            logger.info(f"💰 Prijsfilter toegepast: min_price={min_price}, max_price={max_price}")
            logger.info(f"🧹 Opgeschoonde query: '{cleaned_query}'")
        
        # Check cache first (include price filters in cache key)
        cache_key = cache_manager.get_cache_key(
            "autocomplete", 
            query=cleaned_query, 
            limit=limit, 
            include_popular=include_popular, 
            include_related=include_related,
            min_price=min_price,
            max_price=max_price
        )
        cached_result = cache_manager.get_cached_result(cache_key)
        if cached_result:
            logger.info(f"✅ Cache hit for autocomplete: '{cleaned_query}' (met prijsfilter)")
            return cached_result
            
        logger.info(f"🔍 Getting autocomplete suggestions for: '{cleaned_query}' (met prijsfilter)")
        
        suggestions = []
        
        # Get autocomplete suggestions with price filtering
        autocomplete_suggestions = search_service.get_autocomplete_suggestions_with_price_filter(
            db, cleaned_query, limit, min_price, max_price
        )
        suggestions.extend(autocomplete_suggestions)
        
        # Add popular suggestions (also filtered by price)
        if include_popular and len(suggestions) < limit:
            popular_suggestions = search_service.get_popular_suggestions_with_price_filter(
                db, limit - len(suggestions), min_price, max_price
            )
            suggestions.extend(popular_suggestions)
        
        # Add related suggestions (also filtered by price)
        if include_related and len(suggestions) < limit:
            related_suggestions = search_service.get_related_suggestions_with_price_filter(
                db, cleaned_query, limit - len(suggestions), min_price, max_price
            )
            suggestions.extend(related_suggestions)
        
        # Generate suggestions from product data as fallback (with price filtering)
        if len(suggestions) < limit:
            product_suggestions = search_service.generate_suggestions_from_products_with_price_filter(
                db, cleaned_query, limit - len(suggestions), min_price, max_price
            )
            for suggestion in product_suggestions:
                suggestions.append({
                    "suggestion": suggestion,
                    "type": "product",
                    "search_count": 0,
                    "click_count": 0,
                    "relevance_score": 0.5,
                    "similarity_score": 0.8
                })
        
        # If no suggestions found with price filter, get cheapest alternatives
        if len(suggestions) == 0 and (min_price is not None or max_price is not None):
            logger.warning(f"⚠️ Geen producten gevonden binnen prijsrange, toon goedkoopste alternatieven")
            cheapest_suggestions = search_service.get_cheapest_product_suggestions(db, limit)
            suggestions.extend(cheapest_suggestions)
        
        result = {
            "query": cleaned_query,
            "original_query": original_query,
            "suggestions": suggestions[:limit],
            "count": len(suggestions[:limit]),
            "fallback_used": original_query != query,
            "price_filter": {
                "min_price": min_price,
                "max_price": max_price,
                "applied": min_price is not None or max_price is not None,
                "message": format_price_message(min_price, max_price)
            },
            "no_products_in_range": len(suggestions) == 0 and (min_price is not None or max_price is not None),
            "alternative_message": "Geen producten gevonden binnen de prijsklasse, hier zijn de goedkoopste alternatieven." if len(suggestions) == 0 and (min_price is not None or max_price is not None) else None
        }
        
        # Cache the result
        cache_manager.set_cached_result(cache_key, result)
        
        logger.info(f"✅ Autocomplete suggestions succesvol gegenereerd: {len(suggestions[:limit])} suggesties voor '{cleaned_query}' (met prijsfilter)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in autocomplete suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get autocomplete suggestions")

@router.post("/track-click")
async def track_product_click_endpoint(
    search_analytics_id: int = Query(..., description="Search analytics ID"),
    product_id: int = Query(..., description="Product ID"),
    position: int = Query(..., description="Position in search results (1-based)"),
    click_time_ms: float = Query(..., description="Time after search in milliseconds"),
    db: Session = Depends(get_db)
):
    """Track when a user clicks on a search result."""
    try:
        analytics_manager.track_product_click(db, search_analytics_id, product_id, position, click_time_ms)
        return {"message": "Click tracked successfully", "status": "success"}
        
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        raise HTTPException(status_code=500, detail="Failed to track click")

@router.get("/analytics/performance")
async def get_performance_analytics(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    search_type: Optional[str] = Query(None, description="Filter by search type (basic, ai, faceted)"),
    db: Session = Depends(get_db)
):
    """Get performance analytics for a specific period."""
    try:
        return analytics_manager.get_performance_analytics(db, start_date, end_date, search_type)
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analytics")

@router.get("/analytics/popular-searches")
async def get_popular_searches_analytics(
    limit: int = Query(20, ge=1, le=100, description="Number of popular search terms"),
    min_searches: int = Query(1, ge=1, description="Minimum number of searches"),
    db: Session = Depends(get_db)
):
    """Get popular search terms with statistics."""
    try:
        return analytics_manager.get_popular_searches_analytics(db, limit, min_searches)
        
    except Exception as e:
        logger.error(f"Error getting popular searches analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular searches analytics")

@router.delete("/cache/clear")
async def clear_cache():
    """Clear all product cache."""
    try:
        cache_manager.clear_cache()
        return {"message": "Cache cleared successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        return cache_manager.get_cache_stats()
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")

@router.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics."""
    try:
        metrics = metrics_collector.get_metrics()
        return Response(content=metrics, media_type="text/plain")
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.post("/privacy/cleanup")
async def cleanup_expired_data(db: Session = Depends(get_db)):
    """
    Clean up expired data for GDPR compliance.
    
    This endpoint removes expired analytics data based on retention policies.
    Should be called periodically (e.g., daily) via cron job.
    """
    try:
        # Clean up expired analytics data
        analytics_cleanup = analytics_manager.cleanup_expired_data(db)
        
        # Clean up expired sessions
        sessions_cleanup = analytics_manager.cleanup_expired_sessions(db)
        
        return {
            "message": "Data cleanup completed successfully",
            "cleanup_stats": {
                "analytics_records": analytics_cleanup.get("search_analytics", 0),
                "expired_sessions": sessions_cleanup
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise HTTPException(status_code=500, detail="Error during data cleanup")

@router.get("/privacy/status")
async def get_privacy_status():
    """
    Get privacy compliance status and configuration.
    """
    from utils.privacy_utils import PRIVACY_CONFIG
    
    return {
        "privacy_compliance": {
            "ip_anonymization": PRIVACY_CONFIG["ip_anonymization"],
            "user_agent_sanitization": PRIVACY_CONFIG["user_agent_sanitization"],
            "session_expiry_hours": PRIVACY_CONFIG["session_expiry_hours"],
            "log_sanitization": PRIVACY_CONFIG["log_sanitization"],
            "data_retention_days": PRIVACY_CONFIG["search_analytics_retention_days"]
        },
        "security_features": {
            "input_validation": True,
            "rate_limiting": True,
            "sql_injection_protection": True,
            "xss_protection": True
        },
        "timestamp": datetime.now().isoformat()
    } 