import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def extract_price_intent(query: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extraheert prijsintenties uit een zoekquery en retourneert min_price en max_price.
    
    Args:
        query: De zoekquery string
        
    Returns:
        Tuple van (min_price, max_price) waar beide None kunnen zijn
    """
    if not query:
        return None, None
    
    query_lower = query.lower().strip()
    min_price = None
    max_price = None
    
    logger.info(f"🔍 Analyseren van prijsintentie in query: '{query}'")
    
    # Patronen voor prijsintenties
    patterns = [
        # "goedkoop" → max_price = 75
        (r'\bgoedkoop\b', None, 75),
        (r'\bcheap\b', None, 75),
        (r'\bbudget\b', None, 75),
        (r'\bvoordelig\b', None, 75),
        
        # "duur" → min_price = 200
        (r'\bduur\b', 200, None),
        (r'\bexpensive\b', 200, None),
        (r'\bluxe\b', 200, None),
        (r'\bpremium\b', 200, None),
        (r'\bexclusief\b', 200, None),
        
        # "onder X euro" → max_price = X
        (r'\bonder\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.'))),
        (r'\bbelow\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.'))),
        (r'\bless\s+than\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.'))),
        
        # "boven X euro" → min_price = X
        (r'\bboven\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None),
        (r'\babove\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None),
        (r'\bmore\s+than\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None),
        
        # "tussen X en Y euro" → min_price = X, max_price = Y
        (r'\btussen\s+(\d+(?:[.,]\d+)?)\s+en\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.'))),
        (r'\bbetween\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.'))),
        
        # "tussen X€ en Y€" → min_price = X, max_price = Y (speciale case voor € symbolen)
        (r'\btussen\s+(\d+(?:[.,]\d+)?)€\s+en\s+(\d+(?:[.,]\d+)?)€\b', 
         lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.'))),
        (r'\bbetween\s+(\d+(?:[.,]\d+)?)€\s+and\s+(\d+(?:[.,]\d+)?)€\b', 
         lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.'))),
        
        # "X tot Y euro" → min_price = X, max_price = Y
        (r'\b(\d+(?:[.,]\d+)?)\s+tot\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.'))),
        (r'\b(\d+(?:[.,]\d+)?)\s+to\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.'))),
        
        # "rond X euro" → min_price = X*0.8, max_price = X*1.2
        (r'\brond\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2),
        (r'\baround\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2),
        
        # "ongeveer X euro" → min_price = X*0.8, max_price = X*1.2
        (r'\bongeveer\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2),
        (r'\bapproximately\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
         lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2),
        
        # "X euro" → min_price = X*0.9, max_price = X*1.1 (exacte prijs)
        (r'\b(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)\b', 
         lambda m: float(m.group(1).replace(',', '.')) * 0.9, lambda m: float(m.group(1).replace(',', '.')) * 1.1),
    ]
    
    # Test alle patronen
    for pattern, min_func, max_func in patterns:
        match = re.search(pattern, query_lower)
        if match:
            try:
                # Bereken min_price
                if min_func is not None:
                    if callable(min_func):
                        min_price = min_func(match)
                    else:
                        min_price = min_func
                
                # Bereken max_price
                if max_func is not None:
                    if callable(max_func):
                        max_price = max_func(match)
                    else:
                        max_price = max_func
                
                logger.info(f"💰 Prijsintentie herkend: min_price={min_price}, max_price={max_price} (patroon: {pattern})")
                break
                
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Fout bij verwerken van prijsintentie: {e}")
                continue
    
    # Als geen prijsintentie gevonden
    if min_price is None and max_price is None:
        logger.info("ℹ️ Geen prijsintentie gevonden in query")
    else:
        logger.info(f"✅ Prijsintentie geëxtraheerd: min_price={min_price}, max_price={max_price}")
    
    return min_price, max_price

def clean_query_from_price_intent(query: str) -> str:
    """
    Verwijdert prijsintenties uit de query om een schone zoekterm te krijgen.
    
    Args:
        query: De originele zoekquery
        
    Returns:
        De query zonder prijsintenties
    """
    if not query:
        return query
    
    query_lower = query.lower()
    cleaned_query = query
    
    # Patronen om te verwijderen (zelfde als in extract_price_intent)
    patterns_to_remove = [
        r'\bgoedkoop\b', r'\bcheap\b', r'\bbudget\b', r'\bvoordelig\b',
        r'\bduur\b', r'\bexpensive\b', r'\bluxe\b', r'\bpremium\b', r'\bexclusief\b',
        r'\bonder\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bbelow\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bless\s+than\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bboven\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\babove\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bmore\s+than\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\btussen\s+\d+(?:[.,]\d+)?\s+en\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bbetween\s+\d+(?:[.,]\d+)?\s+and\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\btussen\s+\d+(?:[.,]\d+)?€\s+en\s+\d+(?:[.,]\d+)?€\b',
        r'\bbetween\s+\d+(?:[.,]\d+)?€\s+and\s+\d+(?:[.,]\d+)?€\b',
        r'\b\d+(?:[.,]\d+)?\s+tot\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\b\d+(?:[.,]\d+)?\s+to\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\brond\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\baround\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bongeveer\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\bapproximately\s+\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)?\b',
        r'\b\d+(?:[.,]\d+)?\s*(?:euro?|€|eur)\b',
    ]
    
    for pattern in patterns_to_remove:
        cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
    
    logger.info(f"🧹 Query opgeschoond: '{query}' → '{cleaned_query}'")
    
    return cleaned_query

def format_price_message(min_price: Optional[float], max_price: Optional[float]) -> str:
    """
    Formatteert een gebruiksvriendelijke melding voor prijsfilters.
    
    Args:
        min_price: Minimum prijs
        max_price: Maximum prijs
        
    Returns:
        Geformatteerde melding
    """
    if min_price is not None and max_price is not None:
        return f"Prijs tussen €{min_price:.2f} en €{max_price:.2f}"
    elif min_price is not None:
        return f"Prijs vanaf €{min_price:.2f}"
    elif max_price is not None:
        return f"Prijs tot €{max_price:.2f}"
    else:
        return "Alle prijzen" 