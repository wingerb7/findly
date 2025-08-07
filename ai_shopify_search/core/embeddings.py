import openai
from .config import OPENAI_API_KEY
import re
import hashlib
import json
from typing import List, Dict, Optional, Union
from functools import lru_cache
import logging
import requests
from PIL import Image
import torch
import open_clip
import numpy as np
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = OPENAI_API_KEY

# OpenCLIP model initialization
@lru_cache(maxsize=1)
def get_clip_model():
    """Initialize and cache OpenCLIP model (ViT-B/32, pretrained='openai')."""
    try:
        model, _, preprocess = open_clip.create_model_and_transforms(
            'ViT-B-32', 
            pretrained='openai'
        )
        logger.info("OpenCLIP model loaded successfully")
        return model, preprocess
    except Exception as e:
        logger.error(f"Error loading OpenCLIP model: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def load_image_from_url_or_path(image_path_or_url: str, timeout: int = None) -> Image.Image:
    """
    Load image from URL or local path with retry logic.
    
    Args:
        image_path_or_url: URL or local path to image
        timeout: Request timeout in seconds (default: 15)
        
    Returns:
        PIL Image object
    """
    from .config import IMAGE_EMBEDDING_TIMEOUT, IMAGE_EMBEDDING_MAX_SIZE
    
    if timeout is None:
        timeout = IMAGE_EMBEDDING_TIMEOUT
    
    try:
        if image_path_or_url.startswith(('http://', 'https://')):
            # Load from URL with retry logic
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Findly-Image-Embedding/1.0'
            })
            
            response = session.get(
                image_path_or_url, 
                timeout=timeout,
                allow_redirects=True,
                verify=True
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'webp']):
                logger.warning(f"URL {image_path_or_url} doesn't appear to be an image (content-type: {content_type})")
            
            image = Image.open(BytesIO(response.content))
        else:
            # Load from local path - handle web URLs that need to be converted to local paths
            if image_path_or_url.startswith('/static/demo_images/'):
                local_path = f".{image_path_or_url}"
            else:
                local_path = image_path_or_url
            
            image = Image.open(local_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Validate image size (prevent memory issues)
        if image.size[0] > IMAGE_EMBEDDING_MAX_SIZE or image.size[1] > IMAGE_EMBEDDING_MAX_SIZE:
            logger.info(f"Resizing large image from {image.size} to max {IMAGE_EMBEDDING_MAX_SIZE}x{IMAGE_EMBEDDING_MAX_SIZE}")
            image.thumbnail((IMAGE_EMBEDDING_MAX_SIZE, IMAGE_EMBEDDING_MAX_SIZE), Image.Resampling.LANCZOS)
        
        return image
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout loading image from {image_path_or_url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error loading image from {image_path_or_url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading image from {image_path_or_url}: {e}")
        raise

def generate_image_embedding(image_path_or_url: str) -> List[float]:
    """
    Load an image (URL or path), preprocess with OpenCLIP and return a normalized embedding vector.
    
    Args:
        image_path_or_url: URL or local path to image
        
    Returns:
        Normalized embedding vector as list of floats
    """
    import os
    
    try:
        # Check if file exists for local paths
        if not image_path_or_url.startswith(('http://', 'https://')):
            # Convert web URL to local path if needed
            if image_path_or_url.startswith('/static/demo_images/'):
                local_path = f".{image_path_or_url}"
            else:
                local_path = image_path_or_url
            
            if not os.path.exists(local_path):
                logger.warning(f"Image file does not exist: {local_path}")
                raise FileNotFoundError(f"Image file not found: {local_path}")
        
        # Load image
        image = load_image_from_url_or_path(image_path_or_url)
        
        # Get model and preprocess
        model, preprocess = get_clip_model()
        
        # Preprocess image
        image_tensor = preprocess(image).unsqueeze(0)
        
        # Generate embedding
        with torch.no_grad():
            image_features = model.encode_image(image_tensor)
            
        # Normalize and convert to list
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        embedding = image_features.squeeze().cpu().numpy().tolist()
        
        logger.info(f"Generated image embedding (length: {len(embedding)})")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating image embedding: {e}")
        raise

def combine_embeddings(text_emb: List[float], image_emb: List[float], category: str = None, store_id: str = None) -> List[float]:
    """
    Combine text and image embeddings with dynamic weighting based on category and store.
    
    Args:
        text_emb: Text embedding vector
        image_emb: Image embedding vector
        category: Product category for dynamic weighting
        store_id: Store identifier for store-specific weights
        
    Returns:
        Combined embedding vector
    """
    # Get weights from configuration
    if store_id and category:
        # Use store-specific weights if available
        from .embedding_config import get_embedding_weights
        weights = get_embedding_weights(store_id, category)
    else:
        # Fallback to default configuration
        from .config import EMBEDDING_WEIGHTS
        
        if category:
            category_lower = category.lower()
            
            # Find matching category in config
            weights = None
            for cat_key, cat_weights in EMBEDDING_WEIGHTS.items():
                if cat_key in category_lower or any(word in category_lower for word in cat_key.split()):
                    weights = cat_weights
                    break
            
            if weights is None:
                # Use default weights if no specific category found
                weights = EMBEDDING_WEIGHTS["default"]
        else:
            # Use default weights if no category provided
            weights = EMBEDDING_WEIGHTS["default"]
    
    image_weight = weights["image_weight"]
    text_weight = weights["text_weight"]
    
    # Convert to numpy arrays for easier manipulation
    text_array = np.array(text_emb)
    image_array = np.array(image_emb)
    
    # Ensure same dimensions (pad if necessary)
    max_dim = max(len(text_array), len(image_array))
    if len(text_array) < max_dim:
        text_array = np.pad(text_array, (0, max_dim - len(text_array)), 'constant')
    if len(image_array) < max_dim:
        image_array = np.pad(image_array, (0, max_dim - len(image_array)), 'constant')
    
    # Combine with weights
    combined = image_weight * image_array + text_weight * text_array
    
    # Normalize
    combined = combined / np.linalg.norm(combined)
    
    logger.info(f"Combined embeddings: image_weight={image_weight}, text_weight={text_weight}")
    return combined.tolist()

# Fase 1: Model optimalisatie - Gebruik small model voor efficiency
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536d voor snelle queries
EMBEDDING_MODEL_SMALL = "text-embedding-3-small"  # 1536d voor snelle queries

def get_embedding_model(use_case: str = "product") -> str:
    """
    Selecteer het beste embedding model voor de use case.
    
    Args:
        use_case: "product" voor product embeddings, "query" voor zoektermen
    
    Returns:
        Model naam voor OpenAI API
    """
    # Gebruik small model voor efficiency en consistentie
    if use_case == "product":
        return EMBEDDING_MODEL  # 1536d voor snelle product embeddings
    else:
        return EMBEDDING_MODEL  # 1536d voor snelle query embeddings

def clean_description(html_text: str) -> str:
    """Verwijder HTML-tags uit de beschrijving."""
    return re.sub(r"<[^>]+>", "", html_text or "").strip()

def build_embedding_text(
    title: str,
    description: str = None,
    vendor: str = None,
    product_type: str = None,
    seo_title: str = None,
    seo_description: str = None,
    product_attributes: dict = None,
    stock_status: str = None,
    sku: str = None,
    barcode: str = None,
    status: str = None,
    tags: list = None,
    price: float = None,
    category: str = None,
    subcategory: str = None,
    doelgroep: str = None,
    stijl: str = None,
    gebruik: str = None,
    seizoen: str = None,
    merk: str = None,
    extra: str = None
) -> str:
    """
    Build comprehensive embedding text from all product attributes.
    
    Args:
        title: Product title
        description: Product description
        vendor: Product vendor/brand
        product_type: Product type/category
        seo_title: SEO optimized title
        seo_description: SEO optimized description
        product_attributes: Rich product attributes (sizes, colors, materials, etc.)
        stock_status: Stock status
        sku: Stock keeping unit
        barcode: Product barcode
        status: Product status
        tags: Product tags
        price: Product price
        category: Product category
        subcategory: Product subcategory
        doelgroep: Target audience
        stijl: Style
        gebruik: Usage
        seizoen: Season
        merk: Brand
        extra: Extra information
        
    Returns:
        Combined text for embedding generation
    """
    text_parts = []
    
    # Core product information
    if title:
        text_parts.append(f"Titel: {title}")
    
    if description:
        # Clean HTML from description
        clean_desc = clean_description(description)
        text_parts.append(f"Beschrijving: {clean_desc}")
    
    if vendor:
        text_parts.append(f"Merk: {vendor}")
    
    if product_type:
        text_parts.append(f"Type: {product_type}")
    
    # SEO information
    if seo_title and seo_title != title:
        text_parts.append(f"SEO titel: {seo_title}")
    
    if seo_description and seo_description != description:
        clean_seo_desc = clean_description(seo_description)
        text_parts.append(f"SEO beschrijving: {clean_seo_desc}")
    
    # Rich product attributes
    if product_attributes:
        if isinstance(product_attributes, dict):
            # Sizes
            if 'sizes' in product_attributes and product_attributes['sizes']:
                sizes = ', '.join(product_attributes['sizes'])
                text_parts.append(f"Maten: {sizes}")
            
            # Colors
            if 'colors' in product_attributes and product_attributes['colors']:
                colors = ', '.join(product_attributes['colors'])
                text_parts.append(f"Kleuren: {colors}")
            
            # Materials
            if 'materials' in product_attributes and product_attributes['materials']:
                materials = ', '.join(product_attributes['materials'])
                text_parts.append(f"Materialen: {materials}")
            
            # Weight
            if 'weight' in product_attributes and product_attributes['weight']:
                text_parts.append(f"Gewicht: {product_attributes['weight']}")
            
            # Dimensions
            if 'dimensions' in product_attributes and product_attributes['dimensions']:
                dims = product_attributes['dimensions']
                if isinstance(dims, dict):
                    dim_text = []
                    if 'height' in dims:
                        dim_text.append(f"hoogte {dims['height']}")
                    if 'width' in dims:
                        dim_text.append(f"breedte {dims['width']}")
                    if 'depth' in dims:
                        dim_text.append(f"diepte {dims['depth']}")
                    if dim_text:
                        text_parts.append(f"Afmetingen: {', '.join(dim_text)}")
            
            # Age group
            if 'age_group' in product_attributes and product_attributes['age_group']:
                text_parts.append(f"Doelgroep: {product_attributes['age_group']}")
            
            # Gender
            if 'gender' in product_attributes and product_attributes['gender']:
                text_parts.append(f"Geslacht: {product_attributes['gender']}")
            
            # Season
            if 'season' in product_attributes and product_attributes['season']:
                text_parts.append(f"Seizoen: {product_attributes['season']}")
            
            # Occasion
            if 'occasion' in product_attributes and product_attributes['occasion']:
                text_parts.append(f"Gelegenheid: {product_attributes['occasion']}")
    
    # Stock and status information
    if stock_status:
        text_parts.append(f"Voorraad: {stock_status}")
    
    if status:
        text_parts.append(f"Status: {status}")
    
    # Legacy fields (for backward compatibility)
    if category:
        text_parts.append(f"Categorie: {category}")
    
    if subcategory:
        text_parts.append(f"Subcategorie: {subcategory}")
    
    if doelgroep:
        text_parts.append(f"Doelgroep: {doelgroep}")
    
    if stijl:
        text_parts.append(f"Stijl: {stijl}")
    
    if gebruik:
        text_parts.append(f"Gebruik: {gebruik}")
    
    if seizoen:
        text_parts.append(f"Seizoen: {seizoen}")
    
    if merk:
        text_parts.append(f"Merk: {merk}")
    
    if extra:
        text_parts.append(f"Extra: {extra}")
    
    # Tags
    if tags:
        if isinstance(tags, list):
            tags_text = ', '.join(tags)
            text_parts.append(f"Tags: {tags_text}")
        elif isinstance(tags, str):
            text_parts.append(f"Tags: {tags}")
    
    # Price
    if price:
        text_parts.append(f"Prijs: €{price:.2f}")
    
    # Combine all parts
    combined_text = " | ".join(text_parts)
    
    # Limit length to prevent token overflow
    if len(combined_text) > 4000:
        combined_text = combined_text[:4000] + "..."
    
    return combined_text

def create_embedding_hash(text: str) -> str:
    """Creëer een hash voor caching van embeddings."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

@lru_cache(maxsize=1000)
def generate_embedding_cached(text: str, model: str = None) -> List[float]:
    """
    Genereer embedding met caching voor identieke teksten.
    
    Args:
        text: Tekst om te embedden
        model: OpenAI model naam (optioneel)
    
    Returns:
        Embedding vector
    """
    if not model:
        model = get_embedding_model("query")
    
    try:
        response = openai.embeddings.create(
            model=model,
            input=text
        )
        logger.info(f"Generated embedding for text (length: {len(text)}) with model {model}")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

def generate_embedding(
    title: str = None,
    description: str = None,
    vendor: str = None,
    product_type: str = None,
    seo_title: str = None,
    seo_description: str = None,
    product_attributes: dict = None,
    stock_status: str = None,
    sku: str = None,
    barcode: str = None,
    status: str = None,
    tags: list = None,
    price: float = None,
    category: str = None,
    subcategory: str = None,
    doelgroep: str = None,
    stijl: str = None,
    gebruik: str = None,
    seizoen: str = None,
    merk: str = None,
    extra: str = None,
    use_case: str = "product",
    image_url: Optional[str] = None,
    store_id: str = None
):
    """
    Generate comprehensive embeddings for products with all attributes.
    
    Args:
        title: Product title
        description: Product description
        vendor: Product vendor/brand
        product_type: Product type/category
        seo_title: SEO optimized title
        seo_description: SEO optimized description
        product_attributes: Rich product attributes (sizes, colors, materials, etc.)
        stock_status: Stock status
        sku: Stock keeping unit
        barcode: Product barcode
        status: Product status
        tags: Product tags
        price: Product price
        category: Product category
        subcategory: Product subcategory
        doelgroep: Target audience
        stijl: Style
        gebruik: Usage
        seizoen: Season
        merk: Brand
        extra: Extra information
        use_case: Use case for embedding
        image_url: Image URL for visual embedding
        store_id: Store identifier
        
    Returns:
        Dict containing text_embedding, image_embedding, and combined_embedding
    """
    try:
        # Build comprehensive text for embedding
        embedding_text = build_embedding_text(
            title=title,
            description=description,
            vendor=vendor,
            product_type=product_type,
            seo_title=seo_title,
            seo_description=seo_description,
            product_attributes=product_attributes,
            stock_status=stock_status,
            sku=sku,
            barcode=barcode,
            status=status,
            tags=tags,
            price=price,
            category=category,
            subcategory=subcategory,
            doelgroep=doelgroep,
            stijl=stijl,
            gebruik=gebruik,
            seizoen=seizoen,
            merk=merk,
            extra=extra
        )
        
        # Generate text embedding
        text_embedding = generate_embedding_cached(embedding_text, get_embedding_model(use_case))
        
        # Generate image embedding if URL provided
        image_embedding = None
        if image_url:
            try:
                image_embedding = generate_image_embedding(image_url)
                logger.info(f"Generated image embedding for {image_url}")
            except Exception as e:
                logger.warning(f"Failed to generate image embedding for {image_url}: {e}")
        
        # Generate combined embedding
        combined_embedding = None
        if text_embedding and image_embedding:
            try:
                combined_embedding = combine_embeddings(
                    text_embedding, 
                    image_embedding, 
                    category=category, 
                    store_id=store_id
                )
                logger.info("Generated combined text+image embedding")
            except Exception as e:
                logger.warning(f"Failed to generate combined embedding: {e}")
                combined_embedding = text_embedding  # Fallback to text only
        
        return {
            "text_embedding": text_embedding,
            "image_embedding": image_embedding,
            "combined_embedding": combined_embedding or text_embedding
        }
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

def generate_batch_embeddings(texts: List[str], model: str = None) -> List[List[float]]:
    """
    Genereer embeddings voor meerdere teksten in batch.
    
    Args:
        texts: Lijst van teksten om te embedden
        model: OpenAI model naam (optioneel)
    
    Returns:
        Lijst van embedding vectors
    """
    if not model:
        model = get_embedding_model("product")
    
    if not texts:
        return []
    
    try:
        # OpenAI ondersteunt batch processing
        response = openai.embeddings.create(
            model=model,
            input=texts
        )
        
        embeddings = [data.embedding for data in response.data]
        logger.info(f"Generated {len(embeddings)} embeddings in batch with model {model}")
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        # Fallback naar individuele embeddings
        logger.info("Falling back to individual embedding generation")
        return [generate_embedding_cached(text, model) for text in texts]

def generate_batch_image_embeddings(image_urls: List[str], batch_size: int = None) -> List[List[float]]:
    """
    Genereer image embeddings voor meerdere afbeeldingen in batch.
    
    Args:
        image_urls: Lijst van image URLs om te embedden
        batch_size: Aantal afbeeldingen per batch (default: 10)
    
    Returns:
        Lijst van image embedding vectors
    """
    from .config import IMAGE_EMBEDDING_BATCH_SIZE
    
    if batch_size is None:
        batch_size = IMAGE_EMBEDDING_BATCH_SIZE
    
    if not image_urls:
        return []
    
    all_embeddings = []
    total_batches = (len(image_urls) + batch_size - 1) // batch_size
    
    logger.info(f"[BATCH] Processing {len(image_urls)} images in {total_batches} batches")
    
    try:
        # Get model once for all batches
        model, preprocess = get_clip_model()
        
        for i in range(0, len(image_urls), batch_size):
            batch_urls = image_urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"[BATCH] Processing image batch {batch_num}/{total_batches} ({len(batch_urls)} images)")
            
            batch_embeddings = []
            batch_images = []
            
            # Load all images in batch
            for url in batch_urls:
                try:
                    image = load_image_from_url_or_path(url)
                    batch_images.append(image)
                except Exception as e:
                    logger.warning(f"Failed to load image {url}: {e}")
                    batch_images.append(None)
            
            # Process valid images
            valid_images = [img for img in batch_images if img is not None]
            if valid_images:
                try:
                    # Preprocess all images
                    image_tensors = torch.stack([preprocess(img) for img in valid_images])
                    
                    # Generate embeddings
                    with torch.no_grad():
                        image_features = model.encode_image(image_tensors)
                        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    # Convert to list format
                    batch_embeddings = [features.cpu().numpy().tolist() for features in image_features]
                    
                    logger.info(f"[BATCH] Generated {len(batch_embeddings)} image embeddings in batch {batch_num}")
                    
                except Exception as e:
                    logger.error(f"Error in batch {batch_num}: {e}")
                    batch_embeddings = []
            
            # Handle None images (failed loads)
            final_batch_embeddings = []
            embedding_idx = 0
            for img in batch_images:
                if img is not None and embedding_idx < len(batch_embeddings):
                    final_batch_embeddings.append(batch_embeddings[embedding_idx])
                    embedding_idx += 1
                else:
                    final_batch_embeddings.append(None)
            
            all_embeddings.extend(final_batch_embeddings)
        
        successful_count = sum(1 for emb in all_embeddings if emb is not None)
        logger.info(f"[BATCH] Completed image batch processing: {successful_count}/{len(image_urls)} successful")
        
        return all_embeddings
        
    except Exception as e:
        logger.error(f"Error in batch image embedding generation: {e}")
        # Fallback naar individuele embeddings
        logger.info("Falling back to individual image embedding generation")
        return [generate_image_embedding(url) if url else None for url in image_urls]

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Bereken cosine similarity tussen twee embeddings.
    
    Args:
        embedding1: Eerste embedding vector
        embedding2: Tweede embedding vector
    
    Returns:
        Similarity score tussen 0 en 1
    """
    import numpy as np
    
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)