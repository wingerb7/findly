import re
import json
import logging
import openai
import statistics
import asyncio
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session

from ai_shopify_search.core.database import get_db
from ai_shopify_search.core.models import Product

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 3.0
DEFAULT_MAX_TOKENS = 100
DEFAULT_TEMPERATURE = 0.1
DEFAULT_OVERALL_TIMEOUT = 5.0

# Fallback price values
FALLBACK_PRICES = {
    "min": 10,
    "max": 500,
    "median": 50,
    "budget": 50,
    "premium": 150
}

# Confidence scores
CONFIDENCE_SCORES = {
    "range_pattern": 0.95,
    "below_pattern": 0.9,
    "above_pattern": 0.9,
    "exact_pattern": 0.85,
    "gpt_fallback": 0.6,
    "store_statistics": 0.3
}

# Price parsing
PRICE_DECIMAL_SEPARATOR = ','
PRICE_DECIMAL_REPLACEMENT = '.'

# Error Messages
ERROR_NO_PRICES_FOUND = "No valid prices found, using fallback values"
ERROR_LOADING_PRICE_STATS = "Error loading price statistics: {error}"
ERROR_GPT_EMPTY_RESPONSE = "GPT returned empty response for query: {query}"
ERROR_GPT_TIMEOUT = "GPT timeout after {timeout}s for query: {query}"
ERROR_GPT_INVALID_JSON = "GPT returned invalid JSON: {error} for query: {query}"
ERROR_GPT_FALLBACK_FAILED = "GPT fallback failed: {error_type}: {error} for query: {query}"

# Logging Context Keys
LOG_CONTEXT_QUERY = "query"
LOG_CONTEXT_MIN_PRICE = "min_price"
LOG_CONTEXT_MAX_PRICE = "max_price"
LOG_CONTEXT_CONFIDENCE = "confidence"

# Combined regex patterns with named groups
RANGE_PATTERN = re.compile(
    r'\b(?:(?:tussen|between)\s+(?P<min>\d+(?:[.,]\d+)?)\s+(?:en|and)\s+(?P<max>\d+(?:[.,]\d+)?)|'
    r'(?P<min2>\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<max2>\d+(?:[.,]\d+)?)\s*(?:euro|€)?|'
    r'(?:€|euro)\s*(?P<min3>\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<max3>\d+(?:[.,]\d+)?))',
    re.IGNORECASE
)

BELOW_PATTERN = re.compile(
    r'\b(?:(?:onder|below|less than|max|tot)\s+(?:€|euro\s+)?(?P<max>\d+(?:[.,]\d+)?)|'
    r'(?:€|euro)\s*(?P<max2>\d+(?:[.,]\d+)?)\s*(?:of minder|or less))',
    re.IGNORECASE
)

ABOVE_PATTERN = re.compile(
    r'\b(?:(?:boven|above|more than|min|vanaf)\s+(?:€|euro\s+)?(?P<min>\d+(?:[.,]\d+)?)|'
    r'(?:€|euro)\s*(?P<min2>\d+(?:[.,]\d+)?)\s*(?:of meer|or more))',
    re.IGNORECASE
)

EXACT_PATTERN = re.compile(
    r'\b(?:(?P<price>\d+(?:[.,]\d+)?)\s*(?:euro|€)|'
    r'(?:€|euro)\s*(?P<price2>\d+(?:[.,]\d+)?)|'
    r'(?:ongeveer|about|rond|around)\s+(?:€|euro\s+)?(?P<price3>\d+(?:[.,]\d+)?))',
    re.IGNORECASE
)

