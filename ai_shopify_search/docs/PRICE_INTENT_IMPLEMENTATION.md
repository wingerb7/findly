# 💰 Prijsintentie Implementatie

## 📋 Overzicht

Deze implementatie voegt automatische prijsintentie herkenning toe aan de zoekfunctie. Gebruikers kunnen nu natuurlijke taal gebruiken om prijsfilters toe te passen, zoals "goedkoop", "duur", "onder 50 euro", etc.

## 🎯 Functionaliteiten

### ✅ **Automatische Prijsintentie Herkenning**
- **Nederlandse termen**: goedkoop, duur, onder, boven, tussen, rond, ongeveer
- **Engelse termen**: cheap, expensive, below, above, between, around, approximately
- **Prijsranges**: "tussen 50 en 100 euro", "50 tot 100 euro"
- **Exacte prijzen**: "100 euro" → range rond die prijs

### 🔄 **Intelligente Prijsberekening**
- **Goedkoop**: max_price = 75
- **Duur**: min_price = 200
- **Onder X**: max_price = X
- **Boven X**: min_price = X
- **Tussen X en Y**: min_price = X, max_price = Y
- **Rond X**: min_price = X*0.8, max_price = X*1.2
- **X euro**: min_price = X*0.9, max_price = X*1.1

### 📊 **Uitgebreide Logging**
- Prijsintentie detectie logging
- Query opschoning logging
- Filter toepassing logging
- Fallback logging voor geen resultaten

## 🏗️ Architectuur

### Backend (Python/FastAPI)
```python
# price_intent.py
- extract_price_intent(): Herkent prijsintenties
- clean_query_from_price_intent(): Verwijdert prijsintenties uit query
- format_price_message(): Formatteert gebruiksvriendelijke meldingen

# products_v2.py
- Autocomplete endpoint met prijsfiltering
- Cache key inclusief prijsfilters
- Fallback naar goedkoopste producten

# search_service.py
- Nieuwe functies met prijsfiltering
- Database queries met prijsfilters
- Goedkoopste producten fallback
```

### Frontend (React/TypeScript)
```typescript
// Search.tsx
- Prijsfilter state management
- Visuele prijsfilter indicatie
- Alternatieve meldingen voor geen resultaten
- Prijsweergave in suggesties
```

## 🔧 Implementatie Details

### 1. **Prijsintentie Extractie**
```python
def extract_price_intent(query: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extraheert prijsintenties uit een zoekquery.
    
    Voorbeelden:
    - "goedkoop shirt" → (None, 75)
    - "duur horloge" → (200, None)
    - "onder 50 euro" → (None, 50)
    - "tussen 50 en 100 euro" → (50, 100)
    """
```

### 2. **Query Opschoning**
```python
def clean_query_from_price_intent(query: str) -> str:
    """
    Verwijdert prijsintenties uit de query.
    
    Voorbeelden:
    - "goedkoop blauwe shirt" → "blauwe shirt"
    - "tussen 50 en 100 euro horloge" → "horloge"
    """
```

### 3. **Autocomplete met Prijsfiltering**
```python
@router.get("/suggestions/autocomplete")
async def get_autocomplete_suggestions_endpoint(
    query: str = Query(..., description="Query for autocomplete"),
    # ...
):
    # Extract price intent
    min_price, max_price = extract_price_intent(query)
    cleaned_query = clean_query_from_price_intent(query)
    
    # Apply price filters to all suggestion types
    suggestions = search_service.get_autocomplete_suggestions_with_price_filter(
        db, cleaned_query, limit, min_price, max_price
    )
    
    # Fallback to cheapest products if no results
    if len(suggestions) == 0 and (min_price or max_price):
        suggestions = search_service.get_cheapest_product_suggestions(db, limit)
```

## 📝 Ondersteunde Patronen

### Nederlandse Patronen
| Patroon | Voorbeeld | Resultaat |
|---------|-----------|-----------|
| `goedkoop` | "goedkoop shirt" | max_price = 75 |
| `duur` | "duur horloge" | min_price = 200 |
| `onder X euro` | "onder 50 euro" | max_price = 50 |
| `boven X euro` | "boven 100 euro" | min_price = 100 |
| `tussen X en Y euro` | "tussen 50 en 100 euro" | min_price = 50, max_price = 100 |
| `X tot Y euro` | "50 tot 100 euro" | min_price = 50, max_price = 100 |
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
| `X to Y euros` | "25 to 75 euros" | min_price = 25, max_price = 75 |
| `around X euros` | "around 50 euros" | min_price = 40, max_price = 60 |
| `approximately X euros` | "approximately 80 euros" | min_price = 64, max_price = 96 |

## 🎨 UI Features

### Visuele Prijsfilter Indicatie
- Blue indicator rechts onder search input
- Toont actieve prijsfilter (bijv. "Prijs tot €75")
- Real-time feedback voor gebruiker

