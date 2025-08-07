#!/usr/bin/env python3
"""
Pattern Learning System

Analyzes search patterns and learns from successful queries to improve search performance.
"""

import logging
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import json
import re

logger = logging.getLogger(__name__)

# Constants
DEFAULT_DB_PATH = "data/databases/findly_consolidated.db"
DEFAULT_DAYS_BACK = 30
DEFAULT_TOP_SUGGESTIONS_LIMIT = 10
DEFAULT_MIN_QUERY_LENGTH = 10
DEFAULT_MAX_QUERY_LENGTH = 30
DEFAULT_LONG_QUERY_LENGTH = 50

# Time slots
TIME_SLOTS = {
    "morning": (6, 12),
    "afternoon": (12, 17),
    "evening": (17, 21),
    "night": (21, 6)
}

# Query categories
QUERY_CATEGORIES = {
    "short": "short",
    "medium": "medium", 
    "long": "long"
}

# Priority levels
PRIORITY_LEVELS = {
    "high": "high",
    "medium": "medium",
    "low": "low"
}

# Effort levels
EFFORT_LEVELS = {
    "low": "low",
    "medium": "medium",
    "high": "high"
}

# Error Messages
ERROR_NO_ANALYTICS_DATA = "No analytics data found for store {store_id}"
ERROR_ANALYZE_PATTERNS = "Failed to analyze patterns for store {store_id}: {error}"

# Logging Context Keys
LOG_CONTEXT_STORE_ID = "store_id"
LOG_CONTEXT_DAYS_BACK = "days_back"
LOG_CONTEXT_SUGGESTIONS_COUNT = "suggestions_count"

@dataclass
class PatternSuggestion:
    """Suggestion based on learned patterns."""
    suggestion_type: str
    description: str
    target_category: str
    expected_improvement: float
    confidence: float
    implementation_steps: List[str]
    priority: str  # "high", "medium", "low"
    estimated_effort: str  # "low", "medium", "high"
    last_updated: datetime

@dataclass
class LearnedPattern:
    """A learned pattern from search analytics."""
    pattern_id: str
    pattern_type: str
    success_rate: float
    usage_count: int
    performance_trend: str  # "improving", "declining", "stable"
    confidence: float
    last_used: datetime

