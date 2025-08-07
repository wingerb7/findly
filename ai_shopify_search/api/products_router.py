#!/usr/bin/env python3
"""
Products API Router

Handles all product-related endpoints with AI-powered search and features.

ENDPOINT ORGANIZATION:
- PRODUCTION ENDPOINTS: Core functionality for production use
- DEBUG ENDPOINTS: Development and testing endpoints (DEV-only)
- SEARCH ENDPOINTS: AI-powered search functionality
- UTILITY ENDPOINTS: Additional utility endpoints
"""

import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

from ai_shopify_search.core.database import get_db, get_store_db, get_store_database_url
from ai_shopify_search.core.metrics import metrics_collector
from ai_shopify_search.core.rate_limiter import rate_limiter
from ai_shopify_search.core.progress_tracker import progress_tracker
from ai_shopify_search.services.service_factory import (
    get_ai_search_service, get_facets_service
)
from ai_shopify_search.api.schemas import SearchResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Constants
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 25
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_DEBUG_LIMIT = 5
DEFAULT_DEBUG_SIMILARITY_THRESHOLD = 0.1
MAX_LIMIT = 100
MIN_PAGE = 1
MIN_QUERY_LENGTH = 1

# Error Messages
ERROR_NO_SHOPIFY_URL = "No Shopify store URL provided. Please set SHOPIFY_STORE_URL in your .env file or provide shopify_store_url parameter."
ERROR_NO_SHOPIFY_TOKEN = "No Shopify access token provided. Please set SHOPIFY_API_SECRET in your .env file or provide access_token parameter."
ERROR_SHOPIFY_CREDENTIALS = "Shopify credentials not configured"
ERROR_PRODUCT_NOT_FOUND = "Product not found"
ERROR_GETTING_PRODUCT_DETAILS = "Error getting product details: {error}"
ERROR_IMAGE_SEARCH = "Error in image-based search: {error}"

# Logging Context Keys
LOG_CONTEXT_QUERY = "query"
LOG_CONTEXT_PAGE = "page"
LOG_CONTEXT_LIMIT = "limit"
LOG_CONTEXT_STORE_ID = "store_id"
LOG_CONTEXT_IMPORT_ID = "import_id"

def _validate_search_request(request: SearchRequest) -> None:
    """
    Validate search request parameters.
    
    Args:
        request: SearchRequest object to validate
        
    Raises:
        HTTPException: If validation fails
    """
    if not request.query or len(request.query.strip()) < MIN_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query must be at least {MIN_QUERY_LENGTH} character long"
        )
    
    if request.page < MIN_PAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Page must be at least {MIN_PAGE}"
        )
    
    if request.limit > MAX_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Limit cannot exceed {MAX_LIMIT}"
        )

