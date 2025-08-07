#!/usr/bin/env python3
"""
Shopify Import Service

Handles importing products from multiple Shopify stores with flexible authentication.
Enhanced with batch processing, rate limiting, error handling, and observability.
Now includes image embedding support with OpenCLIP.
"""

import logging
import aiohttp
import asyncio
import urllib.parse 
import time
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from sqlalchemy.dialects.postgresql import insert
from ai_shopify_search.core.models import Product
from ai_shopify_search.core.embeddings import generate_embedding, generate_batch_image_embeddings
from ai_shopify_search.core.metrics import SEARCH_REQUESTS_TOTAL, SEARCH_RESPONSE_TIME
from ai_shopify_search.core.progress_tracker import progress_tracker
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Optional Sentry integration
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 200
DEFAULT_RATE_LIMIT = 2.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RECOVERY_TIMEOUT = 60
DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_TIMEOUT = 60
DEFAULT_CONNECT_TIMEOUT = 30
DEFAULT_LIMIT_PER_HOST = 30
DEFAULT_CONNECTOR_LIMIT = 100
DEFAULT_DNS_CACHE_TTL = 300
DEFAULT_PROGRESS_UPDATE_INTERVAL = 10

# API Constants
SHOPIFY_API_VERSION = "2024-01"
SHOPIFY_PRODUCTS_ENDPOINT = "/admin/api/{version}/products.json"
SHOPIFY_SHOP_ENDPOINT = "/admin/api/{version}/shop.json"

# Error Messages
ERROR_CONNECTION_FAILED = "Connection test failed: {error}"
ERROR_IMPORT_FAILED = "Import failed: {error}"
ERROR_PRODUCT_PROCESSING = "Failed to process product {index}: {error}"
ERROR_EMBEDDING_GENERATION = "Failed to generate embeddings for product {shopify_id}: {error}"

# Logging Context Keys
LOG_CONTEXT_STORE_ID = "store_id"
LOG_CONTEXT_BATCH_NUMBER = "batch_number"
LOG_CONTEXT_PRODUCT_COUNT = "product_count"
LOG_CONTEXT_IMPORT_ID = "import_id"

class RateLimiter:
    """Rate limiter for API calls to respect rate limits."""
    
    def __init__(self, requests_per_second: float = DEFAULT_RATE_LIMIT):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second allowed
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    async def wait_if_needed(self):
        """Wait if needed to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

class CircuitBreaker:
    """Circuit breaker pattern for API calls to handle failures gracefully."""
    
    def __init__(self, failure_threshold: int = DEFAULT_FAILURE_THRESHOLD, recovery_timeout: int = DEFAULT_RECOVERY_TIMEOUT):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """
        Check if the circuit breaker allows execution.
        
        Returns:
            True if execution is allowed, False otherwise
        """
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self):
        """Called when an operation succeeds."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Called when an operation fails."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ImportMetrics:
    """Prometheus metrics for import operations."""
    
    def __init__(self):
        """Initialize import metrics."""
        # Import duration histogram
        self.import_duration = SEARCH_RESPONSE_TIME.labels(
            search_type="shopify_import"
        )
        
        # Import counters
        self.import_requests_total = SEARCH_REQUESTS_TOTAL.labels(
            search_type="shopify_import", cache_hit="false"
        )
    
    def record_import_duration(self, duration: float):
        """
        Record import duration.
        
        Args:
            duration: Duration in seconds
        """
        self.import_duration.observe(duration)
    
    def record_import_request(self):
        """Record import request."""
        self.import_requests_total.inc()

