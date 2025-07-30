# 🔍 AI Search met Prijsfiltering Implementatie

## 📋 Overzicht

Deze implementatie voegt automatische prijsintentie herkenning en filtering toe aan de AI-powered zoek-API. Gebruikers kunnen nu natuurlijke taal gebruiken om prijsfilters toe te passen in combinatie met semantische zoekresultaten.

## 🎯 Functionaliteiten

### ✅ **Semantische Zoekresultaten + Harde Filters**
- **Prijsintentie Herkenning**: Automatische detectie van prijsintenties in zoekqueries
- **Pre-ranking Filtering**: Resultaten worden gefilterd op prijsrange vóór ranking
- **Prijs Sortering**: Gefilterde resultaten worden gesorteerd op prijs (laagste eerst)
- **Intelligente Fallback**: Goedkoopste alternatieven bij geen resultaten in prijsrange

### 🔄 **Pipeline Stappen**
1. **Prijsintentie Extractie**: Herken prijsintenties uit query
2. **Query Opschoning**: Verwijder prijsintenties voor semantische zoekopdracht
3. **Vector Search**: Voer semantische zoekopdracht uit met embeddings
4. **Prijsfiltering**: Filter resultaten op prijsrange vóór ranking
5. **Fallback Mechanisme**: Toon goedkoopste alternatieven indien nodig

### 📊 **Uitgebreide Logging**
- Prijsintentie detectie logging
- Query opschoning logging
- Filter toepassing logging
- Fallback scenario logging

## 🏗️ Architectuur

### Backend (Python/FastAPI)
```python
# products_v2.py
- AI search endpoint met prijsintentie verwerking
- Prijsintentie extractie en query opschoning
- Cache key inclusief prijsfilters

# search_service.py
- ai_search_products_with_price_filter(): Nieuwe hoofdfunctie
- _fallback_text_search(): Uitgebreid met prijsfiltering
- Vector search met prijsfilters in SQL queries
- Fallback naar goedkoopste producten

# price_intent.py
- extract_price_intent(): Prijsintentie extractie
- clean_query_from_price_intent(): Query opschoning
- format_price_message(): Gebruiksvriendelijke meldingen
```

## 🔧 Implementatie Details

### 1. **AI Search Endpoint Aanpassing**
```python
@router.get("/ai-search")
async def ai_search_products(
    query: str = Query(..., description="Natural search term"),
    # ...
):
    # Extract price intent from query
    min_price, max_price = extract_price_intent(query)
    cleaned_query = clean_query_from_price_intent(query)
    
    # Log price intent information
    if min_price is not None or max_price is not None:
        logger.info(f"💰 Prijsfilter toegepast op AI search: min_price={min_price}, max_price={max_price}")
        logger.info(f"🧹 Opgeschoonde query: '{cleaned_query}' (origineel: '{query}')")
    
    # Perform AI search with price filtering
    result = await search_service.ai_search_products_with_price_filter(
        db=db,
        query=cleaned_query,
        min_price=min_price,
        max_price=max_price,
        # ...
    )
```

### 2. **Vector Search met Prijsfiltering**
```python
# Build vector search query with price filtering
sql_query = """
SELECT id, shopify_id, title, description, price, tags,
       1 - (embedding <=> :embedding) as similarity
FROM products 
WHERE embedding IS NOT NULL
"""
params = {"embedding": embedding_str}

# Add price filters if provided
if min_price is not None:
    sql_query += " AND price >= :min_price"
    params["min_price"] = min_price
if max_price is not None:
    sql_query += " AND price <= :max_price"
    params["max_price"] = max_price
```

### 3. **Fallback Mechanisme**
```python
# If no results with price filter, get cheapest alternatives
if total_count == 0 and (min_price is not None or max_price is not None):
    logger.warning(f"⚠️ Geen producten gevonden binnen prijsrange, toon goedkoopste alternatieven")
    
    # Get cheapest products without price filter
    fallback_sql = """
    SELECT id, shopify_id, title, description, price, tags,
           1 - (embedding <=> :embedding) as similarity
    FROM products 
    WHERE embedding IS NOT NULL
    ORDER BY price ASC, similarity DESC
    LIMIT :limit OFFSET :offset
    """
    
    # Create response with fallback message
    response_data = {
        # ... standard fields ...
        "price_filter": {
            "min_price": min_price,
            "max_price": max_price,
            "applied": True,
            "fallback_used": True
        },
        "message": "Geen producten gevonden binnen de prijsklasse, hier zijn de goedkoopste alternatieven."
    }
```

## 📝 Ondersteunde Prijsintenties

### Nederlandse Patronen
| Patroon | Voorbeeld | Resultaat |
|---------|-----------|-----------|
| `goedkoop` | "goedkoop shirt" | max_price = 75 |
| `duur` | "duur horloge" | min_price = 200 |
| `onder X euro` | "onder 50 euro" | max_price = 50 |
| `boven X euro` | "boven 100 euro" | min_price = 100 |
| `tussen X en Y euro` | "tussen 50 en 100 euro" | min_price = 50, max_price = 100 |
| `rond X euro` | "rond 75 euro" | min_price = 60, max_price = 90 |
| `ongeveer X euro` | "ongeveer 100 euro" | min_price = 80, max_price = 120 |
| `X euro` | "100 euro" | min_price = 90, max_price = 110 |