def _check_rate_limit(client_ip: str) -> Dict[str, Any]:
    """
    Check rate limit for the client.
    
    Args:
        client_ip: Client IP address
        
    Returns:
        Rate limit information
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    is_allowed, rate_limit_info = rate_limiter.check_rate_limit(
        identifier=client_ip,
        max_requests=100,
        window_seconds=3600
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded",
            headers=rate_limiter.get_rate_limit_headers(rate_limit_info)
        )
    
    return rate_limit_info

async def _perform_ai_search(
    ai_search_service,
    db: Session,
    request: SearchRequest,
    user_agent: Optional[str],
    ip_address: Optional[str]
) -> Optional[Dict[str, Any]]:
    """
    Perform AI-powered search.
    
    Args:
        ai_search_service: AI search service instance
        db: Database session
        request: Search request
        user_agent: User agent string
        ip_address: IP address
        
    Returns:
        Search result or None if failed
    """
    try:
        result = await ai_search_service.search_products(
            db=db,
            query=request.query,
            page=request.page,
            limit=request.limit,
            min_price=request.min_price,
            max_price=request.max_price,
            user_agent=user_agent,
            ip_address=ip_address,
            similarity_threshold=request.similarity_threshold,
            store_id=request.store_id
        )
        
        if result.get("results") and len(result.get("results", [])) > 0:
            return result
            
    except Exception as ai_error:
        logger.warning(f"AI search failed, falling back to fuzzy search: {ai_error}")
    
    return None

async def _perform_fuzzy_search(
    db: Session,
    request: SearchRequest
) -> Dict[str, Any]:
    """
    Perform fuzzy search as fallback.
    
    Args:
        db: Database session
        request: Search request
        
    Returns:
        Fuzzy search result
    """
    from ai_shopify_search.utils.search.fuzzy_search import fuzzy_search_products
    
    logger.info(f"Using fuzzy search fallback for query: {request.query}")
    
    fuzzy_result = await fuzzy_search_products(
        session=db,
        query=request.query,
        limit=request.limit,
        page=request.page
    )
    
    return {
        "results": fuzzy_result.get("results", []),
        "total_count": fuzzy_result.get("total_count", 0),
        "page": request.page,
        "limit": request.limit,
        "cache_hit": False,
        "search_type": "fuzzy_fallback"
    }

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    limit: int = 25
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    similarity_threshold: float = 0.7
    store_id: Optional[str] = None

class ProductImportResponse(BaseModel):
    imported_count: int
    failed_count: int
    errors: List[str]
    message: str
    import_id: Optional[str] = None
    new_or_updated: Optional[int] = None

class ImportProgressResponse(BaseModel):
    id: str
    status: str
    total_items: int
    processed_items: int
    current_step: str
    percentage: float
    elapsed_time: float
    remaining_time: Optional[float] = None
    errors: List[str]
    warnings: List[str]

# =============================================================================
# PRODUCTION ENDPOINTS - Core functionality for production use
# =============================================================================

@router.get("/import/test-connection")
async def test_shopify_connection(
    shopify_store_url: Optional[str] = Query(None, description="Optional: Override store URL from .env file"),
    access_token: Optional[str] = Query(None, description="Optional: Override access token from .env file")
):
    """Test connection to Shopify store."""
    try:
        from ai_shopify_search.services.shopify_import_service import shopify_import_service
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        # Use provided values or defaults from config
        store_url = shopify_store_url or SHOPIFY_STORE_URL
        token = access_token or SHOPIFY_API_SECRET
        
        if not store_url:
            raise HTTPException(
                status_code=400,
                detail=ERROR_NO_SHOPIFY_URL
            )
        
        if not token:
            raise HTTPException(
                status_code=400, 
                detail=ERROR_NO_SHOPIFY_TOKEN
            )
        
        logger.info(f"Testing connection to store: {store_url}")
        
        # Test the connection
        async with shopify_import_service:
            result = await shopify_import_service.test_connection(store_url, token)
        
        if result["success"]:
            return {
                "success": True,
                "store_url": store_url,
                "message": f"Successfully connected to {store_url}",
                "shop_info": result.get("shop_info", {})
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error testing connection: {str(e)}"
        )

@router.get("/import/count-products")
async def count_shopify_products(
    shopify_store_url: Optional[str] = Query(None, description="Optional: Override store URL from .env file"),
    access_token: Optional[str] = Query(None, description="Optional: Override access token from .env file")
):
    """Count total products in Shopify store."""
    try:
        from ai_shopify_search.services.shopify_import_service import shopify_import_service
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        # Use provided values or defaults from config
        store_url = shopify_store_url or SHOPIFY_STORE_URL
        token = access_token or SHOPIFY_API_SECRET
        
        if not store_url:
            raise HTTPException(
                status_code=400,
                detail=ERROR_NO_SHOPIFY_URL
            )
        
        if not token:
            raise HTTPException(
                status_code=400, 
                detail=ERROR_NO_SHOPIFY_TOKEN
            )
        
        logger.info(f"Counting products in store: {store_url}")
        
        # Count the products
        async with shopify_import_service:
            result = await shopify_import_service.count_products(store_url, token)
        
        if result["success"]:
            return {
                "success": True,
                "count": result["count"],
                "store_url": store_url,
                "message": f"Found {result['count']} products in {store_url}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to count products: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error counting products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error counting products: {str(e)}"
        )

@router.post("/import/shopify", response_model=ProductImportResponse)
async def import_shopify_products(
    shopify_store_url: Optional[str] = Query(None, description="Optional: Override store URL from .env file"),
    access_token: Optional[str] = Query(None, description="Optional: Override access token from .env file"),
    generate_embeddings: bool = Query(True, description="Generate AI embeddings for search"),
    generate_image_embeddings: bool = Query(False, description="Generate image embeddings with OpenCLIP"),
    store_id: Optional[str] = Query(None, description="Optional: Store identifier for multi-store support"),
    limit: Optional[int] = Query(None, description="Optional: Limit number of products to import (default: all)"),
    db: Session = Depends(get_db)
):
    """Import products from Shopify store."""
    try:
        from ai_shopify_search.services.shopify_import_service import shopify_import_service
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        # Use provided values or defaults from config
        store_url = shopify_store_url or SHOPIFY_STORE_URL
        token = access_token or SHOPIFY_API_SECRET
        
        if not store_url:
            raise HTTPException(
                status_code=400,
                detail=ERROR_NO_SHOPIFY_URL
            )
        
        if not token:
            raise HTTPException(
                status_code=400, 
                detail=ERROR_NO_SHOPIFY_TOKEN
            )
        
        logger.info(f"Starting import from store: {store_url}, limit: {limit}")
        
        # Import products
        async with shopify_import_service:
            result = await shopify_import_service.import_products(
                store_url=store_url,
                access_token=token,
                db=db,
                generate_embeddings=generate_embeddings,
                generate_image_embeddings=generate_image_embeddings,
                store_id=store_id,
                limit=limit
            )
        
        return ProductImportResponse(**result)
        
    except Exception as e:
        logger.error(f"Error importing products: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error importing products: {str(e)}"
        )

@router.get("/import/status")
async def get_import_status():
    """Get current import status and statistics."""
    try:
        from ai_shopify_search.services.shopify_import_service import shopify_import_service
        
        async with shopify_import_service:
            status = await shopify_import_service.get_import_status()
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting import status: {str(e)}"
        )

@router.get("/import/progress/{import_id}", response_model=ImportProgressResponse)
async def get_import_progress(import_id: str):
    """Get progress for a specific import job."""
    try:
        progress = progress_tracker.get_progress(import_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Import progress not found")
        
        return ImportProgressResponse(**progress)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import progress: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting import progress: {str(e)}"
        )

# =============================================================================
# DEBUG ENDPOINTS - Development and testing endpoints (DEV-only)
# =============================================================================

@router.get("/import/debug-config")
async def debug_shopify_config():
    """DEBUG: Display current Shopify configuration (DEV-only)."""
    try:
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        return {
            "store_url": SHOPIFY_STORE_URL,
            "has_token": bool(SHOPIFY_API_SECRET),
            "token_length": len(SHOPIFY_API_SECRET) if SHOPIFY_API_SECRET else 0,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
    except Exception as e:
        logger.error(f"Debug config error: {e}")
        return {"error": str(e)}

@router.get("/import/debug-fetch")
async def debug_fetch_products(
    limit: int = Query(10, description="Number of products to fetch")
):
    """DEBUG: Test product fetching with limit (DEV-only)."""
    try:
        from ai_shopify_search.services.shopify_import_service import shopify_import_service
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        store_url = SHOPIFY_STORE_URL
        token = SHOPIFY_API_SECRET
        
        if not store_url or not token:
            raise HTTPException(status_code=400, detail="Shopify credentials not configured")
        
        logger.info(f"Debug: Fetching {limit} products from {store_url}")
        
        async with shopify_import_service:
            products = await shopify_import_service.get_products(store_url, token, limit=limit)
        
        return {
            "success": True,
            "requested_limit": limit,
            "actual_count": len(products),
            "first_product": products[0] if products else None,
            "message": f"Fetched {len(products)} products (requested: {limit})"
        }
        
    except Exception as e:
        logger.error(f"Debug fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Debug fetch failed: {str(e)}")

@router.get("/import/test-simple")
async def test_simple_connection():
    """DEBUG: Simple connection test without complex logic (DEV-only)."""
    try:
        import aiohttp
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        store_url = SHOPIFY_STORE_URL
        token = SHOPIFY_API_SECRET
        
        if not store_url or not token:
            return {
                "success": False,
                "message": "Missing Shopify configuration"
            }
        
        # Ensure proper URL format
        if not store_url.startswith(('http://', 'https://')):
            store_url = f"https://{store_url}"
        store_url = store_url.rstrip('/')
        
        api_url = f"{store_url}/admin/api/2023-10/shop.json"
        headers = {
            'X-Shopify-Access-Token': token,
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "message": "Simple connection successful",
                        "shop_name": data.get("shop", {}).get("name", "Unknown")
                    }
                else:
                    return {
                        "success": False,
                        "message": f"HTTP {response.status}: {await response.text()}"
                    }
                    
    except Exception as e:
        return {
            "success": False,
            "message": f"Simple connection failed: {str(e)}"
        }

@router.get("/import/test-shopify-direct")
async def test_shopify_direct():
    """DEBUG: Test direct connection to Shopify API without retry logic (DEV-only)."""
    try:
        import aiohttp
        import ssl
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        store_url = SHOPIFY_STORE_URL
        token = SHOPIFY_API_SECRET
        
        if not store_url or not token:
            return {
                "success": False,
                "message": "Missing Shopify configuration"
            }
        
        # Ensure proper URL format
        if not store_url.startswith(('http://', 'https://')):
            store_url = f"https://{store_url}"
        store_url = store_url.rstrip('/')
        
        api_url = f"{store_url}/admin/api/2023-10/shop.json"
        headers = {
            'X-Shopify-Access-Token': token,
            'Content-Type': 'application/json'
        }
        
        # Create SSL context without verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "message": "Direct connection successful",
                        "shop_info": data.get("shop", {}),
                        "response_time": response.headers.get("X-Request-Id")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "message": f"Direct connection failed: HTTP {response.status}",
                        "error": error_text,
                        "headers": dict(response.headers)
                    }
                    
    except Exception as e:
        return {
            "success": False,
            "message": f"Direct connection error: {str(e)}"
        }

# =============================================================================
# SEARCH ENDPOINTS - AI-powered search functionality
# =============================================================================

@router.post("/search", response_model=SearchResponse)
async def search_products(
    request: SearchRequest,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None)
):
    # Debug: Add logging to track the flow
    logger.info(f"Search request received: {request.query}")
    """AI-powered product search with all features."""
    start_time = time.time()
    
    try:
        # Validate request
        _validate_search_request(request)
        
        # Rate limiting check
        client_ip = ip_address or "unknown"
        rate_limit_info = _check_rate_limit(client_ip)
        
        ai_search_service = await get_ai_search_service()
        
        # Try AI search first
        result = await _perform_ai_search(ai_search_service, db, request, user_agent, ip_address)
        
        if result:
            # Record metrics for successful AI search
            response_time = time.time() - start_time
            metrics_collector.record_search_request(
                search_type="ai_search",
                cache_hit=result.get("cache_hit", False),
                response_time=response_time,
                results_count=len(result.get("results", []))
            )
            
            # Conversational refinements are now generated in AISearchService
            
            # Add rate limit headers
            result["rate_limit"] = rate_limit_info
            return SearchResponse(**result)
        
        # Fallback to fuzzy search if AI search fails or returns no results
        fuzzy_result = await _perform_fuzzy_search(db, request)
        
        # Record metrics for fallback search
        response_time = time.time() - start_time
        metrics_collector.record_search_request(
            search_type="fuzzy_fallback",
            cache_hit=fuzzy_result.get("cache_hit", False),
            response_time=response_time,
            results_count=len(fuzzy_result.get("results", []))
        )
        
        # Conversational refinements for fuzzy fallback are now handled in AISearchService
        
        # Add rate limit headers and mark as fallback
        fuzzy_result["rate_limit"] = rate_limit_info
        fuzzy_result["fallback_used"] = True
        fuzzy_result["search_type"] = "fuzzy_fallback"
        
        return SearchResponse(**fuzzy_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search service unavailable")

def _validate_shopify_credentials(store_url: Optional[str], token: Optional[str]) -> Tuple[str, str]:
    """
    Validate Shopify credentials.
    
    Args:
        store_url: Shopify store URL
        token: Shopify access token
        
    Returns:
        Tuple of (store_url, token)
        
    Raises:
        HTTPException: If credentials are invalid
    """
    if not store_url:
        raise HTTPException(status_code=400, detail=ERROR_NO_SHOPIFY_URL)
    
    if not token:
        raise HTTPException(status_code=400, detail=ERROR_NO_SHOPIFY_TOKEN)
    
    return store_url, token

async def _test_shopify_connection_internal(store_url: str, token: str) -> Dict[str, Any]:
    """
    Test Shopify connection internally.
    
    Args:
        store_url: Shopify store URL
        token: Shopify access token
        
    Returns:
        Connection test result
    """
    from ai_shopify_search.services.shopify_import_service import shopify_import_service
    
    logger.info(f"Testing connection to store: {store_url}")
    
    async with shopify_import_service:
        connection_test = await shopify_import_service.test_connection(store_url, token)
    
    return connection_test

async def _count_shopify_products_internal(store_url: str, token: str) -> Dict[str, Any]:
    """
    Count Shopify products internally.
    
    Args:
        store_url: Shopify store URL
        token: Shopify access token
        
    Returns:
        Product count result
    """
    from ai_shopify_search.services.shopify_import_service import shopify_import_service
    
    logger.info(f"Counting products for store: {store_url}")
    
    async with shopify_import_service:
        count_result = await shopify_import_service.count_products(store_url, token)
    
    return count_result

async def _import_shopify_products_internal(
    store_url: str,
    token: str,
    generate_embeddings: bool,
    generate_image_embeddings: bool,
    store_id: Optional[str],
    limit: Optional[int],
    db: Session
) -> Dict[str, Any]:
    """
    Import Shopify products internally.
    
    Args:
        store_url: Shopify store URL
        token: Shopify access token
        generate_embeddings: Whether to generate embeddings
        generate_image_embeddings: Whether to generate image embeddings
        store_id: Store identifier
        limit: Product limit
        db: Database session
        
    Returns:
        Import result
    """
    from ai_shopify_search.services.shopify_import_service import shopify_import_service
    
    logger.info(f"Starting import for store: {store_url}")
    
    async with shopify_import_service:
        import_result = await shopify_import_service.import_products(
            db=db,
            store_url=store_url,
            access_token=token,
            generate_embeddings=generate_embeddings,
            generate_image_embeddings=generate_image_embeddings,
            store_id=store_id,
            limit=limit
        )
    
    return import_result

@router.get("/search")
async def search_products_get(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    store_id: Optional[str] = Query(None, description="Store identifier for multi-store support"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None)
):
    """GET endpoint for product search with multi-store support."""
    try:
        logger.info(f"GET search request: query='{query}', store_id='{store_id}', page={page}, limit={limit}")
        
        # Create SearchRequest object for consistency
        search_request = SearchRequest(
            query=query,
            page=page,
            limit=limit,
            store_id=store_id,
            min_price=min_price,
            max_price=max_price
        )
        
        # Get the appropriate database session
        if store_id:
            # Use store-specific database
            store_db_url = get_store_database_url(store_id)
            store_engine = create_engine(store_db_url)
            StoreSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=store_engine)
            db = StoreSessionLocal()
        else:
            # Use main database
            db = next(get_db())
        
                # Use the same logic as POST endpoint
        start_time = time.time()
        
        # Rate limiting check
        is_allowed, rate_limit_info = rate_limiter.check_rate_limit(
            identifier="get_search",
            max_requests=100,
            window_seconds=3600
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded",
                headers=rate_limiter.get_rate_limit_headers(rate_limit_info)
            )
        
        # Use AI Search service
        ai_search_service = await get_ai_search_service()
        
        try:
            # Try AI search first
            result = await ai_search_service.search_products(
                db=db,
                query=search_request.query,
                page=search_request.page,
                limit=search_request.limit,
                min_price=search_request.min_price,
                max_price=search_request.max_price,
                user_agent=None,
                ip_address=None,
                similarity_threshold=search_request.similarity_threshold,
                store_id=search_request.store_id
            )
            
            # Check if AI search returned results
            if result.get("results") and len(result.get("results", [])) > 0:
                # Add rate limit headers
                result["rate_limit"] = rate_limit_info
                return SearchResponse(**result)
            
        except Exception as ai_error:
            logger.warning(f"AI search failed, falling back to fuzzy search: {ai_error}")
        
        # Fallback to fuzzy search if AI search fails or returns no results
        try:
            from ai_shopify_search.utils.search.fuzzy_search import fuzzy_search_products
            
            logger.info(f"Using fuzzy search fallback for query: {search_request.query}")
            
            fuzzy_result = await fuzzy_search_products(
                session=db,
                query=search_request.query,
                limit=search_request.limit,
                page=search_request.page
            )
            
            # Add rate limit headers and mark as fallback
            fuzzy_result["rate_limit"] = rate_limit_info
            fuzzy_result["fallback_used"] = True
            fuzzy_result["search_type"] = "fuzzy_fallback"
            
            return SearchResponse(**fuzzy_result)
            
        except Exception as fallback_error:
            logger.error(f"Both AI search and fuzzy fallback failed: {fallback_error}")
            raise HTTPException(status_code=500, detail="Search service unavailable")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # Close the database session
        if 'db' in locals():
            db.close()

@router.get("/search/fallback")
async def search_with_fallback(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Fallback search using basic text matching when AI search fails."""
    try:
        logger.info(f"=== FALLBACK SEARCH DEBUG ===")
        logger.info(f"Query: {query}, page: {page}, limit: {limit}")
        
        from ai_shopify_search.utils.search.fuzzy_search import fuzzy_search_products
        
        logger.info("Calling fuzzy_search_products...")
        results = await fuzzy_search_products(
            session=db,
            query=query,
            page=page,
            limit=limit
        )
        
        logger.info(f"Fuzzy search results keys: {list(results.keys())}")
        logger.info(f"Results count: {len(results.get('results', []))}")
        logger.info(f"Pagination: {results.get('pagination', {})}")
        
        response = {
            "results": results.get("results", []),
            "pagination": results.get("pagination", {}),
            "search_type": "fallback"
        }
        
        logger.info(f"Returning response with {len(response['results'])} results")
        return response
        
    except Exception as e:
        logger.error(f"Fallback search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fallback search failed")

