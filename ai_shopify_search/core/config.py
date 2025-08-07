import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the ai_shopify_search directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Database configuratie
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/findly")
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
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_TOKEN") or os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")

# Sentry configuratie
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

# App instellingen
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Image Embedding configuratie
IMAGE_EMBEDDING_TIMEOUT = int(os.getenv("IMAGE_EMBEDDING_TIMEOUT", 15))
IMAGE_EMBEDDING_MAX_SIZE = int(os.getenv("IMAGE_EMBEDDING_MAX_SIZE", 2048))
IMAGE_EMBEDDING_BATCH_SIZE = int(os.getenv("IMAGE_EMBEDDING_BATCH_SIZE", 10))

# Embedding combinatie gewichten (per categorie)
EMBEDDING_WEIGHTS = {
    "fashion": {
        "image_weight": float(os.getenv("FASHION_IMAGE_WEIGHT", "0.75")),
        "text_weight": float(os.getenv("FASHION_TEXT_WEIGHT", "0.25"))
    },
    "interieur": {
        "image_weight": float(os.getenv("INTERIEUR_IMAGE_WEIGHT", "0.75")),
        "text_weight": float(os.getenv("INTERIEUR_TEXT_WEIGHT", "0.25"))
    },
    "sieraden": {
        "image_weight": float(os.getenv("SIERADEN_IMAGE_WEIGHT", "0.55")),
        "text_weight": float(os.getenv("SIERADEN_TEXT_WEIGHT", "0.45"))
    },
    "tech": {
        "image_weight": float(os.getenv("TECH_IMAGE_WEIGHT", "0.55")),
        "text_weight": float(os.getenv("TECH_TEXT_WEIGHT", "0.45"))
    },
    "electronics": {
        "image_weight": float(os.getenv("ELECTRONICS_IMAGE_WEIGHT", "0.55")),
        "text_weight": float(os.getenv("ELECTRONICS_TEXT_WEIGHT", "0.45"))
    },
    "default": {
        "image_weight": float(os.getenv("DEFAULT_IMAGE_WEIGHT", "0.60")),
        "text_weight": float(os.getenv("DEFAULT_TEXT_WEIGHT", "0.40"))
    }
}