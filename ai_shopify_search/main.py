import logging
from fastapi import FastAPI, Request
from sqlalchemy import text
from fastapi import APIRouter
from core.database import Base, engine
from core.config import DATABASE_URL
from api.error_handlers import error_handler_middleware

# Import routers
from api.products_router import router as products_router
from api.ai_learning_router import router as ai_learning_router
from api.feedback_router import router as feedback_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create pgvector extension & index (only for PostgreSQL)
if DATABASE_URL.startswith("postgresql"):
    try:
        with engine.connect() as conn:
            # Ensure vector extension exists
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            # Create index for fast cosine similarity (will be recreated if needed)
            conn.execute(text("DROP INDEX IF EXISTS idx_products_embedding;"))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_products_embedding
                ON products
                USING ivfflat (embedding vector_l2_ops)
                WITH (lists = 100);
            """))
            conn.commit()
            logger.info("Database setup completed successfully")
    except Exception as e:
        logger.warning(f"Database setup warning (this is normal for new installations): {e}")

# FastAPI app
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

# Routers
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])
app.include_router(ai_learning_router, prefix="/api/ai-learning", tags=["ai-learning"])

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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Findly AI Search API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)