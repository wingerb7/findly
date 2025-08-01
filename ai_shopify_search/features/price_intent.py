import re, json, sqlite3, logging, openai, statistics, asyncio
from typing import Optional, Tuple, Dict
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "databases" / "findly_consolidated.db"

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

@contextmanager
def get_db_connection():
    """Context manager for SQLite database connections."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        yield conn
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_store_price_statistics() -> Dict[str, float]:
    """Load store price statistics with context manager."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT price FROM products WHERE price > 0 AND price IS NOT NULL")
            prices = [float(row[0]) for row in cursor.fetchall() if row[0] is not None]
            
        if not prices:
            logger.warning("No valid prices found, using fallback values")
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
    """Parse price string to float, handling commas and dots."""
    return float(price_str.replace(',', '.'))

def extract_price_intent(query: str) -> Tuple[Optional[float], Optional[float], float]:
    """Extract price intent using combined regex patterns with confidence scoring."""
    query = query.lower().strip()
    
    # Check range patterns
    if match := RANGE_PATTERN.search(query):
        min_val = _parse_price(match.group('min') or match.group('min2') or match.group('min3'))
        max_val = _parse_price(match.group('max') or match.group('max2') or match.group('max3'))
        return min_val, max_val, 0.95
    
    # Check below patterns
    if match := BELOW_PATTERN.search(query):
        max_val = _parse_price(match.group('max') or match.group('max2'))
        return None, max_val, 0.9
    
    # Check above patterns
    if match := ABOVE_PATTERN.search(query):
        min_val = _parse_price(match.group('min') or match.group('min2'))
        return min_val, None, 0.9
    
    # Check exact patterns
    if match := EXACT_PATTERN.search(query):
        price = _parse_price(match.group('price') or match.group('price2') or match.group('price3'))
        return price * 0.9, price * 1.1, 0.85
    
    return None, None, 0.0

async def gpt_price_fallback(query: str, timeout: float = 5.0) -> Tuple[Optional[float], Optional[float], float]:
    """GPT fallback with timeout and error handling."""
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
                temperature=0.1,
                max_tokens=100
            )
        
        result = json.loads(response.choices[0].message.content.strip())
        min_price = result.get("min_price")
        max_price = result.get("max_price")
        
        if min_price is not None and max_price is not None:
            min_price, max_price = float(min_price), float(max_price)
            if min_price > max_price:
                min_price, max_price = max_price, min_price
        
        return min_price, max_price, 0.6
        
    except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
        logger.error(f"GPT fallback failed: {type(e).__name__}")
        return None, None, 0.0

def get_price_range(query: str) -> Tuple[Optional[float], Optional[float], float, str]:
    """Get price range with confidence and method, including fallback to store statistics."""
    if not query or not query.strip():
        return None, None, 0.0, "empty"
    
    # Try regex first
    min_p, max_p, confidence = extract_price_intent(query)
    if min_p is not None or max_p is not None:
        logger.info(f"Price intent detected via regex: {min_p}-{max_p} (conf: {confidence:.2f})")
        return min_p, max_p, confidence, "regex"
    
    # Try GPT fallback
    try:
        min_p, max_p, confidence = asyncio.run(gpt_price_fallback(query))
        if min_p is not None or max_p is not None:
            logger.info(f"Price intent detected via GPT: {min_p}-{max_p} (conf: {confidence:.2f})")
            return min_p, max_p, confidence, "gpt"
    except Exception as e:
        logger.error(f"GPT fallback error: {e}")
    
    # Final fallback to store statistics
    stats = get_store_price_statistics()
    logger.info(f"Using store statistics fallback: budget={stats['budget']:.0f}, premium={stats['premium']:.0f}")
    return stats['budget'], stats['premium'], 0.3, "fallback"

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