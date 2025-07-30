# 🔍 Findly AI Search

[![CI/CD Pipeline](https://github.com/wingerb7/findly/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/wingerb7/findly/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/wingerb7/findly)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered product search engine** built with FastAPI, featuring intelligent search capabilities, real-time analytics, advanced caching, and comprehensive privacy compliance. Designed for enterprise-grade scalability with modular architecture and extensive testing coverage.

## ✨ Features

### 🔍 **AI-Powered Search**
- **Intelligent query processing** with OpenAI integration
- **Semantic search** and natural language understanding
- **Price intent extraction** and filtering
- **Category-based suggestions** and autocomplete

### 🚀 **Performance & Scalability**
- **Redis caching** with intelligent TTL management
- **Async database operations** with connection pooling
- **Rate limiting** and request throttling
- **Background task processing** for analytics

### 📊 **Analytics & Monitoring**
- **Real-time search analytics** and user behavior tracking
- **Performance metrics** (P95, P99 response times)
- **Popular searches** and trending products
- **Prometheus metrics** and Grafana dashboards

### 🛡️ **Security & Privacy**
- **GDPR compliance** with data anonymization
- **Input validation** and SQL injection prevention
- **XSS protection** and secure headers
- **Session management** and authentication

### 🧪 **Quality Assurance**
- **80%+ test coverage** with unit and integration tests
- **Automated CI/CD pipeline** with GitHub Actions
- **Code quality checks** (Black, isort, flake8, mypy)
- **Security scanning** (Bandit, Safety, Semgrep)

## 🏗️ Architecture & Flow

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI API   │───▶│  Service Layer  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Cache   │    │  PostgreSQL DB  │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Analytics     │    │  Background     │
                       │   Tracking      │    │  Tasks          │
                       └─────────────────┘    └─────────────────┘
```

### Request Flow
1. **API Request** → FastAPI endpoint receives search query
2. **Validation** → Input sanitization and rate limiting
3. **Cache Check** → Redis lookup for existing results
4. **AI Processing** → OpenAI API for query enhancement
5. **Database Query** → PostgreSQL with optimized queries
6. **Response** → Formatted JSON with pagination
7. **Analytics** → Background tracking and metrics

## 📁 Project Structure

```
ai_shopify_search/
├── 📁 .github/                    # GitHub Actions CI/CD
│   ├── workflows/
│   │   ├── ci.yml                # Main CI/CD pipeline
│   │   └── dependabot.yml        # Dependency updates
│   └── CODEOWNERS               # Code ownership rules
├── 📁 api/                       # API endpoints
│   └── products_v2.py           # Main product search API
├── 📁 core/                      # Core database components
│   ├── database.py              # Database configuration
│   ├── database_async.py        # Async database operations
│   └── models.py                # SQLAlchemy models
├── 📁 services/                  # Business logic services
│   ├── __init__.py              # Service factory
│   ├── ai_search_service.py     # AI-powered search
│   ├── cache_service.py         # Redis caching
│   ├── analytics_service.py     # Analytics tracking
│   ├── suggestion_service.py    # Search suggestions
│   └── autocomplete_service.py  # Autocomplete functionality
├── 📁 utils/                     # Utility functions
│   ├── privacy_utils.py         # GDPR compliance
│   ├── validation.py            # Input validation
│   └── error_handling.py        # Error handling
├── 📁 tests/                     # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Test configuration
├── 📁 config/                    # Configuration files
│   ├── prometheus.yml           # Monitoring config
│   └── grafana_dashboard.json   # Dashboard config
├── 📁 docs/                      # Documentation
│   ├── ARCHITECTURE.md          # Architecture details
│   └── MODULARITY_AND_PERFORMANCE.md
├── main.py                      # FastAPI application entry
├── config.py                    # Application configuration
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Local development setup
└── run_tests.py                 # Test runner script
```

## 🚀 Installation

### Prerequisites
- **Python 3.11+**
- **PostgreSQL 15+**
- **Redis 7.0+**
- **Git**

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/wingerb7/findly.git
   cd findly/ai_shopify_search
   ```

2. **Set up environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy example environment file
   cp env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

   **Required environment variables:**
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/findly
   REDIS_URL=redis://localhost:6379
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_secret_key
   ```

4. **Set up database**
   ```bash
   # Create database
   createdb findly
   
   # Run migrations (if using Alembic)
   # alembic upgrade head
   ```

5. **Start services**
   ```bash
   # Option 1: Using Docker Compose (recommended)
   docker-compose up -d
   
   # Option 2: Manual start
   # Start PostgreSQL and Redis separately
   # Then run the application
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📖 Usage

### Starting the API
```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Available Endpoints

#### 🔍 **Product Search**
```bash
# Basic search
curl -X GET "http://localhost:8000/api/v2/products/search?query=electronics&limit=10"

# Search with filters
curl -X GET "http://localhost:8000/api/v2/products/search?query=laptop&min_price=500&max_price=2000&category=Electronics&limit=20&offset=0"
```

#### 💡 **Search Suggestions**
```bash
# Get search suggestions
curl -X GET "http://localhost:8000/api/v2/products/suggestions?query=elec&limit=5"

# Get autocomplete
curl -X GET "http://localhost:8000/api/v2/products/autocomplete?query=lap&limit=10"
```

#### 📊 **Analytics**
```bash
# Get popular searches
curl -X GET "http://localhost:8000/api/v2/analytics/popular-searches?limit=10"

# Get search statistics
curl -X GET "http://localhost:8000/api/v2/analytics/stats"
```

#### 🏥 **Health & Monitoring**
```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Metrics endpoint
curl -X GET "http://localhost:8000/metrics"
```

### Example API Responses

#### Search Response
```json
{
  "products": [
    {
      "id": 1,
      "title": "MacBook Pro 13-inch",
      "price": 1299.99,
      "category": "Electronics",
      "brand": "Apple",
      "rating": 4.8,
      "review_count": 1250,
      "availability": true
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 50,
    "items_per_page": 10,
    "next_page": 2,
    "previous_page": null
  },
  "analytics": {
    "query": "laptop",
    "results_count": 10,
    "response_time": 0.245
  }
}
```

## 🧪 Testing & Coverage

### Running Tests
```bash
# Run all tests
python run_tests.py

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/test_api_endpoints.py -v    # API tests

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### Coverage Reports
- **HTML Report**: `htmlcov/index.html`
- **Terminal Report**: Shows missing lines
- **Coverage Target**: 80%+ (currently achieved)

### Test Categories
- ✅ **Unit Tests**: Individual component testing
- ✅ **Integration Tests**: Service interaction testing
- ✅ **API Tests**: Endpoint functionality testing
- ✅ **Performance Tests**: Load and scalability testing
- ✅ **Security Tests**: Privacy and security compliance

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
The project uses automated CI/CD with the following stages:

1. **🧪 Testing**
   - Unit tests with 35% coverage requirement
   - Integration tests with 80% total coverage
   - Performance and security tests

2. **🔍 Code Quality**
   - Black code formatting
   - isort import sorting
   - flake8 linting
   - mypy type checking

3. **🛡️ Security**
   - Bandit security scanning
   - Safety vulnerability checks
   - Semgrep static analysis

4. **🐳 Build & Deploy**
   - Docker image building
   - Vulnerability scanning
   - Staging deployment (automatic)
   - Production deployment (manual)

### Pipeline Status
[![CI/CD Pipeline](https://github.com/wingerb7/findly/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/wingerb7/findly/actions)

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Ensure all tests pass: `python run_tests.py`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Coding Standards
- **Python**: Follow PEP 8 with Black formatting
- **Type Hints**: Use type hints for all functions
- **Documentation**: Add docstrings for all public functions
- **Testing**: Maintain 80%+ test coverage
- **Commits**: Use conventional commit messages

### Code Quality Checks
```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run pre-commit hooks
pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Findly AI Search

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wingerb7/findly/issues)
- **Documentation**: [Project Wiki](https://github.com/wingerb7/findly/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/wingerb7/findly/discussions)

---

**Built with ❤️ by the Findly team** 