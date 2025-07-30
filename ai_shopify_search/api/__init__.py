"""
API routes and endpoints.
"""

from .products_v2 import router as products_router

__all__ = [
    "products_router"
] 