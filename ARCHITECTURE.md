# 🏗️ Findly - Visuele Architectuurkaart

## 📊 **Systeem Overzicht**

```mermaid
graph TB
    subgraph "🌐 Frontend (React + TypeScript)"
        UI[React UI Components]
        Search[Search Interface]
        Analytics[Analytics Dashboard]
    end
    
    subgraph "🚀 Backend (FastAPI + Python)"
        API[FastAPI Application]
        Router[API Router]
        Middleware[Error Handling Middleware]
    end
    
    subgraph "🔍 Core Services"
        SearchService[Search Service]
        CacheManager[Cache Manager]
        AnalyticsManager[Analytics Manager]
        RateLimiter[Rate Limiter]
        BackgroundTasks[Background Tasks]
    end
    
    subgraph "🗄️ Data Layer"
        PostgreSQL[(PostgreSQL + pgvector)]
        Redis[(Redis Cache)]
        Embeddings[OpenAI Embeddings]
    end
    
    subgraph "📊 Monitoring & Observability"
        Prometheus[Prometheus Metrics]
        Grafana[Grafana Dashboard]
        Logging[Structured Logging]
    end
    
    subgraph "🧪 Testing & Quality"
        UnitTests[Unit Tests]
        IntegrationTests[Integration Tests]
        Coverage[Test Coverage]
    end
    
    UI --> API
    API --> Router
    Router --> SearchService
    Router --> CacheManager
    Router --> AnalyticsManager
    Router --> RateLimiter
    
    SearchService --> PostgreSQL
    SearchService --> Embeddings
    CacheManager --> Redis
    AnalyticsManager --> PostgreSQL
    
    BackgroundTasks --> PostgreSQL
    BackgroundTasks --> Embeddings
    
    API --> Prometheus
    Prometheus --> Grafana
    
    UnitTests --> SearchService
    IntegrationTests --> API
```

## 🔄 **Data Flow Diagram**

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API Gateway
    participant R as Rate Limiter
    participant S as Search Service
    participant C as Cache Manager
    participant E as Embeddings
    participant D as Database
    participant B as Background Tasks
    participant M as Metrics

    U->>F: Search Query
    F->>A: GET /api/ai-search
    A->>R: Check Rate Limit
    R-->>A: Rate Limit Status
    
    alt Rate Limit Exceeded
        A-->>F: 429 Too Many Requests
        F-->>U: Error Message
    else Rate Limit OK
        A->>S: Process Search
        S->>C: Check Cache
        
        alt Cache Hit
            C-->>S: Cached Results
            S-->>A: Return Results
        else Cache Miss
            S->>E: Generate Embedding
            E-->>S: Vector Embedding
            S->>D: Vector Search
            D-->>S: Search Results
            S->>C: Cache Results
            S-->>A: Return Results
        end
        
        A->>B: Log Analytics (Async)
        A->>M: Record Metrics
        A-->>F: Search Results
        F-->>U: Display Results
    end
```

## 🏛️ **Modulaire Architectuur**

```mermaid
graph LR
    subgraph "📦 Core Modules"
        A[products_v2.py<br/>API Router]
        B[search_service.py<br/>Search Logic]
        C[cache_manager.py<br/>Redis Operations]
        D[analytics_manager.py<br/>Analytics]
        E[rate_limiter.py<br/>Rate Limiting]
        F[background_tasks.py<br/>Async Tasks]
        G[error_handlers.py<br/>Error Handling]
        H[metrics.py<br/>Prometheus]
    end
    
    subgraph "🗄️ Data Models"
        I[models.py<br/>SQLAlchemy Models]
        J[database.py<br/>DB Connection]
        K[async_database.py<br/>Async DB]
    end
    
    subgraph "🔧 Utilities"
        L[embeddings.py<br/>OpenAI Integration]
        M[shopify_client.py<br/>Shopify API]
        N[config.py<br/>Configuration]
    end
    
    subgraph "🧪 Testing"
        O[tests/<br/>Test Suite]
        P[conftest.py<br/>Test Config]
        Q[pytest.ini<br/>Pytest Config]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    
    B --> I
    B --> L
    C --> N
    D --> I
    E --> C
    F --> B
    F --> L
    
    O --> A
    O --> B
    O --> C
    O --> D
