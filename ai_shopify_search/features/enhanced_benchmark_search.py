#!/usr/bin/env python3
"""
Enhanced Search Quality Benchmark Script

This script provides comprehensive search quality testing with:
- Query categorization and pattern analysis
- Enhanced metrics collection
- Knowledge base building
- Transfer learning preparation
- Rate limiting and throttling for API protection
"""

import asyncio
import csv
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse
import aiohttp
import openai
from pathlib import Path
import statistics
import re
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_benchmark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_QUERIES = 100
DEFAULT_REQUEST_DELAY = 2.0
DEFAULT_BATCH_SIZE = 5
DEFAULT_RATE_LIMIT_WINDOW = 3600
DEFAULT_RATE_LIMIT_MAX_REQUESTS = 50
DEFAULT_CACHE_TTL = 3600
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5.0
DEFAULT_TIMEOUT = 30
DEFAULT_CONNECT_TIMEOUT = 10

# API Constants
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_ENDPOINT = "/api/ai-search"
DEFAULT_LIMIT = 25

# File Constants
DEFAULT_QUERIES_FILE = "benchmark_queries.csv"
DEFAULT_RESULTS_FILE = "enhanced_benchmark_results.csv"
DEFAULT_LOG_FILE = "enhanced_benchmark.log"

# Performance Constants
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 3600
DEFAULT_MAX_REQUESTS_PER_WINDOW = 50
DEFAULT_CACHE_TTL_SECONDS = 3600

# Error Messages
ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded for query: {query}"
ERROR_REQUEST_FAILED = "Request failed for query: {query}: {error}"
ERROR_CACHE_MISS = "Cache miss for query: {query}"

# Logging Context Keys
LOG_CONTEXT_QUERY = "query"
LOG_CONTEXT_STORE_ID = "store_id"
LOG_CONTEXT_BATCH_NUMBER = "batch_number"
LOG_CONTEXT_ENDPOINT = "endpoint"

# Rate limiting and throttling configuration
BENCHMARK_CONFIG = {
    "max_queries": DEFAULT_MAX_QUERIES,
    "request_delay": DEFAULT_REQUEST_DELAY,
    "batch_size": DEFAULT_BATCH_SIZE,
    "rate_limit_window": DEFAULT_RATE_LIMIT_WINDOW,
    "rate_limit_max_requests": DEFAULT_RATE_LIMIT_MAX_REQUESTS,
    "cache_ttl": DEFAULT_CACHE_TTL,
    "retry_attempts": DEFAULT_RETRY_ATTEMPTS,
    "retry_delay": DEFAULT_RETRY_DELAY,
}

# Query categorization patterns
QUERY_CATEGORIES = {
    "price_intent": [
        "goedkoop", "duur", "betaalbaar", "exclusief", "premium", "luxe", 
        "economisch", "voordelig", "korting", "uitverkoop", "clearance", 
        "discount", "aanbieding", "speciale prijs", "laagste prijs", 
        "beste deal", "goedkoopste", "duurste", "high-end", "top kwaliteit"
    ],
    "color_intent": [
        "zwart", "rood", "blauw", "wit", "groen", "geel", "paars", "oranje", 
        "grijs", "bruin", "beige", "roze", "lila", "turquoise", "marine", 
        "bordeaux", "goud", "zilver", "transparant", "metallic"
    ],
    "material_intent": [
        "leer", "katoen", "wol", "zijde", "denim", "linnen", "polyester", 
        "synthetisch", "kashmir", "cashmere", "angora", "alpaca", "merino", 
        "recycled", "gerecycled", "handgemaakt", "artisan", "crafted"
    ],
    "category_intent": [
        "schoenen", "jas", "shirt", "broek", "jurk", "trui", "hoodie", 
        "blazer", "accessoire", "tas", "sjaal", "muts", "handschoenen", 
        "riem", "sokken", "onderbroek", "bh", "lingerie", "zwemkleding"
    ],
    "size_intent": [
        "maat", "xs", "s", "m", "l", "xl", "xxl", "xxxl", "one size", 
        "universeel", "pasvorm", "fit", "slim fit", "regular fit", 
        "loose fit", "oversized", "petite", "plus size"
    ],
    "occasion_intent": [
        "werk", "feest", "sport", "casual", "bruiloft", "verjaardag", 
        "graduatie", "promotie", "sollicitatie", "interview", "vergadering", 
        "presentatie", "conferentie", "seminar", "workshop", "training", 
        "fitness", "hardlopen", "wandelen", "fietsen", "zwemmen", "tennis", 
        "voetbal", "basketbal", "volleybal", "badminton", "squash", "golf", 
        "skiën", "snowboarden", "surfen", "klimmen", "yoga", "pilates", 
        "dansen", "zumba", "crossfit", "krachttraining", "cardio"
    ],
    "brand_intent": [
        "urbanwear", "fashionista", "stylehub", "classicline", "elegance", 
        "sportflex", "trendify", "urban", "designer", "merk", "brand"
    ],
    "season_intent": [
        "winter", "zomer", "lente", "herfst", "seizoen", "season", 
        "wintercollectie", "zomercollectie", "lentecollectie", "herfstcollectie"
    ],
    "quality_intent": [
        "premium", "luxe", "exclusief", "handgemaakt", "artisan", "crafted", 
        "hoogwaardig", "kwaliteit", "duurzaam", "langdurig", "sterk", 
        "robuust", "comfortabel", "zacht", "soepel", "flexibel", "ademend", 
        "waterdicht", "winddicht", "warm", "koel", "licht", "zwaar", 
        "compact", "ruim", "practisch", "functioneel", "stijlvol", "elegant", 
        "chic", "modieus", "trendy", "hip", "cool", "awesome", "fantastisch", 
        "geweldig", "perfect", "uitstekend", "beste", "top", "super", "mega", 
        "ultra", "hyper", "extreem", "minimaal", "maximaal", "optimaal", 
        "ideaal", "perfect", "uitstekend", "beste keuze", "aanbevolen", 
        "populair", "favoriet", "best verkocht", "top rated", "hoogst gewaardeerd"
    ],
    "gender_intent": [
        "heren", "dames", "kinderen", "unisex", "man", "vrouw", "jongen", 
        "meisje", "baby", "tiener", "volwassen", "senior", "mama", "papa"
    ]
}

@dataclass
class EnhancedSearchResult:
    """Enhanced search result with additional metadata."""
    title: str
    price: float
    similarity: float
    tags: List[str]
    category: Optional[str] = None
    brand: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.title} (€{self.price:.2f}, sim: {self.similarity:.3f})"

@dataclass
class QueryAnalysis:
    """Analysis of a single query."""
    query: str
    detected_intents: Dict[str, List[str]]
    intent_confidence: Dict[str, float]
    complexity_score: float
    expected_difficulty: str  # easy, medium, hard

@dataclass
class QueryFacetMapping:
    """Mapping between query patterns and successful filters/facets."""
    query_pattern: str
    intent_type: str
    successful_filters: Dict[str, Any]
    successful_facets: Dict[str, Any]
    filter_effectiveness: float  # How much filters improved results
    facet_relevance: float  # How relevant facets were
    usage_count: int
    last_updated: datetime

@dataclass
class HistoricalTrend:
    """Historical performance trend for a store."""
    store_id: str
    metric_name: str
    baseline_value: float
    current_value: float
    trend_direction: str  # improving, declining, stable
    change_percentage: float
    confidence_level: float
    last_updated: datetime

