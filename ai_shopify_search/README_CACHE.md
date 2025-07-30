# 🚀 Caching, Pagination, Faceted Search, Analytics, Query Suggestions & Multi-language Support - AI Shopify Search

## 📋 Overzicht

Deze implementatie voegt Redis caching, geavanceerde pagination, faceted search, search analytics, query suggestions en multi-language support toe aan het AI Shopify Search systeem voor verbeterde performance, gebruikerservaring, zoekfunctionaliteit, inzicht in gebruikersgedrag, intelligente zoekassistentie en internationale ondersteuning.

## 🛠️ Installatie

### 1. Redis Installeren

**macOS (met Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Docker:**
```bash
docker run -d --name redis -p 6379:6379 redis:alpine
```

### 2. Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Migratie

Voer de database migratie uit om de analytics en suggestions tabellen aan te maken:

```bash
# Maak de nieuwe tabellen aan
python -c "from ai_shopify_search.database import engine; from ai_shopify_search.models import Base; Base.metadata.create_all(bind=engine)"
```

### 4. Environment Variables

Maak een `.env` bestand aan met de volgende variabelen:

```env
# Database configuratie
DATABASE_URL=postgresql://user:password@localhost/findly

# Redis configuratie
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Cache instellingen (in seconden)
CACHE_TTL=3600
SEARCH_CACHE_TTL=1800
AI_SEARCH_CACHE_TTL=900

# OpenAI configuratie
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=text-embedding-ada-002

# Shopify configuratie
SHOPIFY_API_KEY=your_shopify_api_key_here
SHOPIFY_API_SECRET=your_shopify_api_secret_here
SHOPIFY_STORE_URL=your-store.myshopify.com

# App instellingen
DEBUG=False
LOG_LEVEL=INFO
```

## 🔧 Nieuwe Endpoints

### Cache Management

- `DELETE /cache/clear` - Clear alle product cache
- `GET /cache/stats` - Haal cache statistieken op

### Pagination Endpoints

- `GET /products` - Alle producten met offset/limit pagination
- `GET /products/cursor` - Producten met cursor-based pagination
- `GET /search` - Zoeken met pagination en faceted filtering (30 min TTL)
- `GET /ai-search` - AI zoeken met pagination en faceted filtering (15 min TTL)
- `POST /import-products` - Invalideert cache na updates

### Faceted Search Endpoints

- `GET /faceted-search` - Geavanceerde faceted search met filtering
- `GET /facets` - Beschikbare facetten en aggregaties
- `GET /trending` - Trending zoektermen en populaire facetten

### Analytics Endpoints

- `POST /track-click` - Track product clicks
- `GET /analytics/performance` - Performance analytics
- `GET /analytics/popular-searches` - Populaire zoektermen analytics
- `GET /analytics/facet-usage` - Facet usage analytics

### Query Suggestions Endpoints

- `GET /suggestions/autocomplete` - Autocomplete suggestions
- `GET /suggestions/popular` - Populaire suggestions
- `GET /suggestions/related` - Gerelateerde suggestions
- `GET /suggestions/corrections` - Query correcties
- `POST /suggestions/feedback` - Submit suggestion feedback
- `POST /suggestions/correction` - Submit query correctie
- `POST /suggestions/manage` - Beheer suggestions handmatig
- `GET /suggestions/stats` - Suggestions statistieken

### Multi-language Support Endpoints

- `GET /languages/supported` - Ondersteunde talen
- `POST /languages/detect` - Taal detectie
- `GET /languages/translate` - Tekst vertaling
- `GET /languages/localized-facets` - Gelokaliseerde facetten
- `GET /languages/localized-suggestions` - Gelokaliseerde suggestions
- `POST /languages/localized-facet` - Voeg gelokaliseerde facet toe
- `POST /languages/localized-suggestion` - Voeg gelokaliseerde suggestion toe

## 📊 Multi-language Support Functionaliteit

### Ondersteunde Talen

1. **English (en)** - Standaard taal
2. **Nederlands (nl)** - Nederlandse ondersteuning
3. **Deutsch (de)** - Duitse ondersteuning
4. **Français (fr)** - Franse ondersteuning
5. **Español (es)** - Spaanse ondersteuning
6. **Italiano (it)** - Italiaanse ondersteuning
7. **Português (pt)** - Portugese ondersteuning
8. **Svenska (sv)** - Zweedse ondersteuning
9. **Dansk (da)** - Deense ondersteuning
10. **Norsk (no)** - Noorse ondersteuning

### Features

- **Automatic Language Detection** - Detecteert automatisch de taal van queries
- **Query Translation** - Vertaalt queries voor zoeken in database
- **Result Localization** - Lokaliseert zoekresultaten naar doel taal
- **Localized Facets** - Gelokaliseerde facetten en filters
- **Localized Suggestions** - Taal-specifieke autocomplete suggestions
- **Translation Memory** - Slaat vertalingen op voor hergebruik
- **Fallback Support** - Valt terug op originele taal als vertaling niet beschikbaar is

### Translation Types

- **Query Translation** - Vertaalt zoekqueries
- **Product Translation** - Vertaalt product titels en beschrijvingen
- **Facet Translation** - Vertaalt facet waarden (kleuren, materialen, etc.)
- **Suggestion Translation** - Vertaalt autocomplete suggestions

## 📊 Query Suggestions Functionaliteit

### Suggestion Types

1. **Autocomplete** - Real-time suggestions tijdens typen
2. **Popular** - Meest gebruikte zoektermen
3. **Related** - Gerelateerde zoektermen
4. **Corrections** - Spelfout correcties
5. **Product-based** - Suggestions uit product data

### Features

- **Fuzzy Matching** - Typo-tolerantie met similarity scoring
- **Context-aware** - Suggestions gebaseerd op gebruikerscontext
- **Real-time** - Instant suggestions tijdens typen
- **Feedback Loop** - Leert van gebruikersgedrag
- **Performance Optimized** - Cached suggestions voor snelle response

### Suggestion Sources

- **Database Suggestions** - Opgeslagen suggestions met statistieken
- **Popular Searches** - Meest gebruikte zoektermen
- **Product Data** - Dynamisch gegenereerd uit product titels en tags
- **User Feedback** - Leert van click-through rates

## 📊 Analytics Functionaliteit

### Tracked Metrics

1. **Search Analytics**
   - Query terms en search types
   - Response times en cache hits
   - Filters en pagination parameters
   - User agent en IP address

2. **Click Analytics**
   - Product clicks en positions
   - Click-through rates
   - Time to click metrics

3. **Performance Analytics**
   - Daily performance metrics
   - Search type comparisons
   - Cache hit rates
   - Average response times

4. **Popular Searches**
   - Most searched terms
   - Click-through rates per term
   - Average click positions

5. **Facet Usage**
   - Most used filters
   - Facet type popularity
   - Usage patterns

### Analytics Database Schema

- **search_analytics** - Search query tracking
- **search_clicks** - Product click tracking
- **search_performance** - Daily performance metrics
- **popular_searches** - Popular search terms
- **facet_usage** - Facet usage statistics
- **query_suggestions** - Query suggestions data
- **search_corrections** - Query corrections data
- **language_detection** - Language detection data
- **translations** - Translation memory
- **localized_facets** - Localized facet values
- **localized_suggestions** - Localized suggestion data

## 📊 Faceted Search Functionaliteit

### Ondersteunde Facetten

1. **Categorieën** - Shirts, broeken, jassen, schoenen, truien
2. **Kleuren** - Zwart, wit, blauw, groen, geel, rood, paars, grijs, beige
3. **Materialen** - Katoen, wol, linnen, leer, polyester, denim
4. **Merken** - StyleHub, UrbanWear, Fashionista, Trendify, ClassicLine
5. **Maten** - XS, S, M, L, XL, 36-44 (schoenen)
6. **Prijsbereiken** - 0-25, 25-50, 50-100, 100-200, 200+

### Facet Types

- **Single Select** - Categorieën (één keuze)
- **Multi Select** - Kleuren, materialen, merken, maten (meerdere keuzes)
- **Range** - Prijsbereiken (min/max waarden)

## 📊 Pagination Strategieën

### 1. Offset/Limit Pagination

**Gebruik:** Voor kleine tot middelgrote datasets
**Endpoint:** `GET /products?page=1&limit=50`

```json
{
  "products": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_count": 1250,
    "total_pages": 25,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  }
}
```

### 2. Cursor-based Pagination

**Gebruik:** Voor grote datasets en real-time data
**Endpoint:** `GET /products/cursor?cursor=123&limit=50`

```json
{
  "products": [...],
  "pagination": {
    "has_more": true,
    "next_cursor": "456",
    "limit": 50
  }
}
```

### 3. Search Pagination

**Basis zoeken:** `GET /search?query=shirt&page=1&limit=50`
**AI zoeken:** `GET /ai-search?query=comfortable shirt&page=1&limit=25`

## 📊 Cache Strategie

### TTL (Time To Live) Instellingen

- **Basis cache**: 1 uur (3600 seconden)
- **Zoekresultaten**: 30 minuten (1800 seconden)
- **AI zoekresultaten**: 15 minuten (900 seconden)

### Cache Keys

- `search:{hash}` - Voor basis zoekresultaten
- `ai_search:{hash}` - Voor AI zoekresultaten
- `products:{hash}` - Voor product lijsten
- `products_cursor:{hash}` - Voor cursor-based pagination
- `faceted_search:{hash}` - Voor faceted search resultaten
- `facets:{hash}` - Voor facet aggregaties
- `trending:{hash}` - Voor trending searches
- `autocomplete:{hash}` - Voor autocomplete suggestions
- `popular_suggestions:{hash}` - Voor populaire suggestions
- `related_suggestions:{hash}` - Voor gerelateerde suggestions
- `query_corrections:{hash}` - Voor query correcties
- `language_detection:{hash}` - Voor taal detectie resultaten
- `translations:{hash}` - Voor vertalingen
- `localized_facets:{hash}` - Voor gelokaliseerde facetten
- `localized_suggestions:{hash}` - Voor gelokaliseerde suggestions

## 🚀 Performance Verbeteringen

### Voordelen

1. **Snellere Response Times**: Cached queries zijn 10-100x sneller
2. **Minder Database Load**: Vermindert PostgreSQL queries
3. **Betere User Experience**: Consistente response times
4. **Schaalbaarheid**: Kan meer gelijktijdige gebruikers aan
5. **Efficiënte Pagination**: Geen performance issues bij grote datasets
6. **Flexibele Sortering**: Ondersteunt verschillende sorteeropties
7. **Geavanceerde Filtering**: Faceted search met real-time aggregaties
8. **Trending Analytics**: Populaire zoektermen en facetten
9. **Performance Monitoring**: Real-time performance tracking
10. **User Behavior Insights**: Click-through rates en search patterns
11. **Intelligent Suggestions**: Context-aware autocomplete
12. **Typo Tolerance**: Fuzzy matching voor betere zoekresultaten
13. **Multi-language Support**: Automatische taal detectie en vertaling
14. **International UX**: Gelokaliseerde content en suggestions
15. **Translation Memory**: Efficiënte vertaling caching

### Query Suggestions Voordelen

- **Improved UX**: Real-time autocomplete tijdens typen
- **Reduced Search Friction**: Snellere en accuratere zoekopdrachten
- **Learning System**: Leert van gebruikersgedrag en feedback
- **Typo Correction**: Automatische spelfout correcties
- **Context Awareness**: Suggestions gebaseerd op gebruikerscontext

### Multi-language Support Voordelen

- **Global Reach**: Ondersteuning voor internationale gebruikers
- **Automatic Detection**: Geen handmatige taal selectie nodig
- **Seamless Translation**: Transparante vertaling van queries en resultaten
- **Localized Experience**: Content aangepast aan gebruiker's taal
- **Translation Efficiency**: Cached vertalingen voor snelle response

### Analytics Voordelen

- **Performance Monitoring**: Track response times en cache hit rates
- **User Behavior Analysis**: Begrijp hoe gebruikers zoeken
- **Search Optimization**: Identificeer populaire zoektermen
- **Facet Optimization**: Zie welke filters het meest gebruikt worden
- **Click-through Analysis**: Meet de effectiviteit van zoekresultaten

## 📈 API Voorbeelden

### Multi-language Support

```bash
# Ondersteunde talen
curl "http://localhost:8000/languages/supported"

# Taal detectie
curl -X POST "http://localhost:8000/languages/detect?query=blauwe shirt&user_language=nl"

# Tekst vertaling
curl "http://localhost:8000/languages/translate?text=comfortable shirt&source_language=en&target_language=nl&translation_type=query"

# Gelokaliseerde facetten
curl "http://localhost:8000/languages/localized-facets?facet_type=color&language=nl"

# Gelokaliseerde suggestions
curl "http://localhost:8000/languages/localized-suggestions?language=nl&suggestion_type=autocomplete&limit=10"

# Voeg gelokaliseerde facet toe
curl -X POST "http://localhost:8000/languages/localized-facet?facet_type=color&facet_value=blue&language=nl&localized_value=blauw"

# Voeg gelokaliseerde suggestion toe
curl -X POST "http://localhost:8000/languages/localized-suggestion?original_suggestion=comfortable shirt&language=nl&localized_suggestion=comfortabele shirt&suggestion_type=autocomplete"
```

### Multi-language Search

```bash
# Zoeken met automatische taal detectie
curl "http://localhost:8000/search?query=blauwe shirt&target_language=en"

# AI zoeken met taal detectie
curl "http://localhost:8000/ai-search?query=comfortabele werk shirt&source_language=nl&target_language=en"

# Zoeken met handmatige taal specificatie
curl "http://localhost:8000/search?query=blue shirt&source_language=en&target_language=nl"
```

### Query Suggestions

```bash
# Autocomplete suggestions
curl "http://localhost:8000/suggestions/autocomplete?query=shir&limit=10&include_popular=true&include_related=true"

# Populaire suggestions
curl "http://localhost:8000/suggestions/popular?limit=20&min_searches=5"

# Gerelateerde suggestions
curl "http://localhost:8000/suggestions/related?query=comfortable shirt&limit=10"

# Query correcties
curl "http://localhost:8000/suggestions/corrections?query=shirt"

# Submit suggestion feedback
curl -X POST "http://localhost:8000/suggestions/feedback?suggestion=comfortable shirt&suggestion_type=autocomplete&was_clicked=true"

# Submit query correctie
curl -X POST "http://localhost:8000/suggestions/correction?original_query=shirt&corrected_query=shirt&correction_type=spelling&confidence=0.9"

# Beheer suggestions
curl -X POST "http://localhost:8000/suggestions/manage?action=add&suggestion=comfortable work shirt&suggestion_type=autocomplete&relevance_score=0.8"

# Suggestions statistieken
curl "http://localhost:8000/suggestions/stats?suggestion_type=autocomplete&limit=20"
```

### Analytics

```bash
# Performance analytics
curl "http://localhost:8000/analytics/performance?start_date=2024-01-01&end_date=2024-01-31&search_type=basic"

# Populaire zoektermen
curl "http://localhost:8000/analytics/popular-searches?limit=20&min_searches=5"

# Facet usage analytics
curl "http://localhost:8000/analytics/facet-usage?facet_type=color&limit=10"

# Track product click
curl -X POST "http://localhost:8000/track-click?search_analytics_id=123&product_id=456&position=3&click_time_ms=2500"
```

### Faceted Search

```bash
# Basis faceted search
curl "http://localhost:8000/faceted-search?query=shirt&category=shirt&color=blauw&min_price=20&max_price=100"

# Faceted search met aggregaties
curl "http://localhost:8000/faceted-search?query=shirt&include_aggregations=true"

# Multi-facet filtering
curl "http://localhost:8000/faceted-search?category=shirt&material=katoen&brand=stylehub&size=m"
```

### Beschikbare Facetten

```bash
# Alle beschikbare facetten
curl "http://localhost:8000/facets"

# Context-specifieke facetten
curl "http://localhost:8000/facets?query=shirt"
```

### Trending Searches

```bash
# Trending zoektermen
curl "http://localhost:8000/trending?limit=10"
```

### Basis Zoeken met Analytics

```bash
# Zoeken met analytics tracking
curl "http://localhost:8000/search?query=shirt&color=blauw&user_agent=Mozilla&ip_address=192.168.1.1"

# AI zoeken met analytics tracking
curl "http://localhost:8000/ai-search?query=comfortable work shirt&category=shirt&user_agent=Mozilla&ip_address=192.168.1.1"
```

### Cursor-based Pagination

```bash
# Eerste pagina
curl "http://localhost:8000/products/cursor?limit=50&sort_by=price&sort_order=asc"

# Volgende pagina (met cursor)
curl "http://localhost:8000/products/cursor?cursor=123&limit=50&sort_by=price&sort_order=asc"
```

### Sortering

```bash
# Sorteren op prijs (oplopend)
curl "http://localhost:8000/products?sort_by=price&sort_order=asc&page=1&limit=50"

# Sorteren op titel (aflopend)
curl "http://localhost:8000/products?sort_by=title&sort_order=desc&page=1&limit=50"
```

## 🔍 Monitoring

```bash
# Cache statistieken bekijken
curl http://localhost:8000/cache/stats

# Cache legen
curl -X DELETE http://localhost:8000/cache/clear

# Performance analytics
curl "http://localhost:8000/analytics/performance?start_date=2024-01-01&end_date=2024-01-31"

# Suggestions statistieken
curl "http://localhost:8000/suggestions/stats?limit=20"
```

## 🔍 Troubleshooting

### Redis Connection Issues

```bash
# Test Redis connectie
redis-cli ping

# Check Redis status
redis-cli info server
```

### Cache Performance

```bash
# Monitor cache hits/misses
redis-cli info stats

# Check memory usage
redis-cli info memory
```

### Database Analytics

```bash
# Check analytics tabellen
psql -d findly -c "SELECT COUNT(*) FROM search_analytics;"
psql -d findly -c "SELECT COUNT(*) FROM search_clicks;"
psql -d findly -c "SELECT COUNT(*) FROM popular_searches;"
psql -d findly -c "SELECT COUNT(*) FROM query_suggestions;"
```

### Pagination Issues

```bash
# Check database performance
# Monitor slow queries in PostgreSQL logs
```

### Faceted Search Issues

```bash
# Check facet aggregaties
curl "http://localhost:8000/facets"

# Test individuele facet filters
curl "http://localhost:8000/faceted-search?category=shirt"
```

### Analytics Issues

```bash
# Check analytics data
curl "http://localhost:8000/analytics/popular-searches?limit=5"

# Test click tracking
curl -X POST "http://localhost:8000/track-click?search_analytics_id=1&product_id=1&position=1&click_time_ms=1000"
```

### Query Suggestions Issues

```bash
# Test autocomplete
curl "http://localhost:8000/suggestions/autocomplete?query=shir&limit=5"

# Check suggestions statistieken
curl "http://localhost:8000/suggestions/stats?limit=10"

# Test suggestion feedback
curl -X POST "http://localhost:8000/suggestions/feedback?suggestion=shirt&suggestion_type=autocomplete&was_clicked=false"
```

### Multi-language Issues

```bash
# Test taal detectie
curl -X POST "http://localhost:8000/languages/detect?query=blauwe shirt"

# Test vertaling
curl "http://localhost:8000/languages/translate?text=blue shirt&source_language=en&target_language=nl"

# Check gelokaliseerde facetten
curl "http://localhost:8000/languages/localized-facets?facet_type=color&language=nl"

# Test multi-language search
curl "http://localhost:8000/search?query=blauwe shirt&target_language=en"
```

## 📈 Volgende Stappen

1. **Advanced filtering (price ranges, categories, etc.)**
2. **Personalized recommendations**
3. **Search result ranking improvements**
4. **Real-time analytics dashboard**
5. **A/B testing framework**
6. **Machine learning optimization**
7. **Voice search integration**
8. **Image search capabilities**
9. **Advanced NLP features**
10. **Advanced translation services (Google Translate, DeepL integration)**

## 🤝 Bijdragen

Voor vragen of problemen, maak een issue aan in de repository. 