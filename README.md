# 🚀 Findly - AI-Powered Shopify Search Platform

**Findly** is a comprehensive, production-ready AI-powered search platform designed specifically for Shopify stores. It combines advanced vector search, real-time analytics, and intelligent suggestions to deliver exceptional search experiences.

![Findly Logo](https://img.shields.io/badge/Findly-AI%20Search%20Platform-blue?style=for-the-badge&logo=shopify)

## 🌟 **Key Features**

### 🔍 **AI-Powered Search**
- **Vector Embeddings**: Semantic search using OpenAI embeddings
- **Smart Ranking**: Intelligent result ranking based on relevance
- **Fallback Search**: Text-based search when embeddings fail
- **Multi-language Support**: Automatic language detection and translation

### 📊 **Analytics & Insights**
- **Search Analytics**: Track queries, clicks, and performance metrics
- **Popular Searches**: Identify trending search terms
- **Performance Monitoring**: Real-time response time tracking
- **Click Tracking**: Monitor user engagement and behavior

### ⚡ **Performance & Scalability**
- **Redis Caching**: Smart caching with configurable TTL
- **Async I/O**: High-performance async operations
- **Rate Limiting**: Protection against abuse
- **Background Tasks**: Non-blocking embedding generation

### 🛠 **Developer Experience**
- **Modular Architecture**: Clean, maintainable code structure
- **Comprehensive Testing**: Unit and integration tests
- **Error Handling**: Robust error handling and logging
- **API Documentation**: Auto-generated OpenAPI docs

## 🏗 **Architecture**

```
Findly/
├── ai_shopify_search/          # Backend API (FastAPI)
│   ├── cache_manager.py        # Redis caching
│   ├── analytics_manager.py    # Search analytics
│   ├── search_service.py       # Core search logic
│   ├── rate_limiter.py         # Rate limiting
│   ├── background_tasks.py     # Async operations
│   ├── error_handlers.py       # Error handling
│   ├── metrics.py              # Prometheus metrics
│   └── tests/                  # Test suite
├── front-end/                  # React frontend
│   └── findly-ai-search/       # Modern UI components
└── docs/                       # Documentation
```

## 🚀 **Quick Start**

### Prerequisites
- Python 3.11+
- PostgreSQL with pgvector extension
- Redis server
- Node.js 18+ (for frontend)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/wingerb7/findly.git
   cd findly
   ```

2. **Set up Python environment**
   ```bash
   cd ai_shopify_search
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Create PostgreSQL database with pgvector
   createdb findly_search
   psql findly_search -c "CREATE EXTENSION IF NOT EXISTS vector;"
   
   # Run migrations
   python -c "from ai_shopify_search.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

5. **Start Redis**
   ```bash
   redis-server
   ```

6. **Run the API**
   ```bash
   uvicorn ai_shopify_search.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd front-end/findly-ai-search
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

## 📡 **API Endpoints**

### Search Endpoints
- `GET /api/ai-search` - AI-powered product search
- `GET /api/products` - List products with pagination
- `GET /api/suggestions/autocomplete` - Query suggestions

### Analytics Endpoints
- `GET /api/analytics/performance` - Search performance metrics
- `GET /api/analytics/popular-searches` - Popular search terms
- `POST /api/track-click` - Track product clicks

### Cache Management
- `GET /api/cache/stats` - Cache statistics
- `DELETE /api/cache/clear` - Clear cache

### Monitoring
- `GET /api/metrics` - Prometheus metrics

## 🧪 **Testing**

### Run Tests
```bash
cd ai_shopify_search
pytest tests/ -v --cov=ai_shopify_search --cov-report=html
```

### Test Coverage
- **Unit Tests**: Core business logic
- **Integration Tests**: API endpoints
- **Error Handling**: Exception scenarios
- **Performance Tests**: Load testing

## 📊 **Monitoring & Observability**

### Prometheus Metrics
- Search request rates
- Response times
- Cache hit ratios
- Error rates
- Database connections

### Grafana Dashboard
Import `grafana_dashboard.json` for comprehensive monitoring.

### Logging
- Structured logging with context
- Error tracking and alerting
- Performance monitoring

## 🔧 **Configuration**

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/findly_search

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=your_openai_key

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Cache
CACHE_TTL=3600
```

## 🚀 **Deployment**

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Considerations
- Use production-grade PostgreSQL
- Configure Redis persistence
- Set up monitoring and alerting
- Implement proper logging
- Use HTTPS and security headers

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Write comprehensive tests
- Update documentation
- Use conventional commits

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

- **Documentation**: [Wiki](https://github.com/wingerb7/findly/wiki)
- **Issues**: [GitHub Issues](https://github.com/wingerb7/findly/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wingerb7/findly/discussions)

## 🙏 **Acknowledgments**

- **OpenAI** for embedding models
- **FastAPI** for the web framework
- **PostgreSQL** and **pgvector** for vector storage
- **Redis** for caching
- **React** and **TypeScript** for the frontend

---

**Made with ❤️ by the Findly Team** 