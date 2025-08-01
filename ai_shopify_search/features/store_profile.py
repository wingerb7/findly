#!/usr/bin/env python3
"""
Store Profile System

This module provides automatic store characterization and optimization by:
- Analyzing store product mix and characteristics
- Generating comprehensive store profiles
- Enabling store comparison and similarity matching
- Supporting automatic optimization and transfer learning
"""

import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from pathlib import Path
import sys
from collections import defaultdict, Counter

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class StoreCharacteristics:
    """Represents the characteristics of a store."""
    product_count: int
    price_range: Tuple[float, float]
    average_price: float
    median_price: float
    category_distribution: Dict[str, int]
    brand_distribution: Dict[str, int]
    material_distribution: Dict[str, int]
    color_distribution: Dict[str, int]
    size_distribution: Dict[str, int]
    seasonal_distribution: Dict[str, int]

@dataclass
class PerformanceMetrics:
    """Represents performance metrics for a store."""
    avg_search_score: float
    avg_response_time: float
    cache_hit_rate: float
    conversion_rate: float
    price_filter_usage_rate: float
    fallback_usage_rate: float
    avg_price_coherence: float
    avg_diversity_score: float
    avg_conversion_potential: float

@dataclass
class SearchCharacteristics:
    """Represents search characteristics of a store."""
    most_searched_categories: List[str]
    common_query_patterns: List[str]
    price_sensitivity: str  # low, medium, high
    seasonal_trends: List[str]
    popular_brands: List[str]
    popular_materials: List[str]
    popular_colors: List[str]

@dataclass
class StoreProfile:
    """Represents a comprehensive store profile."""
    store_id: str
    characteristics: StoreCharacteristics
    performance_metrics: PerformanceMetrics
    search_characteristics: SearchCharacteristics
    profile_version: str
    generated_at: datetime
    last_updated: datetime
    confidence_score: float
    data_quality_score: float

@dataclass
class StoreSimilarity:
    """Represents similarity between two stores."""
    store_id_1: str
    store_id_2: str
    overall_similarity: float
    category_similarity: float
    price_similarity: float
    performance_similarity: float
    search_similarity: float
    confidence: float
    comparison_date: datetime

