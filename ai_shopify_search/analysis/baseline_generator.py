#!/usr/bin/env python3
"""
Baseline Generator

Generates performance baselines for stores to measure and improve search performance.
"""

import logging
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import json

logger = logging.getLogger(__name__)

@dataclass
class CategoryBaseline:
    """Baseline metrics for a specific category."""
    avg_score: float
    avg_response_time: float
    avg_price_coherence: float
    avg_diversity_score: float
    avg_conversion_potential: float
    total_queries: int
    successful_queries: int
    success_rate: float
    confidence: float
    trend: str  # "improving", "declining", "stable"
    last_updated: datetime

@dataclass
class IntentBaseline:
    """Baseline metrics for a specific intent type."""
    avg_score: float
    avg_response_time: float
    price_filter_usage_rate: float
    fallback_usage_rate: float
    cache_hit_rate: float
    total_queries: int
    successful_queries: int
    success_rate: float
    confidence: float
    category_distribution: Dict[str, int]
    last_updated: datetime

@dataclass
class StoreBaseline:
    """Complete baseline for a store."""
    store_id: str
    overall_baseline: float
    performance_grade: str  # "A", "B", "C", "D", "F"
    improvement_opportunities: List[str]
    generated_at: datetime
    category_baselines: Dict[str, CategoryBaseline]
    intent_baselines: Dict[str, IntentBaseline]

