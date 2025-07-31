# 🔍 Search Quality Benchmark Tool

Een geavanceerd Python-script voor het automatisch testen van search kwaliteit met GPT-powered scoring.

## 🎯 Doel

Dit script wordt gebruikt als kwaliteitsmeter: bij elke wijziging in de search-logica kunnen we direct zien of het beter of slechter scoort.

## 🚀 Features

- **📊 Automatische Query Testing**: Test honderden queries in één run
- **🤖 GPT-Powered Scoring**: AI-gebaseerde relevantie scoring (0-1)
- **📈 Uitgebreide Metrics**: Response time, price filters, fallbacks
- **📝 Gedetailleerde Logging**: Complete audit trail
- **💾 CSV Export**: Resultaten in gestructureerd formaat
- **🎛️ Flexibele Configuratie**: Headless mode, custom endpoints

## 📋 Vereisten

```bash
pip install aiohttp openai
```

Zorg dat je OpenAI API key beschikbaar is via:
- Environment variable: `OPENAI_API_KEY`
- Of in `ai_shopify_search/config.py`

## 🏃‍♂️ Gebruik

### Basis Gebruik
```bash
python benchmark_search.py
```

### Headless Mode (alleen CSV output)
```bash
python benchmark_search.py --headless
```

### Custom Endpoint
```bash
python benchmark_search.py --endpoint /api/search
```

### Custom Bestanden
```bash
python benchmark_search.py --queries my_queries.csv --results my_results.csv
```

## 📁 Bestandsstructuur

```
├── benchmark_search.py          # Hoofdscript
├── benchmark_queries.csv        # Test queries (input)
├── benchmark_results.csv        # Resultaten (output)
├── benchmark.log               # Logging output
└── BENCHMARK_README.md         # Deze documentatie
```

## 📊 Input Format (benchmark_queries.csv)

```csv
query
goedkope schoenen
duur exclusief jas
zwarte leder schoenen voor heren
betaalbare shirt voor een tiener
...
```

## 📈 Output Format (benchmark_results.csv)

```csv
query,score,avg_price_top5,titles_top5,response_time,result_count,price_filter_applied,fallback_used,gpt_reasoning
"goedkope schoenen",0.850,75.50,"Schoen A | Schoen B | Schoen C",0.245,25,true,false,"De resultaten matchen goed..."
"duur exclusief jas",0.720,250.00,"Jas X | Jas Y | Jas Z",0.198,15,true,false,"Resultaten zijn exclusief..."
```

## 🎯 Console Output

```
============================================================
📊 BENCHMARK SUMMARY
============================================================
Total queries tested: 150
Average relevance score: 0.784
Average response time: 0.234s
Price filter applied: 45/150
Fallback used: 12/150

🔴 TOP 5 WORST PERFORMING QUERIES:
1. 'vage query' - Score: 0.234
   Reasoning: De resultaten matchen niet goed met de intentie...
2. 'onduidelijke zoekterm' - Score: 0.345
   Reasoning: Producten zijn niet relevant voor de query...
...
============================================================
```

## 🔧 Configuratie

### Command Line Arguments

| Argument | Default | Beschrijving |
|----------|---------|--------------|
| `--headless` | False | Geen console output |
| `--endpoint` | `/api/ai-search` | API endpoint om te testen |
| `--queries` | `benchmark_queries.csv` | Input CSV bestand |
| `--results` | `benchmark_results.csv` | Output CSV bestand |
| `--base-url` | `http://localhost:8000` | Base URL voor API |

### Environment Variables

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 🤖 GPT Scoring

Het script gebruikt GPT-4o-mini om search resultaten te scoren:

### Prompt Template
```
Je bent een expert in e-commerce search kwaliteit. Beoordeel hoe goed de zoekresultaten matchen met de intentie van de gebruiker.

QUERY: "goedkope schoenen"

TOP 5 RESULTATEN:
1. Bruin Leer Schoenen (€89.74, similarity: 0.394)
2. Rood Wol Schoenen (€60.44, similarity: 0.394)
...

BEOORDELING:
- Score van 0.0 tot 1.0 (1.0 = perfecte match)
- Overweeg: relevantie, prijs, product type, kwaliteit van resultaten
- Geef een korte uitleg van je score

Antwoord in JSON formaat:
{
    "score": 0.85,
    "reasoning": "De resultaten matchen goed met de query..."
}
```

