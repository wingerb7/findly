# Findly Codebase Cleanup & Refactor Roadmap

## 🎯 Doelen
1. **Behoud alle functionaliteit** - Niets mag stukgaan
2. **Geen scripts of mappen verwijderen of verplaatsen** - Alleen aanbevelingen in TODO secties
3. **Best practices toepassen** - Structuur, logging, error handling, docstrings
4. **Nieuwe helpers toevoegen** - Voor leesbaarheid en herbruikbaarheid
5. **TODO secties** - Aanbevelingen voor toekomstige verbeteringen
6. **Documentatie** - Alle aanpassingen gedocumenteerd

## 📊 Prioriteitsscore per Bestand

### 🔴 **Kritiek (Prioriteit 1) - Grote bestanden met veel duplicaten/structuurproblemen**
- `services/ai_search_service.py` (783 regels) ✅ **AFGEROND**
- `services/shopify_import_service.py` (1070 regels) - **NEXT**
- `features/enhanced_benchmark_search.py` (1601 regels)
- `features/store_profile.py` (988 regels)
- `features/refinement_agent.py` (886 regels)
- `api/products_router.py` (1000 regels)

### 🟡 **Hoog (Prioriteit 2) - Middelgrote bestanden met structuurproblemen**
- `core/embeddings.py` (723 regels)
- `core/analytics_manager.py` (513 regels)
- `features/adaptive_filters.py` (580 regels)
- `features/transfer_learning.py` (594 regels)
- `features/knowledge_base_builder.py` (457 regels)
- `services/analytics_service.py` (456 regels)
- `services/facets_service.py` (454 regels)
- `features/conversational_context.py` (368 regels)
- `features/continuous_benchmark.py` (358 regels)
- `services/suggestion_service.py` (348 regels)

### 🟢 **Medium (Prioriteit 3) - Kleinere bestanden met cleanup nodig**
- `api/conversational_router.py` (407 regels)
- `api/ai_learning_router.py` (298 regels)
- `api/feedback_router.py` (258 regels)
- `services/service_factory.py` (258 regels)
- `api/error_handlers.py` (251 regels)
- `core/embedding_config.py` (271 regels)
- `services/cache_service.py` (288 regels)
- `core/progress_tracker.py` (192 regels)
- `services/baseline_generator_service.py` (175 regels)

### 🔵 **Laag (Prioriteit 4) - Kleine bestanden, minimale cleanup**
- `core/models.py` (319 regels)
- `core/metrics.py` (135 regels)
- `core/rate_limiter.py` (85 regels)
- `core/cache_manager.py` (87 regels)
- `core/database.py` (107 regels)
- `core/config.py` (74 regels)

## 🏗️ Cleanup Checklist per Bestand

### **Structuur & Organisatie**
- [ ] **Imports**: Ongebruikte imports verwijderd? Logisch gegroepeerd?
- [ ] **Configuratie**: Magic numbers/strings vervangen door constanten?
- [ ] **Klassen**: Logische volgorde (imports → config → classes → public → private)?
- [ ] **Methoden**: Public methods bovenaan, private helpers onderaan?

### **Documentatie & Logging**
- [ ] **Docstrings**: Elke class, methode en belangrijke functie heeft duidelijke docstring?
- [ ] **Logging**: Consistente logregels met context (query, store_id, page)?
- [ ] **Comments**: Complexe logica gedocumenteerd?

### **Code Kwaliteit**
- [ ] **Error Handling**: Fouten netjes afgehandeld en gelogd?
- [ ] **Duplicaten**: Dubbele code verplaatst naar helpers?
- [ ] **Type Hints**: Volledige type annotations?
- [ ] **Consistentie**: Naming conventions, formatting?

### **Helpers & Refactoring**
- [ ] **Nieuwe Helpers**: Toegevoegd waar nodig voor leesbaarheid?
- [ ] **Helper Methoden**: `_parse_embedding()`, `_handle_pgvector_fallback()`, etc.?
- [ ] **Code Splitsing**: Grote methoden opgesplitst?

### **TODO Sectie**
- [ ] **Aanbevelingen**: Opsplitsing van modules?
- [ ] **Verwijderen**: Functies die later verwijderd kunnen worden?
- [ ] **Performance**: Optimalisaties voor de toekomst?

## 📋 Gedetailleerd Plan per Bestand

### **1. services/shopify_import_service.py** (1070 regels)
**Problemen geïdentificeerd:**
- Grote import methoden met veel duplicatie
- Inconsistente error handling
- Magic numbers voor batch sizes
- Ongebruikte imports

**Cleanup acties:**
- [ ] Helper methoden: `_parse_shopify_product()`, `_handle_import_batch()`
- [ ] Constants: `BATCH_SIZE`, `MAX_RETRIES`, `RATE_LIMIT_DELAY`
- [ ] Error handling: Consistent try/catch patterns
- [ ] Logging: Context toevoegen (store_id, batch_number)
- [ ] TODO sectie: Aanbevelingen voor opsplitsing

