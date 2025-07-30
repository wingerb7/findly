#!/usr/bin/env python3
"""
Test script voor AI search met prijsfiltering
"""

import sys
import os
import asyncio
import requests
import json
from typing import Dict, Any

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_search_with_price_filters():
    """Test de AI search API met verschillende prijsintenties."""
    
    base_url = "http://localhost:8000"
    
    test_cases = [
        {
            "name": "Normale zoekopdracht zonder prijsintentie",
            "query": "blauwe shirt",
            "expected_price_filter": {"applied": False}
        },
        {
            "name": "Goedkoop zoekopdracht",
            "query": "goedkoop shirt",
            "expected_price_filter": {"applied": True, "max_price": 75}
        },
        {
            "name": "Duur zoekopdracht",
            "query": "duur horloge",
            "expected_price_filter": {"applied": True, "min_price": 200}
        },
        {
            "name": "Onder X euro zoekopdracht",
            "query": "onder 50 euro shirt",
            "expected_price_filter": {"applied": True, "max_price": 50}
        },
        {
            "name": "Boven X euro zoekopdracht",
            "query": "boven 100 euro horloge",
            "expected_price_filter": {"applied": True, "min_price": 100}
        },
        {
            "name": "Tussen X en Y euro zoekopdracht",
            "query": "tussen 50 en 100 euro shirt",
            "expected_price_filter": {"applied": True, "min_price": 50, "max_price": 100}
        },
        {
            "name": "Rond X euro zoekopdracht",
            "query": "rond 75 euro horloge",
            "expected_price_filter": {"applied": True, "min_price": 60, "max_price": 90}
        },
        {
            "name": "Engelse goedkoop zoekopdracht",
            "query": "cheap shoes",
            "expected_price_filter": {"applied": True, "max_price": 75}
        },
        {
            "name": "Engelse duur zoekopdracht",
            "query": "expensive watch",
            "expected_price_filter": {"applied": True, "min_price": 200}
        },
        {
            "name": "Engelse tussen X en Y zoekopdracht",
            "query": "between 25 and 75 euros shirt",
            "expected_price_filter": {"applied": True, "min_price": 25, "max_price": 75}
        }
    ]
    
    print("🧪 Testing AI Search met Prijsfiltering")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Query: '{test_case['query']}'")
        
        try:
            # Make API request
            response = requests.get(
                f"{base_url}/api/ai-search",
                params={
                    "query": test_case['query'],
                    "page": 1,
                    "limit": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["query", "results", "count", "price_filter"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ❌ Ontbrekende velden: {missing_fields}")
                    continue
                
                # Check price filter
                price_filter = data.get("price_filter", {})
                expected = test_case["expected_price_filter"]
                
                # Verify price filter is applied correctly
                if expected["applied"]:
                    if not price_filter.get("applied", False):
                        print(f"   ❌ Prijsfilter niet toegepast (verwacht: True)")
                        continue
                    
                    # Check specific price values
                    if "max_price" in expected and price_filter.get("max_price") != expected["max_price"]:
                        print(f"   ❌ Verkeerde max_price: {price_filter.get('max_price')} (verwacht: {expected['max_price']})")
                        continue
                    
                    if "min_price" in expected and price_filter.get("min_price") != expected["min_price"]:
                        print(f"   ❌ Verkeerde min_price: {price_filter.get('min_price')} (verwacht: {expected['min_price']})")
                        continue
                else:
                    if price_filter.get("applied", False):
                        print(f"   ❌ Prijsfilter toegepast (verwacht: False)")
                        continue
                
                # Check results
                results_count = len(data.get("results", []))
                print(f"   ✅ Prijsfilter: {price_filter}")
                print(f"   ✅ Resultaten: {results_count} producten")
                
                # Show first result if available
                if results_count > 0:
                    first_result = data["results"][0]
                    print(f"   ✅ Eerste resultaat: '{first_result.get('title', 'N/A')}' - €{first_result.get('price', 'N/A')}")
                
                # Check for fallback message
                if data.get("message"):
                    print(f"   ℹ️  Melding: {data['message']}")
                
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request Error: {e}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")

def test_fallback_scenario():
    """Test het fallback scenario wanneer geen producten in prijsrange zijn."""
    
    print("\n🧪 Testing Fallback Scenario")
    print("=" * 40)
    
    # Test een zeer specifieke prijsrange waar waarschijnlijk geen producten in zitten
    test_query = "duur shirt onder 10 euro"  # Conflicterende filters
    
    try:
        response = requests.get(
            "http://localhost:8000/api/ai-search",
            params={
                "query": test_query,
                "page": 1,
                "limit": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Query: '{test_query}'")
            print(f"Prijsfilter: {data.get('price_filter', {})}")
            print(f"Resultaten: {len(data.get('results', []))} producten")
            
            if data.get("message"):
                print(f"Melding: {data['message']}")
            
            # Check if fallback was used
            price_filter = data.get("price_filter", {})
            if price_filter.get("fallback_used", False):
                print("✅ Fallback gebruikt - goedkoopste alternatieven getoond")
            else:
                print("ℹ️  Geen fallback nodig")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting AI Search Price Filter Tests")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    test_ai_search_with_price_filters()
    test_fallback_scenario()
    
    print("\n🎉 AI Search Price Filter tests voltooid!") 