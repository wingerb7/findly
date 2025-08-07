# Image Embeddings voor Findly

Deze documentatie beschrijft de implementatie van OpenCLIP Image Embeddings in Findly voor verbeterde zoekresultaten door het combineren van tekst- en afbeeldings-embeddings.

## 🚀 Overzicht

Findly ondersteunt nu **multimodale embeddings** door het combineren van:
- **Tekst embeddings** (OpenAI text-embedding-3-small)
- **Image embeddings** (OpenCLIP ViT-B/32)

Dit resulteert in betere zoekresultaten, vooral voor visuele producten zoals kleding, interieur en sieraden.

## 📋 Vereisten

### Dependencies
De volgende packages zijn toegevoegd aan `requirements.txt`:
```
open-clip-torch>=2.20.0
torch>=2.0.0
torchvision>=0.15.0
Pillow>=10.0.0
numpy>=1.24.0
```

### Installatie
```bash
pip install -r requirements.txt
```

## 🏗️ Architectuur

### 1. OpenCLIP Model
- **Model**: ViT-B/32 (Vision Transformer)
- **Pretrained**: OpenAI weights
- **Output**: 512-dimensionale embeddings
- **Caching**: Model wordt gecached voor efficiency

### 2. Embedding Combinatie
Dynamische weging op basis van productcategorie:

| Categorie | Image Weight | Text Weight | Beschrijving |
|-----------|--------------|-------------|--------------|
| Fashion & Interieur | 0.75 | 0.25 | Visuele producten |
| Sieraden & Tech | 0.55 | 0.45 | Gemengde focus |
| Algemeen | 0.60 | 0.40 | Standaard weging |

### 3. Database Schema
Nieuwe kolom toegevoegd aan `products` tabel:
```sql
image_embedding JSONB  -- Image embedding voor visuele zoekopdrachten
```

## 🔧 Gebruik

### 1. Basis Image Embedding
```python
from core.embeddings import generate_image_embedding

# Genereer image embedding
image_url = "https://example.com/product-image.jpg"
embedding = generate_image_embedding(image_url)
```

### 2. Gecombineerde Embeddings
```python
from core.embeddings import generate_embedding

# Genereer gecombineerde embedding
embedding = generate_embedding(
    title="Rode T-shirt",
    description="Comfortabele katoenen t-shirt",
    category="fashion",
    price=29.99,
    image_url="https://example.com/tshirt.jpg"
)
```

### 3. Handmatige Combinatie
```python
from core.embeddings import combine_embeddings

# Combineer text en image embeddings
combined = combine_embeddings(
    text_emb=text_embedding,
    image_emb=image_embedding,
    category="fashion"
)
```

## 🛠️ CLI Tools

### Image Embedding Generator
Bulk verwerking van producten voor image embeddings:

```bash
python3 generate_image_embeddings.py --store_id=your_store_id
```

**Opties:**
- `--store_id`: Store ID om te verwerken (verplicht)
- `--batch_size`: Aantal producten per batch (default: 50)
- `--verbose`: Uitgebreide logging

**Voorbeeld output:**
```
🚀 Starting image embedding generation for store: demo_store
📊 Total products to process: 200

[BATCH] Processing batch 1/4 (50 products)
📈 Progress: 0/200 products processed
✅ Successfully generated image embedding for product 123
📊 Progress: 25.0% complete

🎉 Image embedding generation completed!
📊 Final Statistics:
   Total products: 200
   Processed: 200
   Successful: 195
   Failed: 5
   Skipped: 0
   Duration: 45.23 seconds
```

### Test Script
Test de image embedding functionaliteit:

```bash
python3 test_image_embeddings.py
```

**Tests:**
- OpenCLIP model loading
- Image embedding generation
- Embedding combinatie
- Volledige pipeline
- Embedding normalisatie

## 📊 Logging

Verbeterde logging met duidelijke blokken:

```
[TEXT] Generated text-only embedding (length: 1536)
[IMAGE] Generating image embedding for: https://example.com/image.jpg
[COMBINED] Combining text and image embeddings
[COMBINED] Successfully generated combined embedding (length: 1536)
```

## 🔄 Database Migratie

### Automatische Migratie
```bash
cd ai_shopify_search
alembic upgrade head
```

### Handmatige Migratie
Als er problemen zijn met Alembic:

```sql
-- Voeg image_embedding kolom toe
ALTER TABLE products ADD COLUMN image_embedding JSONB;
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/test_image_embeddings.py
```

### Integration Tests
```bash
pytest tests/integration/test_image_embeddings_integration.py
```

### Performance Tests
```bash
python3 test_image_embeddings.py
```

## 📈 Performance

### Benchmarks
- **Image embedding generatie**: ~2-3 seconden per afbeelding
- **Batch processing**: 50 producten per batch
- **Retry logic**: Max 3 pogingen bij falen
- **Memory usage**: ~2GB voor OpenCLIP model

### Optimalisaties
- Model caching met `@lru_cache`
- Batch processing voor efficiency
- Exponential backoff voor retries
- Progress tracking voor lange runs

## 🚨 Troubleshooting

### Veelvoorkomende Problemen

1. **OpenCLIP model laadt niet**
   ```bash
   # Controleer PyTorch installatie
   python -c "import torch; print(torch.__version__)"
   
   # Reïnstalleer dependencies
   pip install --force-reinstall open-clip-torch torch torchvision
   ```

2. **Image URL niet bereikbaar**
   ```python
   # Gebruik timeout en error handling
   embedding = generate_image_embedding(image_url)  # Automatische retry
   ```

3. **Memory issues**
   ```bash
   # Verklein batch size
   python3 generate_image_embeddings.py --store_id=store --batch_size=25
   ```

### Debug Mode
```bash
python3 generate_image_embeddings.py --store_id=store --verbose
```

## 🔮 Toekomstige Verbeteringen

1. **Vector Database**: Migratie naar pgvector voor snellere similarity search
2. **Batch Image Processing**: Parallel processing van meerdere afbeeldingen
3. **Custom Models**: Fine-tuning van OpenCLIP voor specifieke productcategorieën
4. **Image Preprocessing**: Automatische image optimalisatie
5. **Caching**: Redis caching voor image embeddings

## 📝 Changelog

### v1.0.0 (Huidige)
- ✅ OpenCLIP ViT-B/32 integratie
- ✅ Dynamische embedding combinatie
- ✅ CLI tool voor bulk verwerking
- ✅ Database migratie
- ✅ Uitgebreide logging
- ✅ Retry logic en error handling
- ✅ Test suite

## 🤝 Bijdragen

Voor vragen of problemen:
1. Check de troubleshooting sectie
2. Run de test suite
3. Controleer de logs
4. Open een issue met gedetailleerde informatie

---

**Let op**: Deze functionaliteit vereist voldoende RAM (minimaal 4GB) voor het OpenCLIP model. 