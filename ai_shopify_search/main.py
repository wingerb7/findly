import logging
from fastapi import FastAPI, Request
from sqlalchemy import text
from ai_shopify_search import products_v2
from ai_shopify_search.database import Base, engine
from ai_shopify_search.error_handlers import error_handler_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create pgvector extension & index
with engine.connect() as conn:
    # Ensure vector extension exists
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    # Create index for fast cosine similarity
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_products_embedding
        ON products
        USING ivfflat (embedding vector_l2_ops)
        WITH (lists = 100);
    """))
    conn.commit()

app = FastAPI(
    title="Findly - AI-Powered Shopify Search",
    description="Advanced AI-powered search platform for Shopify stores",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    return await error_handler_middleware(request, call_next)

app.include_router(products_v2.router, prefix="/api", tags=["products"])

@app.get("/")
async def root():
    return {
        "message": "Findly - AI-Powered Shopify Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Findly Search API",
        "version": "1.0.0"
    }