# 🚀 Findly AI Search Platform

Een moderne, schaalbare AI-powered zoekplatform voor Shopify stores met uitgebreide privacy en security features.

## 📁 Project Structuur

```
ai_shopify_search/
├── 📁 api/                    # API routes en endpoints
│   ├── __init__.py
│   └── products_v2.py        # Product API endpoints
│
├── 📁 core/                   # Core database en models
│   ├── __init__.py
│   ├── database.py           # Database configuratie
│   ├── database_async.py     # Async database operations
│   └── models.py             # SQLAlchemy models
│
├── 📁 services/              # Business logic services
│   ├── __init__.py           # Service factory
│   ├── ai_search_service.py  # AI-powered search
│   ├── autocomplete_service.py # Autocomplete functionality
│   ├── suggestion_service.py # Search suggestions
│   ├── cache_service.py      # Caching operations
│   └── analytics_service.py  # Analytics tracking
│
├── 📁 utils/                  # Utility functions
│   ├── __init__.py
│   ├── privacy_utils.py      # GDPR compliance utilities
│   ├── validation.py         # Input validation
│   └── error_handling.py     # Error handling system
│
├── 📁 tests/                  # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── performance/          # Performance tests
│
├── 📁 docs/                   # Documentatie
│   ├── MODULARITY_AND_PERFORMANCE.md
│   ├── CODE_ANALYSIS_REPORT.md
│   └── README.md
│
├── 📁 config/                 # Configuratie bestanden
│   ├── grafana_dashboard.json
│   └── env.example
│
├── 📁 scripts/                # Utility scripts
│   └── setup_env.py
│
├── 📁 legacy/                 # Legacy code (voor migratie)
│   ├── search_service.py
│   └── async_database.py
│
├── 📄 main.py                 # FastAPI applicatie entry point
├── 📄 config.py               # Applicatie configuratie
├── 📄 requirements.txt        # Python dependencies
├── 📄 pyproject.toml          # Project configuratie
└── 📄 .pre-commit-config.yaml # Code quality hooks
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Kopieer environment configuratie
cp config/env.example .env

# Setup environment (automatisch)
python scripts/setup_env.py
```

### 2. Dependencies Installeren
```bash
pip install -r requirements.txt
```

### 3. Database Initialiseren
```bash
# Sync database
python -c "from core.database import Base, engine; Base.metadata.create_all(engine)"

# Async database (optioneel)
python -c "import asyncio; from core.database_async import async_db_service; asyncio.run(async_db_service.initialize())"
```

### 4. Applicatie Starten
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🛡️ Security & Privacy Features

### GDPR Compliance
- ✅ **IP Anonimisering**: Automatische IP masking
- ✅ **User Agent Sanitization**: Privacy-bewuste logging
- ✅ **Data Retention**: Automatische data cleanup
- ✅ **Session Management**: GDPR-compliant sessions

### Security
- ✅ **Input Validation**: XSS en SQL injection preventie
- ✅ **Rate Limiting**: Redis-based rate limiting
- ✅ **Error Handling**: Gestructureerde error responses
- ✅ **API Key Validation**: Secure API access

## 📊 Monitoring & Observability

### Metrics
- ✅ **Prometheus Metrics**: Real-time performance tracking
- ✅ **Grafana Dashboard**: Visualisatie van metrics
- ✅ **Health Checks**: Service health monitoring
- ✅ **Performance Monitoring**: Response time tracking

### Logging
- ✅ **Structured Logging**: JSON-formatted logs
- ✅ **Privacy-Aware**: Gevoelige data gefilterd
- ✅ **Error Tracking**: Comprehensive error logging

## 🧪 Testing

### Test Suite
```bash
# Alle tests uitvoeren
pytest tests/

# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# Met coverage
pytest --cov=ai_shopify_search --cov-report=html
```

### Code Quality
```bash
# Code formatting
black .

# Import sorting
isort .

# Linting
flake8 .

# Type checking
mypy .

# Security scanning
bandit -r .
```

## 🔧 Development

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

### Modular Services
```python
from services import service_factory

# Get services
ai_search = service_factory.get_ai_search_service()
suggestions = service_factory.get_suggestion_service()
autocomplete = service_factory.get_autocomplete_service()
```

## 📈 Performance Features

### Async Operations
- ✅ **Async Database**: Connection pooling
- ✅ **Async Services**: Non-blocking operations
- ✅ **Performance Monitoring**: Real-time metrics

### Caching
- ✅ **Redis Caching**: TTL management
- ✅ **Cache Strategies**: Intelligent caching
- ✅ **Cache Monitoring**: Hit/miss tracking

## 🚀 Deployment

### Docker (Coming Soon)
```bash
# Build image
docker build -t findly-ai-search .

# Run container
docker run -p 8000:8000 findly-ai-search
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/findly

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=your-api-key

# Security
SECRET_KEY=your-secret-key
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🤝 Contributing

1. Fork de repository
2. Maak een feature branch
3. Commit je wijzigingen
4. Push naar de branch
5. Maak een Pull Request

## 📄 License

MIT License - zie LICENSE bestand voor details.

---

**Findly AI Search Platform** - Modern, secure, and scalable search solution for Shopify stores. 