class PatternLearningSystem:
    """System for learning and applying search patterns."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
    
    def _get_analytics_data(self, store_id: str, days_back: int) -> List:
        """
        Get analytics data for the specified period.
        
        Args:
            store_id: Store ID
            days_back: Number of days to look back
            
        Returns:
            List of analytics data
        """
        with sqlite3.connect(self.db_path) as conn:
            start_date = datetime.now() - timedelta(days=days_back)
            
            cursor = conn.execute("""
                SELECT * FROM search_analytics 
                WHERE store_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (store_id, start_date.isoformat()))
            
            return cursor.fetchall()
    
    def _analyze_all_pattern_types(self, analytics_data: List) -> List[PatternSuggestion]:
        """
        Analyze all pattern types and generate suggestions.
        
        Args:
            analytics_data: Analytics data to analyze
            
        Returns:
            List of pattern suggestions
        """
        suggestions = []
        
        # Query pattern analysis
        query_suggestions = self._analyze_query_patterns(analytics_data)
        suggestions.extend(query_suggestions)
        
        # Performance pattern analysis
        performance_suggestions = self._analyze_performance_patterns(analytics_data)
        suggestions.extend(performance_suggestions)
        
        # User behavior pattern analysis
        behavior_suggestions = self._analyze_user_behavior_patterns(analytics_data)
        suggestions.extend(behavior_suggestions)
        
        return suggestions
    
    def _sort_and_limit_suggestions(self, suggestions: List[PatternSuggestion]) -> List[PatternSuggestion]:
        """
        Sort suggestions by expected improvement and limit to top results.
        
        Args:
            suggestions: List of pattern suggestions
            
        Returns:
            Sorted and limited list of suggestions
        """
        suggestions.sort(key=lambda x: x.expected_improvement, reverse=True)
        return suggestions[:DEFAULT_TOP_SUGGESTIONS_LIMIT]
    
    def _calculate_success_rate(self, success_count: int, failure_count: int) -> float:
        """
        Calculate success rate from success and failure counts.
        
        Args:
            success_count: Number of successful queries
            failure_count: Number of failed queries
            
        Returns:
            Success rate as float
        """
        total_count = success_count + failure_count
        return success_count / total_count if total_count > 0 else 0
    
    def _create_query_optimization_suggestion(self, pattern: str, success_rate: float, total_count: int) -> PatternSuggestion:
        """
        Create a query optimization suggestion.
        
        Args:
            pattern: Query pattern
            success_rate: Success rate for the pattern
            total_count: Total count of queries with this pattern
            
        Returns:
            PatternSuggestion object
        """
        return PatternSuggestion(
            suggestion_type="query_optimization",
            description=f"Optimize queries using pattern '{pattern}' (success rate: {success_rate:.1%})",
            target_category="search_relevance",
            expected_improvement=success_rate - 0.5,  # Improvement over baseline
            confidence=min(1.0, total_count / 20),
            implementation_steps=[
                f"Identify queries that could benefit from '{pattern}' pattern",
                "Update search algorithm to prioritize this pattern",
                "Monitor success rate improvement"
            ],
            priority=PRIORITY_LEVELS["high"] if success_rate > 0.9 else PRIORITY_LEVELS["medium"],
            estimated_effort=EFFORT_LEVELS["medium"],
            last_updated=datetime.now()
        )
    
    def _filter_high_success_patterns(self, successful_patterns: Dict[str, int], 
                                    unsuccessful_patterns: Dict[str, int]) -> List[tuple]:
        """
        Filter patterns with high success rates.
        
        Args:
            successful_patterns: Dictionary of successful patterns
            unsuccessful_patterns: Dictionary of unsuccessful patterns
            
        Returns:
            List of tuples (pattern, success_rate, total_count)
        """
        high_success_patterns = []
        
        for pattern, success_count in successful_patterns.items():
            failure_count = unsuccessful_patterns.get(pattern, 0)
            total_count = success_count + failure_count
            success_rate = self._calculate_success_rate(success_count, failure_count)
            
            if success_rate > 0.8 and total_count >= 5:  # High success rate with sufficient data
                high_success_patterns.append((pattern, success_rate, total_count))
        
        return high_success_patterns
    
    def analyze_and_learn_patterns(self, store_id: str, days_back: int = DEFAULT_DAYS_BACK) -> List[PatternSuggestion]:
        """Analyze search patterns and generate improvement suggestions."""
        try:
            analytics_data = self._get_analytics_data(store_id, days_back)
            
            if not analytics_data:
                logger.warning(f"No analytics data found for store {store_id}")
                return []
            
            # Analyze different pattern types
            suggestions = self._analyze_all_pattern_types(analytics_data)
            
            # Sort by expected improvement
            suggestions = self._sort_and_limit_suggestions(suggestions)
            
            return suggestions
                
        except Exception as e:
            logger.error(f"Failed to analyze patterns for store {store_id}: {e}")
            return []
    
    def _analyze_query_patterns(self, analytics_data: List) -> List[PatternSuggestion]:
        """
        Analyze query patterns and generate suggestions.
        
        Args:
            analytics_data: Analytics data to analyze
            
        Returns:
            List of pattern suggestions
        """
        suggestions = []
        
        # Analyze successful vs unsuccessful queries
        successful_queries = [row for row in analytics_data if row[6] > 0]  # result_count > 0
        unsuccessful_queries = [row for row in analytics_data if row[6] == 0]
        
        if len(successful_queries) > 0 and len(unsuccessful_queries) > 0:
            # Find common patterns in successful queries
            successful_patterns = self._extract_query_patterns(successful_queries)
            unsuccessful_patterns = self._extract_query_patterns(unsuccessful_queries)
            
            # Filter high success patterns using helper
            high_success_patterns = self._filter_high_success_patterns(successful_patterns, unsuccessful_patterns)
            
            # Create suggestions for high success patterns
            for pattern, success_rate, total_count in high_success_patterns:
                suggestion = self._create_query_optimization_suggestion(pattern, success_rate, total_count)
                suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_performance_patterns(self, analytics_data: List) -> List[PatternSuggestion]:
        """Analyze performance patterns and generate suggestions."""
        suggestions = []
        
        # Analyze response time patterns
        response_times = [row[8] for row in analytics_data if row[8] is not None]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            slow_queries = [row for row in analytics_data if row[8] and row[8] > avg_response_time * 1.5]
            
            if len(slow_queries) > 0:
                # Find common characteristics of slow queries
                slow_patterns = self._extract_slow_query_patterns(slow_queries)
                
                for pattern, count in slow_patterns.items():
                    if count >= 3:  # Pattern appears multiple times
                        suggestions.append(PatternSuggestion(
                            suggestion_type="performance_optimization",
                            description=f"Optimize performance for queries with pattern '{pattern}'",
                            target_category="response_time",
                            expected_improvement=0.2,  # 20% improvement expected
                            confidence=min(1.0, count / 10),
                            implementation_steps=[
                                f"Analyze why '{pattern}' queries are slow",
                                "Implement caching for this query type",
                                "Optimize database queries for this pattern"
                            ],
                            priority="high" if count >= 5 else "medium",
                            estimated_effort="high",
                            last_updated=datetime.now()
                        ))
        
        # Analyze cache hit patterns
        cache_hits = [row for row in analytics_data if row[9]]  # cache_hit
        cache_hit_rate = len(cache_hits) / len(analytics_data) if analytics_data else 0
        
        if cache_hit_rate < 0.5:  # Low cache hit rate
            suggestions.append(PatternSuggestion(
                suggestion_type="caching_optimization",
                description=f"Improve cache hit rate (current: {cache_hit_rate:.1%})",
                target_category="caching",
                expected_improvement=0.3,  # 30% improvement expected
                confidence=0.8,
                implementation_steps=[
                    "Analyze cache miss patterns",
                    "Adjust cache TTL settings",
                    "Implement smarter cache key generation",
                    "Add cache warming for popular queries"
                ],
                priority="medium",
                estimated_effort="medium",
                last_updated=datetime.now()
            ))
        
        return suggestions
    
    def _analyze_user_behavior_patterns(self, analytics_data: List) -> List[PatternSuggestion]:
        """Analyze user behavior patterns and generate suggestions."""
        suggestions = []
        
        # Analyze search refinement patterns
        refinement_patterns = self._extract_refinement_patterns(analytics_data)
        
        for pattern, count in refinement_patterns.items():
            if count >= 5:  # Pattern appears frequently
                suggestions.append(PatternSuggestion(
                    suggestion_type="user_experience",
                    description=f"Improve UX for '{pattern}' search refinement",
                    target_category="user_experience",
                    expected_improvement=0.15,  # 15% improvement expected
                    confidence=min(1.0, count / 15),
                    implementation_steps=[
                        f"Analyze why users need '{pattern}' refinement",
                        "Implement automatic refinement suggestions",
                        "Optimize initial search results for this pattern"
                    ],
                    priority="medium",
                    estimated_effort="low",
                    last_updated=datetime.now()
                ))
        
        # Analyze time-of-day patterns
        time_patterns = self._extract_time_patterns(analytics_data)
        
        for time_slot, count in time_patterns.items():
            if count >= 10:  # Significant time pattern
                suggestions.append(PatternSuggestion(
                    suggestion_type="timing_optimization",
                    description=f"Optimize for {time_slot} search patterns",
                    target_category="timing",
                    expected_improvement=0.1,  # 10% improvement expected
                    confidence=min(1.0, count / 20),
                    implementation_steps=[
                        f"Analyze search patterns during {time_slot}",
                        "Adjust search algorithm for this time period",
                        "Implement time-based caching strategies"
                    ],
                    priority="low",
                    estimated_effort="low",
                    last_updated=datetime.now()
                ))
        
        return suggestions
    
    def _extract_query_patterns(self, queries: List) -> Dict[str, int]:
        """Extract common patterns from queries."""
        patterns = {}
        
        for row in queries:
            query = row[1]  # query column
            if not query:
                continue
            
            # Extract word patterns
            words = query.lower().split()
            if len(words) >= 2:
                # Bigram patterns
                for i in range(len(words) - 1):
                    bigram = f"{words[i]} {words[i+1]}"
                    patterns[bigram] = patterns.get(bigram, 0) + 1
            
            # Extract length patterns
            length_category = self._categorize_query_length(len(query))
            patterns[f"length_{length_category}"] = patterns.get(f"length_{length_category}", 0) + 1
            
            # Extract special character patterns
            if any(char in query for char in ['€', '$', '£']):
                patterns["price_query"] = patterns.get("price_query", 0) + 1
            
            if any(char in query for char in ['-', '_']):
                patterns["hyphenated_query"] = patterns.get("hyphenated_query", 0) + 1
        
        return patterns
    
    def _extract_slow_query_patterns(self, slow_queries: List) -> Dict[str, int]:
        """Extract patterns from slow queries."""
        patterns = {}
        
        for row in slow_queries:
            query = row[1]
            if not query:
                continue
            
            # Long queries tend to be slower
            if len(query) > DEFAULT_LONG_QUERY_LENGTH:
                patterns["long_query"] = patterns.get("long_query", 0) + 1
            
            # Queries with special characters
            if re.search(r'[^\w\s]', query):
                patterns["special_chars"] = patterns.get("special_chars", 0) + 1
            
            # Queries with numbers
            if re.search(r'\d', query):
                patterns["numeric_query"] = patterns.get("numeric_query", 0) + 1
        
        return patterns
    
    def _extract_refinement_patterns(self, analytics_data: List) -> Dict[str, int]:
        """Extract search refinement patterns."""
        patterns = {}
        
        # Group queries by session or user to find refinement patterns
        # This is a simplified analysis
        for i, row in enumerate(analytics_data):
            query = row[1]
            if not query:
                continue
            
            # Look for refinement indicators
            if any(word in query.lower() for word in ["cheaper", "more", "less", "different", "other"]):
                patterns["price_refinement"] = patterns.get("price_refinement", 0) + 1
            
            if any(word in query.lower() for word in ["blue", "red", "black", "white", "color"]):
                patterns["color_refinement"] = patterns.get("color_refinement", 0) + 1
            
            if any(word in query.lower() for word in ["small", "medium", "large", "size"]):
                patterns["size_refinement"] = patterns.get("size_refinement", 0) + 1
        
        return patterns
    
    def _extract_time_patterns(self, analytics_data: List) -> Dict[str, int]:
        """Extract time-based patterns."""
        patterns = {}
        
        for row in analytics_data:
            timestamp_str = row[11]  # timestamp column
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                hour = timestamp.hour
                
                for time_slot_name, (start_hour, end_hour) in TIME_SLOTS.items():
                    if start_hour <= hour < end_hour:
                        patterns[time_slot_name] = patterns.get(time_slot_name, 0) + 1
                        break # Found the correct time slot
            except:
                continue
        
        return patterns
    
    def _categorize_query_length(self, length: int) -> str:
        """Categorize query by length."""
        if length < DEFAULT_MIN_QUERY_LENGTH:
            return QUERY_CATEGORIES["short"]
        elif length < DEFAULT_MAX_QUERY_LENGTH:
            return QUERY_CATEGORIES["medium"]
        else:
            return QUERY_CATEGORIES["long"]
    
    def _get_learned_patterns(self, store_id: str) -> List[LearnedPattern]:
        """Get learned patterns for a store."""
        # This would typically retrieve from a patterns table
        # For now, return empty list
        return []

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `query_pattern_analyzer.py` - Query pattern analysis
  - `performance_pattern_analyzer.py` - Performance pattern analysis
  - `user_behavior_analyzer.py` - User behavior pattern analysis
  - `pattern_suggestion_generator.py` - Pattern suggestion generation
  - `pattern_extractor.py` - Pattern extraction methods
  - `pattern_learning_orchestrator.py` - Main orchestration

