#!/usr/bin/env python3
"""
Database models for Findly AI Search.

Contains SQLAlchemy models for:
- Products
- Search Analytics
- Query Suggestions
- Popular Searches
- Search Corrections
- Search Clicks
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Product(Base):
    """Product model for Shopify products."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    shopify_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float)
    tags = Column(JSON)
    embedding = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SearchAnalytics(Base):
    """Search analytics model."""
    __tablename__ = "search_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    search_type = Column(String, default="ai")
    filters = Column(JSON)
    result_count = Column(Integer)
    page = Column(Integer, default=1)
    limit = Column(Integer, default=25)
    response_time_ms = Column(Float)
    cache_hit = Column(Boolean, default=False)
    user_agent = Column(String)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class QuerySuggestion(Base):
    """Query suggestion model."""
    __tablename__ = "query_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    suggestion = Column(String, nullable=False)
    frequency = Column(Integer, default=1)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class PopularSearch(Base):
    """Popular search model."""
    __tablename__ = "popular_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False, unique=True)
    search_count = Column(Integer, default=1)
    last_searched = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchCorrection(Base):
    """Search correction model."""
    __tablename__ = "search_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    original_query = Column(String, nullable=False)
    corrected_query = Column(String, nullable=False)
    confidence = Column(Float)
    frequency = Column(Integer, default=1)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchClick(Base):
    """Search click tracking model."""
    __tablename__ = "search_clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    search_analytics_id = Column(Integer, ForeignKey("search_analytics.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    position = Column(Integer)
    click_time_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    search_analytics = relationship("SearchAnalytics")
    product = relationship("Product")

class FacetUsage(Base):
    """Facet usage tracking model."""
    __tablename__ = "facet_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    facet_name = Column(String, nullable=False)
    facet_value = Column(String, nullable=False)
    usage_count = Column(Integer, default=1)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchPerformance(Base):
    """Search performance tracking model."""
    __tablename__ = "search_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    response_time_ms = Column(Float)
    result_count = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    search_type = Column(String, default="ai")
    timestamp = Column(DateTime, default=datetime.utcnow) 