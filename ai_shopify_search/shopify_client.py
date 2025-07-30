import random
from faker import Faker
from config import SHOPIFY_STORE_URL, SHOPIFY_API_KEY, SHOPIFY_API_SECRET

fake = Faker('nl_NL')

# Product configuratie
categories = {
    "Shirts": ["XS", "S", "M", "L", "XL"],
    "Broeken": ["XS", "S", "M", "L", "XL"], 
    "Jassen": ["S", "M", "L", "XL"],
    "Schoenen": ["36", "37", "38", "39", "40", "41", "42", "43", "44"],
    "Truien": ["S", "M", "L", "XL"],
    "Jurken": ["XS", "S", "M", "L", "XL"],
    "Rokken": ["XS", "S", "M", "L", "XL"],
    "Tassen": ["One Size"],
    "Accessoires": ["One Size"]
}

colors = ["Zwart", "Wit", "Blauw", "Groen", "Geel", "Rood", "Paars", "Grijs", "Beige", "Bruin", "Roze", "Oranje"]
materials = ["Katoen", "Wol", "Linnen", "Leer", "Polyester", "Denim", "Synthetisch", "Kashmir", "Zijde"]
brands = ["StyleHub", "UrbanWear", "Fashionista", "Trendify", "ClassicLine", "ModernFit", "Elegance", "SportFlex"]

def random_discount(price):
    """Genereer random korting tussen 0 en 30%."""
    if random.random() < 0.3:  # 30% kans op korting
        discount = round(price * random.uniform(0.1, 0.3), 2)
        return price - discount
    return price

def get_products(limit: int = 1000):
    """Genereer mock producten voor testing."""
    products = []
    
    for i in range(min(limit, 1000)):
        category = random.choice(list(categories.keys()))
        size = random.choice(categories[category])
        color = random.choice(colors)
        material = random.choice(materials)
        brand = random.choice(brands)
        
        # Genereer realistische prijzen per categorie
        if category == "Schoenen":
            base_price = random.uniform(50, 200)
        elif category in ["Jassen", "Tassen"]:
            base_price = random.uniform(80, 300)
        elif category == "Accessoires":
            base_price = random.uniform(15, 80)
        else:
            base_price = random.uniform(25, 150)
        
        price = round(random_discount(base_price), 2)
        
        # Genereer titel en beschrijving
        title = f"{color} {material} {category} {brand}"
        description = f"<p>Stijlvolle {category.lower()} van {brand}. Gemaakt van hoogwaardig {material.lower()} in de kleur {color.lower()}. Perfect voor dagelijks gebruik.</p>"
        
        # Genereer tags
        tags = [category, color, material, brand, size]
        if random.random() < 0.5:
            tags.append("nieuw")
        if random.random() < 0.3:
            tags.append("sale")
        if category in ["Shirts", "Broeken", "Schoenen"]:
            tags.append("casual")
        if category in ["Jassen", "Tassen"]:
            tags.append("elegant")
        
        product = {
            "shopify_id": f"gid://shopify/Product/{i+1}",
            "title": title,
            "description": description,
            "tags": tags,
            "price": price
        }
        
        products.append(product)
    
    return products