## 🗑️ Functies voor Verwijdering
- [ ] `_get_learned_patterns()` - Consider moving to a dedicated pattern storage service
- [ ] `_extract_time_patterns()` - Consider moving to a dedicated time analysis service
- [ ] `_extract_refinement_patterns()` - Consider moving to a dedicated refinement analysis service
- [ ] `_categorize_query_length()` - Consider moving to a dedicated query analysis service

## ⚡ Performance Optimalisaties
- [ ] Implement caching for frequently accessed patterns
- [ ] Add batch processing for multiple pattern analyses
- [ ] Implement parallel processing for pattern extraction
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
- [ ] Implement proper data encryption

## 🧪 Testing Verbeteringen
- [ ] Add unit tests for all helper methods
- [ ] Implement integration tests for pattern analysis
- [ ] Add performance tests for large datasets
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete pattern learning flow

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)

## 🎯 Specifieke Verbeteringen
- [ ] Refactor large pattern analysis methods into smaller, more focused ones
- [ ] Implement proper error handling for database operations
- [ ] Add retry mechanisms for failed operations
- [ ] Implement proper caching strategies
- [ ] Add support for different output formats
- [ ] Implement proper progress tracking
- [ ] Add support for custom pattern analysis scenarios
- [ ] Implement proper result aggregation
- [ ] Add support for different data sources
- [ ] Implement proper result validation
- [ ] Add support for real-time pattern learning updates
- [ ] Implement proper data versioning
- [ ] Add support for pattern comparison
- [ ] Implement proper data export functionality
- [ ] Add support for pattern templates
- [ ] Implement proper A/B testing for patterns
- [ ] Add support for personalized patterns
- [ ] Implement proper feedback collection
- [ ] Add support for pattern analytics
- [ ] Implement proper pattern ranking
""" 