# Autocomplete endpoint removed - functionality not needed

# Smart autocomplete endpoint removed - functionality not needed

# Search suggestions endpoint removed - functionality not needed

@router.get("/facets")
async def get_product_facets(
    query: Optional[str] = Query(None),
    product_ids: Optional[str] = Query(None),  # Comma-separated
    db: Session = Depends(get_db)
):
    """Get product facets for filtering."""
    try:
        facets_service = await get_facets_service()
        facets = await facets_service.get_facets(
            db=db,
            query=query,
            product_ids=product_ids.split(',') if product_ids else None
        )
        return {"facets": facets}
    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search/debug")
async def debug_ai_search(
    query: str = Query(..., description="Search query to debug"),
    limit: int = Query(5, description="Number of results"),
    similarity_threshold: float = Query(0.1, description="Similarity threshold")
):
    """Debug AI search functionality step by step."""
    try:
        from ai_shopify_search.core.database import get_db
        from ai_shopify_search.core.embeddings import generate_embedding
        from ai_shopify_search.utils.search import search_similar_products
        
        db = next(get_db())
        
        debug_info = {
            "query": query,
            "limit": limit,
            "similarity_threshold": similarity_threshold,
            "steps": {}
        }
        
        # Step 1: Generate embedding
        try:
            embedding = generate_embedding(title=query, use_case="query")
            debug_info["steps"]["embedding_generation"] = {
                "success": True,
                "dimensions": len(embedding),
                "sample_values": embedding[:5]
            }
        except Exception as e:
            debug_info["steps"]["embedding_generation"] = {
                "success": False,
                "error": str(e)
            }
            return debug_info
        
        # Step 2: Search database
        try:
            results = search_similar_products(
                session=db,
                embedding=embedding,
                min_score=similarity_threshold,
                limit=limit
            )
            debug_info["steps"]["database_search"] = {
                "success": True,
                "results_count": len(results),
                "results": results[:3]  # Show first 3 results
            }
        except Exception as e:
            debug_info["steps"]["database_search"] = {
                "success": False,
                "error": str(e)
            }
        
        return debug_info
        
    except Exception as e:
        return {
            "error": str(e),
            "query": query
        }

