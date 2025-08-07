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

# Constants
DEFAULT_MIN_IMPROVEMENT_THRESHOLD = 0.1  # 10% improvement required
DEFAULT_MAX_STRATEGIES_PER_QUERY = 3     # Max strategies to try
DEFAULT_SUCCESS_RATE = 0.8
DEFAULT_PRIORITY = 1

# Price thresholds
PRICE_THRESHOLDS = {
    "LOW": 50,
    "MEDIUM": 200,
    "HIGH": 1000
}

# Score thresholds
SCORE_THRESHOLDS = {
    "POOR": 0.6,
    "FAIR": 0.7,
    "GOOD": 0.8
}

# Result count thresholds
RESULT_COUNT_THRESHOLDS = {
    "LOW": 5,
    "MEDIUM": 8,
    "HIGH": 15
}

# Category coverage thresholds
CATEGORY_COVERAGE_THRESHOLDS = {
    "LOW": 0.3,
    "MEDIUM": 0.5,
    "HIGH": 0.7
}

# Error Messages
ERROR_ADAPTIVE_FILTERS = "Error getting adaptive filters: {error}"
ERROR_NO_STRATEGIES = "No adaptive filters needed"

# Logging Context Keys
LOG_CONTEXT_QUERY = "query"
LOG_CONTEXT_STRATEGY = "strategy"
LOG_CONTEXT_IMPROVEMENT_SCORE = "improvement_score"

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
        """
        Initialize adaptive filter engine.
        
        Sets up filter strategies and configuration parameters.
        """
        self.filter_strategies = self._initialize_strategies()
        self.min_improvement_threshold = DEFAULT_MIN_IMPROVEMENT_THRESHOLD
        self.max_strategies_per_query = DEFAULT_MAX_STRATEGIES_PER_QUERY
    
    def _create_price_strategies(self) -> List[FilterStrategy]:
        """
        Create price-based filter strategies.
        
        Returns:
            List of price-based strategies
        """
        return [
            FilterStrategy(
                name="price_broaden_low",
                trigger_conditions={
                    "avg_price_top5": {"min": 0, "max": PRICE_THRESHOLDS["LOW"]},
                    "result_count": {"min": 0, "max": RESULT_COUNT_THRESHOLDS["LOW"]},
                    "score": {"min": 0, "max": SCORE_THRESHOLDS["POOR"]}
                },
                filter_actions={
                    "price_range": {"min": 0, "max": 100},
                    "broaden_search": True
                },
                priority=DEFAULT_PRIORITY,
                success_rate=DEFAULT_SUCCESS_RATE,
                usage_count=0
            ),
            
            FilterStrategy(
                name="price_broaden_high",
                trigger_conditions={
                    "avg_price_top5": {"min": PRICE_THRESHOLDS["MEDIUM"], "max": PRICE_THRESHOLDS["HIGH"]},
                    "result_count": {"min": 0, "max": RESULT_COUNT_THRESHOLDS["LOW"]},
                    "score": {"min": 0, "max": SCORE_THRESHOLDS["POOR"]}
                },
                filter_actions={
                    "price_range": {"min": 150, "max": 500},
                    "broaden_search": True
                },
                priority=DEFAULT_PRIORITY,
                success_rate=0.75,
                usage_count=0
            )
        ]
    
    def _create_category_strategies(self) -> List[FilterStrategy]:
        """
        Create category-based filter strategies.
        
        Returns:
            List of category-based strategies
        """
        return [
            FilterStrategy(
                name="category_broaden",
                trigger_conditions={
                    "category_coverage": {"min": 0, "max": CATEGORY_COVERAGE_THRESHOLDS["LOW"]},
                    "result_count": {"min": 0, "max": RESULT_COUNT_THRESHOLDS["MEDIUM"]},
                    "score": {"min": 0, "max": SCORE_THRESHOLDS["FAIR"]}
                },
                filter_actions={
                    "category_expansion": True,
                    "include_related_categories": True
                },
                priority=2,
                success_rate=0.7,
                usage_count=0
            )
        ]
    
    def _create_diversity_strategies(self) -> List[FilterStrategy]:
        """
        Create diversity-based filter strategies.
        
        Returns:
            List of diversity-based strategies
        """
        return [
            FilterStrategy(
                name="diversity_improve",
                trigger_conditions={
                    "diversity_score": {"min": 0, "max": 0.4},
                    "result_count": {"min": 5, "max": 20},
                    "score": {"min": 0, "max": SCORE_THRESHOLDS["FAIR"]}
                },
                filter_actions={
                    "force_diversity": True,
                    "max_similar_items": 3
                },
                priority=3,
                success_rate=0.65,
                usage_count=0
            )
        ]
    
    def _initialize_strategies(self) -> List[FilterStrategy]:
        """
        Initialize predefined filter strategies.
        
        Returns:
            List of filter strategies
        """
        strategies = []
        
        # Add price-based strategies
        strategies.extend(self._create_price_strategies())
        
        # Add category-based strategies
        strategies.extend(self._create_category_strategies())
        
        # Add diversity-based strategies
        strategies.extend(self._create_diversity_strategies())
        
        return strategies
    
    def analyze_search_performance(self, results: List[Dict[str, Any]], 
                                 query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze search performance to determine if adaptive filtering is needed.
        
        Args:
            results: Search results
            query_analysis: Query analysis data
            
        Returns:
            Dictionary with performance analysis
        """
        if not results:
            return {
                "needs_improvement": True,
                "issues": ["no_results"],
                "metrics": {}
            }
        
        # Calculate performance metrics using helper
        metrics = self._calculate_performance_metrics(results, query_analysis)
        
        # Identify issues using helper
        issues = self._identify_performance_issues(metrics)
        
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
    
    def get_adaptive_filters(self, query: str, current_results: List[Dict[str, Any]], 
                           search_service) -> Dict[str, Any]:
        """Get adaptive filters for the current search context."""
        try:
            # Analyze current search performance
            query_analysis = {
                "query": query,
                "result_count": len(current_results),
                "has_price_intent": self._has_price_intent(query),
                "has_category_intent": self._has_category_intent(query)
            }
            
            performance_analysis = self.analyze_search_performance(current_results, query_analysis)
            
            # Select appropriate strategies
            strategies = self.select_adaptive_strategies(performance_analysis)
            
            # Apply adaptive filtering
            if strategies:
                result = self.apply_adaptive_filters(current_results, query_analysis, search_service)
                return {
                    "filters_applied": result.filters_applied,
                    "improvement_score": result.improvement_score,
                    "strategies_used": result.applied_strategies,
                    "reasoning": result.reasoning
                }
            
            return {
                "filters_applied": {},
                "improvement_score": 0.0,
                "strategies_used": [],
                "reasoning": ERROR_NO_STRATEGIES.format(error=ERROR_NO_STRATEGIES)
            }
            
        except Exception as e:
            logger.error(f"Error getting adaptive filters: {e}")
            return {
                "filters_applied": {},
                "improvement_score": 0.0,
                "strategies_used": [],
                "reasoning": ERROR_ADAPTIVE_FILTERS.format(error=str(e))
            }
    
    def _has_price_intent(self, query: str) -> bool:
        """Check if query has price intent."""
        price_keywords = ['euro', '€', 'prijs', 'price', 'onder', 'boven', 'tussen', 'max', 'min']
        return any(keyword in query.lower() for keyword in price_keywords)
    
    def _has_category_intent(self, query: str) -> bool:
        """Check if query has category intent."""
        category_keywords = ['categorie', 'category', 'type', 'soort', 'kleding', 'elektronica']
        return any(keyword in query.lower() for keyword in category_keywords)

    def _calculate_performance_metrics(self, results: List[Dict[str, Any]], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate performance metrics for search results.
        
        Args:
            results: Search results
            query_analysis: Query analysis data
            
        Returns:
            Dictionary with performance metrics
        """
        if not results:
            return {}
        
        scores = [r.get('similarity', 0) for r in results]
        prices = [r.get('price', 0) for r in results if r.get('price')]
        
        return {
            "avg_score": statistics.mean(scores) if scores else 0,
            "result_count": len(results),
            "avg_price_top5": statistics.mean(prices[:5]) if prices else 0,
            "price_range": max(prices) - min(prices) if len(prices) > 1 else 0,
            "category_coverage": self._calculate_category_coverage(results),
            "diversity_score": self._calculate_diversity_score(results),
            "material_intent_detected": "material_intent" in query_analysis.get("detected_intents", {}),
            "color_intent_detected": "color_intent" in query_analysis.get("detected_intents", {})
        }
    
    def _identify_performance_issues(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Identify performance issues based on metrics.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            List of identified issues
        """
        issues = []
        
        if metrics.get("avg_score", 0) < SCORE_THRESHOLDS["POOR"]:
            issues.append("low_relevance")
        
        if metrics.get("result_count", 0) < RESULT_COUNT_THRESHOLDS["LOW"]:
            issues.append("insufficient_results")
        
        if metrics.get("category_coverage", 0) < CATEGORY_COVERAGE_THRESHOLDS["LOW"]:
            issues.append("low_category_coverage")
        
        if metrics.get("diversity_score", 0) < 0.4:
            issues.append("low_diversity")
        
        return issues

# Global instance
adaptive_filter_engine = AdaptiveFilterEngine()

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `filter_strategies.py` - Filter strategy definitions and management
  - `performance_analyzer.py` - Performance analysis and metrics calculation
  - `strategy_selector.py` - Strategy selection and application logic
  - `filter_applicator.py` - Filter application and result improvement
  - `adaptive_filter_types.py` - Filter types and result classes
  - `adaptive_filter_orchestrator.py` - Main adaptive filter orchestration

## 🗑️ Functies voor Verwijdering
- [ ] `_initialize_strategies()` - Consider moving to a dedicated strategy service
- [ ] `get_strategy_statistics()` - Consider moving to a dedicated statistics service
- [ ] `_has_price_intent()` - Consider moving to a dedicated intent detection service
- [ ] `_has_category_intent()` - Consider moving to a dedicated intent detection service

## ⚡ Performance Optimalisaties
- [ ] Implement caching for frequently used strategies
- [ ] Add batch processing for multiple filter applications
- [ ] Implement parallel processing for strategy evaluation
- [ ] Optimize strategy selection for large datasets
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
- [ ] Implement proper data encryption

## 🧪 Testing Verbeteringen
- [ ] Add unit tests for all helper methods
- [ ] Implement integration tests for strategy application
- [ ] Add performance tests for large datasets
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete adaptive filtering

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)

## 🎯 Specifieke Verbeteringen
- [ ] Refactor large strategy initialization methods into smaller, more focused ones
- [ ] Implement proper error handling for strategy application
- [ ] Add retry mechanisms for failed operations
- [ ] Implement proper caching strategies
- [ ] Add support for different output formats
- [ ] Implement proper progress tracking
- [ ] Add support for custom strategies
- [ ] Implement proper result aggregation
- [ ] Add support for different data sources
- [ ] Implement proper result validation
- [ ] Add support for real-time strategy updates
- [ ] Implement proper data versioning
- [ ] Add support for strategy comparison
- [ ] Implement proper data export functionality
- [ ] Add support for strategy templates
- [ ] Implement proper A/B testing for strategies
- [ ] Add support for personalized strategies
- [ ] Implement proper feedback collection
- [ ] Add support for strategy analytics
- [ ] Implement proper strategy ranking
""" 