### **2. features/enhanced_benchmark_search.py** (1601 regels)
**Problemen geïdentificeerd:**
- Zeer grote bestand met meerdere verantwoordelijkheden
- Duplicatie in benchmark logica
- Complexe methoden die opgesplitst moeten worden

**Cleanup acties:**
- [ ] Helper methoden: `_calculate_benchmark_metrics()`, `_prepare_benchmark_data()`
- [ ] Constants: `BENCHMARK_THRESHOLDS`, `METRIC_WEIGHTS`
- [ ] Structuur: Logische groepering van gerelateerde methoden
- [ ] TODO sectie: Aanbevelingen voor module opsplitsing

### **3. features/store_profile.py** (988 regels)
**Problemen geïdentificeerd:**
- Grote profile generation methoden
- Duplicatie in data processing
- Inconsistente error handling

**Cleanup acties:**
- [ ] Helper methoden: `_extract_store_insights()`, `_generate_profile_summary()`
- [ ] Constants: `PROFILE_WEIGHTS`, `INSIGHT_THRESHOLDS`
- [ ] Error handling: Consistent patterns
- [ ] TODO sectie: Aanbevelingen voor refactoring

### **4. features/refinement_agent.py** (886 regels)
**Problemen geïdentificeerd:**
- Complexe refinement logica
- Duplicatie in conversation handling
- Grote methoden die opgesplitst moeten worden

**Cleanup acties:**
- [ ] Helper methoden: `_process_conversation_context()`, `_generate_refinements()`
- [ ] Constants: `REFINEMENT_TYPES`, `CONTEXT_LIMITS`
- [ ] Structuur: Logische groepering
- [ ] TODO sectie: Aanbevelingen voor verbeteringen

### **5. api/products_router.py** (1000 regels)
**Problemen geïdentificeerd:**
- Grote router met veel endpoints
- Duplicatie in response formatting
- Inconsistente error handling

**Cleanup acties:**
- [ ] Helper methoden: `_format_product_response()`, `_validate_search_params()`
- [ ] Constants: `DEFAULT_LIMITS`, `VALID_SORT_OPTIONS`
- [ ] Error handling: Consistent HTTP error responses
- [ ] TODO sectie: Aanbevelingen voor router opsplitsing

## 🎯 Implementatie Strategie

### **Fase 1: Kritieke bestanden (Prioriteit 1)**
1. ✅ `services/ai_search_service.py` - **AFGEROND**
2. `services/shopify_import_service.py` - **NEXT**
3. `features/enhanced_benchmark_search.py`
4. `features/store_profile.py`
5. `features/refinement_agent.py`
6. `api/products_router.py`

### **Fase 2: Hoog prioriteit (Prioriteit 2)**
- `core/embeddings.py`
- `core/analytics_manager.py`
- `features/adaptive_filters.py`
- `features/transfer_learning.py`

### **Fase 3: Medium prioriteit (Prioriteit 3)**
- `api/conversational_router.py`
- `api/ai_learning_router.py`
- `services/analytics_service.py`

### **Fase 4: Laag prioriteit (Prioriteit 4)**
- `core/models.py`
- `core/metrics.py`
- `core/rate_limiter.py`

## 📝 Template voor Cleanup Rapport

```markdown
## Cleanup Rapport: [bestandsnaam]

### ✅ Voltooide Acties
- [ ] Imports opgeschoond en gegroepeerd
- [ ] Constants toegevoegd voor magic numbers
- [ ] Helper methoden toegevoegd: `_helper_name()`
- [ ] Error handling geconsolideerd
- [ ] Logging consistent gemaakt
- [ ] Docstrings toegevoegd/verbeterd
- [ ] TODO sectie toegevoegd

### 📊 Metrieken
- **Voor**: X regels
- **Na**: Y regels
- **Besparing**: Z regels
- **Nieuwe helpers**: N methoden

### 🔍 Specifieke Verbeteringen
- [ ] Duplicatie verwijderd: [beschrijving]
- [ ] Grote methoden opgesplitst: [methode namen]
- [ ] Error handling verbeterd: [beschrijving]
- [ ] Logging toegevoegd: [context]

### 📋 TODO Aanbevelingen
- [ ] Mogelijke opsplitsing: [beschrijving]
- [ ] Functies voor verwijdering: [lijst]
- [ ] Performance optimalisaties: [beschrijving]
```

## 🚀 Volgende Stappen

1. **Start met `services/shopify_import_service.py`** - Volgende grote bestand
2. **Volg de checklist** - Zorg dat alle items afgevinkt worden
3. **Documenteer wijzigingen** - In comments en docstrings
4. **Test functionaliteit** - Zorg dat niets stukgaat
5. **Voeg TODO secties toe** - Voor toekomstige verbeteringen

## 📞 Ondersteuning

Voor vragen of problemen tijdens de cleanup:
- Check de checklist per bestand
- Volg de template voor consistentie
- Test altijd na wijzigingen
- Documenteer alle aanpassingen 