@router.post("/debug/reset-services")
async def reset_services():
    """Reset service factory to force reinitialization."""
    try:
        from ai_shopify_search.services.service_factory import service_factory
        
        # Reset the global service factory
        service_factory._initialized = False
        service_factory._services.clear()
        
        # Reinitialize
        await service_factory.initialize()
        
        return {
            "success": True,
            "message": "Service factory reset and reinitialized",
            "services": list(service_factory._services.keys())
        }
        
    except Exception as e:
        logger.error(f"Service reset error: {e}")
        return {"error": str(e)}

@router.get("/debug/test-store-db")
async def test_store_database(store_id: str = Query(..., description="Store ID to test")):
    """Debug endpoint to test store database connection and count products."""
    try:
        from ai_shopify_search.core.models import Product
        
        # Get store database URL
        store_db_url = get_store_database_url(store_id)
        logger.info(f"Testing store database: {store_db_url}")
        
        # Create engine and session for this store
        store_engine = create_engine(store_db_url)
        StoreSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=store_engine)
        db = StoreSessionLocal()
        
        try:
            # Use StoreProduct model for store databases
            from ai_shopify_search.core.models import StoreProduct
            
            # Count products
            product_count = db.query(StoreProduct).count()
            
            # Get a few sample products
            sample_products = db.query(StoreProduct).limit(5).all()
            
            return {
                "store_id": store_id,
                "database_url": store_db_url,
                "product_count": product_count,
                "sample_products": [
                    {
                        "id": p.id,
                        "shopify_id": p.shopify_id,
                        "title": p.title,
                        "price": p.price
                    } for p in sample_products
                ]
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error testing store database: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/debug/test-refinements")
async def test_refinements():
    """Test conversational refinements directly."""
    try:
        ai_search_service = await get_ai_search_service()
        
        # Test data
        results = [
            {
                "id": "test1",
                "title": "Test Product 1",
                "price": 100.0,
                "tags": ["Zwart", "Katoen"],
                "product_type": "Accessoire",
                "vendor": "Test Brand"
            },
            {
                "id": "test2", 
                "title": "Test Product 2",
                "price": 200.0,
                "tags": ["Wit", "Leder"],
                "product_type": "Accessoire",
                "vendor": "Test Brand 2"
            }
        ]
        
        debug_info = {
            "refinement_agent_available": ai_search_service.refinement_agent is not None,
            "results_length": len(results),
            "condition_met": ai_search_service.refinement_agent and len(results) > 0
        }
        
        if debug_info["condition_met"]:
            try:
                # Extract data from results
                avg_price = sum(r.get('price', 0) for r in results) / len(results) if results else 0
                categories = list(set(r.get('product_type', '') for r in results if r.get('product_type')))
                brands = list(set(r.get('vendor', '') for r in results if r.get('vendor')))
                colors = []
                materials = []
                
                for result in results:
                    tags = result.get('tags', [])
                    for tag in tags:
                        if any(color in tag.lower() for color in ['zwart', 'wit', 'blauw', 'rood', 'groen', 'geel', 'paars', 'grijs', 'bruin', 'beige', 'roze', 'oranje']):
                            colors.append(tag)
                        if any(material in tag.lower() for material in ['leder', 'katoen', 'wol', 'zijde', 'denim', 'polyester', 'linnen']):
                            materials.append(tag)
                

                # RefinementContext creation removed - now handled in AISearchService
                
                debug_info["refinement_context_created"] = False
                debug_info["context_data"] = {
                    "note": "RefinementContext creation moved to AISearchService"
                }
                
                # Test the new _generate_conversational_refinements method
                refinements = ai_search_service._generate_conversational_refinements(results, "test query", None, None)
                debug_info["refinements_generated"] = True
                debug_info["refinements_count"] = len(refinements.refinements) if refinements else 0
                debug_info["refinements"] = [
                    {
                        "title": r.title,
                        "type": r.type,
                        "confidence": r.confidence
                    } for r in refinements.refinements[:3]  # Show first 3
                ] if refinements and refinements.refinements else []
                
            except Exception as e:
                debug_info["refinement_error"] = str(e)
                import traceback
                debug_info["traceback"] = traceback.format_exc()
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

# =============================================================================
# UTILITY ENDPOINTS - Additional utility endpoints
# =============================================================================

@router.get("/products/{shopify_id}/details")
async def get_product_details(
    shopify_id: str,
    shopify_store_url: Optional[str] = Query(None, description="Optional: Override store URL from .env file"),
    access_token: Optional[str] = Query(None, description="Optional: Override access token from .env file")
):
    """Get detailed product information from Shopify."""
    try:
        from ai_shopify_search.services.shopify_import_service import shopify_import_service
        from ai_shopify_search.core.config import SHOPIFY_API_SECRET, SHOPIFY_STORE_URL
        
        store_url = shopify_store_url or SHOPIFY_STORE_URL
        token = access_token or SHOPIFY_API_SECRET
        
        if not store_url or not token:
            raise HTTPException(status_code=400, detail=ERROR_SHOPIFY_CREDENTIALS)
        
        async with shopify_import_service:
            product = await shopify_import_service.get_product_details(store_url, token, shopify_id)
        
        if product:
            return {"success": True, "product": product}
        else:
            raise HTTPException(status_code=404, detail=ERROR_PRODUCT_NOT_FOUND)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        raise HTTPException(status_code=500, detail=ERROR_GETTING_PRODUCT_DETAILS.format(error=str(e))) 

@router.post("/search/image")
async def search_products_by_image(
    image_url: str = Query(..., description="URL of the image to search for"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    store_id: Optional[str] = Query(None, description="Store identifier for multi-store support"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None)
):
    """Search products by image using OpenCLIP embeddings."""
    try:
        # Get AI search service
        ai_search_service = get_ai_search_service()
        
        # Perform image-based search
        result = await ai_search_service.search_products_by_image(
            db=db,
            image_url=image_url,
            page=page,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            user_agent=user_agent,
            ip_address=ip_address,
            similarity_threshold=similarity_threshold,
            store_id=store_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in image-based search: {e}")
        raise HTTPException(
            status_code=500,
            detail=ERROR_IMAGE_SEARCH.format(error=str(e))
        ) 

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `products_import_router.py` - Import-related endpoints
  - `products_search_router.py` - Search-related endpoints
  - `products_debug_router.py` - Debug and testing endpoints
  - `products_utility_router.py` - Utility endpoints
  - `products_schemas.py` - Pydantic models and schemas

## 🗑️ Functies voor Verwijdering
- [ ] `debug_shopify_config()` - Consider moving to a dedicated debug service
- [ ] `debug_fetch_products()` - Consider moving to a dedicated debug service
- [ ] `test_simple_connection()` - Consider moving to a dedicated testing service
- [ ] `test_shopify_direct()` - Consider moving to a dedicated testing service
- [ ] `debug_ai_search()` - Consider moving to a dedicated debug service
- [ ] `reset_services()` - Consider moving to a dedicated admin service
- [ ] `test_store_database()` - Consider moving to a dedicated testing service
- [ ] `test_refinements()` - Consider moving to a dedicated testing service

## ⚡ Performance Optimalisaties
- [ ] Implement caching for frequently accessed product data
- [ ] Add batch processing for multiple search requests
- [ ] Implement parallel processing for search operations
- [ ] Optimize database queries for large datasets
- [ ] Add indexing for frequently accessed patterns

## 🏗️ Architectuur Verbeteringen
- [ ] Implement proper dependency injection
- [ ] Add configuration management for different environments
- [ ] Implement proper error recovery mechanisms
- [ ] Add comprehensive unit and integration tests
- [ ] Implement proper logging strategy with structured logging

## 🔧 Code Verbeteringen
- [ ] Add type hints for all methods
- [ ] Implement proper error handling with custom exceptions
- [ ] Add comprehensive docstrings for all methods
- [ ] Implement proper validation for input parameters
- [ ] Add proper constants for all magic numbers

## 📊 Monitoring en Observability
- [ ] Add comprehensive metrics collection
- [ ] Implement proper distributed tracing
- [ ] Add health checks for the service
- [ ] Implement proper alerting mechanisms
- [ ] Add performance monitoring

## 🔒 Security Verbeteringen
- [ ] Implement proper authentication and authorization
- [ ] Add input validation and sanitization
- [ ] Implement proper secrets management
- [ ] Add audit logging for sensitive operations
- [ ] Implement proper rate limiting strategies

## 🧪 Testing Verbeteringen
- [ ] Add unit tests for all helper methods
- [ ] Implement integration tests for API endpoints
- [ ] Add performance tests for search operations
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete API flow

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)

## 🎯 Specifieke Verbeteringen
- [ ] Refactor large router methods into smaller, more focused ones
- [ ] Implement proper error handling for database operations
- [ ] Add retry mechanisms for failed operations
- [ ] Implement proper caching strategies
- [ ] Add support for different output formats
- [ ] Implement proper progress tracking
- [ ] Add support for custom search scenarios
- [ ] Implement proper result aggregation
- [ ] Add support for different data sources
- [ ] Implement proper result validation
- [ ] Add support for real-time search updates
- [ ] Implement proper data versioning
- [ ] Add support for search comparison
- [ ] Implement proper data export functionality
- [ ] Add support for search templates
- [ ] Implement proper A/B testing for search
- [ ] Add support for personalized search
- [ ] Implement proper feedback collection
- [ ] Add support for search analytics
- [ ] Implement proper search ranking
""" 