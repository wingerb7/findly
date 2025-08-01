#!/usr/bin/env python3
"""
Simple mock server for testing the benchmark rate limiting functionality.
"""

from fastapi import FastAPI, Query
import asyncio
import time
import random
import json
from typing import List, Dict, Any

app = FastAPI(title="Mock AI Search API", version="1.0.0")

# Mock product data
MOCK_PRODUCTS = [
    {
        "title": "Zwarte leren schoenen",
        "price": 89.99,
        "similarity": 0.95,
        "tags": ["schoenen", "leer", "zwart", "casual"],
        "category": "schoenen",
        "brand": "StyleHub"
    },
    {
        "title": "Blauwe katoenen shirt",
        "price": 29.99,
        "similarity": 0.88,
        "tags": ["shirt", "katoen", "blauw", "casual"],
        "category": "shirt",
        "brand": "UrbanWear"
    },
    {
        "title": "Rode leren tas",
        "price": 149.99,
        "similarity": 0.92,
        "tags": ["tas", "leer", "rood", "elegant"],
        "category": "tas",
        "brand": "Fashionista"
    },
    {
        "title": "Grijze hoodie",
        "price": 59.99,
        "similarity": 0.85,
        "tags": ["hoodie", "katoen", "grijs", "casual"],
        "category": "hoodie",
        "brand": "StyleHub"
    },
    {
        "title": "Witte sneakers",
        "price": 79.99,
        "similarity": 0.90,
        "tags": ["schoenen", "wit", "sport", "casual"],
        "category": "schoenen",
        "brand": "SportFlex"
    }
]

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Mock AI Search API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/api/ai-search")
async def ai_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(25, description="Number of results"),
    page: int = Query(1, description="Page number")
):
    """Mock AI search endpoint that simulates the real API."""
    
    # Simulate processing time
    await asyncio.sleep(random.uniform(0.1, 0.5))
    
    # Simulate cache hit occasionally
    cache_hit = random.random() < 0.3
    
    # Filter products based on query (simple keyword matching)
    query_lower = query.lower()
    filtered_products = []
    
    for product in MOCK_PRODUCTS:
        # Simple relevance scoring based on keyword matches
        relevance_score = 0.0
        for tag in product["tags"]:
            if tag.lower() in query_lower:
                relevance_score += 0.2
        if product["title"].lower() in query_lower:
            relevance_score += 0.3
        if product["category"].lower() in query_lower:
            relevance_score += 0.2
        if product["brand"].lower() in query_lower:
            relevance_score += 0.1
            
        if relevance_score > 0:
            product_copy = product.copy()
            product_copy["similarity"] = min(0.99, product_copy["similarity"] + relevance_score)
            filtered_products.append(product_copy)
    
    # Sort by similarity
    filtered_products.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Apply limit
    results = filtered_products[:limit]
    
    # Simulate price filter
    price_filter_applied = any(word in query_lower for word in ["goedkoop", "duur", "betaalbaar"])
    
    # Simulate facets
    facets = {
        "categories": ["schoenen", "shirt", "tas", "hoodie"],
        "brands": ["StyleHub", "UrbanWear", "Fashionista", "SportFlex"],
        "colors": ["zwart", "blauw", "rood", "grijs", "wit"],
        "materials": ["leer", "katoen"]
    }
    
    # Simulate search suggestions
    suggestions = {
        "suggestions": [f"{query} premium", f"{query} goedkoop", f"{query} nieuw"],
        "correction_applied": False
    }
    
    response = {
        "results": results,
        "count": len(results),
        "query": query,
        "cache_hit": cache_hit,
        "price_filter": {
            "applied": price_filter_applied,
            "fallback_used": False
        },
        "facets": facets,
        "search_suggestions": suggestions,
        "metadata": {
            "timing": {
                "embedding_generation_time": random.uniform(0.05, 0.15),
                "search_time": random.uniform(0.1, 0.3)
            }
        }
    }
    
    return response

@app.get("/api/test")
async def test():
    """Simple test endpoint."""
    return {"message": "Mock server is working!", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Mock AI Search API Server...")
    print("📍 Endpoints:")
    print("   - GET /                    - Root endpoint")
    print("   - GET /health              - Health check")
    print("   - GET /api/ai-search       - Mock AI search")
    print("   - GET /api/test            - Test endpoint")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 