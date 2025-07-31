"""
Dynamic facets service for automatic filtering based on search results.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
from core.models import Product

logger = logging.getLogger(__name__)

class FacetsService:
    """Service for generating dynamic facets from search results."""
    
    def __init__(self, cache_service):
        self.cache_service = cache_service
        
        # Define facet categories
        self.facet_categories = {
            "colors": ["zwart", "wit", "blauw", "rood", "groen", "geel", "paars", "grijs", "bruin", "beige", "roze", "oranje"],
            "materials": ["leder", "katoen", "wol", "zijde", "denim", "polyester", "linnen", "synthetisch", "kashmir"],
            "sizes": ["xs", "s", "m", "l", "xl", "xxl", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"],
            "brands": ["urbanwear", "fashionista", "stylehub", "elegance", "modernfit", "sportflex", "classicline", "trendify"],
            "categories": ["schoenen", "jas", "jassen", "shirt", "shirts", "broek", "broeken", "jurk", "jurken", "accessoire", "accessoires"],
            "seasons": ["zomer", "winter", "lente", "herfst"],
            "styles": ["casual", "formeel", "sport", "elegant", "nieuw", "sale"]
        }
        
        # Price ranges for dynamic price facets
        self.price_ranges = [
            {"min": 0, "max": 25, "label": "€0-25"},
            {"min": 25, "max": 50, "label": "€25-50"},
            {"min": 50, "max": 100, "label": "€50-100"},
            {"min": 100, "max": 200, "label": "€100-200"},
            {"min": 200, "max": 500, "label": "€200-500"},
            {"min": 500, "max": None, "label": "€500+"}
        ]
    
    async def generate_facets_from_results(
        self, 
        db: Session, 
        results: List[Dict[str, Any]],
        query: str = None
    ) -> Dict[str, Any]:
        """
        Generate dynamic facets from search results.
        
        Args:
            db: Database session
            results: Search results
            query: Original search query
            
        Returns:
            Dictionary with facet categories and values
        """
        try:
            if not results:
                return self._get_empty_facets()
            
            # Extract product IDs from results
            product_ids = []
            logger.info(f"🔍 Extracting product IDs from {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"🔍 Result {i}: type={type(result)}, keys={list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                if isinstance(result, dict) and result.get("id"):
                    product_ids.append(result["id"])
                    logger.info(f"✅ Added product ID: {result['id']}")
                elif hasattr(result, 'id'):
                    product_ids.append(result.id)
                    logger.info(f"✅ Added product ID: {result.id}")
                else:
                    logger.warning(f"⚠️ Could not extract ID from result {i}")
            
            logger.info(f"🔍 Extracted {len(product_ids)} product IDs: {product_ids[:5]}")
            
            if not product_ids:
                return self._get_empty_facets()
            
            # Check cache
            cache_key = f"facets:{query}:{len(product_ids)}"
            cached_result = self.cache_service.get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Generate facets
            facets = {
                "colors": await self._extract_color_facets(db, product_ids),
                "materials": await self._extract_material_facets(db, product_ids),
                "sizes": await self._extract_size_facets(db, product_ids),
                "brands": await self._extract_brand_facets(db, product_ids),
                "categories": await self._extract_category_facets(db, product_ids),
                "seasons": await self._extract_season_facets(db, product_ids),
                "styles": await self._extract_style_facets(db, product_ids),
                "price_ranges": await self._extract_price_facets(db, product_ids),
                "tags": await self._extract_tag_facets(db, product_ids)
            }
            
            # Add facet metadata
            facets["metadata"] = {
                "total_products": len(product_ids),
                "query": query,
                "facet_count": sum(len(facet) for facet in facets.values() if isinstance(facet, list)),
                "debug": {
                    "product_ids_count": len(product_ids),
                    "product_ids_sample": product_ids[:5] if product_ids else []
                }
            }
            
            # Cache results
            self.cache_service.set_cached_result(cache_key, facets, ttl=1800)  # 30 minutes
            
            return facets
            
        except Exception as e:
            logger.error(f"Error generating facets: {e}")
            return self._get_empty_facets()
    
    async def _extract_color_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract color facets from products."""
        try:
            # Query products and extract colors from tags
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            color_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["colors"]:
                            color_counts[tag_lower] = color_counts.get(tag_lower, 0) + 1
            
            # Convert to facet format
            facets = []
            for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": color,
                    "label": color.title(),
                    "count": count,
                    "type": "color"
                })
            
            return facets[:10]  # Top 10 colors
            
        except Exception as e:
            logger.error(f"Error extracting color facets: {e}")
            return []
    
    async def _extract_material_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract material facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            material_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["materials"]:
                            material_counts[tag_lower] = material_counts.get(tag_lower, 0) + 1
            
            facets = []
            for material, count in sorted(material_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": material,
                    "label": material.title(),
                    "count": count,
                    "type": "material"
                })
            
            return facets[:8]  # Top 8 materials
            
        except Exception as e:
            logger.error(f"Error extracting material facets: {e}")
            return []
    
    async def _extract_size_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract size facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            size_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["sizes"]:
                            size_counts[tag_lower] = size_counts.get(tag_lower, 0) + 1
            
            facets = []
            for size, count in sorted(size_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": size,
                    "label": size.upper(),
                    "count": count,
                    "type": "size"
                })
            
            return facets[:12]  # Top 12 sizes
            
        except Exception as e:
            logger.error(f"Error extracting size facets: {e}")
            return []
    
    async def _extract_brand_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract brand facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            brand_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["brands"]:
                            brand_counts[tag_lower] = brand_counts.get(tag_lower, 0) + 1
            
            facets = []
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": brand,
                    "label": brand.title(),
                    "count": count,
                    "type": "brand"
                })
            
            return facets[:8]  # Top 8 brands
            
        except Exception as e:
            logger.error(f"Error extracting brand facets: {e}")
            return []
    
    async def _extract_category_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract category facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            category_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["categories"]:
                            category_counts[tag_lower] = category_counts.get(tag_lower, 0) + 1
            
            facets = []
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": category,
                    "label": category.title(),
                    "count": count,
                    "type": "category"
                })
            
            return facets[:6]  # Top 6 categories
            
        except Exception as e:
            logger.error(f"Error extracting category facets: {e}")
            return []
    
    async def _extract_season_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract season facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            season_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["seasons"]:
                            season_counts[tag_lower] = season_counts.get(tag_lower, 0) + 1
            
            facets = []
            for season, count in sorted(season_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": season,
                    "label": season.title(),
                    "count": count,
                    "type": "season"
                })
            
            return facets[:4]  # All seasons
            
        except Exception as e:
            logger.error(f"Error extracting season facets: {e}")
            return []
    
    async def _extract_style_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract style facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            style_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        if tag_lower in self.facet_categories["styles"]:
                            style_counts[tag_lower] = style_counts.get(tag_lower, 0) + 1
            
            facets = []
            for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": style,
                    "label": style.title(),
                    "count": count,
                    "type": "style"
                })
            
            return facets[:6]  # Top 6 styles
            
        except Exception as e:
            logger.error(f"Error extracting style facets: {e}")
            return []
    
    async def _extract_price_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract price range facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            price_range_counts = {}
            for product in products:
                price = product.price or 0
                for price_range in self.price_ranges:
                    if price_range["min"] <= price and (price_range["max"] is None or price < price_range["max"]):
                        label = price_range["label"]
                        price_range_counts[label] = price_range_counts.get(label, 0) + 1
                        break
            
            facets = []
            for price_range, count in sorted(price_range_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": price_range,
                    "label": price_range,
                    "count": count,
                    "type": "price_range"
                })
            
            return facets[:6]  # All price ranges
            
        except Exception as e:
            logger.error(f"Error extracting price facets: {e}")
            return []
    
    async def _extract_tag_facets(
        self, 
        db: Session, 
        product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Extract general tag facets from products."""
        try:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            tag_counts = {}
            for product in products:
                if product.tags:
                    for tag in product.tags:
                        tag_lower = tag.lower()
                        # Skip already categorized tags
                        if not any(tag_lower in category for category in self.facet_categories.values()):
                            tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1
            
            facets = []
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
                facets.append({
                    "value": tag,
                    "label": tag.title(),
                    "count": count,
                    "type": "tag"
                })
            
            return facets[:10]  # Top 10 general tags
            
        except Exception as e:
            logger.error(f"Error extracting tag facets: {e}")
            return []
    
    def _get_empty_facets(self) -> Dict[str, Any]:
        """Return empty facets structure."""
        return {
            "colors": [],
            "materials": [],
            "sizes": [],
            "brands": [],
            "categories": [],
            "seasons": [],
            "styles": [],
            "price_ranges": [],
            "tags": [],
            "metadata": {
                "total_products": 0,
                "query": None,
                "facet_count": 0
            }
        }
    
    async def get_facet_filter_query(
        self, 
        facet_type: str, 
        facet_value: str
    ) -> str:
        """Generate a search query for a specific facet filter."""
        try:
            # Map facet types to search terms
            facet_mappings = {
                "color": f"{facet_value}",
                "material": f"{facet_value}",
                "size": f"maat {facet_value}",
                "brand": f"{facet_value}",
                "category": f"{facet_value}",
                "season": f"{facet_value}",
                "style": f"{facet_value}",
                "price_range": f"onder {facet_value.split('-')[1] if '-' in facet_value else facet_value}",
                "tag": f"{facet_value}"
            }
            
            return facet_mappings.get(facet_type, facet_value)
            
        except Exception as e:
            logger.error(f"Error generating facet filter query: {e}")
            return facet_value 