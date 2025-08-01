#!/usr/bin/env python3
"""
Knowledge Base Builder

This script processes benchmark results and builds a knowledge base for:
- Query pattern analysis
- Performance optimization
- Transfer learning
- Store profiling
"""

import csv
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class QueryPattern:
    """Represents a query pattern with performance metrics."""
    pattern_type: str
    pattern_text: str
    success_rate: float
    avg_relevance_score: float
    total_usage: int
    avg_response_time: float
    price_filter_usage_rate: float
    fallback_usage_rate: float
    complexity_score: float
    last_updated: datetime

@dataclass
class StoreProfile:
    """Represents a store profile with performance baselines."""
    store_id: str
    product_count: int
    price_range: Tuple[float, float]
    category_distribution: Dict[str, int]
    brand_distribution: Dict[str, int]
    material_distribution: Dict[str, int]
    color_distribution: Dict[str, int]
    
    # Performance baselines
    avg_response_time_baseline: float
    avg_relevance_score_baseline: float
    price_filter_usage_rate: float
    fallback_usage_rate: float
    cache_hit_rate: float
    
    # Query patterns
    successful_query_patterns: List[str]
    problematic_query_patterns: List[str]
    recommended_improvements: List[str]
    
    # Quality metrics
    avg_price_coherence: float
    avg_diversity_score: float
    avg_conversion_potential: float
    
    # Metadata
    created_at: datetime
    last_updated: datetime

