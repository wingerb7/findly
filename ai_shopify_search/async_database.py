import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from ai_shopify_search.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Convert sync database URL to async
async_database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = create_async_engine(
    async_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_db():
    """Async database dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Keep sync session for backward compatibility
from ai_shopify_search.database import SessionLocal

def get_db():
    """Sync database dependency (for backward compatibility)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 