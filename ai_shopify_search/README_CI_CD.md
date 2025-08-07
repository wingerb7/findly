# Findly AI Search - CI/CD & Development Setup

## 🚀 Overview

This document describes the CI/CD pipeline, testing strategy, and development workflow for the Findly AI Search API.

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Redis 7+
- Docker (for local development)

## 🛠️ Local Development Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd Findly

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r ai_shopify_search/requirements_minimal.txt
pip install -r ai_shopify_search/requirements_dev.txt
```

### 2. Environment Variables

Create a `.env` file in the `ai_shopify_search/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/findly

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Sentry Configuration (Optional)
SENTRY_DSN=your_sentry_dsn_here
ENVIRONMENT=development
VERSION=1.0.0
```

### 3. Database Setup

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name postgres-findly \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=findly \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Start Redis
docker run -d \
  --name redis-findly \
  -p 6379:6379 \
  redis:7
```

### 4. Create Directories

```bash
mkdir -p logs
mkdir -p data/databases
mkdir -p reports
```

## 🧪 Testing

### Running Tests Locally

```bash
# Run all tests
cd ai_shopify_search
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=ai_shopify_search --cov-report=html

# Run specific test categories
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m slow -v
```

### Test Structure

```
tests/
├── test_integration.py      # Integration tests (converted from test_system.py)
├── unit/                    # Unit tests
│   ├── test_ai_search.py
│   ├── test_autocomplete.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_database.py
│   ├── test_api.py
│   └── ...
└── performance/             # Performance tests
    ├── test_load.py
    └── test_benchmark.py
```

## 📊 Load Testing

### Running Load Tests Locally

```bash
# Install Locust
pip install locust

# Run load tests
cd load_test
locust -f locustfile.py --host=http://localhost:8000

# Run headless load test
locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=5m --headless
```

### Load Test Configuration

The load test simulates:
- **100 concurrent users** for 10 minutes
- **Realistic user behavior** with search queries, autocomplete, and AI features
- **Multiple endpoints** including search, autocomplete, transfer learning, and health checks
- **Rate limiting testing** to ensure API protection

## 🔍 Error Monitoring with Sentry

### Setup

1. Create a Sentry account at https://sentry.io
2. Create a new project for your FastAPI application
3. Get your DSN from the project settings
4. Add the DSN to your `.env` file

### Features

- **Automatic error capture** for unhandled exceptions
- **Request breadcrumbs** for debugging
- **Performance monitoring** with transaction tracing
- **Environment-specific** error tracking

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline includes:

1. **Test Job**
   - Runs on Ubuntu with Python 3.11
   - Sets up PostgreSQL and Redis services
   - Installs dependencies
   - Starts FastAPI server
   - Runs pytest with coverage
   - Generates HTML test reports

2. **Load Test Job**
   - Runs only on pushes to main branch
   - Simulates 50 users for 5 minutes
   - Generates load test reports
   - Uploads results as artifacts

3. **Code Quality Job**
   - Runs Black (code formatting)
   - Runs isort (import sorting)
   - Runs flake8 (linting)
   - Runs mypy (type checking)

4. **Security Job**
   - Runs Bandit security scanner
   - Checks for common security issues
   - Generates security report

### Pipeline Triggers

- **Push to main/develop**: Runs all jobs
- **Pull Request to main**: Runs test and code quality jobs
- **Push to main**: Additionally runs load tests

### Artifacts

The pipeline generates:
- **Test Results**: HTML reports, coverage reports, JUnit XML
- **Load Test Results**: Locust HTML reports, CSV statistics
- **Security Reports**: Bandit security scan results

## 📈 Monitoring & Observability

### Metrics Collection

- **Prometheus metrics** for API performance
- **Custom metrics** for search quality and user behavior
- **Database metrics** for query performance
- **Cache metrics** for Redis performance

### Logging

- **Structured logging** with JSON format
- **Log levels** configurable per environment
- **Request/response logging** for debugging
- **Error logging** with stack traces

### Health Checks

- **Application health**: `/health`
- **Database health**: Connection status
- **Redis health**: Cache availability
- **AI services health**: OpenAI API status

## 🚀 Deployment

### Environment Variables for Production

```env
DATABASE_URL=postgresql://user:pass@host:5432/findly_prod
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
OPENAI_API_KEY=your_openai_api_key
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=production
VERSION=1.0.0
DEBUG=false
LOG_LEVEL=WARNING
```

### Docker Deployment

```bash
# Build Docker image
docker build -t findly-ai-search .

# Run with environment variables
docker run -d \
  --name findly-api \
  -p 8000:8000 \
  --env-file .env \
  findly-ai-search
```

## 🔧 Development Commands

### Code Quality

```bash
# Format code
black ai_shopify_search/
isort ai_shopify_search/

# Lint code
flake8 ai_shopify_search/
mypy ai_shopify_search/

# Security scan
bandit -r ai_shopify_search/
```

### Database Management

```bash
# Create database
createdb findly

# Run migrations
alembic upgrade head

# Reset database
dropdb findly && createdb findly
```

### Performance Testing

```bash
# Run benchmarks
python -m pytest tests/performance/ -v

# Profile code
python -m cProfile -o profile.stats main.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)
- [Sentry Documentation](https://docs.sentry.io/)
- [PostgreSQL pgvector](https://github.com/pgvector/pgvector)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

The CI/CD pipeline will automatically test your changes and provide feedback. 