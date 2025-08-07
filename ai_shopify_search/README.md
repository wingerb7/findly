# Findly AI Search - Privacy-Focused Product Search

## 🔒 Privacy-First Design

Findly AI Search is designed with privacy and data minimization as core principles. We only store the minimal data necessary for search functionality, ensuring compliance with privacy regulations and reducing data storage requirements.

## 📊 Data Storage Strategy

### ✅ What We Store Locally (Minimal Data)

We only store essential data for search functionality:

- **Product ID**: Shopify product identifier for live data fetching
- **Title**: Product title for search and display
- **Tags**: Product tags for filtering and search context
- **Price**: Product price for filtering and display
- **Embedding**: AI-generated vector for semantic search (based on title + tags only)
- **Timestamps**: Created/updated timestamps for data management

### ❌ What We DON'T Store Locally

To protect privacy and minimize data storage, we do NOT store:

- **Product Descriptions**: Fetched live when needed
- **Product Images**: Fetched live when needed
- **SEO Data**: Fetched live when needed
- **Inventory Information**: Fetched live when needed
- **Variant Details**: Fetched live when needed
- **Customer Data**: Never stored
- **Order Information**: Never stored

## 🔄 Live Data Fetching

When additional product details are needed (e.g., for product detail pages), we fetch them live from the Shopify API:

```bash
# Get live product details
GET /api/products/{shopify_id}/details
```

This approach ensures:
- **Fresh Data**: Always up-to-date product information
- **Privacy Compliance**: Minimal local data storage
- **Reduced Storage**: Lower database requirements
- **Flexibility**: Easy to add new fields without migrations

## 🧠 AI Search Implementation

### Embedding Generation

Our AI embeddings are generated using only:
- **Product Title**: Primary searchable content
- **Product Tags**: Additional context for semantic search

We deliberately exclude product descriptions from embeddings to:
- **Reduce Privacy Risk**: Less sensitive data in embeddings
- **Improve Performance**: Smaller, more focused embeddings
- **Maintain Relevance**: Title + tags provide sufficient context

### Search Process

1. **Query Processing**: User search query is converted to embedding
2. **Vector Search**: Similarity search against title + tags embeddings
3. **Result Ranking**: AI-powered ranking based on semantic similarity
4. **Live Details**: Additional product details fetched on-demand

## 📋 API Endpoints

### Search Endpoints

- `POST /api/products/search` - AI-powered semantic search
- `GET /api/products/autocomplete` - Search suggestions
- `GET /api/products/smart-autocomplete` - AI-powered suggestions
- `GET /api/products/facets` - Product filtering options

### Product Details

- `GET /api/products/{shopify_id}/details` - Live product details from Shopify

### Import Management

- `POST /api/products/import/shopify` - Import products with minimal data
- `GET /api/products/import/progress/{import_id}` - Import progress tracking
- `GET /api/products/import/count-products` - Count products in Shopify store

## 🛠️ Technical Implementation

### Database Schema

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    shopify_id VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    tags JSON,  -- Array of tags for search context
    price FLOAT,
    embedding JSON,  -- AI embedding vector (title + tags)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Import Process

1. **Fetch Products**: Get product list from Shopify API
2. **Extract Minimal Data**: Only title, tags, price, and shopify_id
3. **Generate Embeddings**: Create embeddings from title + tags only
4. **Store Locally**: Save minimal data to database
5. **Log Privacy Notice**: Clear logging of privacy-focused approach

### Search Process

1. **Query Embedding**: Convert user query to embedding
2. **Vector Search**: Find similar products using pgvector
3. **Filter Results**: Apply price and tag filters
4. **Return Basic Info**: Return minimal product data
5. **Live Details**: Fetch additional details when requested

## 🔐 Privacy Benefits

### Data Minimization

- **Reduced Storage**: Only essential data stored locally
- **Lower Risk**: Less sensitive data in local database
- **Compliance**: Easier to comply with GDPR, CCPA, etc.
- **Transparency**: Clear documentation of data practices

### Security

- **No Sensitive Data**: Customer data never stored locally
- **API-Based**: Fresh data always fetched from source
- **Access Control**: Shopify API handles authentication
- **Audit Trail**: Clear logging of data access

## 📈 Performance Benefits

### Storage Efficiency

- **Smaller Database**: Reduced storage requirements
- **Faster Queries**: Smaller data footprint
- **Lower Costs**: Reduced infrastructure costs
- **Better Scalability**: Easier to scale with growth

### Search Performance

- **Focused Embeddings**: Title + tags provide relevant context
- **Fast Vector Search**: Optimized similarity search
- **Caching**: Redis caching for frequently accessed data
- **Live Updates**: Always current product information

## 🚀 Getting Started

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Shopify and OpenAI credentials

# Run database migrations
alembic upgrade head

# Start the server
uvicorn ai_shopify_search.main:app --reload
```

### Import Products

```bash
# Import products with minimal data storage
curl -X POST "http://localhost:8000/api/products/import/shopify" \
  -H "Content-Type: application/json"
```

### Search Products

```bash
# AI-powered search
curl -X POST "http://localhost:8000/api/products/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "blue jeans", "limit": 10}'

# Get live product details
curl "http://localhost:8000/api/products/123456789/details"
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [CI/CD Setup](README_CI_CD.md) - Development and deployment guide
- [Privacy Policy](PRIVACY.md) - Detailed privacy information

## 🤝 Contributing

We welcome contributions that maintain our privacy-first approach:

1. **Data Minimization**: Only store essential data
2. **Live Fetching**: Prefer live API calls over local storage
3. **Privacy Documentation**: Update privacy documentation
4. **Security Review**: Ensure security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🔒 Privacy by Design**: Findly AI Search is built with privacy and data minimization as core principles, ensuring compliance with privacy regulations while providing powerful AI-powered search capabilities. 