### Alternatieve Meldingen
- Orange waarschuwing als geen producten in prijsrange
- "Geen producten gevonden binnen de prijsklasse, hier zijn de goedkoopste alternatieven"
- Goedkoopste producten worden getoond als fallback

### Prijsweergave
- Prijzen worden getoond bij suggesties waar beschikbaar
- Green prijsindicatie (€X.XX)
- Helpt gebruiker bij beslissing

## 🚀 Gebruik

### 1. **Normale Zoekopdracht**
```
Gebruiker typt: "blauwe shirt"
→ Geen prijsintentie gedetecteerd
→ Alle suggesties getoond
```

### 2. **Prijsintentie Zoekopdracht**
```
Gebruiker typt: "goedkoop blauwe shirt"
→ Prijsintentie gedetecteerd: max_price = 75
→ Opgeschoonde query: "blauwe shirt"
→ Alleen suggesties onder €75 getoond
```

### 3. **Geen Resultaten in Prijsrange**
```
Gebruiker typt: "duur shirt onder 10 euro"
→ Prijsintentie gedetecteerd: min_price = 200, max_price = 10
→ Conflicterende filters
→ Goedkoopste alternatieven getoond
→ Waarschuwing: "Geen producten gevonden binnen de prijsklasse..."
```

## 📊 Logging Voorbeelden

### Backend Logs
```
🔍 Analyseren van prijsintentie in query: 'goedkoop blauwe shirt'
💰 Prijsintentie herkend: min_price=None, max_price=75 (patroon: \bgoedkoop\b)
🧹 Query opgeschoond: 'goedkoop blauwe shirt' → 'blauwe shirt'
💰 Prijsfilter toegepast: min_price=None, max_price=75
🧹 Opgeschoonde query: 'blauwe shirt'
💰 Autocomplete suggestions met prijsfilter: 8 resultaten (min_price=None, max_price=75)
✅ Autocomplete suggestions succesvol gegenereerd: 8 suggesties voor 'blauwe shirt' (met prijsfilter)
```

### Frontend Logs
```
💰 Prijsfilter toegepast: Prijs tot €75.00
✅ Autocomplete succesvol opgehaald voor query: "blauwe shirt"
```

## 🔧 Configuratie

### Prijsdrempels
```python
# In price_intent.py
GOEDKOOP_MAX_PRICE = 75      # "goedkoop" → max_price = 75
DUUR_MIN_PRICE = 200         # "duur" → min_price = 200

# Prijsrange berekeningen
ROND_FACTOR = 0.2            # "rond X" → X ± 20%
EXACT_FACTOR = 0.1           # "X euro" → X ± 10%
```

### Cache Configuratie
```python
# Cache key inclusief prijsfilters
cache_key = cache_manager.get_cache_key(
    "autocomplete", 
    query=cleaned_query, 
    min_price=min_price,
    max_price=max_price
)
```

## 🧪 Testing

### Test Script
```bash
# Run prijsintentie tests
python3 test_price_intent.py
```

### Test Scenario's
1. **Nederlandse prijsintenties** - Alle Nederlandse patronen
2. **Engelse prijsintenties** - Alle Engelse patronen
3. **Edge cases** - Komma's, hoofdletters, verschillende valuta notaties
4. **Geen prijsintentie** - Normale zoekopdrachten
5. **Conflicterende filters** - "duur goedkoop"

### API Testing
```bash
# Test autocomplete met prijsintentie
curl "http://localhost:8000/api/suggestions/autocomplete?query=goedkoop%20shirt"

# Response bevat prijsfilter informatie
{
  "query": "shirt",
  "original_query": "goedkoop shirt",
  "price_filter": {
    "min_price": null,
    "max_price": 75,
    "applied": true,
    "message": "Prijs tot €75.00"
  },
  "suggestions": [...]
}
```

## 📈 Voordelen

1. **Natuurlijke Taal**: Gebruikers kunnen natuurlijk praten over prijzen
2. **Automatische Filtering**: Geen handmatige prijsfilters nodig
3. **Intelligente Fallbacks**: Goedkoopste alternatieven bij geen resultaten
4. **Uitgebreide Logging**: Volledige traceability van prijsintentie verwerking
5. **Cache Optimalisatie**: Prijsfilters worden meegenomen in cache keys
6. **Multi-language**: Ondersteuning voor Nederlands en Engels
7. **Flexibele Patronen**: Verschillende manieren om prijzen uit te drukken

## 🔮 Toekomstige Verbeteringen

1. **Machine Learning**: Slimmere prijsintentie detectie
2. **Meer Talen**: Ondersteuning voor andere talen
3. **Dynamische Drempels**: Aanpasbare prijsdrempels per categorie
4. **Persoonlijke Prijzen**: Gebruikerspecifieke prijsvoorkeuren
5. **A/B Testing**: Verschillende prijsintentie strategieën
6. **Analytics**: Tracking van prijsintentie gebruik
7. **Voice Search**: Spraakgestuurde prijsintenties 