# Combined cleanup pattern
CLEANUP_PATTERN = re.compile(
    r'\b(?:(?:tussen|between)\s+\d+(?:[.,]\d+)?\s+(?:en|and)\s+\d+(?:[.,]\d+)?\s*(?:euro|€)?|'
    r'\d+(?:[.,]\d+)?\s*[-–—]\s*\d+(?:[.,]\d+)?\s*(?:euro|€)?|'
    r'(?:€|euro)\s*\d+(?:[.,]\d+)?\s*[-–—]\s*\d+(?:[.,]\d+)?|'
    r'(?:onder|below|less than|max|tot|boven|above|more than|min|vanaf)\s+(?:€|euro\s+)?\d+(?:[.,]\d+)?|'
    r'(?:€|euro)\s*\d+(?:[.,]\d+)?\s*(?:of minder|or less|of meer|or more)|'
    r'\d+(?:[.,]\d+)?\s*(?:euro|€)|'
    r'(?:€|euro)\s*\d+(?:[.,]\d+)?|'
    r'(?:ongeveer|about|rond|around)\s+(?:€|euro\s+)?\d+(?:[.,]\d+)?)',
    re.IGNORECASE
)

def get_store_price_statistics() -> Dict[str, float]:
    """Load store price statistics using SQLAlchemy."""
    try:
        db = next(get_db())
        products = db.query(Product.price).filter(
            Product.price > 0,
            Product.price.isnot(None)
        ).all()
        
        prices = [float(product.price) for product in products if product.price is not None]
        
        if not prices:
            logger.warning(f"No valid prices found, using fallback values")
            raise ValueError("No prices found")
        
        prices.sort()
        return {
            "min": min(prices),
            "max": max(prices),
            "median": statistics.median(prices),
            "budget": statistics.quantiles(prices, n=4)[0] * 1.5,
            "premium": statistics.quantiles(prices, n=4)[2] * 1.2,
        }
    except Exception as e:
        logger.error(f"Error loading price statistics: {e}")
        return {"min": 10, "max": 500, "median": 50, "budget": 50, "premium": 150}

def _parse_price(price_str: str) -> float:
    """
    Parse price string to float, handling commas and dots.
    
    Args:
        price_str: Price string to parse
        
    Returns:
        Parsed price as float
    """
    return float(price_str.replace(PRICE_DECIMAL_SEPARATOR, PRICE_DECIMAL_REPLACEMENT))

def _extract_range_pattern(query: str) -> Tuple[Optional[float], Optional[float], float]:
    """
    Extract price range pattern from query.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence)
    """
    if match := RANGE_PATTERN.search(query):
        min_val = _parse_price(match.group('min') or match.group('min2') or match.group('min3'))
        max_val = _parse_price(match.group('max') or match.group('max2') or match.group('max3'))
        return min_val, max_val, CONFIDENCE_SCORES["range_pattern"]
    return None, None, 0.0

def _extract_below_pattern(query: str) -> Tuple[Optional[float], Optional[float], float]:
    """
    Extract price below pattern from query.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence)
    """
    if match := BELOW_PATTERN.search(query):
        max_val = _parse_price(match.group('max') or match.group('max2'))
        return None, max_val, CONFIDENCE_SCORES["below_pattern"]
    return None, None, 0.0

def _extract_above_pattern(query: str) -> Tuple[Optional[float], Optional[float], float]:
    """
    Extract price above pattern from query.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence)
    """
    if match := ABOVE_PATTERN.search(query):
        min_val = _parse_price(match.group('min') or match.group('min2'))
        return min_val, None, CONFIDENCE_SCORES["above_pattern"]
    return None, None, 0.0

def _extract_exact_pattern(query: str) -> Tuple[Optional[float], Optional[float], float]:
    """
    Extract exact price pattern from query.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence)
    """
    if match := EXACT_PATTERN.search(query):
        price = _parse_price(match.group('price') or match.group('price2') or match.group('price3'))
        return price * 0.9, price * 1.1, CONFIDENCE_SCORES["exact_pattern"]
    return None, None, 0.0

