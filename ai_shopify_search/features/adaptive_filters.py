#!/usr/bin/env python3
"""
Adaptive Filters Module

This module automatically applies fallback filters when search results are poor.
It analyzes search performance and dynamically adjusts filters to improve results.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import json

logger = logging.getLogger(__name__)

@dataclass
class FilterStrategy:
    """Represents a filter strategy with conditions and actions."""
    name: str
    trigger_conditions: Dict[str, Any]  # When to apply this strategy
    filter_actions: Dict[str, Any]      # What filters to apply
    priority: int                       # Higher priority = applied first
    success_rate: float                 # Historical success rate
    usage_count: int                    # How often used

@dataclass
class AdaptiveFilterResult:
    """Result of adaptive filtering."""
    original_results: List[Dict[str, Any]]
    improved_results: List[Dict[str, Any]]
    applied_strategies: List[str]
    improvement_score: float
    filters_applied: Dict[str, Any]
    reasoning: str

class AdaptiveFilterEngine:
    """Engine for automatically applying adaptive filters to improve search results."""
    
    def __init__(self):
        self.filter_strategies = self._initialize_strategies()
        self.min_improvement_threshold = 0.1  # 10% improvement required
        self.max_strategies_per_query = 3     # Max strategies to try
    
    def _initialize_strategies(self) -> List[FilterStrategy]:
        """Initialize predefined filter strategies."""
        strategies = [
            # Price-based strategies
            FilterStrategy(
                name="price_broaden_low",
                trigger_conditions={
                    "avg_price_top5": {"min": 0, "max": 50},
                    "result_count": {"min": 0, "max": 5},
                    "score": {"min": 0, "max": 0.6}
                },
                filter_actions={
                    "price_range": {"min": 0, "max": 100},
                    "broaden_search": True
                },
                priority=1,
                success_rate=0.8,
                usage_count=0
            ),
            
            FilterStrategy(
                name="price_broaden_high",
                trigger_conditions={
                    "avg_price_top5": {"min": 200, "max": 1000},
                    "result_count": {"min": 0, "max": 5},
                    "score": {"min": 0, "max": 0.6}
                },
                filter_actions={
                    "price_range": {"min": 150, "max": 500},
                    "broaden_search": True
                },
                priority=1,
                success_rate=0.75,
                usage_count=0
            ),
            
            # Category-based strategies
            FilterStrategy(
                name="category_broaden",
                trigger_conditions={
                    "category_coverage": {"min": 0, "max": 0.3},
                    "result_count": {"min": 0, "max": 8},
                    "score": {"min": 0, "max": 0.7}
                },
                filter_actions={
                    "category_expansion": True,
                    "include_related_categories": True
                },
                priority=2,
                success_rate=0.7,
                usage_count=0
            ),
            
            # Diversity-based strategies
            FilterStrategy(
                name="diversity_improve",
                trigger_conditions={
                    "diversity_score": {"min": 0, "max": 0.4},
                    "result_count": {"min": 5, "max": 25},
                    "score": {"min": 0, "max": 0.8}
                },
                filter_actions={
                    "force_diversity": True,
                    "max_similar_results": 3
                },
                priority=3,
                success_rate=0.65,
                usage_count=0
            ),
            
            # Material-based strategies
            FilterStrategy(
                name="material_fallback",
                trigger_conditions={
                    "material_intent_detected": True,
                    "result_count": {"min": 0, "max": 3},
                    "score": {"min": 0, "max": 0.5}
                },
                filter_actions={
                    "material_fallback": True,
                    "include_similar_materials": True
                },
                priority=2,
                success_rate=0.7,
                usage_count=0
            ),
            
            # Color-based strategies
            FilterStrategy(
                name="color_fallback",
                trigger_conditions={
                    "color_intent_detected": True,
                    "result_count": {"min": 0, "max": 3},
                    "score": {"min": 0, "max": 0.5}
                },
                filter_actions={
                    "color_fallback": True,
                    "include_neutral_colors": True
                },
                priority=2,
                success_rate=0.7,
                usage_count=0
            ),
            
            # Emergency fallback strategy
            FilterStrategy(
                name="emergency_fallback",
                trigger_conditions={
                    "result_count": {"min": 0, "max": 2},
                    "score": {"min": 0, "max": 0.3}
                },
                filter_actions={
                    "remove_all_filters": True,
                    "broaden_search": True,
                    "include_all_categories": True
                },
                priority=0,  # Highest priority
                success_rate=0.9,
                usage_count=0
            )
        ]
        
        return strategies
    
    def analyze_search_performance(self, results: List[Dict[str, Any]], 
                                 query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze search performance to determine if adaptive filtering is needed."""
        if not results:
            return {
                "needs_improvement": True,
                "issues": ["no_results"],
                "metrics": {}
            }
        
        # Calculate performance metrics
        scores = [r.get('similarity', 0) for r in results]
        prices = [r.get('price', 0) for r in results if r.get('price')]
        
        metrics = {
            "avg_score": statistics.mean(scores) if scores else 0,
            "result_count": len(results),
            "avg_price_top5": statistics.mean(prices[:5]) if prices else 0,
            "price_range": max(prices) - min(prices) if len(prices) > 1 else 0,
            "category_coverage": self._calculate_category_coverage(results),
            "diversity_score": self._calculate_diversity_score(results),
            "material_intent_detected": "material_intent" in query_analysis.get("detected_intents", {}),
            "color_intent_detected": "color_intent" in query_analysis.get("detected_intents", {})
        }
        
        # Identify issues
        issues = []
        if metrics["avg_score"] < 0.6:
            issues.append("low_relevance")
        if metrics["result_count"] < 5:
            issues.append("insufficient_results")
        if metrics["category_coverage"] < 0.3:
            issues.append("low_category_coverage")
        if metrics["diversity_score"] < 0.4:
            issues.append("low_diversity")
        
        needs_improvement = len(issues) > 0
        
        return {
            "needs_improvement": needs_improvement,
            "issues": issues,
            "metrics": metrics
        }
    
    def select_adaptive_strategies(self, performance_analysis: Dict[str, Any]) -> List[FilterStrategy]:
        """Select appropriate filter strategies based on performance analysis."""
        if not performance_analysis["needs_improvement"]:
            return []
        
        applicable_strategies = []
        metrics = performance_analysis["metrics"]
        issues = performance_analysis["issues"]
        
        for strategy in self.filter_strategies:
            if self._strategy_applies(strategy, metrics, issues):
                applicable_strategies.append(strategy)
        
        # Sort by priority (lower number = higher priority) and success rate
        applicable_strategies.sort(key=lambda s: (s.priority, -s.success_rate))
        
        # Limit to max strategies per query
        return applicable_strategies[:self.max_strategies_per_query]
    
    def _strategy_applies(self, strategy: FilterStrategy, metrics: Dict[str, Any], 
                         issues: List[str]) -> bool:
        """Check if a strategy applies to the current situation."""
        conditions = strategy.trigger_conditions
        
        for condition_key, condition_value in conditions.items():
            if condition_key in metrics:
                metric_value = metrics[condition_key]
                
                if isinstance(condition_value, dict):
                    # Range condition
                    if "min" in condition_value and metric_value < condition_value["min"]:
                        return False
                    if "max" in condition_value and metric_value > condition_value["max"]:
                        return False
                elif isinstance(condition_value, bool):
                    # Boolean condition
                    if metric_value != condition_value:
                        return False
                else:
                    # Exact match condition
                    if metric_value != condition_value:
                        return False
        
        return True
    
    def apply_adaptive_filters(self, original_results: List[Dict[str, Any]], 
                             query_analysis: Dict[str, Any],
                             search_service) -> AdaptiveFilterResult:
        """Apply adaptive filters to improve search results."""
        # Analyze current performance
        performance_analysis = self.analyze_search_performance(original_results, query_analysis)
        
        if not performance_analysis["needs_improvement"]:
            return AdaptiveFilterResult(
                original_results=original_results,
                improved_results=original_results,
                applied_strategies=[],
                improvement_score=0.0,
                filters_applied={},
                reasoning="No improvement needed"
            )
        
        # Select strategies
        strategies = self.select_adaptive_strategies(performance_analysis)
        
        if not strategies:
            return AdaptiveFilterResult(
                original_results=original_results,
                improved_results=original_results,
                applied_strategies=[],
                improvement_score=0.0,
                filters_applied={},
                reasoning="No applicable strategies found"
            )
        
        # Apply strategies
        improved_results = original_results.copy()
        applied_strategies = []
        filters_applied = {}
        
        for strategy in strategies:
            try:
                # Apply the strategy
                strategy_result = self._apply_strategy(strategy, improved_results, search_service)
                
                if strategy_result:
                    improved_results = strategy_result
                    applied_strategies.append(strategy.name)
                    filters_applied.update(strategy.filter_actions)
                    
                    # Update strategy usage
                    strategy.usage_count += 1
                    
                    logger.info(f"Applied adaptive filter strategy: {strategy.name}")
                
            except Exception as e:
                logger.warning(f"Failed to apply strategy {strategy.name}: {e}")
                continue
        
        # Calculate improvement
        improvement_score = self._calculate_improvement_score(original_results, improved_results)
        
        # Only return improved results if there's significant improvement
        if improvement_score < self.min_improvement_threshold:
            return AdaptiveFilterResult(
                original_results=original_results,
                improved_results=original_results,
                applied_strategies=[],
                improvement_score=0.0,
                filters_applied={},
                reasoning=f"Improvement too small ({improvement_score:.3f} < {self.min_improvement_threshold})"
            )
        
        reasoning = f"Applied {len(applied_strategies)} strategies: {', '.join(applied_strategies)}"
        
        return AdaptiveFilterResult(
            original_results=original_results,
            improved_results=improved_results,
            applied_strategies=applied_strategies,
            improvement_score=improvement_score,
            filters_applied=filters_applied,
            reasoning=reasoning
        )
    
    def _apply_strategy(self, strategy: FilterStrategy, current_results: List[Dict[str, Any]], 
                       search_service) -> Optional[List[Dict[str, Any]]]:
        """Apply a specific filter strategy."""
        actions = strategy.filter_actions
        
        # This is a simplified implementation
        # In a real implementation, you would integrate with the actual search service
        
        if "remove_all_filters" in actions and actions["remove_all_filters"]:
            # Remove all filters and broaden search
            return self._broaden_search(current_results, search_service)
        
        elif "price_range" in actions:
            # Apply price range filter
            price_range = actions["price_range"]
            return self._apply_price_filter(current_results, price_range)
        
        elif "category_expansion" in actions and actions["category_expansion"]:
            # Expand category search
            return self._expand_categories(current_results, search_service)
        
        elif "force_diversity" in actions and actions["force_diversity"]:
            # Force diversity in results
            return self._force_diversity(current_results, actions.get("max_similar_results", 3))
        
        elif "material_fallback" in actions and actions["material_fallback"]:
            # Apply material fallback
            return self._apply_material_fallback(current_results)
        
        elif "color_fallback" in actions and actions["color_fallback"]:
            # Apply color fallback
            return self._apply_color_fallback(current_results)
        
        return None
    
    def _broaden_search(self, results: List[Dict[str, Any]], search_service) -> List[Dict[str, Any]]:
        """Broaden the search to get more results."""
        # This would integrate with the actual search service
        # For now, return the original results
        return results
    
    def _apply_price_filter(self, results: List[Dict[str, Any]], 
                           price_range: Dict[str, float]) -> List[Dict[str, Any]]:
        """Apply price range filter."""
        min_price = price_range.get("min", 0)
        max_price = price_range.get("max", float('inf'))
        
        filtered_results = []
        for result in results:
            price = result.get("price", 0)
            if min_price <= price <= max_price:
                filtered_results.append(result)
        
        return filtered_results
    
    def _expand_categories(self, results: List[Dict[str, Any]], search_service) -> List[Dict[str, Any]]:
        """Expand category search."""
        # This would integrate with the actual search service
        return results
    
    def _force_diversity(self, results: List[Dict[str, Any]], max_similar: int) -> List[Dict[str, Any]]:
        """Force diversity by limiting similar results."""
        if len(results) <= max_similar:
            return results
        
        # Simple diversity implementation - take every nth result
        step = len(results) // max_similar
        diverse_results = []
        
        for i in range(0, len(results), step):
            if len(diverse_results) < max_similar:
                diverse_results.append(results[i])
        
        return diverse_results
    
    def _apply_material_fallback(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply material fallback strategy."""
        # This would look for similar materials or remove material constraints
        return results
    
    def _apply_color_fallback(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply color fallback strategy."""
        # This would look for similar colors or include neutral colors
        return results
    
    def _calculate_category_coverage(self, results: List[Dict[str, Any]]) -> float:
        """Calculate category coverage score."""
        if not results:
            return 0.0
        
        categories = set()
        for result in results:
            tags = result.get("tags", [])
            for tag in tags:
                if any(cat in tag.lower() for cat in ["schoenen", "jas", "shirt", "broek", "jurk"]):
                    categories.add(tag)
        
        return len(categories) / len(results)
    
    def _calculate_diversity_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate diversity score."""
        if len(results) < 2:
            return 0.0
        
        # Calculate diversity based on different attributes
        categories = set()
        brands = set()
        colors = set()
        
        for result in results:
            tags = result.get("tags", [])
            for tag in tags:
                if any(cat in tag.lower() for cat in ["schoenen", "jas", "shirt", "broek", "jurk"]):
                    categories.add(tag)
                elif any(brand in tag.lower() for brand in ["urbanwear", "fashionista", "stylehub"]):
                    brands.add(tag)
                elif any(color in tag.lower() for color in ["zwart", "rood", "blauw", "wit", "groen"]):
                    colors.add(tag)
        
        diversity_factors = [
            len(categories) / len(results),
            len(brands) / len(results),
            len(colors) / len(results)
        ]
        
        return statistics.mean(diversity_factors)
    
    def _calculate_improvement_score(self, original_results: List[Dict[str, Any]], 
                                   improved_results: List[Dict[str, Any]]) -> float:
        """Calculate improvement score between original and improved results."""
        if not original_results or not improved_results:
            return 0.0
        
        # Calculate metrics for both result sets
        original_metrics = self._calculate_result_metrics(original_results)
        improved_metrics = self._calculate_result_metrics(improved_results)
        
        # Calculate improvement for each metric
        improvements = []
        
        if original_metrics["avg_score"] > 0:
            score_improvement = (improved_metrics["avg_score"] - original_metrics["avg_score"]) / original_metrics["avg_score"]
            improvements.append(max(0, score_improvement))
        
        if original_metrics["result_count"] > 0:
            count_improvement = (improved_metrics["result_count"] - original_metrics["result_count"]) / original_metrics["result_count"]
            improvements.append(max(0, count_improvement))
        
        if original_metrics["diversity_score"] > 0:
            diversity_improvement = (improved_metrics["diversity_score"] - original_metrics["diversity_score"]) / original_metrics["diversity_score"]
            improvements.append(max(0, diversity_improvement))
        
        return statistics.mean(improvements) if improvements else 0.0
    
    def _calculate_result_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate metrics for a result set."""
        if not results:
            return {
                "avg_score": 0.0,
                "result_count": 0,
                "diversity_score": 0.0
            }
        
        scores = [r.get("similarity", 0) for r in results]
        
        return {
            "avg_score": statistics.mean(scores) if scores else 0.0,
            "result_count": len(results),
            "diversity_score": self._calculate_diversity_score(results)
        }
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get statistics about strategy usage and success rates."""
        stats = {
            "total_strategies": len(self.filter_strategies),
            "total_usage": sum(s.usage_count for s in self.filter_strategies),
            "strategies": []
        }
        
        for strategy in self.filter_strategies:
            stats["strategies"].append({
                "name": strategy.name,
                "usage_count": strategy.usage_count,
                "success_rate": strategy.success_rate,
                "priority": strategy.priority
            })
        
        return stats

# Global instance
adaptive_filter_engine = AdaptiveFilterEngine() 