@dataclass
class EnhancedBenchmarkResult:
    """Enhanced benchmark result with comprehensive metrics."""
    # Basic info
    query: str
    score: float
    response_time: float
    result_count: int
    
    # Query analysis
    query_analysis: QueryAnalysis
    
    # Performance metrics
    cache_hit: bool
    embedding_generation_time: Optional[float]
    price_filter_applied: bool
    fallback_used: bool
    
    # Quality metrics
    avg_price_top5: float
    price_coherence: float  # How well prices match query intent
    diversity_score: float  # How diverse are the results
    category_coverage: float  # How many categories are represented
    
    # Business metrics
    conversion_potential: float  # Estimated conversion likelihood
    price_range_coverage: float  # Breadth of price range
    
    # User experience
    query_correction_applied: bool
    suggestions_provided: int
    facets_generated: int
    
    # Enhanced categorisation
    primary_intent: str  # Main intent category
    secondary_intents: List[str]  # Additional intent categories
    intent_confidence_scores: Dict[str, float]  # Confidence per intent
    
    # Automatic relevance scoring
    semantic_relevance: float  # How semantically relevant results are
    contextual_relevance: float  # How contextually relevant results are
    user_intent_alignment: float  # How well results align with user intent
    
    # Facet and filter mapping
    applied_filters: Dict[str, Any]
    generated_facets: Dict[str, Any]
    filter_effectiveness: float
    facet_relevance: float
    
    # Historical comparison
    baseline_comparison: Optional[Dict[str, float]]  # Comparison with historical baseline
    trend_analysis: Optional[Dict[str, str]]  # Trend direction and confidence
    
    # Results
    titles_top5: str
    gpt_reasoning: str
    
    # Metadata
    timestamp: datetime
    store_id: Optional[str] = None

class BenchmarkRateLimiter:
    """Rate limiter specifically for benchmark operations."""
    
    def __init__(self, max_requests: int = DEFAULT_MAX_REQUESTS_PER_WINDOW, window_seconds: int = DEFAULT_RATE_LIMIT_WINDOW_SECONDS):
        """
        Initialize benchmark rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Rate limit window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_timestamps = []
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self) -> Tuple[bool, float]:
        """
        Check if we can make another request.
        
        Returns:
            Tuple of (can_proceed, wait_time)
        """
        async with self.lock:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            # Remove old timestamps
            self.request_timestamps = [ts for ts in self.request_timestamps if ts > window_start]
            
            # Check if we can make another request
            if len(self.request_timestamps) < self.max_requests:
                self.request_timestamps.append(current_time)
                return True, 0.0
            
            # Calculate wait time
            oldest_timestamp = min(self.request_timestamps)
            wait_time = window_start + self.window_seconds - current_time
            
            return False, max(0.0, wait_time)
    
    async def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        can_proceed, wait_time = await self.check_rate_limit()
        if not can_proceed:
            logger.warning(f"⚠️ Rate limit exceeded, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
            # Try again after waiting
            await self.check_rate_limit()

class BenchmarkCache:
    """Simple in-memory cache for benchmark results."""
    
    def __init__(self, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS):
        """
        Initialize benchmark cache.
        
        Args:
            ttl_seconds: Time to live for cached items in seconds
        """
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_cache_key(self, query: str, endpoint: str) -> str:
        """
        Generate cache key for query and endpoint.
        
        Args:
            query: Search query
            endpoint: API endpoint
            
        Returns:
            MD5 hash of the cache key
        """
        return hashlib.md5(f"{query}:{endpoint}".encode()).hexdigest()
    
    def get(self, query: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result.
        
        Args:
            query: Search query
            endpoint: API endpoint
            
        Returns:
            Cached data if available and not expired, None otherwise
        """
        key = self._generate_cache_key(query, endpoint)
        if key in self.cache:
            timestamp, data = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return data
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, query: str, endpoint: str, data: Dict[str, Any]) -> None:
        """
        Set cached result.
        
        Args:
            query: Search query
            endpoint: API endpoint
            data: Data to cache
        """
        key = self._generate_cache_key(query, endpoint)
        self.cache[key] = (time.time(), data)
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()

class QueryAnalyzer:
    """Analyzes queries for intent detection and categorization."""
    
    def __init__(self):
        """Initialize query analyzer with predefined categories."""
        self.categories = QUERY_CATEGORIES
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a query for intents and complexity.
        
        Args:
            query: Query string to analyze
            
        Returns:
            QueryAnalysis object with detected intents and complexity
        """
        query_lower = query.lower()
        
        # Detect intents for each category
        detected_intents = self._detect_intents(query_lower)
        intent_confidence = self._calculate_intent_confidence(detected_intents)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(query, detected_intents)
        
        # Determine expected difficulty
        expected_difficulty = self._determine_difficulty(complexity_score)
        
        return QueryAnalysis(
            query=query,
            detected_intents=detected_intents,
            intent_confidence=intent_confidence,
            complexity_score=complexity_score,
            expected_difficulty=expected_difficulty
        )
    
    def _detect_intents(self, query_lower: str) -> Dict[str, List[str]]:
        """
        Detect intents for each category.
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Dictionary of detected intents by category
        """
        detected_intents = {}
        
        for category, keywords in self.categories.items():
            matches = []
            for keyword in keywords:
                if keyword in query_lower:
                    matches.append(keyword)
            
            if matches:
                detected_intents[category] = matches
        
        return detected_intents
    
    def _calculate_intent_confidence(self, detected_intents: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Calculate confidence scores for detected intents.
        
        Args:
            detected_intents: Dictionary of detected intents
            
        Returns:
            Dictionary of confidence scores by category
        """
        intent_confidence = {}
        
        for category, matches in detected_intents.items():
            # Calculate confidence based on number and specificity of matches
            intent_confidence[category] = min(1.0, len(matches) * 0.3)
        
        return intent_confidence
    
    def _calculate_complexity(self, query: str, intents: Dict[str, List[str]]) -> float:
        """
        Calculate query complexity score.
        
        Args:
            query: Query string
            intents: Detected intents
            
        Returns:
            Complexity score between 0 and 1
        """
        base_complexity = len(query.split()) / 10.0  # Normalize by word count
        
        # Add complexity for multiple intents
        intent_complexity = len(intents) * 0.2
        
        # Add complexity for specific patterns
        pattern_complexity = self._calculate_pattern_complexity(query)
        
        total_complexity = base_complexity + intent_complexity + pattern_complexity
        return min(1.0, total_complexity)
    
    def _calculate_pattern_complexity(self, query: str) -> float:
        """
        Calculate complexity based on query patterns.
        
        Args:
            query: Query string
            
        Returns:
            Pattern complexity score
        """
        pattern_complexity = 0.0
        
        if re.search(r'\d+', query):  # Numbers
            pattern_complexity += 0.1
        if re.search(r'[€$]', query):  # Currency
            pattern_complexity += 0.1
        if re.search(r'[A-Z]{2,}', query):  # Acronyms
            pattern_complexity += 0.1
        if re.search(r'[^\w\s]', query):  # Special characters
            pattern_complexity += 0.1
        
        return pattern_complexity
    
    def _determine_difficulty(self, complexity_score: float) -> str:
        """
        Determine expected difficulty based on complexity score.
        
        Args:
            complexity_score: Calculated complexity score
            
        Returns:
            Difficulty level: 'easy', 'medium', or 'hard'
        """
        if complexity_score < 0.3:
            return "easy"
        elif complexity_score < 0.7:
            return "medium"
        else:
            return "hard"
    
    def get_primary_intent(self, detected_intents: Dict[str, List[str]]) -> str:
        """
        Get the primary intent from detected intents.
        
        Args:
            detected_intents: Dictionary of detected intents
            
        Returns:
            Primary intent category
        """
        if not detected_intents:
            return "general"
        
        # Sort by number of matches (descending)
        sorted_intents = sorted(detected_intents.items(), key=lambda x: len(x[1]), reverse=True)
        return sorted_intents[0][0]
    
    def get_secondary_intents(self, detected_intents: Dict[str, List[str]], primary_intent: str) -> List[str]:
        """
        Get secondary intents (all except primary).
        
        Args:
            detected_intents: Dictionary of detected intents
            primary_intent: Primary intent category
            
        Returns:
            List of secondary intent categories
        """
        return [intent for intent in detected_intents.keys() if intent != primary_intent]

