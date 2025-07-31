import re
import logging
from typing import Tuple, Optional, Dict, Any
from functools import lru_cache
import json
import openai

logger = logging.getLogger(__name__)

# Fase 1: Enhanced price intent patterns with better accuracy
PRICE_PATTERNS = [
    # Exact price patterns (hoogste prioriteit)
    (r'\b(\d+(?:[.,]\d+)?)\s*€\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(1).replace(',', '.')), "exact"),
    (r'\b(\d+(?:[.,]\d+)?)\s*(?:euro?|eur)\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(1).replace(',', '.')), "exact"),
    
    # Range patterns (hoge prioriteit)
    (r'\btussen\s+(\d+(?:[.,]\d+)?)\s+en\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    (r'\bbetween\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    (r'\b(\d+(?:[.,]\d+)?)\s+tot\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    (r'\b(\d+(?:[.,]\d+)?)\s+to\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    
    # Below/Above patterns
    (r'\bonder\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.')), "below"),
    (r'\bbelow\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.')), "below"),
    (r'\bless\s+than\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.')), "below"),
    (r'\bboven\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None, "above"),
    (r'\babove\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None, "above"),
    (r'\bmore\s+than\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None, "above"),
    
    # Approximate patterns
    (r'\brond\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    (r'\baround\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    (r'\bongeveer\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    
    # Budget patterns (minder strikt)
    (r'\bgoedkoop\w*\b', None, 100, "budget"),  # goedkoop, goedkope, etc.
    (r'\bcheap\w*\b', None, 100, "budget"),     # cheap, cheaper, etc.
    (r'\bbudget\w*\b', None, 100, "budget"),    # budget, budgetary, etc.
    (r'\bvoordelig\w*\b', None, 100, "budget"), # voordelig, voordelige, etc.
    (r'\baffordable\w*\b', None, 100, "budget"), # affordable, etc.
    (r'\bbetaalbaar\w*\b', None, 100, "budget"), # betaalbaar, betaalbare, etc.
    
    # Premium patterns (minder strikt)
    (r'\bduur\w*\b', 150, None, "premium"),    # duur, dure, duurdere, etc.
    (r'\bexpensive\w*\b', 150, None, "premium"), # expensive, etc.
    (r'\bluxe\w*\b', 150, None, "premium"),    # luxe, luxueus, etc.
    (r'\bpremium\w*\b', 150, None, "premium"), # premium, etc.
    (r'\bexclusief\w*\b', 150, None, "premium"), # exclusief, exclusieve, etc.
    (r'\bhigh-end\b', 150, None, "premium"),   # high-end
    
    # Sale patterns (context-aware)
    (r'\bsale\b', None, 150, "sale"),          # sale items zijn vaak goedkoper
    (r'\buitverkoop\b', None, 150, "sale"),    # uitverkoop
    (r'\bclearance\b', None, 150, "sale"),     # clearance
    (r'\bkorting\b', None, 150, "sale"),       # korting
    (r'\bdiscount\b', None, 150, "sale"),      # discount
    
    # Exact price ranges
    (r'\bonder\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.')), "below"),
    (r'\bbelow\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.')), "below"),
    (r'\bless\s+than\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', None, lambda m: float(m.group(1).replace(',', '.')), "below"),
    
    (r'\bboven\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None, "above"),
    (r'\babove\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None, "above"),
    (r'\bmore\s+than\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', lambda m: float(m.group(1).replace(',', '.')), None, "above"),
    
    # Range patterns
    (r'\btussen\s+(\d+(?:[.,]\d+)?)\s+en\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    (r'\bbetween\s+(\d+(?:[.,]\d+)?)\s+and\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    
    # Special € symbol patterns
    (r'\btussen\s+(\d+(?:[.,]\d+)?)€\s+en\s+(\d+(?:[.,]\d+)?)€\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    (r'\bbetween\s+(\d+(?:[.,]\d+)?)€\s+and\s+(\d+(?:[.,]\d+)?)€\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    
    # "tot" patterns
    (r'\b(\d+(?:[.,]\d+)?)\s+tot\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    (r'\b(\d+(?:[.,]\d+)?)\s+to\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')), lambda m: float(m.group(2).replace(',', '.')), "range"),
    
    # Approximate patterns (rond/ongeveer)
    (r'\brond\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    (r'\baround\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    (r'\bongeveer\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    (r'\bapproximately\s+(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)?\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.8, lambda m: float(m.group(1).replace(',', '.')) * 1.2, "approximate"),
    
    # Exact price patterns
    (r'\b(\d+(?:[.,]\d+)?)\s*(?:euro?|€|eur)\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.9, lambda m: float(m.group(1).replace(',', '.')) * 1.1, "exact"),
    (r'\b(\d+(?:[.,]\d+)?)\s*€\b', 
     lambda m: float(m.group(1).replace(',', '.')) * 0.9, lambda m: float(m.group(1).replace(',', '.')) * 1.1, "exact"),
]

# Fallback budget words for additional detection
BUDGET_FALLBACK_WORDS = [
    'goedkoop', 'goedkope', 'goedkopere', 'goedkoopste',
    'cheap', 'cheaper', 'cheapest',
    'budget', 'budgetary',
    'voordelig', 'voordelige', 'voordeligere',
    'affordable', 'economical', 'inexpensive',
    'betaalbaar', 'betaalbare',
    'sale', 'uitverkoop', 'clearance', 'korting', 'discount'
]

@lru_cache(maxsize=1000)
def extract_price_intent(query: str) -> Tuple[Optional[float], Optional[float], Dict[str, Any]]:
    """
    Extraheert prijsintenties uit een zoekquery met context-aware optimalisaties.
    
    Args:
        query: De zoekquery string
        
    Returns:
        Tuple van (min_price, max_price, metadata) waar beide prijzen None kunnen zijn
    """
    if not query or not query.strip():
        return None, None, {"confidence": 0.0, "pattern_type": None, "extracted_text": None}
    
    query_lower = query.lower().strip()
    min_price = None
    max_price = None
    best_match = None
    confidence = 0.0
    
    logger.info(f"🔍 Analyseren van prijsintentie in query: '{query}'")
    
    # Context-aware price adjustment based on product type
    context_multiplier = _get_context_multiplier(query_lower)
    
    # Test alle patronen en vind de beste match
    for pattern, min_func, max_func, pattern_type in PRICE_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            try:
                # Bereken min_price met context adjustment
                current_min = None
                if min_func is not None:
                    if callable(min_func):
                        current_min = min_func(match) * context_multiplier
                    else:
                        current_min = min_func * context_multiplier
                
                # Bereken max_price met context adjustment
                current_max = None
                if max_func is not None:
                    if callable(max_func):
                        current_max = max_func(match) * context_multiplier
                    else:
                        current_max = max_func * context_multiplier
                
                # Bereken confidence score
                match_length = len(match.group(0))
                query_length = len(query_lower)
                current_confidence = match_length / query_length
                
                # Update beste match als deze hogere confidence heeft
                if current_confidence > confidence:
                    confidence = current_confidence
                    min_price = current_min
                    max_price = current_max
                    best_match = {
                        "pattern_type": pattern_type,
                        "extracted_text": match.group(0),
                        "full_match": match.group(0),
                        "confidence": current_confidence
                    }
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing price pattern '{pattern}': {e}")
                continue
    
    # Fallback: Check for budget words if no pattern matched
    if best_match is None:
        for budget_word in BUDGET_FALLBACK_WORDS:
            if budget_word in query_lower:
                logger.info(f"Fallback budget word detected: '{budget_word}'")
                min_price = None
                max_price = 75
                confidence = 0.8  # High confidence for fallback
                best_match = {
                    "pattern_type": "budget_fallback",
                    "extracted_text": budget_word,
                    "full_match": budget_word,
                    "confidence": confidence
                }
                break
    
    # GPT-powered fallback for complex cases
    if best_match is None:
        logger.info("🔄 Geen pattern match gevonden, probeer GPT-powered analyse...")
        gpt_result = get_dynamic_price_range(query)
        
        if gpt_result.get("confidence", 0) > 0.5:
            min_price = gpt_result.get("min_price")
            max_price = gpt_result.get("max_price")
            confidence = gpt_result.get("confidence", 0.0)
            best_match = {
                "pattern_type": "gpt_analysis",
                "extracted_text": gpt_result.get("reasoning", "GPT analysis"),
                "full_match": query,
                "confidence": confidence,
                "reasoning": gpt_result.get("reasoning", "")
            }
            logger.info(f"🤖 GPT analysis successful: {gpt_result.get('reasoning', '')}")
    
    # Valideer prijzen
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            # Swap als min > max
            min_price, max_price = max_price, min_price
            logger.info("Swapped min_price and max_price due to invalid range")
    
    # Bereken finale confidence
    if best_match:
        confidence = best_match["confidence"]
        # Boost confidence voor exacte matches
        if best_match["pattern_type"] == "exact":
            confidence *= 1.2
        elif best_match["pattern_type"] == "range":
            confidence *= 1.1
        elif best_match["pattern_type"] == "budget_fallback":
            confidence = 0.85  # High confidence for fallback
    
    metadata = {
        "confidence": min(confidence, 1.0),
        "pattern_type": best_match["pattern_type"] if best_match else None,
        "extracted_text": best_match["extracted_text"] if best_match else None,
        "query_length": len(query_lower),
        "reasoning": best_match.get("reasoning", "") if best_match else None
    }
    
    logger.info(f"✅ Prijsintentie geëxtraheerd: min={min_price}, max={max_price}, confidence={confidence:.2f}")
    
    return min_price, max_price, metadata


def _get_context_multiplier(query: str) -> float:
    """
    Bepaalt context-aware price multiplier gebaseerd op product type.
    
    Args:
        query: De zoekquery string
        
    Returns:
        Multiplier voor price ranges (1.0 = default, 2.0 = premium items, 0.7 = budget items)
    """
    query_lower = query.lower()
    
    # Premium product types (hogere prijzen verwacht)
    premium_keywords = [
        # Fashion & Luxury
        'jas', 'jassen', 'coat', 'coats', 'jacket', 'jackets',
        'schoenen', 'shoes', 'boots', 'sneakers',
        'tassen', 'bags', 'handbags', 'purses',
        'juwelen', 'jewelry', 'sieraden', 'accessories',
        'parfum', 'perfume', 'cosmetica', 'cosmetics',
        'designer', 'luxe', 'premium', 'exclusief',
        
        # Art & Collectibles
        'beeldjes', 'beelden', 'sculpturen', 'sculptures', 'kunst', 'art',
        'antiek', 'antique', 'vintage', 'collector', 'collectie',
        'horloges', 'watches', 'klokken', 'clocks',
        'meubels', 'furniture', 'design', 'interieur',
        
        # Tech & Electronics
        'tech', 'electronics', 'smartphone', 'laptop', 'computer', 'tablet', 'camera', 'drone',
        'gaming', 'console', 'headphones', 'speakers', 'smartwatch', 'fitness', 'wearables',
        'iphone', 'samsung', 'macbook', 'dell', 'sony', 'canon', 'nikon',
        
        # Automotive
        'car', 'automotive', 'auto', 'vehicle', 'parts', 'accessories', 'maintenance',
        'upgrade', 'modification', 'performance', 'bmw', 'mercedes', 'audi',
        
        # Musical Instruments
        'music', 'instrument', 'guitar', 'piano', 'drums', 'violin', 'saxophone',
        'professional', 'amateur', 'acoustic', 'electric', 'yamaha', 'fender', 'gibson',
        
        # High-end Sport
        'premium sport', 'luxury fitness', 'professional equipment', 'competition gear'
    ]
    
    # Budget product types (lagere prijzen verwacht)
    budget_keywords = [
        # Basic Fashion
        'shirts', 'tshirts', 't-shirts', 'tops', 'blouses',
        'broeken', 'pants', 'trousers', 'jeans',
        'sokken', 'socks', 'ondergoed', 'underwear',
        'basic', 'casual', 'everyday', 'dagelijks',
        
        # Home & Garden
        'kleine', 'mini', 'decoratie', 'decoration', 'accessoires', 'accessories',
        'keuken', 'kitchen', 'badkamer', 'bathroom', 'tuin', 'garden',
        
        # Books & Media
        'books', 'ebooks', 'audiobooks', 'magazines', 'comics', 'manga', 'textbooks',
        'educational', 'fiction', 'non-fiction', 'paperback', 'hardcover',
        
        # Baby & Kids
        'baby', 'kids', 'children', 'toys', 'games', 'educational', 'nursery', 'stroller',
        'car seat', 'baby clothes', 'diapers', 'feeding', 'playtime', 'learning',
        
        # Pet Supplies
        'pet', 'dog', 'cat', 'food', 'toys', 'accessories', 'health', 'grooming',
        'bedding', 'carrier', 'training', 'veterinary', 'care',
        
        # Basic Sport
        'basic sport', 'casual fitness', 'home workout', 'simple equipment',
        
        # Basic Tools
        'basic tools', 'simple diy', 'home repair', 'small projects'
    ]
    
    # Check voor premium keywords
    for keyword in premium_keywords:
        if keyword in query_lower:
            return 2.0  # Premium items zijn duurder
    
    # Check voor budget keywords
    for keyword in budget_keywords:
        if keyword in query_lower:
            return 0.7  # Budget items zijn goedkoper
    
    # Default multiplier
    return 1.0


def get_dynamic_price_range(query: str) -> Dict[str, Any]:
    """
    Gebruik GPT om dynamisch prijsbereik te bepalen op basis van product type en context.
    
    Args:
        query: De zoekquery string
        
    Returns:
        Dict met min_price, max_price, confidence en reasoning
    """
    prompt = f"""Analyseer deze zoekterm: {query}.
• Herken expliciete prijsindicaties (bijv. 'onder €50', 'boven 200 euro', 'tussen 100 en 500').
• Herken impliciete prijsintenties (bijv. 'goedkoop', 'budget', 'luxe', 'exclusief').
• Interpreteer 'goedkoop' of 'duur' relatief aan het producttype en het algemene prijsniveau van die categorie.
• Als er geen directe prijs staat: schat een realistisch prijskader voor dit type product (bv. schilderijen, kleding, meubels), op basis van marktkennis.
• Lever output in dit formaat:

{{
  "min_price": <float|null>,
  "max_price": <float|null>,
  "confidence": <0.0-1.0>,
  "reasoning": "<korte uitleg waarom deze range gekozen is>"
}}

Voorbeelden:
- "goedkope schoenen" → {{"min_price": null, "max_price": 100, "confidence": 0.8, "reasoning": "Schoenen zijn premium items, goedkoop betekent onder €100"}}
- "duur exclusief jas" → {{"min_price": 200, "max_price": null, "confidence": 0.9, "reasoning": "Jassen zijn premium items, duur betekent boven €200"}}
- "beeldjes onder €500" → {{"min_price": null, "max_price": 500, "confidence": 0.95, "reasoning": "Expliciete prijsindicatie voor beeldjes"}}
- "betaalbare casual shirts" → {{"min_price": null, "max_price": 50, "confidence": 0.7, "reasoning": "Shirts zijn budget items, betaalbaar betekent onder €50"}}
- "goedkope smartphone" → {{"min_price": null, "max_price": 300, "confidence": 0.8, "reasoning": "Smartphones zijn premium tech items, goedkoop betekent onder €300"}}
- "professionele camera" → {{"min_price": 500, "max_price": null, "confidence": 0.9, "reasoning": "Professionele camera's zijn premium items, vanaf €500"}}
- "baby spullen" → {{"min_price": null, "max_price": 100, "confidence": 0.7, "reasoning": "Baby items zijn budget-friendly, max €100"}}
- "gaming laptop" → {{"min_price": 800, "max_price": null, "confidence": 0.9, "reasoning": "Gaming laptops zijn premium tech, vanaf €800"}}
- "gitaar voor beginners" → {{"min_price": null, "max_price": 200, "confidence": 0.8, "reasoning": "Beginner gitaren zijn betaalbaar, max €200"}}
- "auto onderdelen" → {{"min_price": null, "max_price": 500, "confidence": 0.7, "reasoning": "Auto onderdelen variëren, max €500 voor algemene delen"}}"""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Je bent een expert in e-commerce prijsanalyse. Geef alleen geldige JSON terug."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            result = json.loads(result_text)
            logger.info(f"🤖 GPT price analysis: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response: {e}")
            return {"min_price": None, "max_price": None, "confidence": 0.0, "reasoning": "JSON parse error"}
            
    except Exception as e:
        logger.error(f"GPT price analysis failed: {e}")
        return {"min_price": None, "max_price": None, "confidence": 0.0, "reasoning": f"GPT error: {str(e)}"}


def clean_query_from_price_intent(query: str) -> str:
    """
    Verwijder prijsintenties uit de query voor betere search results.
    Fase 1: Enhanced met betere pattern matching.
    """
    if not query:
        return query
    
    query_lower = query.lower()
    cleaned_query = query
    
    # Verwijder alle prijs patterns
    for pattern, _, _, _ in PRICE_PATTERNS:
        cleaned_query = re.sub(pattern, '', cleaned_query, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
    
    # Als de query leeg is geworden, gebruik de originele
    if not cleaned_query:
        return query
    
    logger.info(f"🧹 Query opgeschoond: '{query}' → '{cleaned_query}'")
    return cleaned_query

def format_price_message(min_price: Optional[float], max_price: Optional[float], metadata: Dict[str, Any] = None) -> str:
    """
    Format een gebruiksvriendelijke prijsbericht.
    Fase 1: Enhanced met confidence en pattern type informatie.
    """
    if min_price is None and max_price is None:
        return "Geen prijsfilter toegepast."
    
    confidence = metadata.get("confidence", 0.0) if metadata else 0.0
    pattern_type = metadata.get("pattern_type", "unknown") if metadata else "unknown"
    
    # Confidence indicator
    confidence_text = ""
    if confidence > 0.8:
        confidence_text = " (hoog vertrouwen)"
    elif confidence > 0.5:
        confidence_text = " (gemiddeld vertrouwen)"
    else:
        confidence_text = " (laag vertrouwen)"
    
    # Prijsbericht
    if min_price is not None and max_price is not None:
        if min_price == max_price:
            return f"Zoeken naar producten rond €{min_price:.2f}{confidence_text}"
        else:
            return f"Zoeken naar producten tussen €{min_price:.2f} en €{max_price:.2f}{confidence_text}"
    elif min_price is not None:
        return f"Zoeken naar producten vanaf €{min_price:.2f}{confidence_text}"
    elif max_price is not None:
        return f"Zoeken naar producten tot €{max_price:.2f}{confidence_text}"
    
    return "Geen prijsfilter toegepast."

def validate_price_range(min_price: Optional[float], max_price: Optional[float]) -> bool:
    """
    Valideer een prijsbereik.
    
    Args:
        min_price: Minimum prijs
        max_price: Maximum prijs
        
    Returns:
        True als het bereik geldig is
    """
    if min_price is not None and min_price < 0:
        logger.warning(f"Invalid min_price: {min_price} (must be >= 0)")
        return False
    
    if max_price is not None and max_price < 0:
        logger.warning(f"Invalid max_price: {max_price} (must be >= 0)")
        return False
    
    if min_price is not None and max_price is not None and min_price > max_price:
        logger.warning(f"Invalid price range: {min_price} > {max_price}")
        return False
    
    return True

def get_price_category(price: float) -> str:
    """
    Categoriseer een prijs in budget, midden, of premium.
    
    Args:
        price: Prijs in euro
        
    Returns:
        Prijscategorie
    """
    if price < 50:
        return "budget"
    elif price < 200:
        return "midden"
    else:
        return "premium" 