class KnowledgeBaseBuilder:
    """Builds and maintains the search knowledge base."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path from project root
            import os
            # Go up from scripts/data_generation to project root
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            self.db_path = os.path.join(project_root, "data", "databases", "findly_consolidated.db")
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the knowledge base database."""
        with sqlite3.connect(self.db_path) as conn:
            # Query patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_text TEXT NOT NULL,
                    success_rate REAL,
                    avg_relevance_score REAL,
                    total_usage INTEGER DEFAULT 0,
                    avg_response_time REAL,
                    price_filter_usage_rate REAL,
                    fallback_usage_rate REAL,
                    complexity_score REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pattern_type, pattern_text)
                )
            """)
            
            # Store profiles table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS store_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id TEXT UNIQUE NOT NULL,
                    product_count INTEGER,
                    price_range_min REAL,
                    price_range_max REAL,
                    category_distribution TEXT,  -- JSON
                    brand_distribution TEXT,     -- JSON
                    material_distribution TEXT,  -- JSON
                    color_distribution TEXT,     -- JSON
                    avg_response_time_baseline REAL,
                    avg_relevance_score_baseline REAL,
                    price_filter_usage_rate REAL,
                    fallback_usage_rate REAL,
                    cache_hit_rate REAL,
                    successful_query_patterns TEXT,  -- JSON
                    problematic_query_patterns TEXT, -- JSON
                    recommended_improvements TEXT,   -- JSON
                    avg_price_coherence REAL,
                    avg_diversity_score REAL,
                    avg_conversion_potential REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Search intent success matrix
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_intent_success (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_type TEXT NOT NULL,
                    query_template TEXT NOT NULL,
                    success_score REAL,
                    recommended_filters TEXT,  -- JSON
                    fallback_strategies TEXT, -- JSON
                    avg_response_time REAL,
                    usage_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(intent_type, query_template)
                )
            """)
            
            # Product performance mapping
            conn.execute("""
                CREATE TABLE IF NOT EXISTS product_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    category TEXT,
                    avg_search_position REAL,
                    click_through_rate REAL,
                    conversion_rate REAL,
                    search_volume INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Benchmark results history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id TEXT,
                    query TEXT,
                    score REAL,
                    response_time REAL,
                    result_count INTEGER,
                    detected_intents TEXT,  -- JSON
                    complexity_score REAL,
                    cache_hit BOOLEAN,
                    price_filter_applied BOOLEAN,
                    fallback_used BOOLEAN,
                    avg_price_top5 REAL,
                    price_coherence REAL,
                    diversity_score REAL,
                    category_coverage REAL,
                    conversion_potential REAL,
                    timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("✅ Knowledge base database initialized")
    
    def process_benchmark_results(self, results_file: str, store_id: Optional[str] = None) -> StoreProfile:
        """Process benchmark results and build knowledge base."""
        logger.info(f"📊 Processing benchmark results from {results_file}")
        
        # Read benchmark results
        df = pd.read_csv(results_file)
        
        # Extract store ID from results if not provided
        if not store_id and 'store_id' in df.columns:
            store_ids = df['store_id'].dropna().unique()
            if len(store_ids) > 0:
                store_id = store_ids[0]
        
        if not store_id:
            store_id = "default_store"
        
        # Build store profile
        store_profile = self._build_store_profile(df, store_id)
        
        # Extract query patterns
        query_patterns = self._extract_query_patterns(df)
        
        # Build search intent success matrix
        intent_success = self._build_intent_success_matrix(df)
        
        # Save to database
        self._save_store_profile(store_profile)
        self._save_query_patterns(query_patterns)
        self._save_intent_success_matrix(intent_success)
        self._save_benchmark_history(df, store_id)
        
        logger.info(f"✅ Processed {len(df)} benchmark results for store {store_id}")
        
        return store_profile
    
    def _build_store_profile(self, df: pd.DataFrame, store_id: str) -> StoreProfile:
        """Build a comprehensive store profile from benchmark results."""
        
        # Basic metrics
        avg_response_time = df['response_time'].mean()
        avg_relevance_score = df['score'].mean()
        price_filter_usage_rate = df['price_filter_applied'].mean()
        fallback_usage_rate = df['fallback_used'].mean()
        cache_hit_rate = df['cache_hit'].mean() if 'cache_hit' in df.columns else 0.0
        
        # Quality metrics
        avg_price_coherence = df['price_coherence'].mean() if 'price_coherence' in df.columns else 0.0
        avg_diversity_score = df['diversity_score'].mean() if 'diversity_score' in df.columns else 0.0
        avg_conversion_potential = df['conversion_potential'].mean() if 'conversion_potential' in df.columns else 0.0
        
        # Extract distributions from detected intents
        category_distribution = self._extract_intent_distribution(df, 'category_intent')
        brand_distribution = self._extract_intent_distribution(df, 'brand_intent')
        material_distribution = self._extract_intent_distribution(df, 'material_intent')
        color_distribution = self._extract_intent_distribution(df, 'color_intent')
        
        # Price range estimation
        price_range = self._estimate_price_range(df)
        
        # Product count estimation (based on result counts)
        product_count = int(df['result_count'].max() * 1.5)  # Rough estimate
        
        # Identify successful and problematic patterns
        successful_patterns = self._identify_successful_patterns(df)
        problematic_patterns = self._identify_problematic_patterns(df)
        recommended_improvements = self._generate_recommendations(df)
        
        return StoreProfile(
            store_id=store_id,
            product_count=product_count,
            price_range=price_range,
            category_distribution=category_distribution,
            brand_distribution=brand_distribution,
            material_distribution=material_distribution,
            color_distribution=color_distribution,
            avg_response_time_baseline=avg_response_time,
            avg_relevance_score_baseline=avg_relevance_score,
            price_filter_usage_rate=price_filter_usage_rate,
            fallback_usage_rate=fallback_usage_rate,
            cache_hit_rate=cache_hit_rate,
            successful_query_patterns=successful_patterns,
            problematic_query_patterns=problematic_patterns,
            recommended_improvements=recommended_improvements,
            avg_price_coherence=avg_price_coherence,
            avg_diversity_score=avg_diversity_score,
            avg_conversion_potential=avg_conversion_potential,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
    
    def _extract_intent_distribution(self, df: pd.DataFrame, intent_type: str) -> Dict[str, int]:
        """Extract distribution of specific intent types from detected intents."""
        distribution = {}
        
        if 'detected_intents' in df.columns:
            for intents_json in df['detected_intents'].dropna():
                try:
                    intents = json.loads(intents_json)
                    if intent_type in intents:
                        for keyword in intents[intent_type]:
                            distribution[keyword] = distribution.get(keyword, 0) + 1
                except json.JSONDecodeError:
                    continue
        
        return distribution
    
    def _estimate_price_range(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Estimate price range from benchmark results."""
        if 'avg_price_top5' in df.columns:
            prices = df['avg_price_top5'].dropna()
            if len(prices) > 0:
                return (float(prices.min()), float(prices.max()))
        
        # Fallback to reasonable defaults
        return (10.0, 500.0)
    
    def _identify_successful_patterns(self, df: pd.DataFrame) -> List[str]:
        """Identify successful query patterns."""
        successful_queries = df[df['score'] > 0.8]['query'].tolist()
        patterns = []
        
        for query in successful_queries[:10]:  # Top 10
            # Extract simple patterns
            words = query.lower().split()
            if len(words) >= 2:
                patterns.append(f"{words[0]} {words[1]}")
        
        return list(set(patterns))
    
    def _identify_problematic_patterns(self, df: pd.DataFrame) -> List[str]:
        """Identify problematic query patterns."""
        problematic_queries = df[df['score'] < 0.4]['query'].tolist()
        patterns = []
        
        for query in problematic_queries[:10]:  # Top 10
            # Extract simple patterns
            words = query.lower().split()
            if len(words) >= 2:
                patterns.append(f"{words[0]} {words[1]}")
        
        return list(set(patterns))
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate improvement recommendations based on benchmark results."""
        recommendations = []
        
        # Analyze performance metrics
        avg_score = df['score'].mean()
        avg_response_time = df['response_time'].mean()
        price_filter_rate = df['price_filter_applied'].mean()
        
        if avg_score < 0.6:
            recommendations.append("Improve search relevance scoring")
        
        if avg_response_time > 0.5:
            recommendations.append("Optimize response times")
        
        if price_filter_rate < 0.3:
            recommendations.append("Enhance price intent detection")
        
        # Analyze intent patterns
        if 'detected_intents' in df.columns:
            intent_counts = {}
            for intents_json in df['detected_intents'].dropna():
                try:
                    intents = json.loads(intents_json)
                    for intent_type in intents:
                        intent_counts[intent_type] = intent_counts.get(intent_type, 0) + 1
                except json.JSONDecodeError:
                    continue
            
            if 'price_intent' in intent_counts and intent_counts['price_intent'] < len(df) * 0.2:
                recommendations.append("Expand price-related keywords")
            
            if 'category_intent' in intent_counts and intent_counts['category_intent'] < len(df) * 0.3:
                recommendations.append("Improve category detection")
        
        return recommendations
    
    def _extract_query_patterns(self, df: pd.DataFrame) -> List[QueryPattern]:
        """Extract query patterns from benchmark results."""
        patterns = []
        
        # Group by intent types
        if 'detected_intents' in df.columns:
            intent_groups = {}
            
            for _, row in df.iterrows():
                try:
                    intents = json.loads(row['detected_intents'])
                    for intent_type, keywords in intents.items():
                        if intent_type not in intent_groups:
                            intent_groups[intent_type] = []
                        intent_groups[intent_type].append(row)
                except json.JSONDecodeError:
                    continue
            
            # Create patterns for each intent type
            for intent_type, group_data in intent_groups.items():
                if len(group_data) >= 3:  # Minimum threshold
                    group_df = pd.DataFrame(group_data)
                    
                    pattern = QueryPattern(
                        pattern_type=intent_type,
                        pattern_text=f"{intent_type}_pattern",
                        success_rate=group_df['score'].mean(),
                        avg_relevance_score=group_df['score'].mean(),
                        total_usage=len(group_df),
                        avg_response_time=group_df['response_time'].mean(),
                        price_filter_usage_rate=group_df['price_filter_applied'].mean(),
                        fallback_usage_rate=group_df['fallback_used'].mean(),
                        complexity_score=group_df['complexity_score'].mean() if 'complexity_score' in group_df.columns else 0.0,
                        last_updated=datetime.now()
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _build_intent_success_matrix(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Build search intent success matrix."""
        matrix = []
        
        if 'detected_intents' in df.columns:
            intent_groups = {}
            
            for _, row in df.iterrows():
                try:
                    intents = json.loads(row['detected_intents'])
                    for intent_type, keywords in intents.items():
                        if intent_type not in intent_groups:
                            intent_groups[intent_type] = []
                        intent_groups[intent_type].append(row)
                except json.JSONDecodeError:
                    continue
            
            for intent_type, group_data in intent_groups.items():
                if len(group_data) >= 2:  # Minimum threshold
                    group_df = pd.DataFrame(group_data)
                    
                    matrix_entry = {
                        'intent_type': intent_type,
                        'query_template': f"{intent_type}_template",
                        'success_score': group_df['score'].mean(),
                        'recommended_filters': json.dumps({'price_filter': True}),
                        'fallback_strategies': json.dumps({'broaden_search': True}),
                        'avg_response_time': group_df['response_time'].mean(),
                        'usage_count': len(group_df),
                        'last_updated': datetime.now().isoformat()
                    }
                    matrix.append(matrix_entry)
        
        return matrix
    
    def _save_store_profile(self, profile: StoreProfile):
        """Save store profile to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO store_profiles (
                    store_id, product_count, price_range_min, price_range_max,
                    category_distribution, brand_distribution, material_distribution, color_distribution,
                    avg_response_time_baseline, avg_relevance_score_baseline,
                    price_filter_usage_rate, fallback_usage_rate, cache_hit_rate,
                    successful_query_patterns, problematic_query_patterns, recommended_improvements,
                    avg_price_coherence, avg_diversity_score, avg_conversion_potential,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.store_id,
                profile.product_count,
                profile.price_range[0],
                profile.price_range[1],
                json.dumps(profile.category_distribution),
                json.dumps(profile.brand_distribution),
                json.dumps(profile.material_distribution),
                json.dumps(profile.color_distribution),
                profile.avg_response_time_baseline,
                profile.avg_relevance_score_baseline,
                profile.price_filter_usage_rate,
                profile.fallback_usage_rate,
                profile.cache_hit_rate,
                json.dumps(profile.successful_query_patterns),
                json.dumps(profile.problematic_query_patterns),
                json.dumps(profile.recommended_improvements),
                profile.avg_price_coherence,
                profile.avg_diversity_score,
                profile.avg_conversion_potential,
                profile.last_updated.isoformat()
            ))
            conn.commit()
    
    def _save_query_patterns(self, patterns: List[QueryPattern]):
        """Save query patterns to database."""
        with sqlite3.connect(self.db_path) as conn:
            for pattern in patterns:
                conn.execute("""
                    INSERT OR REPLACE INTO query_patterns (
                        pattern_type, pattern_text, success_rate, avg_relevance_score,
                        total_usage, avg_response_time, price_filter_usage_rate,
                        fallback_usage_rate, complexity_score, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.pattern_type,
                    pattern.pattern_text,
                    pattern.success_rate,
                    pattern.avg_relevance_score,
                    pattern.total_usage,
                    pattern.avg_response_time,
                    pattern.price_filter_usage_rate,
                    pattern.fallback_usage_rate,
                    pattern.complexity_score,
                    pattern.last_updated.isoformat()
                ))
            conn.commit()
    
    def _save_intent_success_matrix(self, matrix: List[Dict[str, Any]]):
        """Save intent success matrix to database."""
        with sqlite3.connect(self.db_path) as conn:
            for entry in matrix:
                conn.execute("""
                    INSERT OR REPLACE INTO search_intent_success (
                        intent_type, query_template, success_score, recommended_filters,
                        fallback_strategies, avg_response_time, usage_count, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry['intent_type'],
                    entry['query_template'],
                    entry['success_score'],
                    entry['recommended_filters'],
                    entry['fallback_strategies'],
                    entry['avg_response_time'],
                    entry['usage_count'],
                    entry['last_updated']
                ))
            conn.commit()
    
    def _save_benchmark_history(self, df: pd.DataFrame, store_id: str):
        """Save benchmark results to history table."""
        with sqlite3.connect(self.db_path) as conn:
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT INTO benchmark_history (
                        store_id, query, score, response_time, result_count,
                        detected_intents, complexity_score, cache_hit,
                        price_filter_applied, fallback_used, avg_price_top5,
                        price_coherence, diversity_score, category_coverage,
                        conversion_potential, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    store_id,
                    row['query'],
                    row['score'],
                    row['response_time'],
                    row['result_count'],
                    row.get('detected_intents', '{}'),
                    row.get('complexity_score', 0.0),
                    row.get('cache_hit', False),
                    row.get('price_filter_applied', False),
                    row.get('fallback_used', False),
                    row.get('avg_price_top5', 0.0),
                    row.get('price_coherence', 0.0),
                    row.get('diversity_score', 0.0),
                    row.get('category_coverage', 0.0),
                    row.get('conversion_potential', 0.0),
                    row.get('timestamp', datetime.now().isoformat())
                ))
            conn.commit()
    
    def get_store_profile(self, store_id: str) -> Optional[StoreProfile]:
        """Retrieve store profile from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM store_profiles WHERE store_id = ?
            """, (store_id,))
            
            row = cursor.fetchone()
            if row:
                return StoreProfile(
                    store_id=row[1],
                    product_count=row[2],
                    price_range=(row[3], row[4]),
                    category_distribution=json.loads(row[5]),
                    brand_distribution=json.loads(row[6]),
                    material_distribution=json.loads(row[7]),
                    color_distribution=json.loads(row[8]),
                    avg_response_time_baseline=row[9],
                    avg_relevance_score_baseline=row[10],
                    price_filter_usage_rate=row[11],
                    fallback_usage_rate=row[12],
                    cache_hit_rate=row[13],
                    successful_query_patterns=json.loads(row[14]),
                    problematic_query_patterns=json.loads(row[15]),
                    recommended_improvements=json.loads(row[16]),
                    avg_price_coherence=row[17],
                    avg_diversity_score=row[18],
                    avg_conversion_potential=row[19],
                    created_at=datetime.fromisoformat(row[20]),
                    last_updated=datetime.fromisoformat(row[21])
                )
        
        return None
    
    def get_similar_stores(self, store_profile: StoreProfile, limit: int = 5) -> List[StoreProfile]:
        """Find similar stores based on profile characteristics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM store_profiles 
                WHERE store_id != ? 
                ORDER BY ABS(avg_relevance_score_baseline - ?) + 
                         ABS(avg_response_time_baseline - ?) +
                         ABS(price_filter_usage_rate - ?)
                LIMIT ?
            """, (
                store_profile.store_id,
                store_profile.avg_relevance_score_baseline,
                store_profile.avg_response_time_baseline,
                store_profile.price_filter_usage_rate,
                limit
            ))
            
            similar_stores = []
            for row in cursor.fetchall():
                similar_stores.append(StoreProfile(
                    store_id=row[1],
                    product_count=row[2],
                    price_range=(row[3], row[4]),
                    category_distribution=json.loads(row[5]),
                    brand_distribution=json.loads(row[6]),
                    material_distribution=json.loads(row[7]),
                    color_distribution=json.loads(row[8]),
                    avg_response_time_baseline=row[9],
                    avg_relevance_score_baseline=row[10],
                    price_filter_usage_rate=row[11],
                    fallback_usage_rate=row[12],
                    cache_hit_rate=row[13],
                    successful_query_patterns=json.loads(row[14]),
                    problematic_query_patterns=json.loads(row[15]),
                    recommended_improvements=json.loads(row[16]),
                    avg_price_coherence=row[17],
                    avg_diversity_score=row[18],
                    avg_conversion_potential=row[19],
                    created_at=datetime.fromisoformat(row[20]),
                    last_updated=datetime.fromisoformat(row[21])
                ))
            
            return similar_stores
    
    def generate_transfer_learning_recommendations(self, store_profile: StoreProfile) -> Dict[str, Any]:
        """Generate transfer learning recommendations for a new store."""
        similar_stores = self.get_similar_stores(store_profile)
        
        if not similar_stores:
            return {
                "message": "No similar stores found for transfer learning",
                "recommendations": []
            }
        
        # Aggregate recommendations from similar stores
        all_recommendations = []
        for store in similar_stores:
            all_recommendations.extend(store.recommended_improvements)
        
        # Count and rank recommendations
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # Get top recommendations
        top_recommendations = sorted(
            recommendation_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Calculate expected performance
        avg_similar_score = statistics.mean([s.avg_relevance_score_baseline for s in similar_stores])
        avg_similar_response_time = statistics.mean([s.avg_response_time_baseline for s in similar_stores])
        
        return {
            "similar_stores_count": len(similar_stores),
            "top_recommendations": [rec[0] for rec in top_recommendations],
            "expected_performance": {
                "relevance_score": avg_similar_score,
                "response_time": avg_similar_response_time,
                "confidence": min(0.9, len(similar_stores) * 0.2)
            },
            "transferable_patterns": self._extract_transferable_patterns(similar_stores)
        }
    
    def _extract_transferable_patterns(self, similar_stores: List[StoreProfile]) -> List[str]:
        """Extract transferable patterns from similar stores."""
        patterns = []
        
        for store in similar_stores:
            patterns.extend(store.successful_query_patterns)
        
        # Count and return most common patterns
        pattern_counts = {}
        for pattern in patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        return [pattern for pattern, count in sorted(
            pattern_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]]

def main():
    """Main function for processing benchmark results."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base Builder")
    parser.add_argument("--results", required=True, help="Benchmark results CSV file")
    parser.add_argument("--store-id", help="Store ID for the results")
    parser.add_argument("--db-path", default="search_knowledge_base.db", help="Database path")
    
    args = parser.parse_args()
    
    # Initialize knowledge base builder
    builder = KnowledgeBaseBuilder(args.db_path)
    
    # Process benchmark results
    store_profile = builder.process_benchmark_results(args.results, args.store_id)
    
    # Generate transfer learning recommendations
    recommendations = builder.generate_transfer_learning_recommendations(store_profile)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 KNOWLEDGE BASE BUILD SUMMARY")
    print("="*60)
    print(f"Store ID: {store_profile.store_id}")
    print(f"Product Count: {store_profile.product_count}")
    print(f"Price Range: €{store_profile.price_range[0]:.2f} - €{store_profile.price_range[1]:.2f}")
    print(f"Average Relevance Score: {store_profile.avg_relevance_score_baseline:.3f}")
    print(f"Average Response Time: {store_profile.avg_response_time_baseline:.3f}s")
    print(f"Price Filter Usage Rate: {store_profile.price_filter_usage_rate:.1%}")
    
    print(f"\n🎯 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(store_profile.recommended_improvements[:5], 1):
        print(f"{i}. {rec}")
    
    print(f"\n🔄 TRANSFER LEARNING:")
    print(f"Similar stores found: {recommendations['similar_stores_count']}")
    print(f"Expected relevance score: {recommendations['expected_performance']['relevance_score']:.3f}")
    print(f"Confidence: {recommendations['expected_performance']['confidence']:.1%}")
    
    print(f"\n📈 TRANSFERABLE PATTERNS:")
    for i, pattern in enumerate(recommendations['transferable_patterns'][:5], 1):
        print(f"{i}. {pattern}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main() 