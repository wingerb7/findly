#!/usr/bin/env python3
"""
Pattern Learning System

This module provides automatic pattern learning and improvement suggestions by:
- Analyzing poorly performing query categories
- Learning from successful patterns
- Generating improvement suggestions
- Managing memory and cleaning up old/unused data
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
import re
from collections import defaultdict, Counter

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class PatternSuggestion:
    """Represents a pattern improvement suggestion."""
    suggestion_type: str
    description: str
    target_category: str
    expected_improvement: float
    confidence: float
    implementation_steps: List[str]
    priority: str  # high, medium, low
    estimated_effort: str  # low, medium, high
    last_updated: datetime

@dataclass
class LearningPattern:
    """Represents a learned pattern from search data."""
    pattern_id: str
    pattern_type: str
    pattern_data: Dict[str, Any]
    success_rate: float
    usage_count: int
    last_used: datetime
    created_at: datetime
    performance_trend: str  # improving, declining, stable
    confidence: float

@dataclass
class MemoryPolicy:
    """Represents a memory management policy."""
    policy_name: str
    table_name: str
    retention_days: int
    cleanup_condition: str
    last_cleanup: datetime
    records_cleaned: int

class PatternLearningSystem:
    """System for learning patterns and managing memory."""
    
    def __init__(self, db_path: str = "search_knowledge_base.db"):
        self.db_path = db_path
        
        # Memory management policies
        self.memory_policies = {
            "benchmark_history": MemoryPolicy(
                "benchmark_history",
                "benchmark_history",
                90,  # 90 days retention
                "benchmark_date < datetime('now', '-90 days')",
                datetime.now(),
                0
            ),
            "performance_baselines": MemoryPolicy(
                "performance_baselines",
                "performance_baselines",
                180,  # 180 days retention
                "generated_at < datetime('now', '-180 days')",
                datetime.now(),
                0
            ),
            "transfer_applications": MemoryPolicy(
                "transfer_applications",
                "transfer_applications",
                365,  # 1 year retention
                "applied_at < datetime('now', '-365 days')",
                datetime.now(),
                0
            ),
            "query_patterns": MemoryPolicy(
                "query_patterns",
                "query_patterns",
                60,  # 60 days retention for unused patterns
                "last_used < datetime('now', '-60 days') AND success_rate < 0.5",
                datetime.now(),
                0
            )
        }
        
        # Pattern learning thresholds
        self.learning_thresholds = {
            "min_success_rate": 0.6,
            "min_usage_count": 5,
            "min_confidence": 0.7,
            "max_patterns_per_category": 50
        }
    
    def analyze_and_learn_patterns(self, store_id: str, days_back: int = 30) -> List[PatternSuggestion]:
        """Analyze search patterns and generate improvement suggestions."""
        try:
            # Get recent benchmark data
            benchmark_data = self._get_recent_benchmark_data(store_id, days_back)
            
            if not benchmark_data:
                logger.warning(f"No benchmark data found for store {store_id}")
                return []
            
            suggestions = []
            
            # Analyze poorly performing categories
            poor_performers = self._identify_poor_performers(benchmark_data)
            for category, issues in poor_performers.items():
                category_suggestions = self._generate_category_suggestions(category, issues)
                suggestions.extend(category_suggestions)
            
            # Learn from successful patterns
            successful_patterns = self._extract_successful_patterns(benchmark_data)
            self._store_learned_patterns(store_id, successful_patterns)
            
            # Generate pattern-based suggestions
            pattern_suggestions = self._generate_pattern_suggestions(store_id, benchmark_data)
            suggestions.extend(pattern_suggestions)
            
            # Sort by priority and expected improvement
            suggestions.sort(key=lambda x: (self._priority_score(x.priority), x.expected_improvement), reverse=True)
            
            # Store suggestions
            self._store_pattern_suggestions(store_id, suggestions)
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error analyzing patterns for store {store_id}: {e}")
            return []
    
    def _get_recent_benchmark_data(self, store_id: str, days_back: int) -> List[Dict[str, Any]]:
        """Get recent benchmark data for pattern analysis."""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
            logger.error(f"Error getting recent benchmark data: {e}")
            return []
    
    def _identify_poor_performers(self, benchmark_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify poorly performing categories and their issues."""
        poor_performers = defaultdict(list)
        
        # Group by category
        category_groups = defaultdict(list)
        for data_point in benchmark_data:
            category = data_point.get("category", "unknown")
            category_groups[category].append(data_point)
        
        # Analyze each category
        for category, data_points in category_groups.items():
            if len(data_points) < 3:  # Need minimum data points
                continue
            
            scores = [dp["score"] for dp in data_points if dp["score"] is not None]
            response_times = [dp["response_time"] for dp in data_points if dp["response_time"] is not None]
            
            if not scores:
                continue
            
            avg_score = statistics.mean(scores)
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            
            # Identify issues
            if avg_score < 0.6:
                poor_performers[category].append(f"Low relevance score: {avg_score:.3f}")
            
            if avg_response_time > 2.0:
                poor_performers[category].append(f"Slow response time: {avg_response_time:.2f}s")
            
            # Check for specific issues
            low_scores = [s for s in scores if s < 0.5]
            if len(low_scores) > len(scores) * 0.3:  # More than 30% low scores
                poor_performers[category].append(f"High rate of low scores: {len(low_scores)}/{len(scores)}")
        
        return dict(poor_performers)
    
    def _generate_category_suggestions(self, category: str, issues: List[str]) -> List[PatternSuggestion]:
        """Generate suggestions for improving a specific category."""
        suggestions = []
        
        for issue in issues:
            if "Low relevance score" in issue:
                suggestions.append(PatternSuggestion(
                    suggestion_type="synonym_expansion",
                    description=f"Add synonyms for {category} queries to improve relevance",
                    target_category=category,
                    expected_improvement=0.15,
                    confidence=0.8,
                    implementation_steps=[
                        f"Analyze {category} query patterns",
                        "Identify common synonyms",
                        "Add synonyms to search index",
                        "Test with sample queries"
                    ],
                    priority="high",
                    estimated_effort="medium",
                    last_updated=datetime.now()
                ))
            
            elif "Slow response time" in issue:
                suggestions.append(PatternSuggestion(
                    suggestion_type="caching_optimization",
                    description=f"Optimize caching for {category} queries to improve response time",
                    target_category=category,
                    expected_improvement=0.2,
                    confidence=0.7,
                    implementation_steps=[
                        f"Analyze {category} query frequency",
                        "Implement query-specific caching",
                        "Optimize cache invalidation",
                        "Monitor performance improvements"
                    ],
                    priority="medium",
                    estimated_effort="low",
                    last_updated=datetime.now()
                ))
            
            elif "High rate of low scores" in issue:
                suggestions.append(PatternSuggestion(
                    suggestion_type="query_refinement",
                    description=f"Improve query understanding for {category} searches",
                    target_category=category,
                    expected_improvement=0.25,
                    confidence=0.75,
                    implementation_steps=[
                        f"Analyze failed {category} queries",
                        "Identify common failure patterns",
                        "Implement query refinement logic",
                        "Add fallback search strategies"
                    ],
                    priority="high",
                    estimated_effort="high",
                    last_updated=datetime.now()
                ))
        
        return suggestions
    
    def _extract_successful_patterns(self, benchmark_data: List[Dict[str, Any]]) -> List[LearningPattern]:
        """Extract successful patterns from benchmark data."""
        patterns = []
        
        # Group by category and analyze successful queries
        category_groups = defaultdict(list)
        for data_point in benchmark_data:
            category = data_point.get("category", "unknown")
            category_groups[category].append(data_point)
        
        for category, data_points in category_groups.items():
            # Find high-performing queries
            high_performers = [dp for dp in data_points if dp.get("score", 0) > 0.8]
            
            if len(high_performers) < 3:
                continue
            
            # Extract common patterns
            pattern = self._extract_category_pattern(category, high_performers)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def _extract_category_pattern(self, category: str, high_performers: List[Dict[str, Any]]) -> Optional[LearningPattern]:
        """Extract a pattern from high-performing queries in a category."""
        try:
            # Analyze query characteristics
            queries = [dp["query"] for dp in high_performers]
            scores = [dp["score"] for dp in high_performers]
            response_times = [dp["response_time"] for dp in high_performers]
            
            # Calculate pattern metrics
            avg_score = statistics.mean(scores)
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            
            # Extract common words/phrases
            common_terms = self._extract_common_terms(queries)
            
            pattern_data = {
                "category": category,
                "common_terms": common_terms,
                "avg_score": avg_score,
                "avg_response_time": avg_response_time,
                "query_count": len(queries)
            }
            
            pattern_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return LearningPattern(
                pattern_id=pattern_id,
                pattern_type="successful_category",
                pattern_data=pattern_data,
                success_rate=avg_score,
                usage_count=len(queries),
                last_used=datetime.now(),
                created_at=datetime.now(),
                performance_trend="stable",
                confidence=min(1.0, len(queries) / 10)  # Higher confidence with more data
            )
            
        except Exception as e:
            logger.error(f"Error extracting pattern for category {category}: {e}")
            return None
    
    def _extract_common_terms(self, queries: List[str]) -> List[str]:
        """Extract common terms from a list of queries."""
        # Simple term extraction (could be enhanced with NLP)
        all_terms = []
        for query in queries:
            terms = re.findall(r'\b\w+\b', query.lower())
            all_terms.extend(terms)
        
        # Count terms and return most common
        term_counts = Counter(all_terms)
        return [term for term, count in term_counts.most_common(5) if count > 1]
    
    def _generate_pattern_suggestions(self, store_id: str, benchmark_data: List[Dict[str, Any]]) -> List[PatternSuggestion]:
        """Generate suggestions based on learned patterns."""
        suggestions = []
        
        # Get learned patterns for this store
        learned_patterns = self._get_learned_patterns(store_id)
        
        for pattern in learned_patterns:
            if pattern.success_rate > 0.8 and pattern.confidence > 0.7:
                # Suggest applying this pattern to similar categories
                suggestions.append(PatternSuggestion(
                    suggestion_type="pattern_application",
                    description=f"Apply successful {pattern.pattern_data.get('category', 'unknown')} pattern to similar categories",
                    target_category="similar_categories",
                    expected_improvement=pattern.success_rate * 0.8,  # Conservative estimate
                    confidence=pattern.confidence,
                    implementation_steps=[
                        "Identify similar categories",
                        "Apply pattern logic",
                        "Test with sample queries",
                        "Monitor performance"
                    ],
                    priority="medium",
                    estimated_effort="low",
                    last_updated=datetime.now()
                ))
        
        return suggestions
    
    def _store_learned_patterns(self, store_id: str, patterns: List[LearningPattern]):
        """Store learned patterns in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS learned_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id TEXT,
                        pattern_id TEXT,
                        pattern_type TEXT,
                        pattern_data TEXT,
                        success_rate REAL,
                        usage_count INTEGER,
                        last_used TIMESTAMP,
                        created_at TIMESTAMP,
                        performance_trend TEXT,
                        confidence REAL
                    )
                """)
                
                for pattern in patterns:
                    conn.execute("""
                        INSERT OR REPLACE INTO learned_patterns (
                            store_id, pattern_id, pattern_type, pattern_data, success_rate,
                            usage_count, last_used, created_at, performance_trend, confidence
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        store_id,
                        pattern.pattern_id,
                        pattern.pattern_type,
                        json.dumps(pattern.pattern_data),
                        pattern.success_rate,
                        pattern.usage_count,
                        pattern.last_used.isoformat(),
                        pattern.created_at.isoformat(),
                        pattern.performance_trend,
                        pattern.confidence
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing learned patterns: {e}")
    
    def _get_learned_patterns(self, store_id: str) -> List[LearningPattern]:
        """Get learned patterns for a store."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM learned_patterns 
                    WHERE store_id = ? 
                    ORDER BY success_rate DESC, usage_count DESC
                """, (store_id,))
                
                patterns = []
                for row in cursor.fetchall():
                    patterns.append(LearningPattern(
                        pattern_id=row[2],
                        pattern_type=row[3],
                        pattern_data=json.loads(row[4]),
                        success_rate=row[5],
                        usage_count=row[6],
                        last_used=datetime.fromisoformat(row[7]),
                        created_at=datetime.fromisoformat(row[8]),
                        performance_trend=row[9],
                        confidence=row[10]
                    ))
                
                return patterns
                
        except Exception as e:
            logger.error(f"Error getting learned patterns: {e}")
            return []
    
    def _store_pattern_suggestions(self, store_id: str, suggestions: List[PatternSuggestion]):
        """Store pattern suggestions in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS pattern_suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        store_id TEXT,
                        suggestion_type TEXT,
                        description TEXT,
                        target_category TEXT,
                        expected_improvement REAL,
                        confidence REAL,
                        implementation_steps TEXT,
                        priority TEXT,
                        estimated_effort TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                
                for suggestion in suggestions:
                    conn.execute("""
                        INSERT INTO pattern_suggestions (
                            store_id, suggestion_type, description, target_category,
                            expected_improvement, confidence, implementation_steps,
                            priority, estimated_effort
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        store_id,
                        suggestion.suggestion_type,
                        suggestion.description,
                        suggestion.target_category,
                        suggestion.expected_improvement,
                        suggestion.confidence,
                        json.dumps(suggestion.implementation_steps),
                        suggestion.priority,
                        suggestion.estimated_effort
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing pattern suggestions: {e}")
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score for sorting."""
        priority_scores = {"high": 3, "medium": 2, "low": 1}
        return priority_scores.get(priority, 1)
    
    # ===== MEMORY MANAGEMENT =====
    
    def cleanup_old_data(self) -> Dict[str, int]:
        """Clean up old data based on memory policies."""
        cleanup_results = {}
        
        for policy_name, policy in self.memory_policies.items():
            try:
                cleaned_count = self._apply_cleanup_policy(policy)
                cleanup_results[policy_name] = cleaned_count
                
                # Update policy stats
                policy.last_cleanup = datetime.now()
                policy.records_cleaned += cleaned_count
                
                logger.info(f"Cleaned {cleaned_count} records from {policy_name}")
                
            except Exception as e:
                logger.error(f"Error cleaning up {policy_name}: {e}")
                cleanup_results[policy_name] = 0
        
        return cleanup_results
    
    def _apply_cleanup_policy(self, policy: MemoryPolicy) -> int:
        """Apply a specific cleanup policy."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count records to be deleted
                cursor = conn.execute(f"""
                    SELECT COUNT(*) FROM {policy.table_name} 
                    WHERE {policy.cleanup_condition}
                """)
                count_to_delete = cursor.fetchone()[0]
                
                if count_to_delete > 0:
                    # Delete old records
                    conn.execute(f"""
                        DELETE FROM {policy.table_name} 
                        WHERE {policy.cleanup_condition}
                    """)
                    conn.commit()
                
                return count_to_delete
                
        except Exception as e:
            logger.error(f"Error applying cleanup policy {policy.policy_name}: {e}")
            return 0
    
    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                for policy_name, policy in self.memory_policies.items():
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {policy.table_name}")
                    total_records = cursor.fetchone()[0]
                    
                    # Get oldest record date
                    cursor = conn.execute(f"""
                        SELECT MIN(benchmark_date) FROM {policy.table_name}
                    """)
                    oldest_date = cursor.fetchone()[0]
                    
                    stats[policy_name] = {
                        "total_records": total_records,
                        "oldest_record": oldest_date,
                        "retention_days": policy.retention_days,
                        "last_cleanup": policy.last_cleanup.isoformat(),
                        "total_cleaned": policy.records_cleaned
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting memory usage stats: {e}")
            return {}
    
    def optimize_storage(self) -> Dict[str, Any]:
        """Optimize database storage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get initial size
                cursor = conn.execute("PRAGMA page_count")
                initial_pages = cursor.fetchone()[0]
                
                # Vacuum database to reclaim space
                conn.execute("VACUUM")
                
                # Get final size
                cursor = conn.execute("PRAGMA page_count")
                final_pages = cursor.fetchone()[0]
                
                # Analyze tables for better query performance
                conn.execute("ANALYZE")
                
                return {
                    "initial_pages": initial_pages,
                    "final_pages": final_pages,
                    "space_reclaimed": initial_pages - final_pages,
                    "optimization_completed": True
                }
                
        except Exception as e:
            logger.error(f"Error optimizing storage: {e}")
            return {"optimization_completed": False, "error": str(e)}
    
    def export_pattern_analysis_report(self, store_id: str, output_path: str = None) -> str:
        """Export pattern analysis report to JSON."""
        if not output_path:
            output_path = f"pattern_analysis_{store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Get suggestions
        suggestions = self.analyze_and_learn_patterns(store_id)
        
        # Get learned patterns
        learned_patterns = self._get_learned_patterns(store_id)
        
        # Get memory stats
        memory_stats = self.get_memory_usage_stats()
        
        report_data = {
            "store_id": store_id,
            "generated_at": datetime.now().isoformat(),
            "suggestions": [
                {
                    "type": s.suggestion_type,
                    "description": s.description,
                    "target_category": s.target_category,
                    "expected_improvement": s.expected_improvement,
                    "confidence": s.confidence,
                    "priority": s.priority,
                    "estimated_effort": s.estimated_effort
                }
                for s in suggestions
            ],
            "learned_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "success_rate": p.success_rate,
                    "usage_count": p.usage_count,
                    "confidence": p.confidence
                }
                for p in learned_patterns
            ],
            "memory_stats": memory_stats
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return output_path

# Global instance
pattern_learning_system = PatternLearningSystem() 