class HistoricalTrendAnalyzer:
    """Analyzes historical trends and baseline comparisons."""
    
    def __init__(self, db_path: str = "../data/databases/search_knowledge_base.db"):
        self.db_path = db_path
    
    def get_store_baseline(self, store_id: str) -> Optional[Dict[str, float]]:
        """Get baseline metrics for a store."""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT avg_relevance_score_baseline, avg_response_time_baseline,
                           price_filter_usage_rate, fallback_usage_rate, cache_hit_rate
                    FROM store_profiles WHERE store_id = ?
                """, (store_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "avg_relevance_score": row[0],
                        "avg_response_time": row[1],
                        "price_filter_usage_rate": row[2],
                        "fallback_usage_rate": row[3],
                        "cache_hit_rate": row[4]
                    }
        except Exception as e:
            logger.warning(f"Could not load baseline for store {store_id}: {e}")
        
        return None
    
    def calculate_trends(self, current_metrics: Dict[str, float], baseline: Dict[str, float]) -> Dict[str, HistoricalTrend]:
        """Calculate trends between current and baseline metrics."""
        trends = {}
        
        for metric_name, current_value in current_metrics.items():
            if metric_name in baseline:
                baseline_value = baseline[metric_name]
                
                if baseline_value > 0:
                    change_percentage = ((current_value - baseline_value) / baseline_value) * 100
                    
                    # Determine trend direction
                    if change_percentage > 5:
                        trend_direction = "improving"
                    elif change_percentage < -5:
                        trend_direction = "declining"
                    else:
                        trend_direction = "stable"
                    
                    # Calculate confidence based on magnitude of change
                    confidence_level = min(1.0, abs(change_percentage) / 50.0)
                    
                    trends[metric_name] = HistoricalTrend(
                        store_id="current_store",
                        metric_name=metric_name,
                        baseline_value=baseline_value,
                        current_value=current_value,
                        trend_direction=trend_direction,
                        change_percentage=change_percentage,
                        confidence_level=confidence_level,
                        last_updated=datetime.now()
                    )
        
        return trends

class FacetFilterMapper:
    """Maps query patterns to successful filters and facets."""
    
    def __init__(self):
        self.facet_mappings = {
            "price_intent": {
                "filters": ["price_range"],
                "facets": ["price_ranges", "brands", "categories"],
                "effectiveness_threshold": 0.7
            },
            "color_intent": {
                "filters": ["color"],
                "facets": ["colors", "materials", "categories"],
                "effectiveness_threshold": 0.8
            },
            "material_intent": {
                "filters": ["material"],
                "facets": ["materials", "colors", "brands"],
                "effectiveness_threshold": 0.75
            },
            "category_intent": {
                "filters": ["category"],
                "facets": ["categories", "brands", "price_ranges"],
                "effectiveness_threshold": 0.8
            },
            "brand_intent": {
                "filters": ["brand"],
                "facets": ["brands", "categories", "price_ranges"],
                "effectiveness_threshold": 0.9
            },
            "occasion_intent": {
                "filters": ["occasion", "category"],
                "facets": ["categories", "styles", "price_ranges"],
                "effectiveness_threshold": 0.7
            }
        }
    
    def map_query_to_facets(self, query_analysis: QueryAnalysis, search_response: Dict[str, Any]) -> Dict[str, Any]:
        """Map query to appropriate facets and filters."""
        primary_intent = query_analysis.detected_intents.get(list(query_analysis.detected_intents.keys())[0] if query_analysis.detected_intents else "general", [])
        
        mapping = {
            "applied_filters": {},
            "generated_facets": {},
            "filter_effectiveness": 0.0,
            "facet_relevance": 0.0
        }
        
        # Find best matching intent type
        best_intent = None
        best_confidence = 0.0
        
        for intent_type, keywords in query_analysis.detected_intents.items():
            if intent_type in self.facet_mappings:
                confidence = query_analysis.intent_confidence.get(intent_type, 0.0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent_type
        
        if best_intent and best_intent in self.facet_mappings:
            intent_mapping = self.facet_mappings[best_intent]
            
            # Map to filters
            mapping["applied_filters"] = {
                "filters": intent_mapping["filters"],
                "intent_type": best_intent,
                "confidence": best_confidence
            }
            
            # Map to facets
            facets = search_response.get("facets", {})
            mapping["generated_facets"] = {
                "suggested_facets": intent_mapping["facets"],
                "available_facets": list(facets.keys()),
                "intent_type": best_intent
            }
            
            # Calculate effectiveness
            mapping["filter_effectiveness"] = self._calculate_filter_effectiveness(
                search_response, intent_mapping["effectiveness_threshold"]
            )
            
            mapping["facet_relevance"] = self._calculate_facet_relevance(
                facets, intent_mapping["facets"]
            )
        
        return mapping
    
    def _calculate_filter_effectiveness(self, search_response: Dict[str, Any], threshold: float) -> float:
        """Calculate how effective filters were."""
        price_filter = search_response.get("price_filter", {})
        
        if price_filter.get("applied", False):
            # If price filter was applied and results are good, consider it effective
            results = search_response.get("results", [])
            if len(results) > 0:
                avg_similarity = statistics.mean([r.get("similarity", 0) for r in results[:5]])
                return min(1.0, avg_similarity / threshold)
        
        return 0.0
    
    def _calculate_facet_relevance(self, available_facets: Dict[str, Any], suggested_facets: List[str]) -> float:
        """Calculate how relevant the generated facets are."""
        if not available_facets:
            return 0.0
        
        # Count how many suggested facets are available
        available_count = sum(1 for facet in suggested_facets if facet in available_facets)
        return available_count / len(suggested_facets) if suggested_facets else 0.0

class AutomaticRelevanceScorer:
    """Provides automatic relevance scoring without GPT."""
    
    def __init__(self):
        self.relevance_weights = {
            "similarity": 0.4,
            "price_coherence": 0.2,
            "category_match": 0.2,
            "diversity": 0.1,
            "result_count": 0.1
        }
    
    def calculate_semantic_relevance(self, results: List[EnhancedSearchResult], query_analysis: QueryAnalysis) -> float:
        """Calculate semantic relevance based on similarity scores and intent matching."""
        if not results:
            return 0.0
        
        # Base relevance on similarity scores
        similarities = [r.similarity for r in results[:5]]
        avg_similarity = statistics.mean(similarities)
        
        # Boost for intent matching
        intent_boost = 0.0
        for intent_type, keywords in query_analysis.detected_intents.items():
            for result in results[:5]:
                for keyword in keywords:
                    if keyword.lower() in result.title.lower():
                        intent_boost += 0.1
                        break
        
        return min(1.0, avg_similarity + intent_boost)
    
    def calculate_contextual_relevance(self, results: List[EnhancedSearchResult], query_analysis: QueryAnalysis) -> float:
        """Calculate contextual relevance based on price, category, and other contextual factors."""
        if not results:
            return 0.0
        
        contextual_score = 0.0
        
        # Price coherence
        prices = [r.price for r in results[:5]]
        price_coherence = self._calculate_price_coherence(prices, query_analysis)
        contextual_score += price_coherence * 0.4
        
        # Category relevance
        category_relevance = self._calculate_category_relevance(results, query_analysis)
        contextual_score += category_relevance * 0.3
        
        # Diversity (not too similar results)
        diversity = self._calculate_diversity_score(results)
        contextual_score += diversity * 0.3
        
        return contextual_score
    
    def calculate_user_intent_alignment(self, results: List[EnhancedSearchResult], query_analysis: QueryAnalysis) -> float:
        """Calculate how well results align with user intent."""
        if not results:
            return 0.0
        
        alignment_score = 0.0
        
        # Check if results match detected intents
        for intent_type, keywords in query_analysis.detected_intents.items():
            intent_matches = 0
            for result in results[:5]:
                for keyword in keywords:
                    if keyword.lower() in result.title.lower() or keyword.lower() in " ".join(result.tags).lower():
                        intent_matches += 1
                        break
            
            intent_score = intent_matches / len(results[:5])
            alignment_score += intent_score * query_analysis.intent_confidence.get(intent_type, 0.0)
        
        return min(1.0, alignment_score)
    
    def _calculate_price_coherence(self, prices: List[float], query_analysis: QueryAnalysis) -> float:
        """Calculate price coherence with query intent."""
        if "price_intent" not in query_analysis.detected_intents:
            return 0.5
        
        avg_price = statistics.mean(prices)
        price_intents = query_analysis.detected_intents["price_intent"]
        
        if any(word in ["goedkoop", "betaalbaar"] for word in price_intents):
            return 1.0 if avg_price <= 100 else 0.5 if avg_price <= 200 else 0.0
        elif any(word in ["duur", "exclusief", "premium"] for word in price_intents):
            return 1.0 if avg_price >= 200 else 0.5 if avg_price >= 100 else 0.0
        
        return 0.5
    
    def _calculate_category_relevance(self, results: List[EnhancedSearchResult], query_analysis: QueryAnalysis) -> float:
        """Calculate category relevance."""
        if "category_intent" not in query_analysis.detected_intents:
            return 0.5
        
        category_keywords = query_analysis.detected_intents["category_intent"]
        category_matches = 0
        
        for result in results[:5]:
            for keyword in category_keywords:
                if keyword.lower() in result.title.lower() or keyword.lower() in " ".join(result.tags).lower():
                    category_matches += 1
                    break
        
        return category_matches / len(results[:5])
    
    def _calculate_diversity_score(self, results: List[EnhancedSearchResult]) -> float:
        """Calculate diversity score."""
        if len(results) < 2:
            return 0.0
        
        categories = set(r.category for r in results[:5] if r.category)
        brands = set(r.brand for r in results[:5] if r.brand)
        
        diversity = (len(categories) + len(brands)) / (len(results[:5]) * 2)
        return min(1.0, diversity)

class EnhancedSearchBenchmarker:
    """Enhanced benchmark class with comprehensive analysis and rate limiting."""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL, headless: bool = False, store_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        self.store_id = store_id
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Load configuration
        self.config = config or BENCHMARK_CONFIG.copy()
        
        # Initialize components
        self.query_analyzer = QueryAnalyzer()
        self.historical_analyzer = HistoricalTrendAnalyzer()
        self.facet_mapper = FacetFilterMapper()
        self.relevance_scorer = AutomaticRelevanceScorer()
        
        # Initialize rate limiting and caching
        self.rate_limiter = BenchmarkRateLimiter(
            max_requests=self.config["rate_limit_max_requests"],
            window_seconds=self.config["rate_limit_window"]
        )
        self.cache = BenchmarkCache(ttl_seconds=self.config["cache_ttl"])
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "cached_requests": 0,
            "rate_limited_requests": 0,
            "failed_requests": 0,
            "total_wait_time": 0.0,
            "start_time": None,
            "end_time": None
        }
        
        # Initialize OpenAI client
        try:
            openai.api_key = self._get_openai_key()
            self.openai_client = openai.AsyncOpenAI()
            logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            raise
    
    def _get_openai_key(self) -> str:
        """Get OpenAI API key from environment or config."""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            # Try to read from config file
            config_file = Path('ai_shopify_search/config.py')
            if config_file.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_file)
                config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config)
                api_key = getattr(config, 'OPENAI_API_KEY', None)
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or config")
        
        return api_key
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def execute_search(self, query: str, endpoint: str = DEFAULT_ENDPOINT, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        """Execute a single search query with enhanced tracking, rate limiting, and caching."""
        self.stats["total_requests"] += 1
        
        # Check cache first
        cached_result = self.cache.get(query, endpoint)
        if cached_result:
            self.stats["cached_requests"] += 1
            if not self.headless:
                logger.info(f"💾 Cache hit for query: '{query}'")
            return cached_result
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}{endpoint}"
        params = {
            "query": query,
            "limit": limit,
            "page": 1
        }
        
        start_time = time.time()
        embedding_start = None
        embedding_time = None
        
        # Retry logic
        for attempt in range(self.config["retry_attempts"]):
            try:
                async with self.session.get(url, params=params) as response:
                    response_time = time.time() - start_time
                    
                    if response.status != 200:
                        logger.error(f"❌ Search failed for query '{query}': HTTP {response.status} (attempt {attempt + 1})")
                        if attempt < self.config["retry_attempts"] - 1:
                            await asyncio.sleep(self.config["retry_delay"])
                            continue
                        
                        self.stats["failed_requests"] += 1
                        return {
                            "error": f"HTTP {response.status}",
                            "response_time": response_time,
                            "results": [],
                            "cache_hit": False,
                            "embedding_generation_time": None
                        }
                    
                    data = await response.json()
                    
                    # Extract timing information if available
                    if "metadata" in data and "timing" in data["metadata"]:
                        timing = data["metadata"]["timing"]
                        embedding_time = timing.get("embedding_generation_time")
                    
                    result = {
                        "response_time": response_time,
                        "results": data.get('results', []),
                        "price_filter": data.get('price_filter', {}),
                        "search_suggestions": data.get('search_suggestions'),
                        "facets": data.get('facets', {}),
                        "count": data.get('count', 0),
                        "cache_hit": data.get('cache_hit', False),
                        "embedding_generation_time": embedding_time
                    }
                    
                    # Cache the result
                    self.cache.set(query, endpoint, result)
                    
                    if not self.headless:
                        logger.info(f"🔍 Query: '{query}' → {len(data.get('results', []))} results in {response_time:.3f}s")
                    
                    return result
                    
            except Exception as e:
                logger.error(f"❌ Search error for query '{query}': {e} (attempt {attempt + 1})")
                if attempt < self.config["retry_attempts"] - 1:
                    await asyncio.sleep(self.config["retry_delay"])
                    continue
                
                self.stats["failed_requests"] += 1
                return {
                    "error": str(e),
                    "response_time": time.time() - start_time,
                    "results": [],
                    "cache_hit": False,
                    "embedding_generation_time": None
                }
    
    def parse_enhanced_results(self, results: List[Dict[str, Any]]) -> List[EnhancedSearchResult]:
        """
        Parse search results with enhanced metadata extraction.
        
        Args:
            results: List of raw search results
            
        Returns:
            List of EnhancedSearchResult objects
        """
        enhanced_results = []
        
        for result in results:
            try:
                # Extract basic info
                title = result.get('title', 'Unknown')
                price = float(result.get('price', 0))
                similarity = float(result.get('similarity', 0))
                tags = result.get('tags', [])
                
                # Extract metadata from tags using helper
                metadata = self._extract_metadata_from_tags(tags)
                
                enhanced_results.append(EnhancedSearchResult(
                    title=title,
                    price=price,
                    similarity=similarity,
                    tags=tags,
                    category=metadata['category'],
                    brand=metadata['brand'],
                    material=metadata['material'],
                    color=metadata['color']
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Failed to parse result: {e}")
                continue
        
        return enhanced_results
    
    def _extract_metadata_from_tags(self, tags: List[str]) -> Dict[str, Optional[str]]:
        """
        Extract metadata from tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Dictionary with extracted metadata
        """
        return {
            'category': self._extract_category(tags),
            'brand': self._extract_brand(tags),
            'material': self._extract_material(tags),
            'color': self._extract_color(tags)
        }
    
    def _extract_category(self, tags: List[str]) -> Optional[str]:
        """
        Extract category from tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Extracted category or None
        """
        category_keywords = ["schoenen", "jas", "shirt", "broek", "jurk", "trui", "hoodie", "blazer", "accessoire", "tas"]
        for tag in tags:
            if tag.lower() in category_keywords:
                return tag
        return None
    
    def _extract_brand(self, tags: List[str]) -> Optional[str]:
        """
        Extract brand from tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Extracted brand or None
        """
        brand_keywords = ["urbanwear", "fashionista", "stylehub", "classicline", "elegance", "sportflex", "trendify"]
        for tag in tags:
            if tag.lower() in brand_keywords:
                return tag
        return None
    
    def _extract_material(self, tags: List[str]) -> Optional[str]:
        """
        Extract material from tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Extracted material or None
        """
        material_keywords = ["leer", "katoen", "wol", "zijde", "denim", "linnen", "polyester", "synthetisch", "kashmir"]
        for tag in tags:
            if tag.lower() in material_keywords:
                return tag
        return None
    
    def _extract_color(self, tags: List[str]) -> Optional[str]:
        """
        Extract color from tags.
        
        Args:
            tags: List of tags
            
        Returns:
            Extracted color or None
        """
        color_keywords = ["zwart", "rood", "blauw", "wit", "groen", "geel", "paars", "oranje", "grijs", "bruin", "beige"]
        for tag in tags:
            if tag.lower() in color_keywords:
                return tag
        return None
    
    def calculate_enhanced_metrics(self, results: List[EnhancedSearchResult], query_analysis: QueryAnalysis) -> Dict[str, float]:
        """Calculate comprehensive metrics for search results."""
        if not results:
            return {
                "avg_price_top5": 0.0,
                "price_coherence": 0.0,
                "diversity_score": 0.0,
                "category_coverage": 0.0,
                "conversion_potential": 0.0,
                "price_range_coverage": 0.0
            }
        
        top5 = results[:5]
        
        # Basic metrics
        prices = [r.price for r in top5]
        avg_price_top5 = statistics.mean(prices)
        price_range_coverage = (max(prices) - min(prices)) / max(prices) if max(prices) > 0 else 0.0
        
        # Price coherence (how well prices match query intent)
        price_coherence = self._calculate_price_coherence(prices, query_analysis)
        
        # Diversity score (how diverse are the results)
        diversity_score = self._calculate_diversity_score(top5)
        
        # Category coverage
        categories = set(r.category for r in top5 if r.category)
        category_coverage = len(categories) / 5.0  # Normalize to 0-1
        
        # Conversion potential (estimated likelihood of conversion)
        conversion_potential = self._calculate_conversion_potential(top5, query_analysis)
        
        return {
            "avg_price_top5": avg_price_top5,
            "price_coherence": price_coherence,
            "diversity_score": diversity_score,
            "category_coverage": category_coverage,
            "conversion_potential": conversion_potential,
            "price_range_coverage": price_range_coverage
        }
    
    def _calculate_price_coherence(self, prices: List[float], query_analysis: QueryAnalysis) -> float:
        """Calculate how well prices match query intent."""
        if "price_intent" not in query_analysis.detected_intents:
            return 0.5  # Neutral if no price intent detected
        
        price_intents = query_analysis.detected_intents["price_intent"]
        avg_price = statistics.mean(prices)
        
        # Define price ranges for different intents
        if any(word in ["goedkoop", "betaalbaar", "economisch"] for word in price_intents):
            # Budget: 0-100
            if avg_price <= 100:
                return 1.0
            elif avg_price <= 200:
                return 0.5
            else:
                return 0.0
        elif any(word in ["duur", "exclusief", "premium", "luxe"] for word in price_intents):
            # Premium: 200+
            if avg_price >= 200:
                return 1.0
            elif avg_price >= 100:
                return 0.5
            else:
                return 0.0
        else:
            return 0.5  # Neutral for other price intents
    
    def _calculate_diversity_score(self, results: List[EnhancedSearchResult]) -> float:
        """Calculate diversity score based on categories, brands, materials, colors."""
        if not results:
            return 0.0
        
        categories = set(r.category for r in results if r.category)
        brands = set(r.brand for r in results if r.brand)
        materials = set(r.material for r in results if r.material)
        colors = set(r.color for r in results if r.color)
        
        # Calculate diversity as average of unique attributes
        diversity_factors = [
            len(categories) / len(results),
            len(brands) / len(results),
            len(materials) / len(results),
            len(colors) / len(results)
        ]
        
        return statistics.mean(diversity_factors)
    
    def _calculate_conversion_potential(self, results: List[EnhancedSearchResult], query_analysis: QueryAnalysis) -> float:
        """Calculate estimated conversion potential."""
        if not results:
            return 0.0
        
        # Base conversion potential on similarity scores
        avg_similarity = statistics.mean([r.similarity for r in results])
        
        # Adjust based on query complexity (simpler queries might convert better)
        complexity_factor = 1.0 - query_analysis.complexity_score * 0.3
        
        # Adjust based on price coherence
        price_coherence = self._calculate_price_coherence([r.price for r in results], query_analysis)
        
        # Combine factors
        conversion_potential = avg_similarity * complexity_factor * (0.7 + price_coherence * 0.3)
        
        return min(1.0, conversion_potential)
    
    async def score_relevance_with_gpt(self, query: str, top_results: List[EnhancedSearchResult]) -> Tuple[float, str]:
        """Score search relevance using GPT-4o-mini with enhanced context."""
        if not top_results:
            return 0.0, "No results to score"
        
        # Prepare enhanced results for GPT
        results_text = "\n".join([
            f"{i+1}. {result.title} (€{result.price:.2f}, sim: {result.similarity:.3f}, "
            f"cat: {result.category or 'N/A'}, brand: {result.brand or 'N/A'})"
            for i, result in enumerate(top_results[:5])
        ])
        
        prompt = f"""
