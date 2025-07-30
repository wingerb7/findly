import openai
from config import OPENAI_API_KEY
import re

openai.api_key = OPENAI_API_KEY

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
    extra: str = None
):
    """
    Genereer een embedding:
    - Alleen `title` voor zoektermen.
    - Volledig verrijkt met context voor productdata.
    """
    if description is None and not any([tags, price, category, subcategory, doelgroep, stijl, gebruik, seizoen, merk, extra]):
        enriched_text = title or ""  # Zoekterm
    else:
        enriched_text = build_embedding_text(
            title, description, tags, price, category, subcategory,
            doelgroep, stijl, gebruik, seizoen, merk, extra
        )
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=enriched_text
    )
    return response.data[0].embedding