class BaselineGenerator:
    """Generates comprehensive performance baselines for stores."""
    
    def __init__(self, db_path: str = "data/databases/findly_consolidated.db"):
        self.db_path = db_path
    
    def generate_store_baselines(self, store_id: str, days_back: int = 30) -> StoreBaseline:
        """Generate comprehensive baselines for a store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get search analytics for the period
                start_date = datetime.now() - timedelta(days=days_back)
                
                cursor = conn.execute("""
                    SELECT * FROM search_analytics 
                    WHERE store_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (store_id, start_date.isoformat()))
                
                analytics_data = cursor.fetchall()
                
                if not analytics_data:
                    logger.warning(f"No analytics data found for store {store_id}")
                    return self._create_empty_baseline(store_id)
                
                # Generate category baselines
                category_baselines = self._generate_category_baselines(analytics_data)
                
                # Generate intent baselines
                intent_baselines = self._generate_intent_baselines(analytics_data)
                
                # Calculate overall baseline
                overall_baseline = self._calculate_overall_baseline(category_baselines, intent_baselines)
                
                # Determine performance grade
                performance_grade = self._calculate_performance_grade(overall_baseline)
                
                # Identify improvement opportunities
                improvement_opportunities = self._identify_improvement_opportunities(
                    category_baselines, intent_baselines
                )
                
                return StoreBaseline(
                    store_id=store_id,
                    overall_baseline=overall_baseline,
                    performance_grade=performance_grade,
                    improvement_opportunities=improvement_opportunities,
                    generated_at=datetime.now(),
                    category_baselines=category_baselines,
                    intent_baselines=intent_baselines
                )
                
        except Exception as e:
            logger.error(f"Failed to generate baselines for store {store_id}: {e}")
            return self._create_empty_baseline(store_id)
    
    def _generate_category_baselines(self, analytics_data: List) -> Dict[str, CategoryBaseline]:
        """Generate baselines for different product categories."""
        category_data = {}
        
        for row in analytics_data:
            # Extract category from query or filters
            category = self._extract_category_from_query(row[1])  # query column
            if not category:
                continue
                
            if category not in category_data:
                category_data[category] = []
            category_data[category].append(row)
        
        baselines = {}
        for category, data in category_data.items():
            if len(data) < 5:  # Need minimum data points
                continue
                
            scores = [row[8] for row in data if row[8] is not None]  # response_time_ms
            response_times = [row[8] for row in data if row[8] is not None]
            
            if not scores:
                continue
                
            baseline = CategoryBaseline(
                avg_score=statistics.mean(scores),
                avg_response_time=statistics.mean(response_times) if response_times else 0,
                avg_price_coherence=self._calculate_price_coherence(data),
                avg_diversity_score=self._calculate_diversity_score(data),
                avg_conversion_potential=self._calculate_conversion_potential(data),
                total_queries=len(data),
                successful_queries=len([row for row in data if row[6] > 0]),  # result_count > 0
                success_rate=len([row for row in data if row[6] > 0]) / len(data),
                confidence=min(1.0, len(data) / 100),  # More data = higher confidence
                trend=self._calculate_trend(data),
                last_updated=datetime.now()
            )
            
            baselines[category] = baseline
        
        return baselines
    
    def _generate_intent_baselines(self, analytics_data: List) -> Dict[str, IntentBaseline]:
        """Generate baselines for different search intents."""
        intent_data = {}
        
        for row in analytics_data:
            intent_type = self._classify_search_intent(row[1])  # query column
            if intent_type not in intent_data:
                intent_data[intent_type] = []
            intent_data[intent_type].append(row)
        
        baselines = {}
        for intent_type, data in intent_data.items():
            if len(data) < 3:  # Need minimum data points
                continue
                
            scores = [row[8] for row in data if row[8] is not None]
            response_times = [row[8] for row in data if row[8] is not None]
            
            if not scores:
                continue
                
            baseline = IntentBaseline(
                avg_score=statistics.mean(scores),
                avg_response_time=statistics.mean(response_times) if response_times else 0,
                price_filter_usage_rate=self._calculate_price_filter_usage(data),
                fallback_usage_rate=self._calculate_fallback_usage(data),
                cache_hit_rate=self._calculate_cache_hit_rate(data),
                total_queries=len(data),
                successful_queries=len([row for row in data if row[6] > 0]),
                success_rate=len([row for row in data if row[6] > 0]) / len(data),
                confidence=min(1.0, len(data) / 50),
                category_distribution=self._calculate_category_distribution(data),
                last_updated=datetime.now()
            )
            
            baselines[intent_type] = baseline
        
        return baselines
    
    def _calculate_overall_baseline(self, category_baselines: Dict, intent_baselines: Dict) -> float:
        """Calculate overall baseline score."""
        if not category_baselines and not intent_baselines:
            return 0.0
        
        scores = []
        
        # Add category baseline scores
        for baseline in category_baselines.values():
            scores.append(baseline.avg_score)
        
        # Add intent baseline scores
        for baseline in intent_baselines.values():
            scores.append(baseline.avg_score)
        
        return statistics.mean(scores) if scores else 0.0
    
    def _calculate_performance_grade(self, baseline_score: float) -> str:
        """Calculate performance grade based on baseline score."""
        if baseline_score >= 0.9:
            return "A"
        elif baseline_score >= 0.8:
            return "B"
        elif baseline_score >= 0.7:
            return "C"
        elif baseline_score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _identify_improvement_opportunities(self, category_baselines: Dict, intent_baselines: Dict) -> List[str]:
        """Identify improvement opportunities based on baselines."""
        opportunities = []
        
        # Check category baselines
        for category, baseline in category_baselines.items():
            if baseline.success_rate < 0.7:
                opportunities.append(f"Improve success rate for {category} searches")
            if baseline.avg_response_time > 2000:  # > 2 seconds
                opportunities.append(f"Optimize response time for {category} searches")
            if baseline.avg_score < 0.7:
                opportunities.append(f"Enhance search relevance for {category} products")
        
        # Check intent baselines
        for intent_type, baseline in intent_baselines.items():
            if baseline.cache_hit_rate < 0.5:
                opportunities.append(f"Improve caching for {intent_type} searches")
            if baseline.fallback_usage_rate > 0.3:
                opportunities.append(f"Optimize primary search for {intent_type} queries")
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    def _extract_category_from_query(self, query: str) -> Optional[str]:
        """Extract category from search query."""
        query_lower = query.lower()
        
        categories = {
            "shirts": ["shirt", "t-shirt", "blouse", "top"],
            "pants": ["pants", "jeans", "trousers", "leggings"],
            "shoes": ["shoes", "sneakers", "boots", "sandals"],
            "accessories": ["bag", "purse", "jewelry", "watch", "hat"],
            "dresses": ["dress", "gown", "frock"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _classify_search_intent(self, query: str) -> str:
        """Classify search intent from query."""
        query_lower = query.lower()
        
        # Price intent
        if any(word in query_lower for word in ["cheap", "budget", "under", "less than", "€", "euro"]):
            return "price_budget"
        if any(word in query_lower for word in ["expensive", "premium", "luxury", "over"]):
            return "price_premium"
        
        # Brand intent
        if any(word in query_lower for word in ["brand", "nike", "adidas", "zara", "h&m"]):
            return "brand_specific"
        
        # Category intent
        if any(word in query_lower for word in ["shirt", "pants", "shoes", "dress"]):
            return "category_specific"
        
        return "general"
    
    def _calculate_price_coherence(self, data: List) -> float:
        """Calculate price coherence score."""
        # Simplified calculation
        return 0.8  # Placeholder
    
    def _calculate_diversity_score(self, data: List) -> float:
        """Calculate result diversity score."""
        # Simplified calculation
        return 0.7  # Placeholder
    
    def _calculate_conversion_potential(self, data: List) -> float:
        """Calculate conversion potential score."""
        # Simplified calculation
        return 0.6  # Placeholder
    
    def _calculate_trend(self, data: List) -> str:
        """Calculate performance trend."""
        if len(data) < 10:
            return "stable"
        
        # Simplified trend calculation
        return "stable"
    
    def _calculate_price_filter_usage(self, data: List) -> float:
        """Calculate price filter usage rate."""
        # Simplified calculation
        return 0.3  # Placeholder
    
    def _calculate_fallback_usage(self, data: List) -> float:
        """Calculate fallback search usage rate."""
        # Simplified calculation
        return 0.1  # Placeholder
    
    def _calculate_cache_hit_rate(self, data: List) -> float:
        """Calculate cache hit rate."""
        cache_hits = len([row for row in data if row[9]])  # cache_hit column
        return cache_hits / len(data) if data else 0.0
    
    def _calculate_category_distribution(self, data: List) -> Dict[str, int]:
        """Calculate category distribution for intent."""
        distribution = {}
        for row in data:
            category = self._extract_category_from_query(row[1])
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def _create_empty_baseline(self, store_id: str) -> StoreBaseline:
        """Create empty baseline when no data is available."""
        return StoreBaseline(
            store_id=store_id,
            overall_baseline=0.0,
            performance_grade="F",
            improvement_opportunities=["No data available for baseline generation"],
            generated_at=datetime.now(),
            category_baselines={},
            intent_baselines={}
        )
    
    def get_latest_baseline(self, store_id: str) -> Optional[StoreBaseline]:
        """Get the latest baseline for a store."""
        # For now, generate a new baseline
        # In production, this would retrieve from cache or database
        return self.generate_store_baselines(store_id) 