### Scoring Criteria
- **0.0-0.3**: Slechte match, irrelevante resultaten
- **0.3-0.6**: Matige match, enkele relevante items
- **0.6-0.8**: Goede match, meeste resultaten relevant
- **0.8-1.0**: Uitstekende match, perfecte relevantie

## 📊 Metrics

### Per Query
- **Score**: GPT relevance score (0-1)
- **Response Time**: API response tijd in seconden
- **Result Count**: Aantal gevonden resultaten
- **Price Filter Applied**: Of price intent is toegepast
- **Fallback Used**: Of fallback search is gebruikt
- **Avg Price Top 5**: Gemiddelde prijs van top 5 resultaten

### Aggregated
- **Average Score**: Gemiddelde relevantie score
- **Average Response Time**: Gemiddelde response tijd
- **Price Filter Usage**: Percentage queries met price filter
- **Fallback Usage**: Percentage queries met fallback
- **Worst Queries**: Top 5 slechtst presterende queries

## 🔄 Workflow

1. **Setup**: Zorg dat de FastAPI server draait
2. **Prepare**: Maak `benchmark_queries.csv` met test queries
3. **Run**: Voer `python benchmark_search.py` uit
4. **Analyze**: Bekijk `benchmark_results.csv` en console output
5. **Compare**: Vergelijk resultaten met vorige runs

## 🎯 Use Cases

### Development
```bash
# Test voor wijziging
python benchmark_search.py --results before_results.csv

# Maak wijziging aan search logic

# Test na wijziging
python benchmark_search.py --results after_results.csv

# Vergelijk resultaten
diff before_results.csv after_results.csv
```

### CI/CD
```bash
# Headless mode voor automation
python benchmark_search.py --headless --results ci_results.csv

# Check of score boven threshold is
python -c "
import pandas as pd
df = pd.read_csv('ci_results.csv')
avg_score = df['score'].mean()
print(f'Average score: {avg_score:.3f}')
assert avg_score > 0.7, 'Search quality below threshold'
"
```

### A/B Testing
```bash
# Test endpoint A
python benchmark_search.py --endpoint /api/search-a --results results_a.csv

# Test endpoint B
python benchmark_search.py --endpoint /api/search-b --results results_b.csv

# Vergelijk performance
python compare_results.py results_a.csv results_b.csv
```

## 🐛 Troubleshooting

### Common Issues

**OpenAI API Error**
```
❌ Failed to initialize OpenAI client: OPENAI_API_KEY not found
```
**Oplossing**: Zet `OPENAI_API_KEY` environment variable of voeg toe aan config.py

**Connection Error**
```
❌ Search failed for query 'test': HTTP 500
```
**Oplossing**: Controleer of FastAPI server draait op localhost:8000

**CSV Error**
```
❌ Query file not found: benchmark_queries.csv
```
**Oplossing**: Maak benchmark_queries.csv aan met 'query' kolom

### Debug Mode
```bash
# Verhoog logging level
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import benchmark_search
"
```

## 📈 Performance Tips

1. **Batch Processing**: Script heeft built-in delays om API niet te overbelasten
2. **Caching**: Resultaten worden gecached in Redis (indien beschikbaar)
3. **Parallel Processing**: Queries worden sequentieel uitgevoerd voor stabiliteit
4. **Error Handling**: Script blijft draaien bij individuele query failures

## 🔮 Toekomstige Uitbreidingen

- [ ] **Multi-endpoint Testing**: Vergelijk meerdere endpoints tegelijk
- [ ] **Performance Metrics**: Memory usage, CPU utilization
- [ ] **Visualization**: Grafieken en charts van resultaten
- [ ] **Regression Testing**: Automatische detectie van performance regressies
- [ ] **Custom Scoring**: Mogelijkheid om eigen scoring algoritmes toe te voegen

## 📞 Support

Voor vragen of problemen:
1. Check de logs in `benchmark.log`
2. Controleer of alle dependencies geïnstalleerd zijn
3. Verifieer dat de FastAPI server correct draait
4. Controleer OpenAI API key configuratie 