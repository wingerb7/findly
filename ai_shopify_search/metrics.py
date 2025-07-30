import time
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Prometheus metrics
SEARCH_REQUESTS_TOTAL = Counter(
    'search_requests_total',
    'Total number of search requests',
    ['search_type', 'cache_hit']
)

SEARCH_RESPONSE_TIME = Histogram(
    'search_response_time_seconds',
    'Search response time in seconds',
    ['search_type']
)

SEARCH_RESULTS_COUNT = Histogram(
    'search_results_count',
    'Number of results returned by search',
    ['search_type']
)

CACHE_HIT_RATIO = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio for search requests',
    ['search_type']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active database connections'
)

REDIS_CONNECTIONS = Gauge(
    'redis_connections',
    'Number of active Redis connections'
)

class MetricsCollector:
    """Collect and expose metrics for observability."""
    
    def __init__(self):
        self.search_metrics = {}
    
    def record_search_request(
        self, 
        search_type: str, 
        cache_hit: bool, 
        response_time: float, 
        results_count: int
    ):
        """Record search request metrics."""
        try:
            # Increment request counter
            SEARCH_REQUESTS_TOTAL.labels(search_type=search_type, cache_hit=str(cache_hit)).inc()
            
            # Record response time
            SEARCH_RESPONSE_TIME.labels(search_type=search_type).observe(response_time)
            
            # Record results count
            SEARCH_RESULTS_COUNT.labels(search_type=search_type).observe(results_count)
            
            # Update cache hit ratio (simplified calculation)
            cache_hit_value = 1.0 if cache_hit else 0.0
            CACHE_HIT_RATIO.labels(search_type=search_type).set(cache_hit_value)
            
            logger.debug(f"Recorded metrics for {search_type} search: cache_hit={cache_hit}, "
                        f"response_time={response_time:.3f}s, results={results_count}")
            
        except Exception as e:
            logger.error(f"Error recording search metrics: {e}")
    
    def record_database_connections(self, count: int):
        """Record active database connections."""
        try:
            ACTIVE_CONNECTIONS.set(count)
        except Exception as e:
            logger.error(f"Error recording database connections: {e}")
    
    def record_redis_connections(self, count: int):
        """Record active Redis connections."""
        try:
            REDIS_CONNECTIONS.set(count)
        except Exception as e:
            logger.error(f"Error recording Redis connections: {e}")
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics as string."""
        try:
            return generate_latest()
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return ""

# Global metrics collector instance
metrics_collector = MetricsCollector() 