class StoreProfileGenerator:
    """Generator for comprehensive store profiles."""
    
    def __init__(self, db_path: str = "search_knowledge_base.db"):
        self.db_path = db_path
        
        # Similarity weights for store comparison
        self.similarity_weights = {
            "category": 0.3,
            "price": 0.25,
            "performance": 0.2,
            "search": 0.15,
            "brand": 0.1
        }
    
    def generate_store_profile(self, store_id: str) -> Optional[StoreProfile]:
        """Generate a comprehensive profile for a store."""
        try:
            # Get store data
            store_data = self._get_store_data(store_id)
            if not store_data:
                logger.warning(f"No data found for store {store_id}")
                return None
            
            # Generate characteristics
            characteristics = self._generate_characteristics(store_data)
            
            # Generate performance metrics
            performance_metrics = self._generate_performance_metrics(store_id)
            
            # Generate search characteristics
            search_characteristics = self._generate_search_characteristics(store_id)
            
            # Calculate confidence and quality scores
            confidence_score = self._calculate_confidence_score(store_data)
            data_quality_score = self._calculate_data_quality_score(store_data)
            
            profile = StoreProfile(
                store_id=store_id,
                characteristics=characteristics,
                performance_metrics=performance_metrics,
                search_characteristics=search_characteristics,
                profile_version="1.0",
                generated_at=datetime.now(),
                last_updated=datetime.now(),
                confidence_score=confidence_score,
                data_quality_score=data_quality_score
            )
            
            # Store the profile
            self._store_profile(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error generating profile for store {store_id}: {e}")
            return None
    
    def _get_store_data(self, store_id: str) -> List[Dict[str, Any]]:
        """Get store data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get products data (simulated for now)
                # In a real implementation, this would come from Shopify API or product database
                
                # For now, generate sample data based on store_id
                sample_data = self._generate_sample_store_data(store_id)
                return sample_data
                
        except Exception as e:
            logger.error(f"Error getting store data: {e}")
            return []
    
    def _generate_sample_store_data(self, store_id: str) -> List[Dict[str, Any]]:
        """Generate sample store data for testing."""
        # This is a placeholder - in real implementation, this would come from actual store data
        
        # Generate different data based on store_id to simulate different store types
        if "fashion" in store_id.lower():
            return self._generate_fashion_store_data()
        elif "tech" in store_id.lower():
            return self._generate_tech_store_data()
        elif "sports" in store_id.lower():
            return self._generate_sports_store_data()
        else:
            return self._generate_general_store_data()
    
    def _generate_fashion_store_data(self) -> List[Dict[str, Any]]:
        """Generate sample fashion store data."""
        products = []
        
        categories = ["shirts", "pants", "dresses", "shoes", "accessories"]
        brands = ["nike", "adidas", "zara", "h&m", "levi's", "calvin klein"]
        materials = ["cotton", "denim", "polyester", "wool", "leather"]
        colors = ["black", "white", "blue", "red", "green", "yellow"]
        sizes = ["xs", "s", "m", "l", "xl", "xxl"]
        
        for i in range(2500):  # 2500 products
            category = categories[i % len(categories)]
            brand = brands[i % len(brands)]
            material = materials[i % len(materials)]
            color = colors[i % len(colors)]
            size = sizes[i % len(sizes)]
            
            # Generate realistic price based on category and brand
            base_price = 25.0
            if category == "shoes":
                base_price = 80.0
            elif category == "accessories":
                base_price = 15.0
            elif brand in ["nike", "adidas"]:
                base_price *= 1.5
            
            price = base_price + (i % 100)  # Add some variation
            
            products.append({
                "id": f"prod_{i}",
                "title": f"{color} {material} {category}",
                "category": category,
                "brand": brand,
                "material": material,
                "color": color,
                "size": size,
                "price": price,
                "tags": [category, brand, material, color, size]
            })
        
        return products
    
    def _generate_tech_store_data(self) -> List[Dict[str, Any]]:
        """Generate sample tech store data."""
        products = []
        
        categories = ["phones", "laptops", "tablets", "accessories", "gaming"]
        brands = ["apple", "samsung", "dell", "hp", "lenovo", "sony"]
        materials = ["plastic", "aluminum", "glass", "steel"]
        colors = ["black", "white", "silver", "gold", "blue"]
        
        for i in range(1500):  # 1500 products
            category = categories[i % len(categories)]
            brand = brands[i % len(brands)]
            material = materials[i % len(materials)]
            color = colors[i % len(colors)]
            
            # Generate realistic tech prices
            base_price = 100.0
            if category == "phones":
                base_price = 800.0
            elif category == "laptops":
                base_price = 1200.0
            elif category == "tablets":
                base_price = 400.0
            elif category == "gaming":
                base_price = 200.0
            
            price = base_price + (i % 500)  # Add variation
            
            products.append({
                "id": f"prod_{i}",
                "title": f"{brand} {category}",
                "category": category,
                "brand": brand,
                "material": material,
                "color": color,
                "size": "standard",
                "price": price,
                "tags": [category, brand, material, color]
            })
        
        return products
    
    def _generate_sports_store_data(self) -> List[Dict[str, Any]]:
        """Generate sample sports store data."""
        products = []
        
        categories = ["running", "fitness", "outdoor", "team_sports", "swimming"]
        brands = ["nike", "adidas", "under armour", "puma", "reebok"]
        materials = ["polyester", "spandex", "cotton", "nylon"]
        colors = ["black", "white", "blue", "red", "green", "orange"]
        sizes = ["xs", "s", "m", "l", "xl", "xxl"]
        
        for i in range(1800):  # 1800 products
            category = categories[i % len(categories)]
            brand = brands[i % len(brands)]
            material = materials[i % len(materials)]
            color = colors[i % len(colors)]
            size = sizes[i % len(sizes)]
            
            # Generate realistic sports prices
            base_price = 30.0
            if category == "running":
                base_price = 80.0
            elif category == "fitness":
                base_price = 50.0
            elif category == "outdoor":
                base_price = 120.0
            
            price = base_price + (i % 150)  # Add variation
            
            products.append({
                "id": f"prod_{i}",
                "title": f"{brand} {category} gear",
                "category": category,
                "brand": brand,
                "material": material,
                "color": color,
                "size": size,
                "price": price,
                "tags": [category, brand, material, color, size]
            })
        
        return products
    
    def _generate_general_store_data(self) -> List[Dict[str, Any]]:
        """Generate sample general store data."""
        products = []
        
        categories = ["home", "kitchen", "garden", "tools", "books"]
        brands = ["generic", "premium", "budget", "quality"]
        materials = ["plastic", "wood", "metal", "fabric"]
        colors = ["black", "white", "brown", "gray", "multicolor"]
        
        for i in range(2000):  # 2000 products
            category = categories[i % len(categories)]
            brand = brands[i % len(brands)]
            material = materials[i % len(materials)]
            color = colors[i % len(colors)]
            
            # Generate realistic general prices
            base_price = 20.0
            if category == "tools":
                base_price = 50.0
            elif category == "kitchen":
                base_price = 35.0
            
            price = base_price + (i % 80)  # Add variation
            
            products.append({
                "id": f"prod_{i}",
                "title": f"{brand} {category} item",
                "category": category,
                "brand": brand,
                "material": material,
                "color": color,
                "size": "standard",
                "price": price,
                "tags": [category, brand, material, color]
            })
        
        return products
    
    def _generate_characteristics(self, store_data: List[Dict[str, Any]]) -> StoreCharacteristics:
        """Generate store characteristics from data."""
        if not store_data:
            return self._create_empty_characteristics()
        
        # Calculate basic metrics
        prices = [item["price"] for item in store_data]
        categories = [item["category"] for item in store_data]
        brands = [item["brand"] for item in store_data]
        materials = [item["material"] for item in store_data]
        colors = [item["color"] for item in store_data]
        sizes = [item["size"] for item in store_data]
        
        # Calculate distributions
        category_dist = Counter(categories)
        brand_dist = Counter(brands)
        material_dist = Counter(materials)
        color_dist = Counter(colors)
        size_dist = Counter(sizes)
        
        # Calculate price metrics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        
        # Calculate seasonal distribution (placeholder)
        seasonal_dist = {"spring": 25, "summer": 25, "fall": 25, "winter": 25}
        
        return StoreCharacteristics(
            product_count=len(store_data),
            price_range=(min_price, max_price),
            average_price=avg_price,
            median_price=median_price,
            category_distribution=dict(category_dist),
            brand_distribution=dict(brand_dist),
            material_distribution=dict(material_dist),
            color_distribution=dict(color_dist),
            size_distribution=dict(size_dist),
            seasonal_distribution=seasonal_dist
        )
    
    def _create_empty_characteristics(self) -> StoreCharacteristics:
        """Create empty characteristics for stores with no data."""
        return StoreCharacteristics(
            product_count=0,
            price_range=(0.0, 0.0),
            average_price=0.0,
            median_price=0.0,
            category_distribution={},
            brand_distribution={},
            material_distribution={},
            color_distribution={},
            size_distribution={},
            seasonal_distribution={}
        )
    
    def _generate_performance_metrics(self, store_id: str) -> PerformanceMetrics:
        """Generate performance metrics for a store."""
        try:
            # Get performance data from database
            with sqlite3.connect(self.db_path) as conn:
                # Get latest baseline
                cursor = conn.execute("""
                    SELECT * FROM performance_baselines 
                    WHERE store_id = ? 
                    ORDER BY generated_at DESC 
                    LIMIT 1
                """, (store_id,))
                
                row = cursor.fetchone()
                if row:
                    # Extract metrics from baseline
                    return PerformanceMetrics(
                        avg_search_score=row[2] or 0.7,  # overall_baseline
                        avg_response_time=1.2,  # placeholder
                        cache_hit_rate=0.65,  # placeholder
                        conversion_rate=0.12,  # placeholder
                        price_filter_usage_rate=0.3,  # placeholder
                        fallback_usage_rate=0.1,  # placeholder
                        avg_price_coherence=0.75,  # placeholder
                        avg_diversity_score=0.8,  # placeholder
                        avg_conversion_potential=0.6  # placeholder
                    )
                else:
                    # Return default metrics
                    return PerformanceMetrics(
                        avg_search_score=0.7,
                        avg_response_time=1.2,
                        cache_hit_rate=0.65,
                        conversion_rate=0.12,
                        price_filter_usage_rate=0.3,
                        fallback_usage_rate=0.1,
                        avg_price_coherence=0.75,
                        avg_diversity_score=0.8,
                        avg_conversion_potential=0.6
                    )
                    
        except Exception as e:
            logger.error(f"Error generating performance metrics: {e}")
            # Return default metrics
            return PerformanceMetrics(
                avg_search_score=0.7,
                avg_response_time=1.2,
                cache_hit_rate=0.65,
                conversion_rate=0.12,
                price_filter_usage_rate=0.3,
                fallback_usage_rate=0.1,
                avg_price_coherence=0.75,
                avg_diversity_score=0.8,
                avg_conversion_potential=0.6
            )
    
    def _generate_search_characteristics(self, store_id: str) -> SearchCharacteristics:
        """Generate search characteristics for a store."""
        try:
            # Get search data from database
            with sqlite3.connect(self.db_path) as conn:
                # Get recent search queries
                cursor = conn.execute("""
                    SELECT category, intent_type FROM benchmark_history 
                    WHERE store_id = ? 
                    ORDER BY benchmark_date DESC 
                    LIMIT 100
                """, (store_id,))
                
                search_data = cursor.fetchall()
                
                if search_data:
                    # Analyze search patterns
                    categories = [row[0] for row in search_data if row[0]]
                    intents = [row[1] for row in search_data if row[1]]
                    
                    most_searched = Counter(categories).most_common(5)
                    most_searched_categories = [cat for cat, count in most_searched]
                    
                    # Analyze intent patterns
                    intent_patterns = Counter(intents).most_common(3)
                    common_patterns = [intent for intent, count in intent_patterns]
                    
                    # Determine price sensitivity based on store characteristics
                    price_sensitivity = self._determine_price_sensitivity(store_id)
                    
                    # Seasonal trends (placeholder)
                    seasonal_trends = ["summer", "winter"]
                    
                    # Popular attributes (placeholder)
                    popular_brands = ["nike", "adidas", "zara"]
                    popular_materials = ["cotton", "denim", "polyester"]
                    popular_colors = ["black", "white", "blue"]
                    
                else:
                    # Default characteristics
                    most_searched_categories = ["general"]
                    common_patterns = ["category_intent"]
                    price_sensitivity = "medium"
                    seasonal_trends = ["all_seasons"]
                    popular_brands = []
                    popular_materials = []
                    popular_colors = []
                
                return SearchCharacteristics(
                    most_searched_categories=most_searched_categories,
                    common_query_patterns=common_patterns,
                    price_sensitivity=price_sensitivity,
                    seasonal_trends=seasonal_trends,
                    popular_brands=popular_brands,
                    popular_materials=popular_materials,
                    popular_colors=popular_colors
                )
                
        except Exception as e:
            logger.error(f"Error generating search characteristics: {e}")
            # Return default characteristics
            return SearchCharacteristics(
                most_searched_categories=["general"],
                common_query_patterns=["category_intent"],
                price_sensitivity="medium",
                seasonal_trends=["all_seasons"],
                popular_brands=[],
                popular_materials=[],
                popular_colors=[]
            )
    
    def _determine_price_sensitivity(self, store_id: str) -> str:
        """Determine price sensitivity based on store characteristics."""
        # This would be based on actual store data analysis
        # For now, use store_id to determine
        if "budget" in store_id.lower() or "cheap" in store_id.lower():
            return "high"
        elif "premium" in store_id.lower() or "luxury" in store_id.lower():
            return "low"
        else:
            return "medium"
    
    def _calculate_confidence_score(self, store_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the profile."""
        if not store_data:
            return 0.0
        
        # Higher confidence with more data
        data_points = len(store_data)
        if data_points > 1000:
            return 0.95
        elif data_points > 500:
            return 0.85
        elif data_points > 100:
            return 0.75
        else:
            return 0.5
    
    def _calculate_data_quality_score(self, store_data: List[Dict[str, Any]]) -> float:
        """Calculate data quality score for the profile."""
        if not store_data:
            return 0.0
        
        # Check completeness of data
        complete_records = 0
        for item in store_data:
            required_fields = ["title", "category", "price"]
            if all(field in item and item[field] for field in required_fields):
                complete_records += 1
        
        quality_score = complete_records / len(store_data)
        return min(1.0, quality_score)
    
    def _store_profile(self, profile: StoreProfile):
        """Store profile in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS store_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id TEXT UNIQUE,
                        characteristics TEXT,
                        performance_metrics TEXT,
                        search_characteristics TEXT,
                        profile_version TEXT,
                        generated_at TIMESTAMP,
                        last_updated TIMESTAMP,
                        confidence_score REAL,
                        data_quality_score REAL
                    )
                """)
                
                conn.execute("""
                    INSERT OR REPLACE INTO store_profiles (
                        store_id, characteristics, performance_metrics, search_characteristics,
                        profile_version, generated_at, last_updated, confidence_score, data_quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.store_id,
                    json.dumps(self._serialize_characteristics(profile.characteristics)),
                    json.dumps(self._serialize_performance_metrics(profile.performance_metrics)),
                    json.dumps(self._serialize_search_characteristics(profile.search_characteristics)),
                    profile.profile_version,
                    profile.generated_at.isoformat(),
                    profile.last_updated.isoformat(),
                    profile.confidence_score,
                    profile.data_quality_score
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing profile: {e}")
    
    def _serialize_characteristics(self, characteristics: StoreCharacteristics) -> Dict[str, Any]:
        """Serialize characteristics for storage."""
        return {
            "product_count": characteristics.product_count,
            "price_range": characteristics.price_range,
            "average_price": characteristics.average_price,
            "median_price": characteristics.median_price,
            "category_distribution": characteristics.category_distribution,
            "brand_distribution": characteristics.brand_distribution,
            "material_distribution": characteristics.material_distribution,
            "color_distribution": characteristics.color_distribution,
            "size_distribution": characteristics.size_distribution,
            "seasonal_distribution": characteristics.seasonal_distribution
        }
    
    def _serialize_performance_metrics(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Serialize performance metrics for storage."""
        return {
            "avg_search_score": metrics.avg_search_score,
            "avg_response_time": metrics.avg_response_time,
            "cache_hit_rate": metrics.cache_hit_rate,
            "conversion_rate": metrics.conversion_rate,
            "price_filter_usage_rate": metrics.price_filter_usage_rate,
            "fallback_usage_rate": metrics.fallback_usage_rate,
            "avg_price_coherence": metrics.avg_price_coherence,
            "avg_diversity_score": metrics.avg_diversity_score,
            "avg_conversion_potential": metrics.avg_conversion_potential
        }
    
    def _serialize_search_characteristics(self, characteristics: SearchCharacteristics) -> Dict[str, Any]:
        """Serialize search characteristics for storage."""
        return {
            "most_searched_categories": characteristics.most_searched_categories,
            "common_query_patterns": characteristics.common_query_patterns,
            "price_sensitivity": characteristics.price_sensitivity,
            "seasonal_trends": characteristics.seasonal_trends,
            "popular_brands": characteristics.popular_brands,
            "popular_materials": characteristics.popular_materials,
            "popular_colors": characteristics.popular_colors
        }
    
    def get_store_profile(self, store_id: str) -> Optional[StoreProfile]:
        """Get store profile from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM store_profiles 
                    WHERE store_id = ?
                """, (store_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._deserialize_profile(row)
                
        except Exception as e:
            logger.error(f"Error getting store profile: {e}")
            return None
    
    def _deserialize_profile(self, row) -> StoreProfile:
        """Deserialize profile from database row."""
        characteristics_data = json.loads(row[2])
        performance_data = json.loads(row[3])
        search_data = json.loads(row[4])
        
        characteristics = StoreCharacteristics(
            product_count=characteristics_data["product_count"],
            price_range=tuple(characteristics_data["price_range"]),
            average_price=characteristics_data["average_price"],
            median_price=characteristics_data["median_price"],
            category_distribution=characteristics_data["category_distribution"],
            brand_distribution=characteristics_data["brand_distribution"],
            material_distribution=characteristics_data["material_distribution"],
            color_distribution=characteristics_data["color_distribution"],
            size_distribution=characteristics_data["size_distribution"],
            seasonal_distribution=characteristics_data["seasonal_distribution"]
        )
        
        performance_metrics = PerformanceMetrics(
            avg_search_score=performance_data["avg_search_score"],
            avg_response_time=performance_data["avg_response_time"],
            cache_hit_rate=performance_data["cache_hit_rate"],
            conversion_rate=performance_data["conversion_rate"],
            price_filter_usage_rate=performance_data["price_filter_usage_rate"],
            fallback_usage_rate=performance_data["fallback_usage_rate"],
            avg_price_coherence=performance_data["avg_price_coherence"],
            avg_diversity_score=performance_data["avg_diversity_score"],
            avg_conversion_potential=performance_data["avg_conversion_potential"]
        )
        
        search_characteristics = SearchCharacteristics(
            most_searched_categories=search_data["most_searched_categories"],
            common_query_patterns=search_data["common_query_patterns"],
            price_sensitivity=search_data["price_sensitivity"],
            seasonal_trends=search_data["seasonal_trends"],
            popular_brands=search_data["popular_brands"],
            popular_materials=search_data["popular_materials"],
            popular_colors=search_data["popular_colors"]
        )
        
        return StoreProfile(
            store_id=row[1],
            characteristics=characteristics,
            performance_metrics=performance_metrics,
            search_characteristics=search_characteristics,
            profile_version=row[5],
            generated_at=datetime.fromisoformat(row[6]),
            last_updated=datetime.fromisoformat(row[7]),
            confidence_score=row[8],
            data_quality_score=row[9]
        )
    
    def find_similar_stores(self, target_store_id: str, limit: int = 5) -> List[StoreSimilarity]:
        """Find stores similar to the target store."""
        try:
            target_profile = self.get_store_profile(target_store_id)
            if not target_profile:
                return []
            
            # Get all other store profiles
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM store_profiles WHERE store_id != ?
                """, (target_store_id,))
                
                similarities = []
                for row in cursor.fetchall():
                    other_profile = self._deserialize_profile(row)
                    similarity = self._calculate_store_similarity(target_profile, other_profile)
                    
                    if similarity.overall_similarity > 0.3:  # Minimum similarity threshold
                        similarities.append(similarity)
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x.overall_similarity, reverse=True)
                return similarities[:limit]
                
        except Exception as e:
            logger.error(f"Error finding similar stores: {e}")
            return []
    
    def _calculate_store_similarity(self, store1: StoreProfile, store2: StoreProfile) -> StoreSimilarity:
        """Calculate similarity between two stores."""
        # Category similarity
        category_sim = self._calculate_distribution_similarity(
            store1.characteristics.category_distribution,
            store2.characteristics.category_distribution
        )
        
        # Price similarity
        price_sim = self._calculate_price_similarity(
            store1.characteristics.price_range,
            store2.characteristics.price_range
        )
        
        # Performance similarity
        perf_sim = self._calculate_performance_similarity(
            store1.performance_metrics,
            store2.performance_metrics
        )
        
        # Search similarity
        search_sim = self._calculate_search_similarity(
            store1.search_characteristics,
            store2.search_characteristics
        )
        
        # Calculate weighted overall similarity
        overall_sim = (
            category_sim * self.similarity_weights["category"] +
            price_sim * self.similarity_weights["price"] +
            perf_sim * self.similarity_weights["performance"] +
            search_sim * self.similarity_weights["search"]
        )
        
        # Calculate confidence
        confidence = min(store1.confidence_score, store2.confidence_score)
        
        return StoreSimilarity(
            store_id_1=store1.store_id,
            store_id_2=store2.store_id,
            overall_similarity=overall_sim,
            category_similarity=category_sim,
            price_similarity=price_sim,
            performance_similarity=perf_sim,
            search_similarity=search_sim,
            confidence=confidence,
            comparison_date=datetime.now()
        )
    
    def _calculate_distribution_similarity(self, dist1: Dict[str, int], dist2: Dict[str, int]) -> float:
        """Calculate similarity between two distributions."""
        if not dist1 or not dist2:
            return 0.0
        
        # Get all unique keys
        all_keys = set(dist1.keys()) | set(dist2.keys())
        if not all_keys:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = 0
        norm1 = 0
        norm2 = 0
        
        for key in all_keys:
            val1 = dist1.get(key, 0)
            val2 = dist2.get(key, 0)
            dot_product += val1 * val2
            norm1 += val1 * val1
            norm2 += val2 * val2
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 ** 0.5 * norm2 ** 0.5)
    
    def _calculate_price_similarity(self, range1: Tuple[float, float], range2: Tuple[float, float]) -> float:
        """Calculate similarity between price ranges."""
        min1, max1 = range1
        min2, max2 = range2
        
        # Calculate overlap
        overlap_min = max(min1, min2)
        overlap_max = min(max1, max2)
        
        if overlap_max < overlap_min:
            return 0.0
        
        overlap_size = overlap_max - overlap_min
        total_size = (max1 - min1 + max2 - min2) / 2
        
        return overlap_size / total_size if total_size > 0 else 0.0
    
    def _calculate_performance_similarity(self, metrics1: PerformanceMetrics, metrics2: PerformanceMetrics) -> float:
        """Calculate similarity between performance metrics."""
        metrics = [
            metrics1.avg_search_score, metrics1.avg_response_time, metrics1.cache_hit_rate,
            metrics2.avg_search_score, metrics2.avg_response_time, metrics2.cache_hit_rate
        ]
        
        # Calculate average similarity
        similarities = []
        for i in range(0, len(metrics), 2):
            if metrics[i] is not None and metrics[i+1] is not None:
                sim = min(metrics[i], metrics[i+1]) / max(metrics[i], metrics[i+1])
                similarities.append(sim)
        
        return statistics.mean(similarities) if similarities else 0.0
    
    def _calculate_search_similarity(self, search1: SearchCharacteristics, search2: SearchCharacteristics) -> float:
        """Calculate similarity between search characteristics."""
        # Compare most searched categories
        cat_sim = len(set(search1.most_searched_categories) & set(search2.most_searched_categories)) / \
                  len(set(search1.most_searched_categories) | set(search2.most_searched_categories))
        
        # Compare price sensitivity
        price_sim = 1.0 if search1.price_sensitivity == search2.price_sensitivity else 0.0
        
        return (cat_sim + price_sim) / 2
    
    def export_store_profile(self, store_id: str, output_path: str = None) -> str:
        """Export store profile to JSON."""
        profile = self.get_store_profile(store_id)
        if not profile:
            return None
        
        if not output_path:
            output_path = f"store_profile_{store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "store_id": profile.store_id,
            "profile_version": profile.profile_version,
            "generated_at": profile.generated_at.isoformat(),
            "last_updated": profile.last_updated.isoformat(),
            "confidence_score": profile.confidence_score,
            "data_quality_score": profile.data_quality_score,
            "characteristics": self._serialize_characteristics(profile.characteristics),
            "performance_metrics": self._serialize_performance_metrics(profile.performance_metrics),
            "search_characteristics": self._serialize_search_characteristics(profile.search_characteristics)
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_path

# Global instance
store_profile_generator = StoreProfileGenerator() 