#!/usr/bin/env python3
"""
Transfer Learning Engine

This module enables knowledge transfer between similar stores by:
- Analyzing store similarities
- Transferring successful patterns
- Applying best practices automatically
- Learning from successful stores
"""

import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_base_builder import KnowledgeBaseBuilder

logger = logging.getLogger(__name__)

@dataclass
class TransferablePattern:
    """Represents a transferable pattern from one store to another."""
    pattern_type: str
    pattern_data: Dict[str, Any]
    source_store_id: str
    success_rate: float
    applicability_score: float
    transfer_confidence: float
    last_updated: datetime

@dataclass
class StoreSimilarity:
    """Represents similarity between two stores."""
    store_id_1: str
    store_id_2: str
    similarity_score: float
    similarity_factors: Dict[str, float]
    confidence: float

@dataclass
class TransferRecommendation:
    """Represents a transfer recommendation for a new store."""
    pattern_type: str
    pattern_description: str
    source_stores: List[str]
    expected_improvement: float
    confidence: float
    implementation_steps: List[str]
    risk_level: str  # low, medium, high

class TransferLearningEngine:
    """Engine for transferring knowledge between similar stores."""
    
    def __init__(self, db_path: str = "search_knowledge_base.db"):
        self.db_path = db_path
        self.knowledge_builder = KnowledgeBaseBuilder(db_path)
        
        # Similarity weights for different factors
        self.similarity_weights = {
            "category_distribution": 0.3,
            "price_range": 0.25,
            "product_count": 0.15,
            "performance_metrics": 0.2,
            "query_patterns": 0.1
        }
    
    def find_similar_stores(self, target_store_id: str, limit: int = 5) -> List[StoreSimilarity]:
        """Find stores similar to the target store."""
        try:
            target_profile = self.knowledge_builder.get_store_profile(target_store_id)
            if not target_profile:
                logger.warning(f"Target store {target_store_id} not found")
                return []
            
            # Get all other store profiles
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM store_profiles WHERE store_id != ?
                """, (target_store_id,))
                
                similar_stores = []
                for row in cursor.fetchall():
                    other_profile = self._row_to_store_profile(row)
                    similarity = self._calculate_store_similarity(target_profile, other_profile)
                    
                    if similarity.similarity_score > 0.3:  # Minimum similarity threshold
                        similar_stores.append(similarity)
                
                # Sort by similarity score and return top results
                similar_stores.sort(key=lambda x: x.similarity_score, reverse=True)
                return similar_stores[:limit]
                
        except Exception as e:
            logger.error(f"Error finding similar stores: {e}")
            return []
    
    def _calculate_store_similarity(self, store1, store2) -> StoreSimilarity:
        """Calculate similarity between two stores."""
        similarity_factors = {}
        
        # Category distribution similarity
        category_sim = self._calculate_distribution_similarity(
            store1.category_distribution, store2.category_distribution
        )
        similarity_factors["category_distribution"] = category_sim
        
        # Price range similarity
        price_sim = self._calculate_price_range_similarity(
            store1.price_range, store2.price_range
        )
        similarity_factors["price_range"] = price_sim
        
        # Product count similarity
        count_sim = self._calculate_numeric_similarity(
            store1.product_count, store2.product_count
        )
        similarity_factors["product_count"] = count_sim
        
        # Performance metrics similarity
        perf_sim = self._calculate_performance_similarity(store1, store2)
        similarity_factors["performance_metrics"] = perf_sim
        
        # Query patterns similarity
        pattern_sim = self._calculate_pattern_similarity(store1, store2)
        similarity_factors["query_patterns"] = pattern_sim
        
        # Calculate weighted similarity score
        total_score = 0
        total_weight = 0
        
        for factor, weight in self.similarity_weights.items():
            if factor in similarity_factors:
                total_score += similarity_factors[factor] * weight
                total_weight += weight
        
        similarity_score = total_score / total_weight if total_weight > 0 else 0
        
        # Calculate confidence based on data quality
        confidence = self._calculate_similarity_confidence(similarity_factors)
        
        return StoreSimilarity(
            store_id_1=store1.store_id,
            store_id_2=store2.store_id,
            similarity_score=similarity_score,
            similarity_factors=similarity_factors,
            confidence=confidence
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
    
    def _calculate_price_range_similarity(self, range1: Tuple[float, float], range2: Tuple[float, float]) -> float:
        """Calculate similarity between price ranges."""
        if not range1 or not range2:
            return 0.0
        
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
    
    def _calculate_numeric_similarity(self, val1: float, val2: float) -> float:
        """Calculate similarity between numeric values."""
        if val1 == 0 and val2 == 0:
            return 1.0
        if val1 == 0 or val2 == 0:
            return 0.0
        
        ratio = min(val1, val2) / max(val1, val2)
        return ratio
    
    def _calculate_performance_similarity(self, store1, store2) -> float:
        """Calculate similarity based on performance metrics."""
        metrics1 = [
            store1.avg_relevance_score_baseline,
            store1.avg_response_time_baseline,
            store1.price_filter_usage_rate,
            store1.fallback_usage_rate
        ]
        
        metrics2 = [
            store2.avg_relevance_score_baseline,
            store2.avg_response_time_baseline,
            store2.price_filter_usage_rate,
            store2.fallback_usage_rate
        ]
        
        # Calculate average similarity across metrics
        similarities = []
        for m1, m2 in zip(metrics1, metrics2):
            if m1 is not None and m2 is not None:
                sim = self._calculate_numeric_similarity(m1, m2)
                similarities.append(sim)
        
        return statistics.mean(similarities) if similarities else 0.0
    
    def _calculate_pattern_similarity(self, store1, store2) -> float:
        """Calculate similarity based on query patterns."""
        patterns1 = set(store1.successful_query_patterns)
        patterns2 = set(store2.successful_query_patterns)
        
        if not patterns1 and not patterns2:
            return 1.0  # Both have no patterns
        if not patterns1 or not patterns2:
            return 0.0
        
        intersection = patterns1 & patterns2
        union = patterns1 | patterns2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_similarity_confidence(self, similarity_factors: Dict[str, float]) -> float:
        """Calculate confidence in similarity calculation."""
        # Higher confidence when more factors are available and have good scores
        available_factors = len([f for f in similarity_factors.values() if f > 0])
        avg_score = statistics.mean(similarity_factors.values())
        
        confidence = (available_factors / len(similarity_factors)) * avg_score
        return min(1.0, confidence)
    
    def extract_transferable_patterns(self, source_store_id: str) -> List[TransferablePattern]:
        """Extract transferable patterns from a source store."""
        try:
            source_profile = self.knowledge_builder.get_store_profile(source_store_id)
            if not source_profile:
                return []
            
            patterns = []
            
            # Extract successful query patterns
            for pattern in source_profile.successful_query_patterns:
                patterns.append(TransferablePattern(
                    pattern_type="query_pattern",
                    pattern_data={"pattern": pattern},
                    source_store_id=source_store_id,
                    success_rate=0.8,  # Default success rate
                    applicability_score=0.7,  # Default applicability
                    transfer_confidence=0.75,
                    last_updated=datetime.now()
                ))
            
            # Extract performance optimizations
            if source_profile.avg_relevance_score_baseline > 0.7:
                patterns.append(TransferablePattern(
                    pattern_type="performance_optimization",
                    pattern_data={
                        "target_score": source_profile.avg_relevance_score_baseline,
                        "response_time": source_profile.avg_response_time_baseline,
                        "cache_hit_rate": source_profile.cache_hit_rate
                    },
                    source_store_id=source_store_id,
                    success_rate=source_profile.avg_relevance_score_baseline,
                    applicability_score=0.8,
                    transfer_confidence=0.8,
                    last_updated=datetime.now()
                ))
            
            # Extract filter strategies
            if source_profile.price_filter_usage_rate > 0.5:
                patterns.append(TransferablePattern(
                    pattern_type="filter_strategy",
                    pattern_data={
                        "price_filter_usage": source_profile.price_filter_usage_rate,
                        "fallback_usage": source_profile.fallback_usage_rate
                    },
                    source_store_id=source_store_id,
                    success_rate=0.7,
                    applicability_score=0.6,
                    transfer_confidence=0.7,
                    last_updated=datetime.now()
                ))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error extracting patterns from {source_store_id}: {e}")
            return []
    
    def generate_transfer_recommendations(self, target_store_id: str) -> List[TransferRecommendation]:
        """Generate transfer recommendations for a target store."""
        similar_stores = self.find_similar_stores(target_store_id)
        
        if not similar_stores:
            return []
        
        recommendations = []
        
        # Group patterns by type
        pattern_groups = {}
        for store_sim in similar_stores:
            patterns = self.extract_transferable_patterns(store_sim.store_id_2)
            
            for pattern in patterns:
                if pattern.pattern_type not in pattern_groups:
                    pattern_groups[pattern.pattern_type] = []
                pattern_groups[pattern.pattern_type].append(pattern)
        
        # Generate recommendations for each pattern type
        for pattern_type, patterns in pattern_groups.items():
            if len(patterns) >= 2:  # Need at least 2 similar patterns
                recommendation = self._create_recommendation(pattern_type, patterns, similar_stores)
                if recommendation:
                    recommendations.append(recommendation)
        
        # Sort by expected improvement
        recommendations.sort(key=lambda x: x.expected_improvement, reverse=True)
        
        return recommendations
    
    def _create_recommendation(self, pattern_type: str, patterns: List[TransferablePattern], 
                             similar_stores: List[StoreSimilarity]) -> Optional[TransferRecommendation]:
        """Create a recommendation from patterns."""
        if not patterns:
            return None
        
        # Calculate aggregate metrics
        avg_success_rate = statistics.mean([p.success_rate for p in patterns])
        avg_confidence = statistics.mean([p.transfer_confidence for p in patterns])
        source_stores = list(set([p.source_store_id for p in patterns]))
        
        # Determine pattern description and implementation steps
        pattern_description, implementation_steps = self._get_pattern_details(pattern_type, patterns)
        
        # Calculate expected improvement
        expected_improvement = avg_success_rate * avg_confidence * 0.8  # Conservative estimate
        
        # Determine risk level
        risk_level = "low" if avg_confidence > 0.8 else "medium" if avg_confidence > 0.6 else "high"
        
        return TransferRecommendation(
            pattern_type=pattern_type,
            pattern_description=pattern_description,
            source_stores=source_stores,
            expected_improvement=expected_improvement,
            confidence=avg_confidence,
            implementation_steps=implementation_steps,
            risk_level=risk_level
        )
    
    def _get_pattern_details(self, pattern_type: str, patterns: List[TransferablePattern]) -> Tuple[str, List[str]]:
        """Get pattern description and implementation steps."""
        if pattern_type == "query_pattern":
            return (
                "Successful query patterns from similar stores",
                [
                    "Analyze successful query patterns",
                    "Implement pattern matching logic",
                    "Add pattern-based suggestions",
                    "Monitor pattern effectiveness"
                ]
            )
        elif pattern_type == "performance_optimization":
            return (
                "Performance optimization strategies",
                [
                    "Review current performance metrics",
                    "Implement caching strategies",
                    "Optimize response times",
                    "Monitor performance improvements"
                ]
            )
        elif pattern_type == "filter_strategy":
            return (
                "Effective filter usage patterns",
                [
                    "Analyze current filter usage",
                    "Implement recommended filter strategies",
                    "Optimize filter effectiveness",
                    "Track filter performance"
                ]
            )
        else:
            return (
                f"Transfer {pattern_type} patterns",
                [
                    "Analyze pattern effectiveness",
                    "Implement pattern logic",
                    "Monitor results",
                    "Adjust as needed"
                ]
            )
    
    def apply_transfer_recommendations(self, target_store_id: str, 
                                     recommendations: List[TransferRecommendation]) -> Dict[str, Any]:
        """Apply transfer recommendations to a target store."""
        results = {
            "target_store_id": target_store_id,
            "applied_recommendations": [],
            "skipped_recommendations": [],
            "expected_improvements": {},
            "implementation_status": "pending"
        }
        
        for recommendation in recommendations:
            if recommendation.confidence > 0.6:  # Only apply high-confidence recommendations
                try:
                    # Apply the recommendation
                    application_result = self._apply_recommendation(target_store_id, recommendation)
                    
                    results["applied_recommendations"].append({
                        "pattern_type": recommendation.pattern_type,
                        "description": recommendation.pattern_description,
                        "expected_improvement": recommendation.expected_improvement,
                        "confidence": recommendation.confidence,
                        "risk_level": recommendation.risk_level,
                        "application_result": application_result
                    })
                    
                    results["expected_improvements"][recommendation.pattern_type] = recommendation.expected_improvement
                    
                except Exception as e:
                    logger.error(f"Failed to apply recommendation {recommendation.pattern_type}: {e}")
                    results["skipped_recommendations"].append({
                        "pattern_type": recommendation.pattern_type,
                        "reason": str(e)
                    })
            else:
                results["skipped_recommendations"].append({
                    "pattern_type": recommendation.pattern_type,
                    "reason": "Low confidence"
                })
        
        # Update implementation status
        if results["applied_recommendations"]:
            results["implementation_status"] = "completed"
        
        return results
    
    def _apply_recommendation(self, target_store_id: str, 
                            recommendation: TransferRecommendation) -> Dict[str, Any]:
        """Apply a single recommendation to the target store."""
        # This is a simplified implementation
        # In a real implementation, you would integrate with the actual search system
        
        application_result = {
            "status": "applied",
            "timestamp": datetime.now().isoformat(),
            "implementation_notes": f"Applied {recommendation.pattern_type} from {len(recommendation.source_stores)} source stores",
            "expected_improvement": recommendation.expected_improvement
        }
        
        # Store the application in the database
        self._store_transfer_application(target_store_id, recommendation, application_result)
        
        return application_result
    
    def _store_transfer_application(self, target_store_id: str, recommendation: TransferRecommendation, 
                                  result: Dict[str, Any]):
        """Store transfer application in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transfer_applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_store_id TEXT,
                        pattern_type TEXT,
                        source_stores TEXT,
                        expected_improvement REAL,
                        confidence REAL,
                        risk_level TEXT,
                        application_result TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    INSERT INTO transfer_applications (
                        target_store_id, pattern_type, source_stores, expected_improvement,
                        confidence, risk_level, application_result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    target_store_id,
                    recommendation.pattern_type,
                    json.dumps(recommendation.source_stores),
                    recommendation.expected_improvement,
                    recommendation.confidence,
                    recommendation.risk_level,
                    json.dumps(result)
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing transfer application: {e}")
    
    def _row_to_store_profile(self, row) -> Any:
        """Convert database row to store profile object."""
        # This would need to be implemented based on the actual store profile structure
        # For now, return a simple object
        class SimpleStoreProfile:
            def __init__(self, row_data):
                self.store_id = row_data[1]
                self.product_count = row_data[2]
                self.price_range = (row_data[3], row_data[4])
                self.category_distribution = json.loads(row_data[5]) if row_data[5] else {}
                self.brand_distribution = json.loads(row_data[6]) if row_data[6] else {}
                self.material_distribution = json.loads(row_data[7]) if row_data[7] else {}
                self.color_distribution = json.loads(row_data[8]) if row_data[8] else {}
                self.avg_response_time_baseline = row_data[9]
                self.avg_relevance_score_baseline = row_data[10]
                self.price_filter_usage_rate = row_data[11]
                self.fallback_usage_rate = row_data[12]
                self.cache_hit_rate = row_data[13]
                self.successful_query_patterns = json.loads(row_data[14]) if row_data[14] else []
                self.problematic_query_patterns = json.loads(row_data[15]) if row_data[15] else []
                self.recommended_improvements = json.loads(row_data[16]) if row_data[16] else []
                self.avg_price_coherence = row_data[17]
                self.avg_diversity_score = row_data[18]
                self.avg_conversion_potential = row_data[19]
        
        return SimpleStoreProfile(row)
    
    def get_transfer_history(self, store_id: str) -> List[Dict[str, Any]]:
        """Get transfer history for a store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM transfer_applications 
                    WHERE target_store_id = ? 
                    ORDER BY applied_at DESC
                """, (store_id,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        "pattern_type": row[2],
                        "source_stores": json.loads(row[3]),
                        "expected_improvement": row[4],
                        "confidence": row[5],
                        "risk_level": row[6],
                        "application_result": json.loads(row[7]),
                        "applied_at": row[8]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting transfer history: {e}")
            return []

# Global instance
transfer_learning_engine = TransferLearningEngine() 