def extract_price_intent(query: str) -> Tuple[Optional[float], Optional[float], float]:
    """
    Extract price intent using combined regex patterns with confidence scoring.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence)
    """
    query = query.lower().strip()
    
    # Check range patterns
    min_val, max_val, confidence = _extract_range_pattern(query)
    if min_val is not None or max_val is not None:
        return min_val, max_val, confidence
    
    # Check below patterns
    min_val, max_val, confidence = _extract_below_pattern(query)
    if min_val is not None or max_val is not None:
        return min_val, max_val, confidence
    
    # Check above patterns
    min_val, max_val, confidence = _extract_above_pattern(query)
    if min_val is not None or max_val is not None:
        return min_val, max_val, confidence
    
    # Check exact patterns
    min_val, max_val, confidence = _extract_exact_pattern(query)
    if min_val is not None or max_val is not None:
        return min_val, max_val, confidence
    
    return None, None, 0.0

async def gpt_price_fallback(query: str, timeout: float = DEFAULT_TIMEOUT) -> Tuple[Optional[float], Optional[float], float]:
    """GPT fallback with improved timeout and error handling."""
    stats = get_store_price_statistics()
    
    prompt = f"""Analyze: '{query[:100]}' (truncated)
Store context: min=€{stats['min']:.0f}, max=€{stats['max']:.0f}, budget=€{stats['budget']:.0f}, premium=€{stats['premium']:.0f}
Return JSON: {{"min_price": <number>, "max_price": <number>, "reason": "<short>"}}"""
    
    try:
        async with asyncio.timeout(timeout):
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Price analysis expert. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS
            )
        
        content = response.choices[0].message.content.strip()
        if not content:
            logger.warning(f"GPT returned empty response for query: {query[:50]}")
            return None, None, 0.0
        
        result = json.loads(content)
        min_price = result.get("min_price")
        max_price = result.get("max_price")
        
        if min_price is not None and max_price is not None:
            min_price, max_price = float(min_price), float(max_price)
            if min_price > max_price:
                min_price, max_price = max_price, min_price
        
        logger.info(f"GPT price intent successful: {min_price}-{max_price} for query: {query[:50]}")
        return min_price, max_price, CONFIDENCE_SCORES["gpt_fallback"]
        
    except asyncio.TimeoutError:
        logger.warning(f"GPT timeout after {timeout}s for query: {query[:50]}")
        return None, None, 0.0
    except json.JSONDecodeError as e:
        logger.error(f"GPT returned invalid JSON: {e} for query: {query[:50]}")
        return None, None, 0.0
    except Exception as e:
        logger.error(f"GPT fallback failed: {type(e).__name__}: {e} for query: {query[:50]}")
        return None, None, 0.0

def _try_regex_price_extraction(query: str) -> Tuple[Optional[float], Optional[float], float, str]:
    """
    Try to extract price intent using regex patterns.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence, method)
    """
    min_p, max_p, confidence = extract_price_intent(query)
    if min_p is not None or max_p is not None:
        logger.info(f"Price intent detected via regex: {min_p}-{max_p} (conf: {confidence:.2f})")
        return min_p, max_p, confidence, "regex"
    return None, None, 0.0, "regex"

def _try_gpt_price_extraction(query: str) -> Tuple[Optional[float], Optional[float], float, str]:
    """
    Try to extract price intent using GPT fallback.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence, method)
    """
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task with shorter timeout
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, gpt_price_fallback(query, timeout=DEFAULT_TIMEOUT))
                min_p, max_p, confidence = future.result(timeout=DEFAULT_OVERALL_TIMEOUT)
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            min_p, max_p, confidence = asyncio.run(gpt_price_fallback(query, timeout=DEFAULT_TIMEOUT))
        
        if min_p is not None or max_p is not None:
            logger.info(f"Price intent detected via GPT: {min_p}-{max_p} (conf: {confidence:.2f})")
            return min_p, max_p, confidence, "gpt"
    except concurrent.futures.TimeoutError:
        logger.warning(f"GPT fallback timeout for query: {query[:50]}")
    except Exception as e:
        logger.error(f"GPT fallback error: {e} for query: {query[:50]}")
    
    return None, None, 0.0, "gpt"

