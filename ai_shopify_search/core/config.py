import os
from dotenv import load_dotenv

load_dotenv()

# Database configuratie
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/databases/findly_consolidated.db")
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 10))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", 20))

# Redis configuratie
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Cache instellingen
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1 uur default
SEARCH_CACHE_TTL = int(os.getenv("SEARCH_CACHE_TTL", 1800))  # 30 minuten voor zoeken
AI_SEARCH_CACHE_TTL = int(os.getenv("AI_SEARCH_CACHE_TTL", 900))  # 15 minuten voor AI zoeken

# OpenAI configuratie
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "text-embedding-ada-002")

# Shopify configuratie
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

# App instellingen
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")