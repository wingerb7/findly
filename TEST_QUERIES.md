# Test Queries voor Price Intent Detection

## 🎯 **Basis Price Intent Tests**

### **Exacte Prijzen**
- `"schoenen 150€"`
- `"jas onder €200"`
- `"shirt boven 50 euro"`
- `"broek tussen 80 en 120 euro"`
- `"accessoire €25"`

### **Budget & Goedkoop**
- `"goedkope schoenen"`
- `"betaalbare jas"`
- `"shirt onder €30"`
- `"broek goedkoop"`
- `"accessoire budget"`

### **Premium & Duur**
- `"duur exclusief jas"`
- `"premium schoenen"`
- `"luxe shirt"`
- `"designer broek"`
- `"exclusieve accessoire"`

## 🏷️ **Product Type Tests**

### **Schoenen (Premium Category)**
- `"goedkope schoenen voor werk"`
- `"duur exclusief schoenen"`
- `"schoenen onder €100"`
- `"premium schoenen voor heren"`
- `"schoenen tussen 50 en 150 euro"`

### **Jassen (Premium Category)**
- `"jas goedkoop"`
- `"duur exclusief jas"`
- `"jas onder €150"`
- `"premium jas voor dames"`
- `"jas tussen 100 en 300 euro"`

### **Shirts (Budget Category)**
- `"shirt goedkoop"`
- `"betaalbare shirt"`
- `"shirt onder €50"`
- `"casual shirt"`
- `"shirt tussen 20 en 80 euro"`

### **Broeken (Budget Category)**
- `"broek goedkoop"`
- `"betaalbare broek"`
- `"broek onder €60"`
- `"casual broek"`
- `"broek tussen 30 en 100 euro"`

### **Jurken (Mixed Category)**
- `"jurk goedkoop"`
- `"duur exclusief jurk"`
- `"jurk onder €80"`
- `"premium jurk"`
- `"jurk tussen 40 en 200 euro"`

### **Accessoires (Budget Category)**
- `"accessoire goedkoop"`
- `"betaalbare accessoire"`
- `"accessoire onder €25"`
- `"kleine accessoire"`
- `"accessoire tussen 10 en 50 euro"`

## 🎨 **Materiaal Tests**

### **Premium Materialen**
- `"leder schoenen goedkoop"`
- `"zijde jas duur"`
- `"wol shirt premium"`
- `"kashmir accessoire exclusief"`

### **Budget Materialen**
- `"katoen shirt goedkoop"`
- `"polyester broek betaalbaar"`
- `"denim jas onder €100"`
- `"synthetisch accessoire budget"`

## 👥 **Doelgroep Tests**

### **Heren**
- `"heren schoenen goedkoop"`
- `"duur exclusief heren jas"`
- `"heren shirt onder €40"`
- `"heren broek premium"`

### **Dames**
- `"dames schoenen goedkoop"`
- `"duur exclusief dames jas"`
- `"dames shirt onder €50"`
- `"dames jurk premium"`

### **Unisex**
- `"unisex schoenen goedkoop"`
- `"unisex jas duur"`
- `"unisex shirt betaalbaar"`

## 🌈 **Kleur Tests**

### **Basis Kleuren**
- `"zwarte schoenen goedkoop"`
- `"witte jas duur"`
- `"blauwe shirt onder €30"`
- `"rode broek premium"`

### **Speciale Kleuren**
- `"beige schoenen goedkoop"`
- `"paarse jas duur"`
- `"grijze shirt betaalbaar"`
- `"gele broek onder €50"`

## 🌍 **Seizoen Tests**

### **Zomer**
- `"zomer schoenen goedkoop"`
- `"zomer jas duur"`
- `"zomer shirt onder €40"`

### **Winter**
- `"winter schoenen goedkoop"`
- `"winter jas duur"`
- `"winter shirt betaalbaar"`

### **Lente/Herfst**
- `"lente schoenen goedkoop"`
- `"herfst jas duur"`
- `"lente shirt onder €35"`

## 🎯 **Gebruik Tests**

### **Casual**
- `"casual schoenen goedkoop"`
- `"casual jas duur"`
- `"casual shirt onder €30"`

### **Sport**
- `"sport schoenen goedkoop"`
- `"sport jas duur"`
- `"sport shirt betaalbaar"`

### **Werk/Formeel**
- `"werk schoenen goedkoop"`
- `"formeel jas duur"`
- `"werk shirt onder €50"`

## 🔄 **Complexe Combinaties**

### **Multi-Criteria**
- `"goedkope zwarte heren schoenen voor werk"`
- `"duur exclusief rode dames jas voor winter"`
- `"betaalbare blauwe unisex shirt voor casual"`
- `"premium beige heren broek voor formeel"`

### **Materiaal + Type**
- `"leder schoenen goedkoop"`
- `"katoen shirt duur"`
- `"wol jas betaalbaar"`
- `"denim broek premium"`

