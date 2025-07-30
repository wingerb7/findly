# 🚀 AI Shopify Search - Modular Architecture

## 📋 **Overview**

This is a high-performance, modular AI-powered search API for Shopify products with advanced features including:

- **🔍 AI-Powered Vector Search** - Semantic product search using embeddings
- **⚡ Async I/O** - High-performance async operations
- **🛡️ Rate Limiting** - Protection against abuse
- **📊 Observability** - Prometheus metrics & Grafana dashboards
- **💾 Smart Caching** - Redis-based caching with analytics
- **📈 Analytics** - Comprehensive search analytics and insights

## 🏗️ **Modular Architecture**

### **Core Modules:**

1. **`cache_manager.py`** - Centralized Redis caching operations
2. **`analytics_manager.py`** - Search analytics and tracking
3. **`search_service.py`** - AI search and suggestion services
4. **`async_database.py`** - Async database operations
5. **`rate_limiter.py`** - Rate limiting protection
6. **`metrics.py`** - Prometheus metrics collection

### **API Endpoints:**

- **`products_v2.py`** - Main API router with async endpoints

## 🚀 **Quick Start**

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **2. Environment Setup**

```bash
# Database
export DATABASE_URL="postgresql://user:pass@localhost/shopify_search"

# Redis
export REDIS_HOST="localhost"
export REDIS_PORT=6379
export REDIS_DB=0

# Optional: Redis password
export REDIS_PASSWORD="your_redis_password"
```

### **3. Start the Application**

```bash
# Development
uvicorn ai_shopify_search.main:app --reload

# Production
uvicorn ai_shopify_search.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔍 **API Endpoints**

### **AI Search**
```http
GET /api/ai-search?query=blue cotton shirt&page=1&limit=25
```

**Features:**
- ✅ Rate limiting (100 requests/hour per IP)
- ✅ Async processing
- ✅ Vector similarity search
- ✅ Fallback text search
- ✅ Response time metrics
- ✅ Cache hit tracking

### **Product Management**
```http
POST /api/import-products
GET /api/products?page=1&limit=50&sort_by=price&sort_order=desc
```

### **Analytics**
```http
GET /api/analytics/performance?start_date=2024-01-01&end_date=2024-01-31
GET /api/analytics/popular-searches?limit=20
```

### **Suggestions**
```http
GET /api/suggestions/autocomplete?query=shirt&limit=10
```

### **Monitoring**
```http
GET /api/metrics                    # Prometheus metrics
GET /api/cache/stats               # Cache statistics
DELETE /api/cache/clear            # Clear cache
```

## 📊 **Observability**

### **Prometheus Metrics**

The application exposes the following metrics:

- `search_requests_total` - Total search requests by type and cache hit
- `search_response_time_seconds` - Response time histograms
- `search_results_count` - Number of results returned
- `cache_hit_ratio` - Cache hit ratio by search type
- `active_connections` - Database connection count
- `redis_connections` - Redis connection count

### **Grafana Dashboard**

Import the `grafana_dashboard.json` configuration to get:

- 📈 Search requests per second
- ⏱️ Response time percentiles
- 💾 Cache hit ratios
- 🔗 Connection monitoring
- 📊 Results distribution
- 🛡️ Rate limit violations

## 🔧 **Configuration**

### **Rate Limiting**
```python
# In products_v2.py
AI_SEARCH_RATE_LIMIT = 100  # requests per hour
AI_SEARCH_RATE_WINDOW = 3600  # seconds
```

### **Cache TTL**
```python
# In config.py
CACHE_TTL = 3600              # 1 hour
SEARCH_CACHE_TTL = 1800       # 30 minutes
AI_SEARCH_CACHE_TTL = 900     # 15 minutes
```

## 🏃‍♂️ **Performance Features**

### **Async I/O**
- ✅ Async database operations with `asyncpg`
- ✅ Non-blocking Redis operations
- ✅ Concurrent request handling

### **Smart Caching**
- ✅ Multi-level caching strategy
- ✅ Cache invalidation on product updates
- ✅ Cache hit ratio tracking

### **Rate Limiting**
- ✅ IP-based rate limiting
- ✅ Configurable limits and windows
- ✅ Rate limit headers in responses

### **Metrics Collection**
- ✅ Real-time performance metrics
- ✅ Cache hit ratio monitoring
- ✅ Response time tracking
- ✅ Error rate monitoring

## 🔍 **Search Features**

### **AI-Powered Search**
- Vector embeddings for semantic search
- Cosine similarity ranking
- Fallback to text search
- Multi-language support

### **Analytics**
- Search query tracking
- Click-through rate analysis
- Popular search terms
- Performance analytics

### **Suggestions**
- Autocomplete suggestions
- Popular search suggestions
- Related search suggestions
- Query corrections

## 🛠️ **Development**

### **Module Structure**
```
ai_shopify_search/
├── cache_manager.py      # Redis caching
├── analytics_manager.py  # Analytics tracking
├── search_service.py     # Search operations
├── async_database.py     # Async DB operations
├── rate_limiter.py       # Rate limiting
├── metrics.py           # Prometheus metrics
├── products_v2.py       # Main API router
├── main.py              # FastAPI app
└── config.py            # Configuration
```

### **Testing**
```bash
# Run tests
pytest tests/

# Load testing
locust -f load_test.py
```

## 📈 **Monitoring & Alerts**

### **Key Metrics to Monitor**
- Response time > 2 seconds
- Cache hit ratio < 80%
- Rate limit violations > 10/hour
- Database connections > 80%
- Redis memory usage > 80%

### **Alerting Rules**
```yaml
# prometheus/rules/alerts.yml
groups:
  - name: ai_search_alerts
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(search_response_time_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High search response time"
```

## 🚀 **Deployment**

### **Docker**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "ai_shopify_search.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Kubernetes**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-shopify-search
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-shopify-search
  template:
    metadata:
      labels:
        app: ai-shopify-search
    spec:
      containers:
      - name: ai-shopify-search
        image: ai-shopify-search:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## 📚 **API Documentation**

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

MIT License - see LICENSE file for details. 