def _get_store_statistics_fallback() -> Tuple[float, float, float, str]:
    """
    Get price range using store statistics as fallback.
    
    Returns:
        Tuple of (min_price, max_price, confidence, method)
    """
    stats = get_store_price_statistics()
    logger.info(f"Using store statistics fallback: budget={stats['budget']:.0f}, premium={stats['premium']:.0f}")
    return stats['budget'], stats['premium'], CONFIDENCE_SCORES["store_statistics"], "fallback"

def get_price_range(query: str) -> Tuple[Optional[float], Optional[float], float, str]:
    """
    Get price range with confidence and method, including improved fallback to store statistics.
    
    Args:
        query: Query string to analyze
        
    Returns:
        Tuple of (min_price, max_price, confidence, method)
    """
    if not query or not query.strip():
        return None, None, 0.0, "empty"
    
    # Try regex first
    min_p, max_p, confidence, method = _try_regex_price_extraction(query)
    if min_p is not None or max_p is not None:
        return min_p, max_p, confidence, method
    
    # Try GPT fallback with improved error handling
    min_p, max_p, confidence, method = _try_gpt_price_extraction(query)
    if min_p is not None or max_p is not None:
        return min_p, max_p, confidence, method
    
    # Final fallback to store statistics (faster)
    return _get_store_statistics_fallback()

def clean_query_from_price_intent(query: str) -> str:
    """Clean query from price intent in one pass using combined regex."""
    if not query:
        return query
    
    # Remove all price patterns in one pass
    cleaned = CLEANUP_PATTERN.sub('', query)
    
    # Clean up whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned if cleaned else query

def format_price_message(min_price: Optional[float], max_price: Optional[float]) -> str:
    """Format user-friendly price message."""
    if min_price is None and max_price is None:
        return ""
    
    if min_price is not None and max_price is not None:
        if abs(max_price - min_price) < 0.01:
            return f"Prijs: €{min_price:.2f}"
        return f"Prijs: €{min_price:.2f} - €{max_price:.2f}"
    
    elif min_price is not None:
        return f"Prijs: vanaf €{min_price:.2f}"
    
    elif max_price is not None:
        return f"Prijs: tot €{max_price:.2f}"
    
    return ""

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `price_pattern_extractor.py` - Price pattern extraction logic
  - `price_parser.py` - Price parsing utilities
  - `gpt_price_analyzer.py` - GPT-based price analysis
  - `price_statistics.py` - Price statistics calculation
  - `price_formatter.py` - Price formatting utilities
  - `price_intent_orchestrator.py` - Main orchestration

## 🗑️ Functies voor Verwijdering
- [ ] `gpt_price_fallback()` - Consider moving to a dedicated GPT service
- [ ] `get_store_price_statistics()` - Consider moving to a dedicated statistics service
- [ ] `clean_query_from_price_intent()` - Consider moving to a dedicated query cleaning service
- [ ] `format_price_message()` - Consider moving to a dedicated formatting service

## ⚡ Performance Optimalisaties
- [ ] Implement caching for frequently accessed price statistics
- [ ] Add batch processing for multiple price extractions
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
- [ ] Implement integration tests for price extraction
- [ ] Add performance tests for large datasets
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete price intent flow

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)

## 🎯 Specifieke Verbeteringen
- [ ] Refactor large price extraction methods into smaller, more focused ones
- [ ] Implement proper error handling for database operations
- [ ] Add retry mechanisms for failed operations
- [ ] Implement proper caching strategies
- [ ] Add support for different output formats
- [ ] Implement proper progress tracking
- [ ] Add support for custom price extraction scenarios
- [ ] Implement proper result aggregation
- [ ] Add support for different data sources
- [ ] Implement proper result validation
- [ ] Add support for real-time price intent updates
- [ ] Implement proper data versioning
- [ ] Add support for price intent comparison
- [ ] Implement proper data export functionality
- [ ] Add support for price intent templates
- [ ] Implement proper A/B testing for price intent
- [ ] Add support for personalized price intent
- [ ] Implement proper feedback collection
- [ ] Add support for price intent analytics
- [ ] Implement proper price intent ranking
"""