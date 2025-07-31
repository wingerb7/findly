#!/usr/bin/env python3
"""
Baseline Generator

This module generates category-specific baselines and performance metrics by:
- Analyzing benchmark results by query category
- Calculating baseline scores per intent type
- Generating performance benchmarks
- Providing category-specific optimization insights
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
import pandas as pd

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class CategoryBaseline:
    """Represents a baseline for a specific query category."""
    category: str
    avg_score: float
    avg_response_time: float
    avg_price_coherence: float
    avg_diversity_score: float
    avg_conversion_potential: float
    total_queries: int
    successful_queries: int
    success_rate: float
    confidence: float
    last_updated: datetime
    trend: str  # improving, declining, stable

@dataclass
class IntentBaseline:
    """Represents a baseline for a specific intent type."""
    intent_type: str
    avg_score: float
    avg_response_time: float
    price_filter_usage_rate: float
    fallback_usage_rate: float
    cache_hit_rate: float
    total_queries: int
    successful_queries: int
    success_rate: float
    confidence: float
    last_updated: datetime
    category_distribution: Dict[str, int]

@dataclass
class PerformanceBenchmark:
    """Represents a performance benchmark for a store."""
    store_id: str
    overall_baseline: float
    category_baselines: Dict[str, CategoryBaseline]
    intent_baselines: Dict[str, IntentBaseline]
    performance_grade: str  # A, B, C, D, F
    improvement_opportunities: List[str]
    generated_at: datetime

class BaselineGenerator:
    """Generator for category-specific baselines and performance metrics."""
    
    def __init__(self, db_path: str = "search_knowledge_base.db"):
        self.db_path = db_path
        
        # Query categories for baseline calculation
        self.query_categories = {
            "price_intent": ["goedkoop", "duur", "betaalbaar", "prijs", "korting", "sale"],
            "color_intent": ["zwart", "wit", "rood", "blauw", "groen", "geel", "paars", "oranje", "roze"],
            "category_intent": ["shirt", "broek", "jas", "schoenen", "tas", "accessoires", "kleding"],
            "season_intent": ["winter", "zomer", "lente", "herfst", "seizoen"],
            "occasion_intent": ["casual", "formel", "sport", "feest", "werk", "bruiloft", "feestje"],
            "material_intent": ["katoen", "linnen", "wol", "leer", "denim", "zijde", "polyester"],
            "brand_intent": ["nike", "adidas", "zara", "h&m", "levi's", "calvin klein"],
            "size_intent": ["klein", "medium", "groot", "xs", "s", "m", "l", "xl", "xxl"]
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            "excellent": 0.85,
            "good": 0.75,
            "average": 0.65,
            "poor": 0.55,
            "failing": 0.45
        }
    
    def generate_store_baselines(self, store_id: str, days_back: int = 30) -> PerformanceBenchmark:
        """Generate comprehensive baselines for a store."""
        try:
            # Get benchmark data for the store
            benchmark_data = self._get_benchmark_data(store_id, days_back)
            
            if not benchmark_data:
                logger.warning(f"No benchmark data found for store {store_id}")
                return None
            
            # Generate category baselines
            category_baselines = self._generate_category_baselines(benchmark_data)
            
            # Generate intent baselines
            intent_baselines = self._generate_intent_baselines(benchmark_data)
            
            # Calculate overall baseline
            overall_baseline = self._calculate_overall_baseline(category_baselines)
            
            # Determine performance grade
            performance_grade = self._calculate_performance_grade(overall_baseline)
            
            # Identify improvement opportunities
            improvement_opportunities = self._identify_improvement_opportunities(
                category_baselines, intent_baselines
            )
            
            benchmark = PerformanceBenchmark(
                store_id=store_id,
                overall_baseline=overall_baseline,
                category_baselines=category_baselines,
                intent_baselines=intent_baselines,
                performance_grade=performance_grade,
                improvement_opportunities=improvement_opportunities,
                generated_at=datetime.now()
            )
            
            # Store the benchmark
            self._store_performance_benchmark(benchmark)
            
            return benchmark
            
        except Exception as e:
            logger.error(f"Error generating baselines for store {store_id}: {e}")
            return None
    
    def _get_benchmark_data(self, store_id: str, days_back: int) -> List[Dict[str, Any]]:
        """Get benchmark data for a store from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get benchmark history for the store
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                cursor = conn.execute("""
                    SELECT * FROM benchmark_history 
                    WHERE store_id = ? AND benchmark_date >= ?
                    ORDER BY benchmark_date DESC
                """, (store_id, cutoff_date.isoformat()))
                
                data = []
                for row in cursor.fetchall():
                    data.append({
                        "query": row[2],
                        "score": row[3],
                        "response_time": row[4],
                        "result_count": row[5],
                        "price_coherence": row[6],
                        "diversity_score": row[7],
                        "conversion_potential": row[8],
                        "category": row[9],
                        "intent_type": row[10],
                        "cache_hit": row[11],
                        "embedding_generation_time": row[12],
                        "benchmark_date": row[13]
                    })
                
                return data
                
        except Exception as e:
            logger.error(f"Error getting benchmark data: {e}")
            return []
    
    def _generate_category_baselines(self, benchmark_data: List[Dict[str, Any]]) -> Dict[str, CategoryBaseline]:
        """Generate baselines for each query category."""
        category_baselines = {}
        
        # Group data by category
        category_groups = {}
        for data_point in benchmark_data:
            category = data_point.get("category", "unknown")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(data_point)
        
        # Calculate baselines for each category
        for category, data_points in category_groups.items():
            if len(data_points) < 3:  # Need at least 3 data points for meaningful baseline
                continue
            
            baseline = self._calculate_category_baseline(category, data_points)
            if baseline:
                category_baselines[category] = baseline
        
        return category_baselines
    
    def _calculate_category_baseline(self, category: str, data_points: List[Dict[str, Any]]) -> Optional[CategoryBaseline]:
        """Calculate baseline for a specific category."""
        try:
            scores = [dp["score"] for dp in data_points if dp["score"] is not None]
            response_times = [dp["response_time"] for dp in data_points if dp["response_time"] is not None]
            price_coherences = [dp["price_coherence"] for dp in data_points if dp["price_coherence"] is not None]
            diversity_scores = [dp["diversity_score"] for dp in data_points if dp["diversity_score"] is not None]
            conversion_potentials = [dp["conversion_potential"] for dp in data_points if dp["conversion_potential"] is not None]
            
            if not scores:
                return None
            
            # Calculate averages
            avg_score = statistics.mean(scores)
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            avg_price_coherence = statistics.mean(price_coherences) if price_coherences else 0.0
            avg_diversity_score = statistics.mean(diversity_scores) if diversity_scores else 0.0
            avg_conversion_potential = statistics.mean(conversion_potentials) if conversion_potentials else 0.0
            
            # Calculate success rate
            successful_queries = len([s for s in scores if s >= 0.7])
            success_rate = successful_queries / len(scores)
            
            # Calculate confidence based on data quality
            confidence = min(1.0, len(scores) / 20)  # Higher confidence with more data points
            
            # Determine trend (simplified - would need historical data for real trend analysis)
            trend = "stable"  # Placeholder
            
            return CategoryBaseline(
                category=category,
                avg_score=avg_score,
                avg_response_time=avg_response_time,
                avg_price_coherence=avg_price_coherence,
                avg_diversity_score=avg_diversity_score,
                avg_conversion_potential=avg_conversion_potential,
                total_queries=len(data_points),
                successful_queries=successful_queries,
                success_rate=success_rate,
                confidence=confidence,
                last_updated=datetime.now(),
                trend=trend
            )
            
        except Exception as e:
            logger.error(f"Error calculating baseline for category {category}: {e}")
            return None
    
    def _generate_intent_baselines(self, benchmark_data: List[Dict[str, Any]]) -> Dict[str, IntentBaseline]:
        """Generate baselines for each intent type."""
        intent_baselines = {}
        
        # Group data by intent type
        intent_groups = {}
        for data_point in benchmark_data:
            intent_type = data_point.get("intent_type", "unknown")
            if intent_type not in intent_groups:
                intent_groups[intent_type] = []
            intent_groups[intent_type].append(data_point)
        
        # Calculate baselines for each intent type
        for intent_type, data_points in intent_groups.items():
            if len(data_points) < 3:  # Need at least 3 data points
                continue
            
            baseline = self._calculate_intent_baseline(intent_type, data_points)
            if baseline:
                intent_baselines[intent_type] = baseline
        
        return intent_baselines
    
    def _calculate_intent_baseline(self, intent_type: str, data_points: List[Dict[str, Any]]) -> Optional[IntentBaseline]:
        """Calculate baseline for a specific intent type."""
        try:
            scores = [dp["score"] for dp in data_points if dp["score"] is not None]
            response_times = [dp["response_time"] for dp in data_points if dp["response_time"] is not None]
            cache_hits = [dp["cache_hit"] for dp in data_points if dp["cache_hit"] is not None]
            
            if not scores:
                return None
            
            # Calculate averages
            avg_score = statistics.mean(scores)
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            
            # Calculate cache hit rate
            cache_hit_rate = statistics.mean(cache_hits) if cache_hits else 0.0
            
            # Calculate success rate
            successful_queries = len([s for s in scores if s >= 0.7])
            success_rate = successful_queries / len(scores)
            
            # Calculate confidence
            confidence = min(1.0, len(scores) / 20)
            
            # Calculate category distribution for this intent
            category_distribution = {}
            for dp in data_points:
                category = dp.get("category", "unknown")
                category_distribution[category] = category_distribution.get(category, 0) + 1
            
            # Placeholder values for filter usage rates (would need actual data)
            price_filter_usage_rate = 0.3  # Placeholder
            fallback_usage_rate = 0.1  # Placeholder
            
            return IntentBaseline(
                intent_type=intent_type,
                avg_score=avg_score,
                avg_response_time=avg_response_time,
                price_filter_usage_rate=price_filter_usage_rate,
                fallback_usage_rate=fallback_usage_rate,
                cache_hit_rate=cache_hit_rate,
                total_queries=len(data_points),
                successful_queries=successful_queries,
                success_rate=success_rate,
                confidence=confidence,
                last_updated=datetime.now(),
                category_distribution=category_distribution
            )
            
        except Exception as e:
            logger.error(f"Error calculating baseline for intent {intent_type}: {e}")
            return None
    
    def _calculate_overall_baseline(self, category_baselines: Dict[str, CategoryBaseline]) -> float:
        """Calculate overall baseline from category baselines."""
        if not category_baselines:
            return 0.0
        
        # Weighted average based on number of queries per category
        total_queries = sum(baseline.total_queries for baseline in category_baselines.values())
        
        if total_queries == 0:
            return 0.0
        
        weighted_sum = 0
        for baseline in category_baselines.values():
            weight = baseline.total_queries / total_queries
            weighted_sum += baseline.avg_score * weight
        
        return weighted_sum
    
    def _calculate_performance_grade(self, overall_baseline: float) -> str:
        """Calculate performance grade based on overall baseline."""
        if overall_baseline >= self.performance_thresholds["excellent"]:
            return "A"
        elif overall_baseline >= self.performance_thresholds["good"]:
            return "B"
        elif overall_baseline >= self.performance_thresholds["average"]:
            return "C"
        elif overall_baseline >= self.performance_thresholds["poor"]:
            return "D"
        else:
            return "F"
    
    def _identify_improvement_opportunities(self, category_baselines: Dict[str, CategoryBaseline], 
                                         intent_baselines: Dict[str, IntentBaseline]) -> List[str]:
        """Identify improvement opportunities based on baselines."""
        opportunities = []
        
        # Check for low-performing categories
        for category, baseline in category_baselines.items():
            if baseline.avg_score < 0.6:
                opportunities.append(f"Improve {category} search performance (current: {baseline.avg_score:.2f})")
            
            if baseline.success_rate < 0.5:
                opportunities.append(f"Increase success rate for {category} queries (current: {baseline.success_rate:.2f})")
        
        # Check for low-performing intent types
        for intent_type, baseline in intent_baselines.items():
            if baseline.avg_score < 0.6:
                opportunities.append(f"Optimize {intent_type} intent handling (current: {baseline.avg_score:.2f})")
            
            if baseline.cache_hit_rate < 0.3:
                opportunities.append(f"Improve caching for {intent_type} queries (current: {baseline.cache_hit_rate:.2f})")
        
        # Check for response time issues
        slow_categories = [cat for cat, baseline in category_baselines.items() 
                          if baseline.avg_response_time > 2.0]
        if slow_categories:
            opportunities.append(f"Optimize response times for: {', '.join(slow_categories)}")
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    def _store_performance_benchmark(self, benchmark: PerformanceBenchmark):
        """Store performance benchmark in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_baselines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id TEXT,
                        overall_baseline REAL,
                        category_baselines TEXT,
                        intent_baselines TEXT,
                        performance_grade TEXT,
                        improvement_opportunities TEXT,
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    INSERT INTO performance_baselines (
                        store_id, overall_baseline, category_baselines, intent_baselines,
                        performance_grade, improvement_opportunities
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    benchmark.store_id,
                    benchmark.overall_baseline,
                    json.dumps(self._serialize_category_baselines(benchmark.category_baselines)),
                    json.dumps(self._serialize_intent_baselines(benchmark.intent_baselines)),
                    benchmark.performance_grade,
                    json.dumps(benchmark.improvement_opportunities)
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing performance benchmark: {e}")
    
    def _serialize_category_baselines(self, category_baselines: Dict[str, CategoryBaseline]) -> Dict[str, Dict]:
        """Serialize category baselines for database storage."""
        serialized = {}
        for category, baseline in category_baselines.items():
            serialized[category] = {
                "avg_score": baseline.avg_score,
                "avg_response_time": baseline.avg_response_time,
                "avg_price_coherence": baseline.avg_price_coherence,
                "avg_diversity_score": baseline.avg_diversity_score,
                "avg_conversion_potential": baseline.avg_conversion_potential,
                "total_queries": baseline.total_queries,
                "successful_queries": baseline.successful_queries,
                "success_rate": baseline.success_rate,
                "confidence": baseline.confidence,
                "trend": baseline.trend
            }
        return serialized
    
    def _serialize_intent_baselines(self, intent_baselines: Dict[str, IntentBaseline]) -> Dict[str, Dict]:
        """Serialize intent baselines for database storage."""
        serialized = {}
        for intent_type, baseline in intent_baselines.items():
            serialized[intent_type] = {
                "avg_score": baseline.avg_score,
                "avg_response_time": baseline.avg_response_time,
                "price_filter_usage_rate": baseline.price_filter_usage_rate,
                "fallback_usage_rate": baseline.fallback_usage_rate,
                "cache_hit_rate": baseline.cache_hit_rate,
                "total_queries": baseline.total_queries,
                "successful_queries": baseline.successful_queries,
                "success_rate": baseline.success_rate,
                "confidence": baseline.confidence,
                "category_distribution": baseline.category_distribution
            }
        return serialized
    
    def get_latest_baseline(self, store_id: str) -> Optional[PerformanceBenchmark]:
        """Get the latest performance benchmark for a store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM performance_baselines 
                    WHERE store_id = ? 
                    ORDER BY generated_at DESC 
                    LIMIT 1
                """, (store_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._deserialize_performance_benchmark(row)
                
        except Exception as e:
            logger.error(f"Error getting latest baseline: {e}")
            return None
    
    def _deserialize_performance_benchmark(self, row) -> PerformanceBenchmark:
        """Deserialize performance benchmark from database row."""
        category_baselines = {}
        intent_baselines = {}
        
        # Deserialize category baselines
        if row[3]:  # category_baselines
            cat_data = json.loads(row[3])
            for category, data in cat_data.items():
                category_baselines[category] = CategoryBaseline(
                    category=category,
                    avg_score=data["avg_score"],
                    avg_response_time=data["avg_response_time"],
                    avg_price_coherence=data["avg_price_coherence"],
                    avg_diversity_score=data["avg_diversity_score"],
                    avg_conversion_potential=data["avg_conversion_potential"],
                    total_queries=data["total_queries"],
                    successful_queries=data["successful_queries"],
                    success_rate=data["success_rate"],
                    confidence=data["confidence"],
                    last_updated=datetime.now(),
                    trend=data["trend"]
                )
        
        # Deserialize intent baselines
        if row[4]:  # intent_baselines
            intent_data = json.loads(row[4])
            for intent_type, data in intent_data.items():
                intent_baselines[intent_type] = IntentBaseline(
                    intent_type=intent_type,
                    avg_score=data["avg_score"],
                    avg_response_time=data["avg_response_time"],
                    price_filter_usage_rate=data["price_filter_usage_rate"],
                    fallback_usage_rate=data["fallback_usage_rate"],
                    cache_hit_rate=data["cache_hit_rate"],
                    total_queries=data["total_queries"],
                    successful_queries=data["successful_queries"],
                    success_rate=data["success_rate"],
                    confidence=data["confidence"],
                    last_updated=datetime.now(),
                    category_distribution=data["category_distribution"]
                )
        
        return PerformanceBenchmark(
            store_id=row[1],
            overall_baseline=row[2],
            category_baselines=category_baselines,
            intent_baselines=intent_baselines,
            performance_grade=row[5],
            improvement_opportunities=json.loads(row[6]) if row[6] else [],
            generated_at=datetime.fromisoformat(row[7])
        )
    
    def export_baselines_to_json(self, store_id: str, output_path: str = None) -> str:
        """Export baselines to JSON file."""
        baseline = self.get_latest_baseline(store_id)
        if not baseline:
            return None
        
        if not output_path:
            output_path = f"baselines_{store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "store_id": baseline.store_id,
            "overall_baseline": baseline.overall_baseline,
            "performance_grade": baseline.performance_grade,
            "generated_at": baseline.generated_at.isoformat(),
            "category_baselines": self._serialize_category_baselines(baseline.category_baselines),
            "intent_baselines": self._serialize_intent_baselines(baseline.intent_baselines),
            "improvement_opportunities": baseline.improvement_opportunities
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_path

# Global instance
baseline_generator = BaselineGenerator() 