Je bent een expert in e-commerce search kwaliteit. Beoordeel hoe goed de zoekresultaten matchen met de intentie van de gebruiker.

QUERY: "{query}"

TOP 5 RESULTATEN:
{results_text}

BEOORDELING:
- Score van 0.0 tot 1.0 (1.0 = perfecte match)
- Overweeg: relevantie, prijs, product type, kwaliteit van resultaten, diversiteit
- Geef een korte uitleg van je score

Antwoord in JSON formaat:
{{
    "score": 0.85,
    "reasoning": "De resultaten matchen goed met de query. Alle producten zijn schoenen, prijzen zijn redelijk, en de similarity scores zijn hoog."
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(content)
                score = float(result.get('score', 0.0))
                reasoning = result.get('reasoning', 'No reasoning provided')
                
                # Validate score range
                score = max(0.0, min(1.0, score))
                
                return score, reasoning
                
            except json.JSONDecodeError:
                # Fallback: try to extract score from text
                score_match = re.search(r'["\']?score["\']?\s*:\s*([0-9]*\.?[0-9]+)', content)
                if score_match:
                    score = float(score_match.group(1))
                    score = max(0.0, min(1.0, score))
                    return score, content
                else:
                    logger.warning(f"⚠️ Could not parse GPT response: {content}")
                    return 0.5, "Failed to parse GPT response"
                    
        except Exception as e:
            logger.error(f"❌ GPT scoring failed: {e}")
            return 0.5, f"GPT error: {e}"
    
    async def benchmark_query(self, query: str, endpoint: str = DEFAULT_ENDPOINT) -> EnhancedBenchmarkResult:
        """Execute full enhanced benchmark for a single query."""
        # Analyze query first
        query_analysis = self.query_analyzer.analyze_query(query)
        
        # Execute search
        search_response = await self.execute_search(query, endpoint)
        
        if "error" in search_response:
            return EnhancedBenchmarkResult(
                query=query,
                score=0.0,
                response_time=search_response["response_time"],
                result_count=0,
                query_analysis=query_analysis,
                cache_hit=False,
                embedding_generation_time=search_response.get("embedding_generation_time"),
                price_filter_applied=False,
                fallback_used=False,
                avg_price_top5=0.0,
                price_coherence=0.0,
                diversity_score=0.0,
                category_coverage=0.0,
                conversion_potential=0.0,
                price_range_coverage=0.0,
                query_correction_applied=False,
                suggestions_provided=0,
                facets_generated=0,
                # Enhanced categorisation
                primary_intent="general",
                secondary_intents=[],
                intent_confidence_scores={},
                # Automatic relevance scoring
                semantic_relevance=0.0,
                contextual_relevance=0.0,
                user_intent_alignment=0.0,
                # Facet and filter mapping
                applied_filters={},
                generated_facets={},
                filter_effectiveness=0.0,
                facet_relevance=0.0,
                # Historical comparison
                baseline_comparison=None,
                trend_analysis=None,
                titles_top5="",
                gpt_reasoning=f"Search failed: {search_response['error']}",
                timestamp=datetime.now(),
                store_id=self.store_id
            )
        
        # Parse enhanced results
        results = self.parse_enhanced_results(search_response["results"])
        
        # Enhanced categorisation
        primary_intent = self.query_analyzer.get_primary_intent(query_analysis.detected_intents)
        secondary_intents = self.query_analyzer.get_secondary_intents(query_analysis.detected_intents, primary_intent)
        
        # Automatic relevance scoring
        semantic_relevance = self.relevance_scorer.calculate_semantic_relevance(results, query_analysis)
        contextual_relevance = self.relevance_scorer.calculate_contextual_relevance(results, query_analysis)
        user_intent_alignment = self.relevance_scorer.calculate_user_intent_alignment(results, query_analysis)
        
        # Facet and filter mapping
        facet_mapping = self.facet_mapper.map_query_to_facets(query_analysis, search_response)
        
        # Historical comparison
        baseline_comparison = None
        trend_analysis = None
        if self.store_id:
            baseline = self.historical_analyzer.get_store_baseline(self.store_id)
            if baseline:
                current_metrics = {
                    "avg_relevance_score": semantic_relevance,
                    "avg_response_time": search_response["response_time"],
                    "price_filter_usage_rate": 1.0 if search_response.get("price_filter", {}).get("applied", False) else 0.0
                }
                trends = self.historical_analyzer.calculate_trends(current_metrics, baseline)
                baseline_comparison = {name: trend.current_value for name, trend in trends.items()}
                trend_analysis = {name: trend.trend_direction for name, trend in trends.items()}
        
        # Score with GPT (fallback to automatic scoring if GPT fails)
        try:
            score, reasoning = await self.score_relevance_with_gpt(query, results)
        except Exception as e:
            logger.warning(f"GPT scoring failed, using automatic scoring: {e}")
            score = (semantic_relevance + contextual_relevance + user_intent_alignment) / 3
            reasoning = f"Automatic scoring: semantic={semantic_relevance:.3f}, contextual={contextual_relevance:.3f}, alignment={user_intent_alignment:.3f}"
        
        # Calculate enhanced metrics
        metrics = self.calculate_enhanced_metrics(results, query_analysis)
        
        # Prepare titles string
        titles_top5 = " | ".join([r.title for r in results[:5]])
        
        # Extract additional info
        price_filter = search_response.get("price_filter", {})
        search_suggestions = search_response.get("search_suggestions", {})
        facets = search_response.get("facets", {})
        
        return EnhancedBenchmarkResult(
            query=query,
            score=score,
            response_time=search_response["response_time"],
            result_count=len(results),
            query_analysis=query_analysis,
            cache_hit=search_response.get("cache_hit", False),
            embedding_generation_time=search_response.get("embedding_generation_time"),
            price_filter_applied=price_filter.get("applied", False),
            fallback_used=price_filter.get("fallback_used", False),
            avg_price_top5=metrics["avg_price_top5"],
            price_coherence=metrics["price_coherence"],
            diversity_score=metrics["diversity_score"],
            category_coverage=metrics["category_coverage"],
            conversion_potential=metrics["conversion_potential"],
            price_range_coverage=metrics["price_range_coverage"],
            query_correction_applied=bool(search_suggestions.get("correction_applied", False) if search_suggestions else False),
            suggestions_provided=len(search_suggestions.get("suggestions", []) if search_suggestions else []),
            facets_generated=len(facets),
            # Enhanced categorisation
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            intent_confidence_scores=query_analysis.intent_confidence,
            # Automatic relevance scoring
            semantic_relevance=semantic_relevance,
            contextual_relevance=contextual_relevance,
            user_intent_alignment=user_intent_alignment,
            # Facet and filter mapping
            applied_filters=facet_mapping["applied_filters"],
            generated_facets=facet_mapping["generated_facets"],
            filter_effectiveness=facet_mapping["filter_effectiveness"],
            facet_relevance=facet_mapping["facet_relevance"],
            # Historical comparison
            baseline_comparison=baseline_comparison,
            trend_analysis=trend_analysis,
            titles_top5=titles_top5,
            gpt_reasoning=reasoning,
            timestamp=datetime.now(),
            store_id=self.store_id
        )
    
    async def run_enhanced_benchmark(self, queries_file: str = DEFAULT_QUERIES_FILE, 
                                   results_file: str = DEFAULT_RESULTS_FILE,
                                   endpoint: str = DEFAULT_ENDPOINT) -> List[EnhancedBenchmarkResult]:
        """Run enhanced benchmark with rate limiting and throttling."""
        # Record start time
        self.stats["start_time"] = time.time()
        
        # Read queries
        queries = self._read_queries(queries_file)
        if not queries:
            logger.error(f"❌ No queries found in {queries_file}")
            return []
        
        # Limit queries to maximum allowed
        max_queries = self.config["max_queries"]
        if len(queries) > max_queries:
            logger.warning(f"⚠️ Limiting queries from {len(queries)} to {max_queries}")
            queries = queries[:max_queries]
        
        logger.info(f"🚀 Starting enhanced benchmark with {len(queries)} queries against {endpoint}")
        logger.info(f"⚙️ Configuration: max_queries={max_queries}, delay={self.config['request_delay']}s, batch_size={self.config['batch_size']}")
        
        # Execute benchmarks sequentially (one by one) with rate limiting
        results = []
        
        for i, query in enumerate(queries, 1):
            if not self.headless:
                logger.info(f"🔍 Processing query {i}/{len(queries)}: '{query}'")
            
            try:
                result = await self.benchmark_query(query, endpoint)
                results.append(result)
                
                # Delay between requests
                if i < len(queries):
                    delay = self.config["request_delay"]
                    if not self.headless:
                        logger.info(f"⏳ Waiting {delay}s before next query...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"❌ Query failed for '{query}': {e}")
                # Create error result
                error_result = EnhancedBenchmarkResult(
                    query=query,
                    score=0.0,
                    response_time=0.0,
                    result_count=0,
                    query_analysis=self.query_analyzer.analyze_query(query),
                    cache_hit=False,
                    embedding_generation_time=None,
                    price_filter_applied=False,
                    fallback_used=False,
                    avg_price_top5=0.0,
                    price_coherence=0.0,
                    diversity_score=0.0,
                    category_coverage=0.0,
                    conversion_potential=0.0,
                    price_range_coverage=0.0,
                    query_correction_applied=False,
                    suggestions_provided=0,
                    facets_generated=0,
                    primary_intent="general",
                    secondary_intents=[],
                    intent_confidence_scores={},
                    semantic_relevance=0.0,
                    contextual_relevance=0.0,
                    user_intent_alignment=0.0,
                    applied_filters={},
                    generated_facets={},
                    filter_effectiveness=0.0,
                    facet_relevance=0.0,
                    baseline_comparison=None,
                    trend_analysis=None,
                    titles_top5="",
                    gpt_reasoning=f"Query failed: {e}",
                    timestamp=datetime.now(),
                    store_id=self.store_id
                )
                results.append(error_result)
        
        # Record end time
        self.stats["end_time"] = time.time()
        
        # Save enhanced results
        self._save_enhanced_results(results, results_file)
        
        # Print enhanced summary with rate limiting stats
        self._print_enhanced_summary(results)
        self._print_rate_limiting_stats()
        
        return results
    
    def _read_queries(self, filename: str) -> List[str]:
        """Read queries from CSV file."""
        queries = []
        try:
            # Try relative path first, then absolute path
            file_paths = [
                filename,
                f"../data/{filename}",
                f"../{filename}"
            ]
            
            for file_path in file_paths:
                if Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        if 'query' in reader.fieldnames:
                            queries = [row['query'] for row in reader if row['query'].strip()]
                        else:
                            # Fallback: assume first column contains queries
                            f.seek(0)
                            reader = csv.reader(f)
                            next(reader)  # Skip header
                            queries = [row[0] for row in reader if row and row[0].strip()]
                    break
            else:
                raise FileNotFoundError(f"Query file not found in any of the expected locations: {file_paths}")
                
        except Exception as e:
            logger.error(f"Error reading queries from {filename}: {e}")
            raise
        
        logger.info(f"📖 Loaded {len(queries)} queries from {filename}")
        return queries
    
    def _save_enhanced_results(self, results: List[EnhancedBenchmarkResult], filename: str):
        """Save enhanced benchmark results to CSV file."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write enhanced header
                writer.writerow([
                    'query', 'score', 'response_time', 'result_count',
                    'detected_intents', 'intent_confidence', 'complexity_score', 'expected_difficulty',
                    'cache_hit', 'embedding_generation_time', 'price_filter_applied', 'fallback_used',
                    'avg_price_top5', 'price_coherence', 'diversity_score', 'category_coverage',
                    'conversion_potential', 'price_range_coverage',
                    'query_correction_applied', 'suggestions_provided', 'facets_generated',
                    # Enhanced categorisation
                    'primary_intent', 'secondary_intents', 'intent_confidence_scores',
                    # Automatic relevance scoring
                    'semantic_relevance', 'contextual_relevance', 'user_intent_alignment',
                    # Facet and filter mapping
                    'applied_filters', 'generated_facets', 'filter_effectiveness', 'facet_relevance',
                    # Historical comparison
                    'baseline_comparison', 'trend_analysis',
                    'titles_top5', 'gpt_reasoning', 'timestamp', 'store_id'
                ])
                
                # Write enhanced results
                for result in results:
                    writer.writerow([
                        result.query,
                        f"{result.score:.3f}",
                        f"{result.response_time:.3f}",
                        result.result_count,
                        json.dumps(result.query_analysis.detected_intents),
                        json.dumps(result.query_analysis.intent_confidence),
                        f"{result.query_analysis.complexity_score:.3f}",
                        result.query_analysis.expected_difficulty,
                        result.cache_hit,
                        f"{result.embedding_generation_time:.3f}" if result.embedding_generation_time else "",
                        result.price_filter_applied,
                        result.fallback_used,
                        f"{result.avg_price_top5:.2f}",
                        f"{result.price_coherence:.3f}",
                        f"{result.diversity_score:.3f}",
                        f"{result.category_coverage:.3f}",
                        f"{result.conversion_potential:.3f}",
                        f"{result.price_range_coverage:.3f}",
                        result.query_correction_applied,
                        result.suggestions_provided,
                        result.facets_generated,
                        # Enhanced categorisation
                        result.primary_intent,
                        json.dumps(result.secondary_intents),
                        json.dumps(result.intent_confidence_scores),
                        # Automatic relevance scoring
                        f"{result.semantic_relevance:.3f}",
                        f"{result.contextual_relevance:.3f}",
                        f"{result.user_intent_alignment:.3f}",
                        # Facet and filter mapping
                        json.dumps(result.applied_filters),
                        json.dumps(result.generated_facets),
                        f"{result.filter_effectiveness:.3f}",
                        f"{result.facet_relevance:.3f}",
                        # Historical comparison
                        json.dumps(result.baseline_comparison) if result.baseline_comparison else "",
                        json.dumps(result.trend_analysis) if result.trend_analysis else "",
                        result.titles_top5,
                        result.gpt_reasoning,
                        result.timestamp.isoformat(),
                        result.store_id or ""
                    ])
            
            logger.info(f"💾 Saved {len(results)} enhanced results to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving enhanced results: {e}")
    
    def _print_enhanced_summary(self, results: List[EnhancedBenchmarkResult]):
        """Print enhanced benchmark summary."""
        if not results:
            return
        
        # Calculate comprehensive statistics
        scores = [r.score for r in results]
        response_times = [r.response_time for r in results]
        complexity_scores = [r.query_analysis.complexity_score for r in results]
        
        avg_score = statistics.mean(scores)
        avg_response_time = statistics.mean(response_times)
        avg_complexity = statistics.mean(complexity_scores)
        
        # Intent analysis
        intent_usage = {}
        for result in results:
            for intent_type in result.query_analysis.detected_intents:
                intent_usage[intent_type] = intent_usage.get(intent_type, 0) + 1
        
        # Performance analysis
        cache_hits = sum(1 for r in results if r.cache_hit)
        cache_rate = cache_hits / len(results)
        
        # Quality analysis
        avg_price_coherence = statistics.mean([r.price_coherence for r in results])
        avg_diversity = statistics.mean([r.diversity_score for r in results])
        avg_conversion_potential = statistics.mean([r.conversion_potential for r in results])
        
        # Enhanced categorisation analysis
        primary_intents = [r.primary_intent for r in results]
        intent_distribution = {}
        for intent in primary_intents:
            intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
        
        # Automatic relevance scoring analysis
        avg_semantic_relevance = statistics.mean([r.semantic_relevance for r in results])
        avg_contextual_relevance = statistics.mean([r.contextual_relevance for r in results])
        avg_user_intent_alignment = statistics.mean([r.user_intent_alignment for r in results])
        
        # Facet and filter analysis
        avg_filter_effectiveness = statistics.mean([r.filter_effectiveness for r in results])
        avg_facet_relevance = statistics.mean([r.facet_relevance for r in results])
        
        # Historical trends analysis
        trends_available = sum(1 for r in results if r.trend_analysis)
        improving_trends = 0
        declining_trends = 0
        for result in results:
            if result.trend_analysis:
                for trend_direction in result.trend_analysis.values():
                    if trend_direction == "improving":
                        improving_trends += 1
                    elif trend_direction == "declining":
                        declining_trends += 1
        
        # Find worst performing queries
        worst_queries = sorted(results, key=lambda x: x.score)[:5]
        
        # Print enhanced summary
        print("\n" + "="*80)
        print("📊 ENHANCED BENCHMARK SUMMARY")
        print("="*80)
        print(f"Total queries tested: {len(results)}")
        print(f"Store ID: {self.store_id or 'N/A'}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        print(f"\n🎯 PERFORMANCE METRICS:")
        print(f"  Average relevance score: {avg_score:.3f}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Cache hit rate: {cache_rate:.1%}")
        print(f"  Price filter applied: {sum(1 for r in results if r.price_filter_applied)}/{len(results)}")
        print(f"  Fallback used: {sum(1 for r in results if r.fallback_used)}/{len(results)}")
        
        print(f"\n🧠 QUERY ANALYSIS:")
        print(f"  Average complexity score: {avg_complexity:.3f}")
        print(f"  Most common intents: {sorted(intent_usage.items(), key=lambda x: x[1], reverse=True)[:5]}")
        print(f"  Primary intent distribution: {sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True)[:5]}")
        
        print(f"\n📈 QUALITY METRICS:")
        print(f"  Average price coherence: {avg_price_coherence:.3f}")
        print(f"  Average diversity score: {avg_diversity:.3f}")
        print(f"  Average conversion potential: {avg_conversion_potential:.3f}")
        
        print(f"\n🤖 AUTOMATIC RELEVANCE SCORING:")
        print(f"  Average semantic relevance: {avg_semantic_relevance:.3f}")
        print(f"  Average contextual relevance: {avg_contextual_relevance:.3f}")
        print(f"  Average user intent alignment: {avg_user_intent_alignment:.3f}")
        
        print(f"\n🔍 FACET & FILTER ANALYSIS:")
        print(f"  Average filter effectiveness: {avg_filter_effectiveness:.3f}")
        print(f"  Average facet relevance: {avg_facet_relevance:.3f}")
        
        print(f"\n📊 HISTORICAL TRENDS:")
        print(f"  Trends available: {trends_available}/{len(results)}")
        print(f"  Improving trends: {improving_trends}")
        print(f"  Declining trends: {declining_trends}")
        
        print(f"\n🔴 TOP 5 WORST PERFORMING QUERIES:")
        for i, result in enumerate(worst_queries, 1):
            print(f"{i}. '{result.query}' - Score: {result.score:.3f}")
            print(f"   Complexity: {result.query_analysis.expected_difficulty}")
            print(f"   Intents: {list(result.query_analysis.detected_intents.keys())}")
            print(f"   Reasoning: {result.gpt_reasoning[:100]}...")
        
        print("\n" + "="*80)
    
    def _print_rate_limiting_stats(self):
        """Print rate limiting and performance statistics."""
        if not self.stats["start_time"]:
            return
        
        total_time = self.stats["end_time"] - self.stats["start_time"]
        cache_rate = (self.stats["cached_requests"] / self.stats["total_requests"]) * 100 if self.stats["total_requests"] > 0 else 0
        failure_rate = (self.stats["failed_requests"] / self.stats["total_requests"]) * 100 if self.stats["total_requests"] > 0 else 0
        
        print(f"\n🔧 RATE LIMITING & PERFORMANCE STATS:")
        print(f"  Total execution time: {total_time:.1f}s")
        print(f"  Total requests made: {self.stats['total_requests']}")
        print(f"  Cached requests: {self.stats['cached_requests']} ({cache_rate:.1f}%)")
        print(f"  Failed requests: {self.stats['failed_requests']} ({failure_rate:.1f}%)")
        print(f"  Rate limited requests: {self.stats['rate_limited_requests']}")
        print(f"  Total wait time: {self.stats['total_wait_time']:.1f}s")
        print(f"  Average requests per second: {self.stats['total_requests'] / total_time:.2f}")
        
        print(f"\n⚙️ CONFIGURATION USED:")
        for key, value in self.config.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*80)

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced Search Quality Benchmark Tool with Rate Limiting")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no console output)")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="API endpoint to test")
    parser.add_argument("--queries", default=DEFAULT_QUERIES_FILE, help="CSV file with test queries")
    parser.add_argument("--results", default=DEFAULT_RESULTS_FILE, help="CSV file to save results")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for API")
    parser.add_argument("--store-id", help="Store ID for tracking")
    
    # Rate limiting arguments
    parser.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES, help="Maximum number of queries to test (default: 100)")
    parser.add_argument("--request-delay", type=float, default=DEFAULT_REQUEST_DELAY, help="Delay between request batches in seconds (default: 2.0)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Number of requests to process in parallel (default: 5)")
    parser.add_argument("--rate-limit-max", type=int, default=DEFAULT_RATE_LIMIT_MAX_REQUESTS, help="Maximum requests per rate limit window (default: 50)")
    parser.add_argument("--rate-limit-window", type=int, default=DEFAULT_RATE_LIMIT_WINDOW, help="Rate limit window in seconds (default: 3600)")
    parser.add_argument("--retry-attempts", type=int, default=DEFAULT_RETRY_ATTEMPTS, help="Number of retry attempts for failed requests (default: 3)")
    parser.add_argument("--retry-delay", type=float, default=DEFAULT_RETRY_DELAY, help="Delay between retries in seconds (default: 5.0)")
    
    args = parser.parse_args()
    
    # Create custom configuration
    config = BENCHMARK_CONFIG.copy()
    config.update({
        "max_queries": args.max_queries,
        "request_delay": args.request_delay,
        "batch_size": args.batch_size,
        "rate_limit_max_requests": args.rate_limit_max,
        "rate_limit_window": args.rate_limit_window,
        "retry_attempts": args.retry_attempts,
        "retry_delay": args.retry_delay,
    })
    
    # Create enhanced benchmarker with custom configuration
    async with EnhancedSearchBenchmarker(
        base_url=args.base_url, 
        headless=args.headless,
        store_id=args.store_id,
        config=config
    ) as benchmarker:
        await benchmarker.run_enhanced_benchmark(
            queries_file=args.queries,
            results_file=args.results,
            endpoint=args.endpoint
        )

if __name__ == "__main__":
    asyncio.run(main())

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `benchmark_rate_limiter.py` - Rate limiting and throttling
  - `benchmark_cache.py` - Caching functionality
  - `query_analyzer.py` - Query analysis and intent detection
  - `historical_trend_analyzer.py` - Historical trend analysis
  - `facet_filter_mapper.py` - Facet and filter mapping
  - `automatic_relevance_scorer.py` - Automatic relevance scoring
  - `enhanced_benchmark_orchestrator.py` - Main benchmark orchestration

## 🗑️ Functies voor Verwijdering
- [ ] `_get_openai_key()` - Consider moving to a dedicated configuration service
- [ ] `_print_enhanced_summary()` - Consider moving to a dedicated reporting service
- [ ] `_print_rate_limiting_stats()` - Consider moving to a dedicated monitoring service

## ⚡ Performance Optimalisaties
- [ ] Implement connection pooling for aiohttp sessions
- [ ] Add caching for frequently accessed query analysis results
- [ ] Implement batch processing for GPT scoring
- [ ] Add parallel processing for query analysis
- [ ] Optimize database operations for historical trends

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
- [ ] Implement proper rate limiting strategies

## 🧪 Testing Verbeteringen
- [ ] Add unit tests for all helper methods
- [ ] Implement integration tests for API communication
- [ ] Add performance tests for benchmark operations
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete benchmark flow

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)

## 🎯 Specifieke Verbeteringen
- [ ] Refactor large dataclasses into smaller, more focused ones
- [ ] Implement proper error handling for GPT API calls
- [ ] Add retry mechanisms for failed requests
- [ ] Implement proper caching strategies
- [ ] Add support for different output formats
- [ ] Implement proper progress tracking
- [ ] Add support for custom metrics
- [ ] Implement proper result aggregation
- [ ] Add support for different query sources
- [ ] Implement proper result validation
""" 