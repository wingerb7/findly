import csv
import random
from faker import Faker

fake = Faker('nl_NL')

# Basis instellingen
PRODUCT_COUNT = 1000
OUTPUT_FILE = "fashion_catalog_generated.csv"

categories = {
    "Shirts": ["XS", "S", "M", "L", "XL"],
    "Broeken": ["XS", "S", "M", "L", "XL"],
    "Jassen": ["S", "M", "L", "XL"],
    "Schoenen": ["36", "37", "38", "39", "40", "41", "42", "43", "44"],
    "Truien": ["S", "M", "L", "XL"]
}
colors = ["Zwart", "Wit", "Blauw", "Groen", "Geel", "Rood", "Paars", "Grijs", "Beige"]
materials = ["Katoen", "Wol", "Linnen", "Leer", "Polyester"]
brands = ["StyleHub", "UrbanWear", "Fashionista", "Trendify", "ClassicLine"]

def random_discount(price):
    """Genereer random korting tussen 0 en 30%."""
    if random.random() < 0.3:  # 30% kans op korting
        discount = round(price * random.uniform(0.1, 0.3), 2)
        return price - discount, discount
    return price, 0

# Shopify-headers
headers = [
    "Handle","Title","Body (HTML)","Vendor","Product Category","Type","Tags",
    "Published","Option1 Name","Option1 Value","Option2 Name","Option2 Value",
    "Variant SKU","Variant Price","Variant Compare At Price","Variant Inventory Qty",
    "Variant Taxable","Image Src","SEO Title","SEO Description"
]

rows = []
for i in range(PRODUCT_COUNT):
    category = random.choice(list(categories.keys()))
    size = random.choice(categories[category])
    color = random.choice(colors)
    material = random.choice(materials)
    brand = random.choice(brands)
    price = round(random.uniform(20, 250), 2)
    discounted_price, discount_amount = random_discount(price)

    title = f"{category} {brand} ({color}, {size})"
    handle = f"{category.lower()}-{brand.lower()}-{i}"
    description = f"<p>{fake.sentence(nb_words=12)} Gemaakt van {material.lower()} in de kleur {color.lower()}.</p>"
    tags = f"{category},{color},{material},{brand}"
    sku = f"{category[:3].upper()}-{i:04d}-{size}"
    image_src = f"https://placehold.co/600x400?text={category}+{color}"
    seo_title = f"{title} kopen | {brand}"
    seo_description = f"Bestel nu {title} van {brand}. Hoogwaardige kwaliteit, snel geleverd."

    rows.append([
        handle, title, description, brand, "Apparel & Accessories", category, tags,
        "TRUE", "Kleur", color, "Maat", size, sku, discounted_price,
        price if discount_amount > 0 else "", random.randint(0, 200),
        "TRUE", image_src, seo_title, seo_description
    ])

# CSV schrijven
with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"✔ {PRODUCT_COUNT} producten gegenereerd in {OUTPUT_FILE}")