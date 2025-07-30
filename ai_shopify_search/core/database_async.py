"""
Async database service with connection pooling for improved performance.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL

logger = logging.getLogger(__name__)

class AsyncDatabaseService:
    """Async database service with connection pooling."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self._pool_size = 20
        self._max_overflow = 30
        self._pool_timeout = 30
        self._pool_recycle = 3600
        
    async def initialize(self):
        """Initialize async database engine and session maker."""
        if self.engine is not None:
            return
            
        # Convert sync URL to async if needed
        async_url = self._get_async_url(DATABASE_URL)
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            async_url,
            echo=False,  # Set to True for SQL debugging
            poolclass=QueuePool,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_timeout=self._pool_timeout,
            pool_recycle=self._pool_recycle,
            pool_pre_ping=True,  # Verify connections before use
        )
        
        # Create async session maker
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info(f"Async database initialized with pool_size={self._pool_size}, max_overflow={self._max_overflow}")
    
    def _get_async_url(self, url: str) -> str:
        """Convert sync database URL to async URL."""
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup."""
        if self.async_session_maker is None:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: dict = None) -> list:
        """Execute a raw SQL query asynchronously."""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()
    
    async def execute_scalar(self, query: str, params: dict = None):
        """Execute a query and return scalar result."""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.scalar()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            await self.execute_scalar("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if self.engine is None:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    async def close(self):
        """Close database engine and cleanup resources."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Async database engine disposed")

# Global async database service instance
async_db_service = AsyncDatabaseService()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_db_service.get_session() as session:
        yield session 