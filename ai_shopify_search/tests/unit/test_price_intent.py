#!/usr/bin/env python3
"""
Test script voor prijsintentie functionaliteit
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from price_intent import extract_price_intent, clean_query_from_price_intent, format_price_message

def test_price_intent():
    """Test de prijsintentie extractie functionaliteit."""
    
    test_cases = [
        # Nederlandse tests
        ("goedkoop shirt", None, 75),
        ("duur horloge", 200, None),
        ("onder 50 euro", None, 50),
        ("boven 100 euro", 100, None),
        ("tussen 50 en 100 euro", 50, 100),
        ("50 tot 100 euro", 50, 100),
        ("rond 75 euro", 60, 90),  # 75 * 0.8 = 60, 75 * 1.2 = 90
        ("ongeveer 100 euro", 80, 120),  # 100 * 0.8 = 80, 100 * 1.2 = 120
        ("100 euro", 90, 110),  # 100 * 0.9 = 90, 100 * 1.1 = 110
        
        # Engelse tests
        ("cheap shoes", None, 75),
        ("expensive watch", 200, None),
        ("below 30 euros", None, 30),
        ("above 150 euros", 150, None),
        ("between 25 and 75 euros", 25, 75),
        ("25 to 75 euros", 25, 75),
        ("around 50 euros", 40, 60),  # 50 * 0.8 = 40, 50 * 1.2 = 60
        ("approximately 80 euros", 64, 96),  # 80 * 0.8 = 64, 80 * 1.2 = 96
        
        # Geen prijsintentie
        ("blauwe shirt", None, None),
        ("wireless headphones", None, None),
        ("", None, None),
    ]
    
    print("🧪 Testing Prijsintentie Extractie")
    print("=" * 50)
    
    for i, (query, expected_min, expected_max) in enumerate(test_cases, 1):
        min_price, max_price = extract_price_intent(query)
        cleaned_query = clean_query_from_price_intent(query)
        
        # Check results (with floating point tolerance)
        min_match = (min_price == expected_min) or (min_price is None and expected_min is None) or (min_price is not None and expected_min is not None and abs(min_price - expected_min) < 0.01)
        max_match = (max_price == expected_max) or (max_price is None and expected_max is None) or (max_price is not None and expected_max is not None and abs(max_price - expected_max) < 0.01)
        
        status = "✅" if min_match and max_match else "❌"
        
        print(f"{i:2d}. {status} Query: '{query}'")
        print(f"    Min: {min_price} (expected: {expected_min})")
        print(f"    Max: {max_price} (expected: {expected_max})")
        print(f"    Cleaned: '{cleaned_query}'")
        print(f"    Message: {format_price_message(min_price, max_price)}")
        print()

def test_edge_cases():
    """Test edge cases en speciale gevallen."""
    
    print("🧪 Testing Edge Cases")
    print("=" * 30)
    
    edge_cases = [
        "onder 50,50 euro",
        "tussen 25,5 en 75,25 euro",
        "GOEDKOOP SHIRT",
        "DuUr WaTcH",
        "onder 50€",
        "tussen 25€ en 75€",
        "rond 100 EUR",
    ]
    
    for i, query in enumerate(edge_cases, 1):
        min_price, max_price = extract_price_intent(query)
        cleaned_query = clean_query_from_price_intent(query)
        
        print(f"{i}. Query: '{query}'")
        print(f"   Min: {min_price}, Max: {max_price}")
        print(f"   Cleaned: '{cleaned_query}'")
        print(f"   Message: {format_price_message(min_price, max_price)}")
        print()

if __name__ == "__main__":
    test_price_intent()
    print()
    test_edge_cases()
    
    print("🎉 Prijsintentie tests voltooid!") 