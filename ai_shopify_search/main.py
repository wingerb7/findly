import logging
from fastapi import FastAPI
from sqlalchemy import text
from ai_shopify_search import products_v2
from ai_shopify_search.database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
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

app = FastAPI(title="AI Shopify Search")
app.include_router(products_v2.router, prefix="/api", tags=["products"])