import os
from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

# Get DATABASE_URL from environment or config
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    try:
        from config import DATABASE_URL
    except ImportError:
        DATABASE_URL = 'sqlite:///./test.db'

# Conditional imports for PostgreSQL vs SQLite
if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    from pgvector.sqlalchemy import Vector
    VectorType = Vector(1536)
    ArrayType = ARRAY(String)
else:
    # SQLite fallbacks
    VectorType = Text  # Store as JSON string
    ArrayType = Text   # Store as JSON string

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    shopify_domain = Column(String, unique=True, nullable=False)
    access_token = Column(String, nullable=False)
    installed_at = Column(TIMESTAMP, server_default=func.now())
    products = relationship("Product", back_populates="store")

import json

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=True)
    shopify_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String)
    price = Column(Float)
    tags = Column(ArrayType)
    embedding = Column(VectorType)
    store = relationship("Store", back_populates="products")
    
    def __init__(self, **kwargs):
        # Serialize lists for SQLite
        if 'tags' in kwargs and isinstance(kwargs['tags'], list):
            if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
                kwargs['tags'] = json.dumps(kwargs['tags'])
        if 'embedding' in kwargs and isinstance(kwargs['embedding'], list):
            if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
                kwargs['embedding'] = json.dumps(kwargs['embedding'])
        super().__init__(**kwargs)

class SearchAnalytics(Base):
    __tablename__ = "search_analytics"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)  # Unieke sessie ID
    query = Column(String, nullable=False)
    search_type = Column(String)  # 'basic', 'ai', 'faceted'
    filters = Column(JSON)  # Opgeslagen filters
    results_count = Column(Integer)
    page = Column(Integer, default=1)
    limit = Column(Integer, default=50)
    response_time_ms = Column(Float)  # Response tijd in milliseconden
    cache_hit = Column(Boolean, default=False)
    user_agent = Column(String)
    ip_address = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())

class SearchClick(Base):
    __tablename__ = "search_clicks"
    id = Column(Integer, primary_key=True, index=True)
    search_analytics_id = Column(Integer, ForeignKey("search_analytics.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    position = Column(Integer)  # Positie in zoekresultaten (1-based)
    click_time_ms = Column(Float)  # Tijd na search in milliseconden
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    search_analytics = relationship("SearchAnalytics")
    product = relationship("Product")

class SearchPerformance(Base):
    __tablename__ = "search_performance"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD format
    search_type = Column(String, index=True)
    total_searches = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0)
    cache_hit_rate = Column(Float, default=0)  # Percentage cache hits
    avg_results_count = Column(Float, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class PopularSearch(Base):
    __tablename__ = "popular_searches"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    search_count = Column(Integer, default=1)
    click_count = Column(Integer, default=0)
    avg_position_clicked = Column(Float, default=0)
    last_searched = Column(TIMESTAMP, server_default=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class FacetUsage(Base):
    __tablename__ = "facet_usage"
    id = Column(Integer, primary_key=True, index=True)
    facet_type = Column(String, index=True)  # category, color, material, etc.
    facet_value = Column(String, index=True)
    usage_count = Column(Integer, default=1)
    last_used = Column(TIMESTAMP, server_default=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class QuerySuggestion(Base):
    __tablename__ = "query_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)  # Basis query
    suggestion = Column(String, index=True)  # Volledige suggestion
    suggestion_type = Column(String, index=True)  # 'autocomplete', 'popular', 'related', 'correction'
    search_count = Column(Integer, default=0)  # Hoe vaak deze suggestion gebruikt is
    click_count = Column(Integer, default=0)  # Hoe vaak er op geklikt is
    relevance_score = Column(Float, default=0.0)  # AI-based relevance score
    context = Column(JSON)  # Context data (filters, categories, etc.)
    is_active = Column(Boolean, default=True)  # Of de suggestion actief is
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class SearchCorrection(Base):
    __tablename__ = "search_corrections"
    id = Column(Integer, primary_key=True, index=True)
    original_query = Column(String, index=True)  # Originele (mogelijk foutieve) query
    corrected_query = Column(String, index=True)  # Gecorrigeerde query
    correction_type = Column(String, index=True)  # 'spelling', 'synonym', 'expansion'
    confidence_score = Column(Float, default=0.0)  # Vertrouwen in de correctie
    usage_count = Column(Integer, default=0)  # Hoe vaak deze correctie gebruikt is
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class LanguageDetection(Base):
    __tablename__ = "language_detection"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)  # Originele query
    detected_language = Column(String, index=True)  # Gedetecteerde taal (ISO 639-1)
    confidence_score = Column(Float, default=0.0)  # Vertrouwen in taal detectie
    user_language = Column(String, index=True)  # Gebruiker's voorkeur taal
    created_at = Column(TIMESTAMP, server_default=func.now())

class Translation(Base):
    __tablename__ = "translations"
    id = Column(Integer, primary_key=True, index=True)
    source_text = Column(String, index=True)  # Bron tekst
    source_language = Column(String, index=True)  # Bron taal (ISO 639-1)
    target_language = Column(String, index=True)  # Doel taal (ISO 639-1)
    translated_text = Column(String, index=True)  # Vertaalde tekst
    translation_type = Column(String, index=True)  # 'query', 'suggestion', 'facet', 'product'
    context = Column(JSON)  # Context data
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class LocalizedFacet(Base):
    __tablename__ = "localized_facets"
    id = Column(Integer, primary_key=True, index=True)
    facet_type = Column(String, index=True)  # category, color, material, etc.
    facet_value = Column(String, index=True)  # Originele waarde
    language = Column(String, index=True)  # Taal (ISO 639-1)
    localized_value = Column(String, index=True)  # Gelokaliseerde waarde
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class LocalizedSuggestion(Base):
    __tablename__ = "localized_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    original_suggestion = Column(String, index=True)  # Originele suggestion
    language = Column(String, index=True)  # Taal (ISO 639-1)
    localized_suggestion = Column(String, index=True)  # Gelokaliseerde suggestion
    suggestion_type = Column(String, index=True)  # autocomplete, popular, related
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())