import openai
from .config import OPENAI_API_KEY
import re
import hashlib
import json
from typing import List, Dict, Optional, Union
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = OPENAI_API_KEY

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
    description: str,
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
    """Bouw een verrijkte embeddingtekst met alle context."""
    desc_clean = clean_description(description)
    tags_text = ", ".join(tags) if tags else "Geen"

    # Prijscategorie
    if price is not None:
        if price < 50:
            prijs_cat = "goedkoop"
        elif price < 200:
            prijs_cat = "gemiddeld geprijsd"
        else:
            prijs_cat = "duur"
    else:
        prijs_cat = "onbekend"

    return (
        f"Product: {title}. "
        f"Beschrijving: {desc_clean}. "
        f"Tags: {tags_text}. "
        f"Categorie: {category or 'Onbekend'}. "
        f"Subcategorie: {subcategory or 'Onbekend'}. "
        f"Prijs: {price if price is not None else 'Onbekend'} euro ({prijs_cat}). "
        f"Doelgroep: {doelgroep or 'Algemeen'}. "
        f"Stijl: {stijl or 'Algemeen'}. "
        f"Gebruik: {gebruik or 'Algemeen'}. "
        f"Seizoen/gelegenheid: {seizoen or 'Algemeen'}. "
        f"Merk: {merk or 'Onbekend'}. "
        f"Extra kenmerken: {extra or 'Geen'}."
    )

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
    use_case: str = "product"
):
    """
    Genereer een embedding met Fase 1 optimalisaties:
    - Model selectie op basis van use case
    - Caching voor identieke teksten
    - Betere error handling
    
    Args:
        use_case: "product" voor product embeddings, "query" voor zoektermen
    """
    if description is None and not any([tags, price, category, subcategory, doelgroep, stijl, gebruik, seizoen, merk, extra]):
        enriched_text = title or ""  # Zoekterm
        use_case = "query"
    else:
        enriched_text = build_embedding_text(
            title, description, tags, price, category, subcategory,
            doelgroep, stijl, gebruik, seizoen, merk, extra
        )
    
    model = get_embedding_model(use_case)
    return generate_embedding_cached(enriched_text, model)

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