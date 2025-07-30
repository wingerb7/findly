# ai_shopify_search/intent.py

def parse_query_intent(query: str):
    query_lower = query.lower()

    return {
        # Prijsintentie
        "cheap": any(word in query_lower for word in ["goedkoop", "budget", "betaalbaar", "lage prijs", "onder de", "goedkope"]),
        "expensive": any(word in query_lower for word in ["duur", "premium", "luxe", "high-end", "exclusief"]),
        "midrange": any(word in query_lower for word in ["middenklasse", "gemiddeld geprijsd", "normaal geprijsd"]),

        # Gebruikscontext
        "work": any(word in query_lower for word in ["werk", "kantoor", "zakelijk", "business"]),
        "sport": any(word in query_lower for word in ["sport", "fitness", "hardlopen", "gym", "training"]),
        "casual": any(word in query_lower for word in ["casual", "vrijetijd", "dagelijks", "ontspanning"]),
        "formal": any(word in query_lower for word in ["formeel", "chique", "gala", "avondkleding", "ceremonie"]),

        # Doelgroep
        "men": any(word in query_lower for word in ["heren", "mannen", "man"]),
        "women": any(word in query_lower for word in ["dames", "vrouwen", "vrouw"]),
        "kids": any(word in query_lower for word in ["kinderen", "kids", "jongens", "meisjes", "kinder"]),

        # Seizoen/gelegenheid
        "summer": any(word in query_lower for word in ["zomer", "lente", "warm weer", "strand"]),
        "winter": any(word in query_lower for word in ["winter", "herfst", "koud weer", "sneeuw"]),
        "party": any(word in query_lower for word in ["feest", "party", "verjaardag", "festival"]),
        "wedding": any(word in query_lower for word in ["bruiloft", "trouw", "huwelijk"]),

        # Producttype hints
        "electronics": any(word in query_lower for word in ["smartphone", "telefoon", "laptop", "tablet", "elektronica"]),
        "furniture": any(word in query_lower for word in ["stoel", "tafel", "kast", "bank", "meubel"]),
        "clothing": any(word in query_lower for word in ["shirt", "broek", "jas", "jurk", "trui", "kleding"]),
        "accessories": any(word in query_lower for word in ["horloge", "sieraden", "riem", "tas", "ketting"]),
        "pet": any(word in query_lower for word in ["hond", "kat", "dieren", "huisdier", "speelgoed hond"]),
    }

def rerank_results(rows, intent):
    results = []
    for row in rows:
        base_score = float(row[6]) if row[6] else 0.0
        price = float(row[4]) if row[4] else 0.0

        # Pas score aan op basis van intent
        if intent["cheap"]:
            price_boost = max(0, (200 - price) / 200)  # Boost lage prijzen
            final_score = base_score + (0.2 * price_boost)
        elif intent["expensive"]:
            price_boost = min(1, price / 5000)  # Boost hoge prijzen
            final_score = base_score + (0.2 * price_boost)
        else:
            final_score = base_score

        results.append({
            "id": row[0],
            "shopify_id": row[1],
            "title": row[2],
            "description": row[3],
            "price": price,
            "tags": list(row[5]) if row[5] else [],
            "similarity": final_score
        })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results