class ImportService(ABC):
    """Abstract base class for import services."""
    
    def __init__(self, rate_limit: float = DEFAULT_RATE_LIMIT):
        """
        Initialize import service.
        
        Args:
            rate_limit: Rate limit for API calls
        """
        self.rate_limiter = RateLimiter(rate_limit)
        self.circuit_breaker = CircuitBreaker()
        self.metrics = ImportMetrics()
        self.batch_size = DEFAULT_BATCH_SIZE
    
    @abstractmethod
    async def test_connection(self, store_url: str, access_token: str) -> Dict[str, Any]:
        """
        Test connection to store.
        
        Args:
            store_url: Store URL
            access_token: Access token
            
        Returns:
            Connection test result
        """
        pass
    
    @abstractmethod
    async def get_products(self, store_url: str, access_token: str, limit: int = 250) -> List[Dict[str, Any]]:
        """
        Get products from store.
        
        Args:
            store_url: Store URL
            access_token: Access token
            limit: Maximum number of products to fetch
            
        Returns:
            List of products
        """
        pass
    
    @abstractmethod
    async def import_products(
        self, 
        db: Session, 
        store_url: str, 
        access_token: str, 
        generate_embeddings: bool = True,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import products from store into database.
        
        Args:
            db: Database session
            store_url: Store URL
            access_token: Access token
            generate_embeddings: Whether to generate embeddings
            store_id: Store identifier
            
        Returns:
            Import result
        """
        pass
    
    def _add_sentry_breadcrumb(self, message: str, category: str = "import", level: str = "info", **kwargs):
        """
        Add Sentry breadcrumb if available.
        
        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Breadcrumb level
            **kwargs: Additional breadcrumb data
        """
        if SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=kwargs
            )
    
    def _capture_sentry_error(self, error: Exception, context: Dict[str, Any] = None):
        """
        Capture error in Sentry if available.
        
        Args:
            error: Exception to capture
            context: Additional context
        """
        if SENTRY_AVAILABLE:
            if context:
                sentry_sdk.set_context("import_context", context)
            sentry_sdk.capture_exception(error)

class ShopifyImportService(ImportService):
    """Service for importing products from Shopify stores."""
    
    def __init__(self):
        """
        Initialize Shopify import service.
        
        Sets up rate limiting, circuit breaker, metrics, and OpenAI client.
        """
        super().__init__(rate_limit=1.0)  # More conservative rate limit
        self.session = None
        self.rate_limiter = RateLimiter(requests_per_second=DEFAULT_RATE_LIMIT)
        self.circuit_breaker = CircuitBreaker()
        self.metrics = ImportMetrics()
        self.batch_size = 1  # Process each product individually to ensure all products get embeddings
        self.openai_client = AsyncOpenAI()  # Async OpenAI client
    
    async def __aenter__(self):
        """
        Create aiohttp session with SSL verification disabled for development.
        
        Returns:
            Self for context manager usage
        """
        import ssl
        
        logger.info("Creating aiohttp session with SSL verification disabled for development")
        
        # Create SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create connector with disabled SSL verification
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            use_dns_cache=True,
            ttl_dns_cache=DEFAULT_DNS_CACHE_TTL,
            limit=DEFAULT_CONNECTOR_LIMIT,
            limit_per_host=DEFAULT_LIMIT_PER_HOST
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT, connect=DEFAULT_CONNECT_TIMEOUT)
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up aiohttp session.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.session:
            await self.session.close()
            self.session = None
    
    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, aiohttp.ClientConnectorCertificateError))
    )
    async def _make_api_request(self, url: str, headers: Dict[str, str]) -> aiohttp.ClientResponse:
        """
        Make API request with retry logic and rate limiting.
        
        Args:
            url: API endpoint URL
            headers: Request headers
            
        Returns:
            aiohttp.ClientResponse object
            
        Raises:
            Exception: If circuit breaker is open
            aiohttp.ClientError: If request fails
        """
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN")
        
        try:
            await self.rate_limiter.wait_if_needed()
            
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT, connect=DEFAULT_CONNECT_TIMEOUT)) as response:
                if response.status in [429, 500, 502, 503, 504]:
                    self.circuit_breaker.on_failure()
                    self._add_sentry_breadcrumb(
                        f"API request failed: HTTP {response.status}",
                        category="api_error",
                        level="error",
                        url=url,
                        status_code=response.status
                    )
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                else:
                    self.circuit_breaker.on_success()
                    self._add_sentry_breadcrumb(
                        f"API request successful: HTTP {response.status}",
                        category="api_success",
                        level="info",
                        url=url,
                        status_code=response.status
                    )
                    return response
        except aiohttp.ClientConnectorCertificateError as e:
            self.circuit_breaker.on_failure()
            logger.error(f"SSL Certificate error for {url}: {e}")
            self._add_sentry_breadcrumb(
                f"SSL Certificate error: {e}",
                category="ssl_error",
                level="error",
                url=url
            )
            raise
        except aiohttp.ClientConnectorError as e:
            self.circuit_breaker.on_failure()
            logger.error(f"Connection error for {url}: {e}")
            self._add_sentry_breadcrumb(
                f"Connection error: {e}",
                category="connection_error",
                level="error",
                url=url
            )
            raise
        except aiohttp.ClientError as e:
            self.circuit_breaker.on_failure()
            logger.error(f"Client error for {url}: {e}")
            self._add_sentry_breadcrumb(
                f"Client error: {e}",
                category="client_error",
                level="error",
                url=url
            )
            raise
        except Exception as e:
            self.circuit_breaker.on_failure()
            logger.error(f"Unexpected error for {url}: {e}")
            raise
    
    async def test_connection(self, store_url: str, access_token: str) -> Dict[str, Any]:
        """Test connection to Shopify store."""
        try:
            # Ensure proper URL format
            if not store_url.startswith(('http://', 'https://')):
                store_url = f"https://{store_url}"
            
            # Remove trailing slash if present
            store_url = store_url.rstrip('/')
            
            api_url = f"{store_url}/admin/api/2023-10/shop.json"
            headers = {
                'X-Shopify-Access-Token': access_token,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Testing connection to: {api_url}")
            
            self._add_sentry_breadcrumb(
                "Testing Shopify connection",
                category="connection_test",
                store_url=store_url,
                api_url=api_url
            )
            
            # Use direct request instead of retry logic for connection test
            async with self.session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    shop_data = await response.json()
                    shop_name = shop_data.get("shop", {}).get("name", "Unknown")
                    
                    logger.info(f"Successfully connected to shop: {shop_name}")
                    
                    self._add_sentry_breadcrumb(
                        f"Successfully connected to {shop_name}",
                        category="connection_success",
                        shop_name=shop_name
                    )
                    
                    return {
                        "success": True,
                        "shop_name": shop_name,
                        "shop_domain": shop_data.get("shop", {}).get("domain", store_url)
                    }
                elif response.status == 401:
                    error_text = await response.text()
                    logger.error(f"Authentication failed: {error_text}")
                    return {
                        "success": False,
                        "error": f"Authentication failed: Invalid access token (HTTP 401)"
                    }
                elif response.status == 403:
                    error_text = await response.text()
                    logger.error(f"Access denied: {error_text}")
                    return {
                        "success": False,
                        "error": f"Access denied: Insufficient permissions (HTTP 403)"
                    }
                elif response.status == 404:
                    logger.error(f"Store not found: {store_url}")
                    return {
                        "success": False,
                        "error": f"Store not found: Invalid store URL (HTTP 404)"
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status}: {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error: {e}")
            return {
                "success": False,
                "error": f"Connection error: Unable to connect to {store_url}. Please check the store URL and your internet connection."
            }
        except aiohttp.ClientError as e:
            logger.error(f"Client error: {e}")
            return {
                "success": False,
                "error": f"Client error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            self._capture_sentry_error(e, {"store_url": store_url, "operation": "test_connection"})
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}"
            }
    

    async def get_products(self, store_url: str, access_token: str, limit: int = 250) -> List[Dict[str, Any]]:
        """Get all products from Shopify store with robust cursor-based pagination."""
        if not store_url.startswith(('http://', 'https://')):
            store_url = f"https://{store_url}"
        
        base_url = f"{store_url}/admin/api/2023-10/products.json?limit=250"
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        all_products = []
        page_info = None
        page_count = 0
        
        while True:
            url = base_url
            if page_info:
                encoded_page_info = urllib.parse.quote(page_info, safe="")
                url = f"{store_url}/admin/api/2023-10/products.json?limit=250&page_info={encoded_page_info}"
            
            await self.rate_limiter.wait_if_needed()
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to fetch products: HTTP {response.status} - {error_text}")
                
                data = await response.json()
                products = data.get("products", [])
                all_products.extend(products)
                page_count += 1
                
                logger.info(f"📄 Page {page_count}: fetched {len(products)} products (total so far: {len(all_products)})")
                
                # Stop if we've hit the limit
                if limit and len(all_products) >= limit:
                    logger.info(f"Reached limit of {limit} products after {page_count} pages.")
                    return all_products[:limit]
                
                # Parse Link header for next page
                link_header = response.headers.get("Link", "")
                if 'rel="next"' in link_header:
                    import re
                    match = re.search(r'page_info=([^&>]+)', link_header)
                    if match:
                        page_info = match.group(1)
                        logger.debug(f"Next page_info: {page_info}")
                    else:
                        logger.warning(f"⚠️ Found 'rel=\"next\"' but couldn't extract page_info. Stopping pagination.")
                        break
                else:
                    logger.info("No more pages. Pagination complete.")
                    break

        logger.info(f"🎉 Completed fetching products: {len(all_products)} total across {page_count} pages.")
        return all_products
    
    async def count_products(self, store_url: str, access_token: str) -> Dict[str, Any]:
        """Count total products in Shopify store."""
        if not store_url.startswith(('http://', 'https://')):
            store_url = f"https://{store_url}"
        
        api_url = f"{store_url}/admin/api/2023-10/products/count.json"
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            await self.rate_limiter.wait_if_needed()
            async with self.session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get product count: HTTP {response.status} - {error_text}")
                
                data = await response.json()
                count = data.get("count", 0)
                
                logger.info(f"Found {count} products in Shopify store")
                
                return {
                    "success": True,
                    "count": count,
                    "store_url": store_url
                }
                
        except Exception as e:
            logger.error(f"Failed to count products: {e}")
            return {
                "success": False,
                "error": str(e),
                "count": 0
            }
    
    def _parse_shopify_product(self, shopify_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Shopify product data into our rich product model.
        
        Args:
            shopify_product: Raw Shopify product data
            
        Returns:
            Parsed product data with all new fields
        """
        try:
            # Extract basic fields
            product_data = self._extract_basic_fields(shopify_product)
            
            # Extract SEO fields
            product_data.update(self._extract_seo_fields(shopify_product))
            
            # Extract price and stock status from variants
            variants = shopify_product.get('variants', [])
            product_data.update(self._extract_variant_data(variants))
            
            # Extract product attributes from variants
            product_attributes = self._extract_product_attributes(variants)
            
            # Extract additional attributes from tags
            self._extract_tag_attributes(product_data, product_attributes)
            
            # Add product attributes if we found any
            if product_attributes:
                product_data['product_attributes'] = product_attributes
            
            # Extract image data
            image_data = self._extract_image_data(shopify_product)
            product_data.update(image_data)
            
            logger.debug(f"Parsed product {product_data['shopify_id']}: {product_data['title']}")
            return product_data
            
        except Exception as e:
            logger.error(f"Error parsing Shopify product {shopify_product.get('id', 'unknown')}: {e}")
            # Return minimal data to prevent import failure
            return {
                'shopify_id': str(shopify_product.get('id', '')),
                'title': shopify_product.get('title', 'Unknown Product'),
                'price': 0.0,
                'tags': [],
                'stock_status': 'unknown'
            }

    def _extract_basic_fields(self, shopify_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic fields from Shopify product.
        
        Args:
            shopify_product: Raw Shopify product data
            
        Returns:
            Dictionary with basic fields
        """
        return {
            'shopify_id': str(shopify_product.get('id', '')),
            'title': shopify_product.get('title', ''),
            'description': shopify_product.get('body_html', ''),
            'vendor': shopify_product.get('vendor', ''),
            'product_type': shopify_product.get('product_type', ''),
            'status': shopify_product.get('status', 'active'),
            'tags': shopify_product.get('tags', '').split(', ') if shopify_product.get('tags') else [],
            'created_at': shopify_product.get('created_at'),
            'updated_at': shopify_product.get('updated_at'),
        }
    
    def _extract_seo_fields(self, shopify_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract SEO fields from Shopify product.
        
        Args:
            shopify_product: Raw Shopify product data
            
        Returns:
            Dictionary with SEO fields
        """
        seo_fields = {}
        
        # Extract SEO title
        if 'metafields_global_title_tag' in shopify_product:
            seo_fields['seo_title'] = shopify_product['metafields_global_title_tag']
        elif 'metafields' in shopify_product:
            for metafield in shopify_product['metafields']:
                if metafield.get('key') == 'title_tag':
                    seo_fields['seo_title'] = metafield.get('value')
                    break
        
        # Extract SEO description
        if 'metafields_global_description_tag' in shopify_product:
            seo_fields['seo_description'] = shopify_product['metafields_global_description_tag']
        elif 'metafields' in shopify_product:
            for metafield in shopify_product['metafields']:
                if metafield.get('key') == 'description_tag':
                    seo_fields['seo_description'] = metafield.get('value')
                    break
        
        return seo_fields
    
    def _extract_variant_data(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract data from product variants.
        
        Args:
            variants: List of product variants
            
        Returns:
            Dictionary with variant data
        """
        variant_data = {}
        
        if not variants:
            return variant_data
        
        first_variant = variants[0]
        variant_data.update({
            'price': float(first_variant.get('price', 0)),
            'sku': first_variant.get('sku', ''),
            'barcode': first_variant.get('barcode', ''),
        })
        
        # Determine stock status
        inventory_quantity = first_variant.get('inventory_quantity', 0)
        variant_data['stock_status'] = 'in_stock' if inventory_quantity > 0 else 'out_of_stock'
        
        return variant_data
    
    def _extract_product_attributes(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract product attributes from variants.
        
        Args:
            variants: List of product variants
            
        Returns:
            Dictionary with product attributes
        """
        product_attributes = {}
        sizes = set()
        colors = set()
        materials = set()
        
        for variant in variants:
            # Extract size, color, material from options
            if variant.get('option1'):
                sizes.add(variant['option1'])
            if variant.get('option2'):
                colors.add(variant['option2'])
            if variant.get('option3'):
                materials.add(variant['option3'])
            
            # Extract weight and dimensions
            if variant.get('weight'):
                product_attributes['weight'] = f"{variant['weight']}g"
            
            if variant.get('weight_unit'):
                product_attributes['weight_unit'] = variant['weight_unit']
        
        # Add extracted attributes
        if sizes:
            product_attributes['sizes'] = list(sizes)
        if colors:
            product_attributes['colors'] = list(colors)
        if materials:
            product_attributes['materials'] = list(materials)
        
        return product_attributes
    
    def _extract_image_data(self, shopify_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract image data from Shopify product.
        
        Args:
            shopify_product: Raw Shopify product data
            
        Returns:
            Dictionary with image data
        """
        image_data = {}
        
        # Extract main image
        if 'image' in shopify_product and shopify_product['image']:
            image_data['image_url'] = shopify_product['image'].get('src', '')
        
        # Extract additional images
        images = shopify_product.get('images', [])
        if images:
            image_data['additional_images'] = [img.get('src', '') for img in images if img.get('src')]
        
        return image_data

    async def generate_embeddings_batch(self, texts: List[str], batch_number: int = 0) -> List[List[float]]:
        """Generate embeddings for a batch of texts using AsyncOpenAI."""
        if not texts:
            return []
        
        logger.info(f"Processing embedding batch #{batch_number}: {len(texts)} texts")
        
        try:
            # Use AsyncOpenAI client for batch processing
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
                encoding_format="float"
            )
            
            embeddings = [embedding.embedding for embedding in response.data]
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings for batch #{batch_number}")
            
            self._add_sentry_breadcrumb(
                f"Generated embeddings for batch #{batch_number}: {len(texts)} texts",
                category="embedding_generation",
                batch_size=len(texts),
                batch_number=batch_number
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch #{batch_number} embedding generation failed: {e}")
            self._capture_sentry_error(e, {
                "batch_size": len(texts), 
                "operation": "embedding_generation",
                "batch_number": batch_number
            })
            
            # Fallback to individual embeddings
            logger.info(f"Falling back to individual embeddings for batch #{batch_number}")
            embeddings = []
            for i, text in enumerate(texts):
                try:
                    # Use the correct function signature (not async)
                    embedding = generate_embedding(title=text)
                    embeddings.append(embedding)
                    logger.debug(f"Individual embedding {i+1}/{len(texts)} successful for batch #{batch_number}")
                except Exception as e2:
                    logger.warning(f"Individual embedding {i+1}/{len(texts)} failed for batch #{batch_number}: {e2}")
                    embeddings.append([0.0] * 1536)  # Default embedding
            
            logger.info(f"Fallback completed for batch #{batch_number}: {len(embeddings)} embeddings")
            return embeddings
    
    def bulk_save_products(
        self, 
        db: Session, 
        products_data: List[Dict[str, Any]], 
        batch_size: int = 200
    ) -> Dict[str, int]:
        """
        Bulk upsert products to PostgreSQL with batching.
        Uses INSERT ... ON CONFLICT DO UPDATE for safe idempotent writes.
        Returns dict with inserted, updated, and failed counts.
        """
        if not products_data:
            logger.info("No products to upsert")
            return {"inserted": 0, "updated": 0, "failed": 0}

        total = len(products_data)
        success_batches = fail_batches = 0
        success_count = fail_count = 0
        total_inserted = 0
        total_updated = 0
        
        logger.info(f"🔄 Starting bulk upsert of {total} products (batch size={batch_size})")

        # Get existing shopify_ids for conflict detection
        existing_shopify_ids = set()
        try:
            existing_products = db.query(Product.shopify_id).all()
            existing_shopify_ids = {p.shopify_id for p in existing_products}
            logger.info(f"📋 Found {len(existing_shopify_ids)} existing products in database")
        except Exception as e:
            logger.warning(f"⚠️ Could not query existing products: {e}")

        for batch_num, start in enumerate(range(0, total, batch_size), 1):
            batch = products_data[start:start + batch_size]
            batch_shopify_ids = [p.get('shopify_id') for p in batch]
            product_ids = [p.get('shopify_id', f'unknown_{i}') for i, p in enumerate(batch, start + 1)]
            logger.info(f"📦 Batch {batch_num}: {len(batch)} products ({product_ids[0]}...{product_ids[-1] if len(product_ids) > 1 else ''})")

            try:
                # Count new vs existing products in this batch
                batch_new = sum(1 for sid in batch_shopify_ids if sid not in existing_shopify_ids)
                batch_updated = len(batch) - batch_new

                # Add updated_at field
                batch_with_timestamps = [{**p, "updated_at": func.now()} for p in batch]

                # Build the base insert
                base_stmt = insert(Product).values(batch_with_timestamps)

                # Add upsert behavior
                stmt = base_stmt.on_conflict_do_update(
                    index_elements=["shopify_id"],
                    set_={
                        "title": base_stmt.excluded.title,
                        "description": base_stmt.excluded.description,
                        "vendor": base_stmt.excluded.vendor,
                        "product_type": base_stmt.excluded.product_type,
                        "seo_title": base_stmt.excluded.seo_title,
                        "seo_description": base_stmt.excluded.seo_description,
                        "product_attributes": base_stmt.excluded.product_attributes,
                        "stock_status": base_stmt.excluded.stock_status,
                        "sku": base_stmt.excluded.sku,
                        "barcode": base_stmt.excluded.barcode,
                        "status": base_stmt.excluded.status,
                        "tags": base_stmt.excluded.tags,
                        "price": base_stmt.excluded.price,
                        "embedding": base_stmt.excluded.embedding,
                        "image_embedding": base_stmt.excluded.image_embedding,
                        "text_embedding": base_stmt.excluded.text_embedding,
                        "combined_embedding": base_stmt.excluded.combined_embedding,
                        "combined_embedding_vector": base_stmt.excluded.combined_embedding_vector,
                        "updated_at": base_stmt.excluded.updated_at,
                    },
                )

                db.execute(stmt)
                db.commit()

                success_batches += 1
                success_count += len(batch)
                total_inserted += batch_new
                total_updated += batch_updated
                
                # Enhanced logging as requested
                logger.info(f"✅ Batch {batch_num} committed: {batch_new} new, {batch_updated} updated")

                self._add_sentry_breadcrumb(
                    "Batch upsert successful",
                    category="database_operation",
                    batch_number=batch_num,
                    product_count=len(batch),
                    new_count=batch_new,
                    updated_count=batch_updated,
                    product_ids=product_ids[:10],
                )

            except Exception as e:
                db.rollback()
                fail_batches += 1
                fail_count += len(batch)
                logger.exception(f"❌ Batch {batch_num} failed: {e}")
                self._capture_sentry_error(
                    e,
                    {
                        "operation": "bulk_upsert",
                        "batch_number": batch_num,
                        "product_ids": product_ids[:20],
                        "total_products": total,
                    },
                )
                # Continue with next batch instead of breaking the entire process
                continue

        logger.info(
            f"📊 Bulk upsert completed: {success_count}/{total} products "
            f"({success_batches} batches succeeded, {fail_batches} failed)"
        )

        if success_batches == 0:
            raise Exception(f"All {fail_batches} batches failed during bulk upsert")
        if fail_batches > 0:
            logger.warning(f"⚠️ Partial failure: {fail_batches} batches failed.")

        return {
            "inserted": total_inserted,
            "updated": total_updated,
            "failed": fail_count
        }
    
    async def _progress_step(self, import_id: Optional[str], step: int, message: str) -> None:
        """Helper method to safely update progress only if import_id is set."""
        if import_id:
            await progress_tracker.update_progress(import_id, step, message)
    
    async def _generate_import_report(self, db: Session, imported_count: int, bulk_result: Dict[str, int], shop_name: str) -> None:
        """Generate a comprehensive report after import completion."""
        try:
            from datetime import datetime
            
            # Get database statistics
            total_products = db.query(Product).count()
            products_with_embeddings = db.query(Product).filter(Product.embedding.isnot(None)).count()
            products_without_embeddings = total_products - products_with_embeddings
            
            # Get column count from information_schema
            column_count_result = db.execute("""
                SELECT COUNT(*) as column_count 
                FROM information_schema.columns 
                WHERE table_name = 'products'
            """).fetchone()
            column_count = column_count_result[0] if column_count_result else 0
            
            # Calculate embedding coverage
            embedding_coverage = (products_with_embeddings / total_products * 100) if total_products > 0 else 0
            
            # Generate report
            report = f"""
📊 IMPORT RAPPORT - {shop_name}
{'='*50}
🏪 Winkel: {shop_name}
📅 Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📦 PRODUCTEN:
   • Totaal geïmporteerd: {imported_count}
   • Nieuwe producten: {bulk_result.get('inserted', 0)}
   • Bijgewerkte producten: {bulk_result.get('updated', 0)}
   • Mislukte imports: {bulk_result.get('failed', 0)}

🗄️ DATABASE:
   • Totaal producten in DB: {total_products}
   • Producten met embeddings: {products_with_embeddings}
   • Producten zonder embeddings: {products_without_embeddings}
   • Embedding coverage: {embedding_coverage:.1f}%
   • Aantal kolommen in products tabel: {column_count}

✅ Import succesvol voltooid!
"""
            
            logger.info(report)
            
        except Exception as e:
            logger.error(f"Failed to generate import report: {e}")
            # Don't fail the import if report generation fails

    async def import_products(
        self, 
        db: Session, 
        store_url: str, 
        access_token: str, 
        generate_embeddings: bool = True,
        generate_image_embeddings: bool = False,
        store_id: Optional[str] = None,
        import_id: Optional[str] = None,
        limit: Optional[int] = 250
    ) -> Dict[str, Any]:
        """Import products from Shopify store into database, optionally with progress tracking and image embeddings."""
        start_time = time.time()
        imported_count, failed_count = 0, 0
        errors = []

        self.metrics.record_import_request()
        logger.info("🔒 Privacy-focused import: Only storing minimal product data (title, tags, price, embedding)")
        if generate_image_embeddings:
            logger.info("🖼️ Image embedding generation enabled")

        # Initialize progress tracking if needed
        await self._progress_step(import_id, 0, "Starting Shopify import...")

        try:
            # 1. Test connection
            await self._progress_step(import_id, 0, "Testing connection...")
            connection_test = await self.test_connection(store_url, access_token)
            if not connection_test["success"]:
                if import_id:
                    await progress_tracker.add_error(import_id, connection_test['error'])
                    await progress_tracker.complete_import(import_id, success=False)
                raise Exception(f"Connection test failed: {connection_test['error']}")

            # 2. Fetch products
            await self._progress_step(import_id, 0, "Fetching products...")
            products = await self.get_products(store_url, access_token, limit=limit)
            total_products = len(products)
            logger.info(f"Found {total_products} products in store")

            # 3. Prepare product dicts with O(1) lookup optimization
            products_data = []
            product_lookup = {}  # {shopify_id: product_dict} for O(1) embedding assignment
            texts_for_embeddings = []
            image_urls_for_embeddings = []
            
            for i, shopify_product in enumerate(products):
                try:
                    # Parse Shopify product using new parser
                    product_data = self._parse_shopify_product(shopify_product)
                    
                    # Add store_id if provided
                    if store_id:
                        product_data['store_id'] = store_id
                        if product_data.get('tags'):
                            product_data['tags'].append(f"store:{store_id}")
                    
                    # Extract image URL for image embeddings
                    image_url = product_data.get('image_url')
                    if generate_image_embeddings and image_url:
                        image_urls_for_embeddings.append((product_data['shopify_id'], image_url))
                    
                    # Initialize embedding fields
                    product_data.update({
                        'embedding': None,
                        'image_embedding': None,
                        'text_embedding': None,
                        'combined_embedding': None
                    })
                    
                    products_data.append(product_data)
                    product_lookup[product_data['shopify_id']] = product_data  # O(1) lookup for embedding assignment

                    if generate_embeddings and product_data.get('title'):
                        # Build comprehensive text for embedding
                        from ai_shopify_search.core.embeddings import build_embedding_text
                        embedding_text = build_embedding_text(
                            title=product_data.get('title'),
                            description=product_data.get('description'),
                            vendor=product_data.get('vendor'),
                            product_type=product_data.get('product_type'),
                            seo_title=product_data.get('seo_title'),
                            seo_description=product_data.get('seo_description'),
                            product_attributes=product_data.get('product_attributes'),
                            stock_status=product_data.get('stock_status'),
                            sku=product_data.get('sku'),
                            barcode=product_data.get('barcode'),
                            status=product_data.get('status'),
                            tags=product_data.get('tags'),
                            price=product_data.get('price')
                        )
                        texts_for_embeddings.append((product_data['shopify_id'], embedding_text))
                    
                    imported_count += 1

                    if import_id and i % 10 == 0:
                        await self._progress_step(import_id, i, f"Processed {i+1}/{total_products} products...")

                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to process product {i}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    if import_id:
                        await progress_tracker.add_error(import_id, error_msg)

            # 4. Generate comprehensive embeddings with new function
            if generate_embeddings and products_data:
                await self._progress_step(import_id, imported_count, "Generating comprehensive embeddings...")
                logger.info(f"Generating comprehensive embeddings for {len(products_data)} products")
                
                from ai_shopify_search.core.embeddings import generate_embedding
                
                for i, product_data in enumerate(products_data):
                    try:
                        if product_data.get('title'):
                            # Generate comprehensive embeddings using new function
                            embeddings = generate_embedding(
                                title=product_data.get('title'),
                                description=product_data.get('description'),
                                vendor=product_data.get('vendor'),
                                product_type=product_data.get('product_type'),
                                seo_title=product_data.get('seo_title'),
                                seo_description=product_data.get('seo_description'),
                                product_attributes=product_data.get('product_attributes'),
                                stock_status=product_data.get('stock_status'),
                                sku=product_data.get('sku'),
                                barcode=product_data.get('barcode'),
                                status=product_data.get('status'),
                                tags=product_data.get('tags'),
                                price=product_data.get('price'),
                                image_url=product_data.get('image_url') if generate_image_embeddings else None,
                                store_id=store_id
                            )
                            
                            # Assign all embedding types
                            product_data['text_embedding'] = embeddings.get('text_embedding')
                            product_data['image_embedding'] = embeddings.get('image_embedding')
                            product_data['combined_embedding'] = embeddings.get('combined_embedding')
                            product_data['embedding'] = embeddings.get('combined_embedding') or embeddings.get('text_embedding')  # Backward compatibility
                            
                            # Convert combined_embedding to vector format for AI search
                            combined_embedding = embeddings.get('combined_embedding')
                            if combined_embedding and isinstance(combined_embedding, list):
                                try:
                                    # Convert list to vector format (comma-separated string)
                                    vector_str = '[' + ','.join(str(x) for x in combined_embedding) + ']'
                                    product_data['combined_embedding_vector'] = vector_str
                                    logger.debug(f"✅ Converted combined_embedding to vector for product {product_data.get('shopify_id', 'unknown')}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Failed to convert combined_embedding to vector for product {product_data.get('shopify_id', 'unknown')}: {e}")
                                    product_data['combined_embedding_vector'] = None
                            else:
                                product_data['combined_embedding_vector'] = None
                        
                        if import_id and i % 10 == 0:
                            await self._progress_step(import_id, imported_count + i, f"Generated embeddings for {i+1}/{len(products_data)} products...")
                    
                    except Exception as e:
                        error_msg = f"Failed to generate embeddings for product {product_data.get('shopify_id', 'unknown')}: {e}"
                        logger.error(error_msg)
                        if import_id:
                            await progress_tracker.add_warning(import_id, error_msg)
                
                logger.info(f"✅ Generated comprehensive embeddings for {len(products_data)} products")

            # 5. Bulk upsert
            await self._progress_step(import_id, total_products, "Saving products to database...")
            bulk_result = {"inserted": 0, "updated": 0, "failed": 0}
            if products_data:
                logger.info(f"Starting bulk upsert of {len(products_data)} products")
                bulk_result = self.bulk_save_products(db, products_data, batch_size=200)

                        # 6. Generate import report
            await self._generate_import_report(db, imported_count, bulk_result, connection_test['shop_name'])
            
            # 7. Done
            response_time = time.time() - start_time
            self.metrics.record_import_duration(response_time)
            
            # Enhanced logging as requested
            new_or_updated = bulk_result["inserted"] + bulk_result["updated"]
            logger.info(f"Import completed: {imported_count} processed, {bulk_result['inserted']} new, {bulk_result['updated']} updated")
            
            message = f"Successfully imported {imported_count} products from {connection_test['shop_name']}"
            if failed_count > 0:
                message += f", {failed_count} failed"
            
            logger.info(f"Import completed: {message}")
            if import_id:
                await progress_tracker.complete_import(import_id, success=True)
            
            return {
                "success": True,
                "imported_count": imported_count,
                "failed_count": failed_count,
                "errors": errors,
                "message": message,
                "shop_name": connection_test["shop_name"],
                "response_time": response_time,
                "import_id": import_id,
                "new_or_updated": new_or_updated
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Import failed: {e}")
            if import_id:
                await progress_tracker.add_error(import_id, str(e))
                await progress_tracker.complete_import(import_id, success=False)
            return {
                "success": False,
                "imported_count": imported_count,
                "failed_count": failed_count,
                "errors": errors + [str(e)],
                "message": f"Import failed: {e}",
                "response_time": time.time() - start_time,
                "import_id": import_id
            }

# Global service instance
shopify_import_service = ShopifyImportService()

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `shopify_api_client.py` - API communication and rate limiting
  - `shopify_product_parser.py` - Product parsing and data extraction
  - `shopify_import_orchestrator.py` - Main import orchestration
  - `shopify_metrics.py` - Metrics and monitoring

## 🗑️ Functies voor Verwijdering
- [ ] `_add_sentry_breadcrumb()` - Consider moving to a dedicated logging service
- [ ] `_capture_sentry_error()` - Consider moving to a dedicated error handling service
- [ ] `_progress_step()` - Consider moving to a dedicated progress tracking service

## ⚡ Performance Optimalisaties
- [ ] Implement connection pooling for aiohttp sessions
- [ ] Add caching for frequently accessed product data
- [ ] Implement batch processing for embeddings generation
- [ ] Add parallel processing for product parsing
- [ ] Optimize database bulk operations

## 🏗️ Architectuur Verbeteringen
- [ ] Implement proper dependency injection
- [ ] Add configuration management for different environments
- [ ] Implement proper error recovery mechanisms
- [ ] Add comprehensive unit and integration tests
- [ ] Implement proper logging strategy with structured logging

## 🔧 Code Verbeteringen
- [ ] Add type hints for all methods
- [ ] Implement proper error handling with custom exceptions
- [ ] Add comprehensive docstrings for all methods
- [ ] Implement proper validation for input parameters
- [ ] Add proper constants for all magic numbers

## 📊 Monitoring en Observability
- [ ] Add comprehensive metrics collection
- [ ] Implement proper distributed tracing
- [ ] Add health checks for the service
- [ ] Implement proper alerting mechanisms
- [ ] Add performance monitoring

## 🔒 Security Verbeteringen
- [ ] Implement proper authentication and authorization
- [ ] Add input validation and sanitization
- [ ] Implement proper secrets management
- [ ] Add audit logging for sensitive operations
- [ ] Implement proper rate limiting strategies

## 🧪 Testing Verbeteringen
- [ ] Add unit tests for all helper methods
- [ ] Implement integration tests for API communication
- [ ] Add performance tests for bulk operations
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete import flow

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)
""" 