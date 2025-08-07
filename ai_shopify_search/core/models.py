#!/usr/bin/env python3
"""
Database models for Findly AI Search.

Contains SQLAlchemy models for:
- Products (minimal data for privacy and performance)
- Store Registry (NEW - multi-store support)
- Store Settings (NEW - store-specific configuration)
- Search Analytics
- Query Suggestions
- Popular Searches
- Search Corrections
- Search Clicks
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects import postgresql
from datetime import datetime
import json


Base = declarative_base()

# Base class for store-specific models (separate from main models)
StoreBase = declarative_base()

class StoreRegistry(Base):
    """
    Central registry for all stores in the multi-store system.
    
    Contains basic store information and connection details.
    """
    __tablename__ = "store_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, unique=True, nullable=False, index=True)  # Unique store identifier
    store_name = Column(String, nullable=False)  # Display name
    shopify_domain = Column(String, unique=True)  # Shopify domain (e.g., "mystore.myshopify.com")
    shopify_access_token = Column(String)  # Encrypted Shopify access token
    shopify_webhook_secret = Column(String)  # Webhook verification secret
    
    # Store status and configuration
    is_active = Column(Boolean, default=True)
    store_type = Column(String, default="demo")  # demo, production, trial
    plan_type = Column(String, default="basic")  # basic, pro, enterprise
    
    # Connection details
    database_url = Column(String)  # Store-specific database URL
    redis_prefix = Column(String)  # Redis key prefix for this store
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_sync_at = Column(DateTime)  # Last successful product sync

class StoreSettings(Base):
    """
    Store-specific configuration and settings.
    
    Contains store preferences, search configuration, and refinement settings.
    """
    __tablename__ = "store_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("store_registry.store_id"), unique=True, nullable=False, index=True)
    
    # Store metadata
    description = Column(Text)  # Store description
    logo_url = Column(String)  # Store logo URL
    primary_color = Column(String, default="#000000")  # Brand color
    
    # Store preferences and configuration
    style_preferences = Column(postgresql.JSONB)  # Store style (fashion, accessories, home, etc.)
    price_range = Column(postgresql.JSONB)  # Min/max price range for the store
    tone_of_voice = Column(String, default="professional")  # Tone for refinements
    
    # Search configuration
    default_search_limit = Column(Integer, default=25)
    enable_fuzzy_search = Column(Boolean, default=True)
    enable_ai_search = Column(Boolean, default=True)
    enable_refinements = Column(Boolean, default=True)
    enable_autocomplete = Column(Boolean, default=True)
    
    # Refinement configuration
    refinement_templates = Column(postgresql.JSONB)  # Store-specific refinement templates
    category_mappings = Column(postgresql.JSONB)  # Custom category mappings
    brand_priorities = Column(postgresql.JSONB)  # Priority brands for this store
    color_preferences = Column(postgresql.JSONB)  # Preferred colors
    
    # Analytics and monitoring
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Product(Base):
    """
    Product model for main database (with store_id).
    
    Used in the main database to track products across all stores.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("store_registry.store_id"), nullable=False, index=True)  # Store identifier
    shopify_id = Column(String, nullable=False, index=True)  # Shopify product ID
    title = Column(String, nullable=False)  # Product title for search and display
    description = Column(Text, nullable=True)  # Product description
    vendor = Column(String, nullable=True)  # Product vendor/brand
    product_type = Column(String, nullable=True)  # Product type/category
    seo_title = Column(String, nullable=True)  # SEO optimized title
    seo_description = Column(Text, nullable=True)  # SEO optimized description
    product_attributes = Column(postgresql.JSONB, nullable=True)  # Rich product attributes (sizes, colors, materials, etc.)
    stock_status = Column(String, nullable=True)  # in_stock, out_of_stock, etc.
    sku = Column(String, nullable=True)  # Stock keeping unit
    barcode = Column(String, nullable=True)  # Product barcode
    status = Column(String, nullable=True)  # active, draft, archived
    tags = Column(postgresql.JSONB)  # Product tags for filtering and search context
    price = Column(Float)  # Product price for filtering and display
    image_url = Column(String, nullable=True)  # Product image URL
    embedding = Column(postgresql.JSONB)  # AI embedding for semantic search
    image_embedding = Column(postgresql.JSONB)  # Image embedding for visual search
    text_embedding = Column(postgresql.JSONB)  # Text-only embedding
    combined_embedding = Column(postgresql.JSONB)  # Combined text + image embedding
    combined_embedding_vector = Column(postgresql.VECTOR(1536))  # Combined embedding as vector for AI search
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class StoreProduct(StoreBase):
    """
    Product model for store-specific databases (without store_id).
    
    Used in individual store databases for search operations.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    shopify_id = Column(String, nullable=False, index=True)  # Shopify product ID
    title = Column(String, nullable=False)  # Product title for search and display
    description = Column(Text, nullable=True)  # Product description
    vendor = Column(String, nullable=True)  # Product vendor/brand
    product_type = Column(String, nullable=True)  # Product type/category
    seo_title = Column(String, nullable=True)  # SEO optimized title
    seo_description = Column(Text, nullable=True)  # SEO optimized description
    product_attributes = Column(postgresql.JSONB, nullable=True)  # Rich product attributes (sizes, colors, materials, etc.)
    stock_status = Column(String, nullable=True)  # in_stock, out_of_stock, etc.
    sku = Column(String, nullable=True)  # Stock keeping unit
    barcode = Column(String, nullable=True)  # Product barcode
    status = Column(String, nullable=True)  # active, draft, archived
    tags = Column(postgresql.JSONB)  # Product tags for filtering and search context
    price = Column(Float)  # Product price for filtering and display
    image_url = Column(String, nullable=True)  # Product image URL
    embedding = Column(postgresql.JSONB)  # AI embedding for semantic search
    image_embedding = Column(postgresql.JSONB)  # Image embedding for visual search
    text_embedding = Column(postgresql.JSONB)  # Text-only embedding
    combined_embedding = Column(postgresql.JSONB)  # Combined text + image embedding
    combined_embedding_vector = Column(postgresql.VECTOR(1536))  # Combined embedding as vector for AI search
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

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


class StoreProfileModel(Base):
    __tablename__ = "store_profiles"
    id = Column(Integer, primary_key=True)
    store_id = Column(String, unique=True, index=True)
    product_count = Column(Integer)
    price_range_min = Column(Float)
    price_range_max = Column(Float)
    category_distribution = Column(JSON)
    brand_distribution = Column(JSON)
    material_distribution = Column(JSON)
    color_distribution = Column(JSON)
    avg_response_time_baseline = Column(Float)
    avg_relevance_score_baseline = Column(Float)
    price_filter_usage_rate = Column(Float)
    fallback_usage_rate = Column(Float)
    cache_hit_rate = Column(Float)
    successful_query_patterns = Column(JSON)
    problematic_query_patterns = Column(JSON)
    recommended_improvements = Column(JSON)
    avg_price_coherence = Column(Float)
    avg_diversity_score = Column(Float)
    avg_conversion_potential = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QueryPatternModel(Base):
    __tablename__ = "query_patterns"
    id = Column(Integer, primary_key=True)
    pattern_type = Column(String)
    pattern_text = Column(String)
    success_rate = Column(Float)
    avg_relevance_score = Column(Float)
    total_usage = Column(Integer)
    avg_response_time = Column(Float)
    price_filter_usage_rate = Column(Float)
    fallback_usage_rate = Column(Float)
    complexity_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IntentMatrixModel(Base):
    __tablename__ = "intent_matrix"
    id = Column(Integer, primary_key=True)
    intent_type = Column(String)
    query_template = Column(String)
    success_score = Column(Float)
    recommended_filters = Column(JSON)
    fallback_strategies = Column(JSON)
    avg_response_time = Column(Float)
    usage_count = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BenchmarkHistoryModel(Base):
    __tablename__ = "benchmark_history"
    id = Column(Integer, primary_key=True)
    store_id = Column(String, index=True)
    query = Column(String)
    score = Column(Float)
    response_time = Column(Float)
    result_count = Column(Integer)
    detected_intents = Column(JSON)
    complexity_score = Column(Float)
    cache_hit = Column(Boolean)
    price_filter_applied = Column(Boolean)
    fallback_used = Column(Boolean)
    avg_price_top5 = Column(Float)
    price_coherence = Column(Float)
    diversity_score = Column(Float)
    category_coverage = Column(Float)
    conversion_potential = Column(Float)
    timestamp = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)