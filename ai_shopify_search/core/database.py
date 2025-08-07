#!/usr/bin/env python3
"""
Database configuration and session management for Findly AI Search.
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from ai_shopify_search.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_store_database_url(store_id: str) -> str:
    """
    Get the database URL for a specific store.
    
    Args:
        store_id: Store identifier (e.g., 'sportkleding-pro')
        
    Returns:
        Database URL for the store
    """
    if not store_id:
        return DATABASE_URL
    
    # Convert store_id to database name format
    # Replace hyphens with underscores and add findly_ prefix
    db_name = f"findly_{store_id.replace('-', '_')}"
    
    # Extract base connection info from main DATABASE_URL
    if DATABASE_URL.startswith("postgresql://"):
        # Parse the main DATABASE_URL
        parts = DATABASE_URL.split("/")
        if len(parts) >= 2:
            base_url = "/".join(parts[:-1])  # Everything except the database name
            return f"{base_url}/{db_name}"
    
    # Fallback to main database if parsing fails
    logger.warning(f"Could not parse DATABASE_URL, using main database for store {store_id}")
    return DATABASE_URL

def get_store_db(store_id: str):
    """
    Get database session for a specific store.
    
    Args:
        store_id: Store identifier
        
    Yields:
        Database session for the store
    """
    store_db_url = get_store_database_url(store_id)
    
    # Create a new engine for this store
    store_engine = create_engine(
        store_db_url,
        poolclass=StaticPool,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    
    # Create session factory for this store
    StoreSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=store_engine)
    
    db = StoreSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

# Initialize database only when module is run directly
if __name__ == "__main__":
    create_tables() 