### Engelse Patronen
| Patroon | Voorbeeld | Resultaat |
|---------|-----------|-----------|
| `cheap` | "cheap shoes" | max_price = 75 |
| `expensive` | "expensive watch" | min_price = 200 |
| `below X euros` | "below 30 euros" | max_price = 30 |
| `above X euros` | "above 150 euros" | min_price = 150 |
| `between X and Y euros` | "between 25 and 75 euros" | min_price = 25, max_price = 75 |
| `around X euros` | "around 50 euros" | min_price = 40, max_price = 60 |
| `approximately X euros` | "approximately 80 euros" | min_price = 64, max_price = 96 |

## 🚀 API Response Structuur

### Normale Response
```json
{
  "query": "shirt",
  "results": [
    {
      "id": 1,
      "shopify_id": "123",
      "title": "Blauwe Shirt",
      "description": "Comfortabele blauwe shirt",
      "price": 45.99,
      "tags": ["shirt", "blauw", "katoen"],
      "similarity": 0.85
    }
  ],
  "count": 1,
  "total_count": 1,
  "page": 1,
  "total_pages": 1,
  "limit": 25,
  "cache_hit": false,
  "pagination": {
    "has_next": false,
    "has_prev": false,
    "next_page": null,
    "prev_page": null
  },
  "price_filter": {
    "min_price": null,
    "max_price": 75,
    "applied": true,
    "fallback_used": false
  }
}
```

### Fallback Response
```json
{
  "query": "shirt",
  "results": [
    {
      "id": 2,
      "shopify_id": "124",
      "title": "Goedkope Shirt",
      "description": "Betaalbare shirt",
      "price": 15.99,
      "tags": ["shirt", "goedkoop"],
      "similarity": 0.75
    }
  ],
  "count": 1,
  "total_count": 1,
  "page": 1,
  "total_pages": 1,
  "limit": 25,
  "cache_hit": false,
  "pagination": {
    "has_next": false,
    "has_prev": false,
    "next_page": null,
    "prev_page": null
  },
  "price_filter": {
    "min_price": null,
    "max_price": 75,
    "applied": true,
    "fallback_used": true
  },
  "message": "Geen producten gevonden binnen de prijsklasse, hier zijn de goedkoopste alternatieven."
}
```

## 📊 Logging Voorbeelden

### Backend Logs
```
💰 Prijsfilter toegepast op AI search: min_price=None, max_price=75
🧹 Opgeschoonde query: 'shirt' (origineel: 'goedkoop shirt')
Executing vector search with price filter (page 1/1, total: 5, min_price=None, max_price=75)
✅ AI search met prijsfiltering succesvol: 5 resultaten voor 'shirt'
```

### Fallback Scenario
```
💰 Prijsfilter toegepast op AI search: min_price=200, max_price=10
🧹 Opgeschoonde query: 'shirt' (origineel: 'duur shirt onder 10 euro')
Executing vector search with price filter (page 1/1, total: 0, min_price=200, max_price=10)
⚠️ Geen producten gevonden binnen prijsrange, toon goedkoopste alternatieven
✅ Fallback naar goedkoopste producten: 3 resultaten
```

## 🧪 Testing

### Test Script
```bash
# Run AI search price filter tests
python3 test_ai_search_price_filter.py
```

### Test Scenario's
1. **Normale zoekopdracht** - Geen prijsintentie
2. **Goedkoop zoekopdracht** - max_price = 75
3. **Duur zoekopdracht** - min_price = 200
4. **Prijsrange zoekopdracht** - min_price en max_price
5. **Fallback scenario** - Geen resultaten in prijsrange
6. **Engelse zoekopdrachten** - Alle Engelse patronen

### API Testing
```bash
# Test normale zoekopdracht
curl "http://localhost:8000/api/ai-search?query=blauwe%20shirt"

# Test met prijsintentie
curl "http://localhost:8000/api/ai-search?query=goedkoop%20shirt"

# Test fallback scenario
curl "http://localhost:8000/api/ai-search?query=duur%20shirt%20onder%2010%20euro"
```

## 🔧 Configuratie

### Cache Configuratie
```python
# Cache key inclusief prijsfilters
cache_key = cache_manager.get_cache_key(
    "ai_search", 
    query=search_query, 
    page=page, 
    limit=limit, 
    target_language=target_language,
    min_price=min_price,
    max_price=max_price
)
```

### Analytics Tracking
```python
# Track analytics met prijsfilter informatie
self.analytics_manager.track_search_analytics(
    db, query, "ai", {"price_filter": {"min": min_price, "max": max_price}}, 
    len(results), page, limit, response_time_ms, cache_hit, user_agent, ip_address
)
```

## 📈 Voordelen

1. **Natuurlijke Taal**: Gebruikers kunnen natuurlijk praten over prijzen
2. **Semantische Zoekopdracht**: Behoud van AI-powered zoekfunctionaliteit
3. **Harde Filters**: Precieze prijsfiltering vóór ranking
4. **Intelligente Fallbacks**: Nooit lege resultaten
5. **Cache Optimalisatie**: Prijsfilters worden meegenomen in cache keys
6. **Uitgebreide Logging**: Volledige traceability
7. **API Compatibiliteit**: Behoud van bestaande response structuur

## 🔮 Toekomstige Verbeteringen

1. **Machine Learning**: Slimmere prijsintentie detectie
2. **Meer Filters**: Categorie, merk, kleur filters
3. **Persoonlijke Prijzen**: Gebruikerspecifieke prijsvoorkeuren
4. **A/B Testing**: Verschillende filter strategieën
5. **Analytics**: Uitgebreide prijsfilter analytics
6. **Performance**: Query optimalisatie voor grote datasets
7. **Internationalization**: Ondersteuning voor meer valuta's 