### **Seizoen + Type**
- `"winter jas goedkoop"`
- `"zomer schoenen duur"`
- `"lente shirt betaalbaar"`
- `"herfst broek premium"`

## 🧠 **GPT-Powered Test Cases**

### **Context-Aware Queries**
- `"schoenen voor een sollicitatie"`
- `"jas voor een bruiloft"`
- `"shirt voor een date"`
- `"broek voor een feest"`
- `"accessoire voor een cadeau"`

### **Relative Price Queries**
- `"goedkope schoenen voor een student"`
- `"duur exclusief jas voor een manager"`
- `"betaalbare shirt voor een tiener"`
- `"premium broek voor een professional"`

### **Market Knowledge Queries**
- `"schoenen zoals Nike maar goedkoper"`
- `"jas zoals een designer merk"`
- `"shirt van goede kwaliteit"`
- `"broek die lang meegaat"`

## 📊 **Edge Cases**

### **Geen Price Intent**
- `"rode schoenen"`
- `"winter jas"`
- `"heren shirt"`
- `"casual broek"`

### **Vage Price Intent**
- `"niet te duur"`
- `"redelijke prijs"`
- `"normale prijs"`
- `"betaalbaar"`

### **Contradictory Intent**
- `"goedkope premium schoenen"`
- `"duur exclusief budget jas"`
- `"betaalbare luxe shirt"`

## 🎯 **Test Scenarios**

### **Scenario 1: Student Budget**
- `"goedkope schoenen voor school"`
- `"betaalbare jas voor student"`
- `"shirt onder €25"`
- `"broek goedkoop voor college"`

### **Scenario 2: Professional**
- `"duur exclusief jas voor werk"`
- `"premium schoenen voor kantoor"`
- `"shirt van goede kwaliteit"`
- `"broek voor een sollicitatie"`

### **Scenario 3: Casual Shopper**
- `"casual schoenen goedkoop"`
- `"comfortabele jas betaalbaar"`
- `"shirt voor dagelijks gebruik"`
- `"broek voor thuis"`

### **Scenario 4: Fashion Conscious**
- `"trendy schoenen"`
- `"moderne jas"`
- `"stijlvolle shirt"`
- `"fashion broek"`

## 📈 **Performance Tests**

### **Bulk Testing**
```bash
# Test alle basis queries
for query in "goedkope schoenen" "duur exclusief jas" "betaalbare shirt" "premium broek"; do
  curl -X GET "http://localhost:8000/api/ai-search?query=$query&page=1&limit=25"
done
```

### **Stress Testing**
```bash
# Test met veel verschillende queries
queries=("goedkope schoenen" "duur exclusief jas" "betaalbare shirt" "premium broek" "casual accessoire")
for i in {1..10}; do
  for query in "${queries[@]}"; do
    curl -X GET "http://localhost:8000/api/ai-search?query=$query&page=1&limit=25" &
  done
done
wait
```

## 🎯 **Verwachte Resultaten**

### **Premium Items (Schoenen, Jassen)**
- `"goedkope schoenen"` → max_price: 100-150€
- `"duur exclusief jas"` → min_price: 200-300€
- `"premium schoenen"` → min_price: 150-200€

### **Budget Items (Shirts, Broeken, Accessoires)**
- `"goedkope shirt"` → max_price: 30-50€
- `"betaalbare broek"` → max_price: 60-80€
- `"accessoire goedkoop"` → max_price: 20-30€

### **Mixed Items (Jurken)**
- `"goedkope jurk"` → max_price: 80-120€
- `"duur exclusief jurk"` → min_price: 150-250€

## 🔍 **Monitoring**

### **Log Output Verwachting**
```
🔎 [SEARCH] "goedkope schoenen"
    User: 192.168.*.* | UA: Windows/Chrome
💰 [PRICE INTENT] max_price=100 (pattern: budget, confidence: 0.85)
🔗 [FILTERS] min_price=None, max_price=100 | Fallback: NO | Filtered: 15/1001
📈 [SIMILARITY] Top: 0.84 | Avg: 0.62 | Min: 0.40
⚙️ [ENGINE] Mode: AI + BM25 | Model: text-embedding-3-small
🔄 [CACHE] HIT (TTL: 55s)
⚡ [RESULT] 12 hits | 0.42s
```

### **GPT Analysis Verwachting**
```
🔎 [SEARCH] "schoenen voor een sollicitatie"
    User: 192.168.*.* | UA: Windows/Chrome
💰 [PRICE INTENT] min_price=80, max_price=200 (pattern: gpt_analysis, confidence: 0.75)
🔗 [FILTERS] min_price=80, max_price=200 | Fallback: YES | Filtered: 8/1001
📈 [SIMILARITY] Top: 0.84 | Avg: 0.62 | Min: 0.40
⚙️ [ENGINE] Mode: AI + BM25 | Model: text-embedding-3-small
🔄 [CACHE] MISS
⚡ [RESULT] 8 hits | 0.85s
``` 