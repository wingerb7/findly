# AI Shopify Search

Dit project is een backend-service voor het importeren, opslaan en semantisch doorzoeken van Shopify-producten met behulp van AI-embeddings (OpenAI + pgvector) en FastAPI.

## Database structuur

- **Store**: Slaat informatie op over een Shopify-winkel (domein, access token, installatiedatum).
- **Product**: Slaat producten op die bij een winkel horen, inclusief titel, beschrijving, prijs, tags en een AI-embedding vector voor semantisch zoeken.
- Relatie: Eén winkel kan meerdere producten hebben. Producten zijn gekoppeld aan een winkel via `store_id`.

## Belangrijkste technologieën
- **FastAPI**: Voor de API.
- **SQLAlchemy**: ORM voor database interactie.
- **PostgreSQL + pgvector**: Database met vector search support.
- **OpenAI**: Voor het genereren van embeddings.
- **Shopify API**: Voor het importeren van producten.

## Installatie & Setup

1. **Clone de repository**
2. **Installeer dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Zorg voor een PostgreSQL database met pgvector-extensie**
   - Installeer pgvector: `brew install pgvector`
   - Maak de extensie aan in je database:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
4. **Vul een `.env` bestand in de project-root met:**
   ```env
   DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/<dbname>
   SHOPIFY_API_KEY=...
   SHOPIFY_ACCESS_TOKEN=...
   SHOPIFY_STORE=...
   OPENAI_API_KEY=...
   ```
5. **Start de API**
   ```bash
   uvicorn ai_shopify_search.main:app --reload
   ```
6. **Gebruik de Swagger UI**
   - Ga naar [http://localhost:8000/docs](http://localhost:8000/docs) om de API te testen.

## Functionaliteit
- **/api/import-products**: Importeert producten uit Shopify, genereert embeddings en slaat ze op.
- **Database**: Slaat winkels en producten op, inclusief vector-embeddings voor AI-zoekopdrachten.

## Uitbreiden
- Voeg endpoints toe voor zoeken op basis van AI-embeddings.
- Koppel een frontend voor gebruikersinterface.

---
*Deze backend is ideaal als basis voor een slimme, AI-gedreven zoekfunctie in je eigen Shopify-app of -plugin.*