```

## 🗄️ **Database Schema**

```mermaid
erDiagram
    PRODUCTS {
        int id PK
        string shopify_id UK
        string title
        text description
        decimal price
        json tags
        vector embedding
        datetime created_at
        datetime updated_at
    }
    
    SEARCH_ANALYTICS {
        int id PK
        string session_id
        string query
        string search_type
        json filters
        int results_count
        int page
        int limit
        float response_time_ms
        boolean cache_hit
        string user_agent
        string ip_address
        datetime created_at
    }
    
    POPULAR_SEARCHES {
        int id PK
        string query UK
        int search_count
        int click_count
        float avg_position_clicked
        datetime last_searched
        datetime created_at
    }
    
    QUERY_SUGGESTIONS {
        int id PK
        string query
        string suggestion
        string suggestion_type
        int search_count
        int click_count
        float relevance_score
        boolean is_active
        datetime created_at
    }
    
    SEARCH_CLICKS {
        int id PK
        int search_analytics_id FK
        int product_id FK
        int position
        float click_time_ms
        datetime created_at
    }
    
    PRODUCTS ||--o{ SEARCH_ANALYTICS : "searched"
    SEARCH_ANALYTICS ||--o{ SEARCH_CLICKS : "clicks"
    PRODUCTS ||--o{ SEARCH_CLICKS : "clicked"
```

## ⚡ **Performance Architecture**

```mermaid
graph TB
    subgraph "🚀 High Performance Features"
        A[Async I/O Operations]
        B[Background Tasks]
        C[Redis Caching]
        D[Vector Indexing]
        E[Connection Pooling]
    end
    
    subgraph "📊 Performance Monitoring"
        F[Response Time Tracking]
        G[Cache Hit Ratio]
        H[Database Connections]
        I[Rate Limit Metrics]
        J[Error Rate Tracking]
    end
    
    subgraph "🛡️ Reliability Features"
        K[Circuit Breakers]
        L[Retry Logic]
        M[Graceful Degradation]
        N[Error Recovery]
        O[Health Checks]
    end
    
    A --> F
    B --> F
    C --> G
    D --> F
    E --> H
    
    K --> M
    L --> N
    M --> O
```

## 🔐 **Security & Rate Limiting**

```mermaid
graph LR
    subgraph "🛡️ Security Layers"
        A[Input Validation]
        B[Rate Limiting]
        C[Error Handling]
        D[Logging & Monitoring]
    end
    
    subgraph "📊 Rate Limiting Strategy"
        E[IP-based Limits]
        F[User-based Limits]
        G[Endpoint-specific Limits]
        H[Time Window Management]
    end
    
    subgraph "🔍 Monitoring & Alerting"
        I[Anomaly Detection]
        J[Performance Alerts]
        K[Security Alerts]
        L[Capacity Planning]
    end
    
    A --> B
    B --> C
    C --> D
    
    E --> I
    F --> J
    G --> K
    H --> L
```

## 🚀 **Deployment Architecture**

```mermaid
graph TB
    subgraph "🌐 Production Environment"
        A[Load Balancer]
        B[API Servers]
        C[Background Workers]
        D[Redis Cluster]
        E[PostgreSQL Cluster]
    end
    
    subgraph "📊 Monitoring Stack"
        F[Prometheus]
        G[Grafana]
        H[Alert Manager]
        I[Log Aggregation]
    end
    
    subgraph "🔧 CI/CD Pipeline"
        J[GitHub Actions]
        K[Automated Testing]
        L[Security Scanning]
        M[Deployment]
    end
    
    A --> B
    B --> C
    B --> D
    B --> E
    
    B --> F
    F --> G
    F --> H
    B --> I
    
    J --> K
    K --> L
    L --> M
    M --> A
```

## 📈 **Scalability Strategy**

```mermaid
graph LR
    subgraph "📈 Horizontal Scaling"
        A[API Server 1]
        B[API Server 2]
        C[API Server N]
        D[Load Balancer]
    end
    
    subgraph "🗄️ Database Scaling"
        E[Primary DB]
        F[Read Replicas]
        G[Connection Pool]
    end
    
    subgraph "⚡ Cache Scaling"
        H[Redis Master]
        I[Redis Replicas]
        J[Cache Distribution]
    end
    
    subgraph "🔍 Search Scaling"
        K[Vector Index]
        L[Sharding Strategy]
        M[Query Optimization]
    end
    
    D --> A
    D --> B
    D --> C
    
    A --> E
    B --> F
    C --> G
    
    A --> H
    B --> I
    C --> J
    
    A --> K
    B --> L
    C --> M
```

## 🎯 **Key Performance Indicators (KPIs)**

| Metric | Target | Monitoring |
|--------|--------|------------|
| **Response Time** | < 200ms | Prometheus + Grafana |
| **Cache Hit Ratio** | > 80% | Redis Metrics |
| **Error Rate** | < 1% | Error Tracking |
| **Throughput** | > 1000 req/s | Load Testing |
| **Availability** | > 99.9% | Health Checks |
| **Search Accuracy** | > 95% | A/B Testing |

## 🔧 **Technologie Stack**

### **Backend**
- **FastAPI** - High-performance web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL + pgvector** - Vector database
- **Redis** - In-memory caching
- **OpenAI API** - Embedding generation

### **Frontend**
- **React + TypeScript** - Modern UI framework
- **Tailwind CSS** - Utility-first styling
- **Shadcn/ui** - Component library
- **Vite** - Fast build tool

### **DevOps & Monitoring**
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboard
- **Pytest** - Testing framework
- **GitHub Actions** - CI/CD pipeline

### **Performance & Reliability**
- **Async I/O** - Non-blocking operations
- **Background Tasks** - Heavy operations
- **Rate Limiting** - API protection
- **Error Handling** - Graceful failures

---

**🏗️ Deze architectuur zorgt voor:**
- ⚡ **Hoge performance** door async operaties en caching
- 🛡️ **Betrouwbaarheid** door error handling en monitoring
- 📈 **Schaalbaarheid** door modulaire opzet
- 🔍 **Observability** door uitgebreide metrics
- 🧪 **Kwaliteit** door comprehensive testing 