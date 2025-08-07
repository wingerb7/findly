#!/usr/bin/env python3
"""
Test script for Store Profile System
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ai_shopify_search.features.store_profile import StoreProfileGenerator

def test_store_profiles():
    """Test the store profile system functionality."""
    print("🏪 Testing Store Profile System")
    print("="*50)
    
    # Initialize generator
    generator = StoreProfileGenerator()
    
    # Test 1: Generate fashion store profile
    print("\n1. Testing fashion store profile generation...")
    fashion_profile = generator.generate_store_profile("fashion-store-123")
    
    if fashion_profile:
        print(f"✅ Generated profile for {fashion_profile.store_id}:")
        print(f"   Product count: {fashion_profile.characteristics.product_count}")
        print(f"   Price range: €{fashion_profile.characteristics.price_range[0]:.2f} - €{fashion_profile.characteristics.price_range[1]:.2f}")
        print(f"   Average price: €{fashion_profile.characteristics.average_price:.2f}")
        print(f"   Confidence score: {fashion_profile.confidence_score:.3f}")
        print(f"   Data quality score: {fashion_profile.data_quality_score:.3f}")
        
        print(f"\n   Category distribution:")
        for category, count in list(fashion_profile.characteristics.category_distribution.items())[:5]:
            print(f"     {category}: {count} products")
        
        print(f"\n   Performance metrics:")
        print(f"     Search score: {fashion_profile.performance_metrics.avg_search_score:.3f}")
        print(f"     Response time: {fashion_profile.performance_metrics.avg_response_time:.2f}s")
        print(f"     Cache hit rate: {fashion_profile.performance_metrics.cache_hit_rate:.3f}")
        
        print(f"\n   Search characteristics:")
        print(f"     Most searched: {fashion_profile.search_characteristics.most_searched_categories}")
        print(f"     Price sensitivity: {fashion_profile.search_characteristics.price_sensitivity}")
    else:
        print("⚠️ Failed to generate fashion store profile")
    
    # Test 2: Generate tech store profile
    print("\n2. Testing tech store profile generation...")
    tech_profile = generator.generate_store_profile("tech-store-456")
    
    if tech_profile:
        print(f"✅ Generated profile for {tech_profile.store_id}:")
        print(f"   Product count: {tech_profile.characteristics.product_count}")
        print(f"   Price range: €{tech_profile.characteristics.price_range[0]:.2f} - €{tech_profile.characteristics.price_range[1]:.2f}")
        print(f"   Average price: €{tech_profile.characteristics.average_price:.2f}")
        print(f"   Confidence score: {tech_profile.confidence_score:.3f}")
        
        print(f"\n   Category distribution:")
        for category, count in list(tech_profile.characteristics.category_distribution.items())[:5]:
            print(f"     {category}: {count} products")
    else:
        print("⚠️ Failed to generate tech store profile")
    
    # Test 3: Generate sports store profile
    print("\n3. Testing sports store profile generation...")
    sports_profile = generator.generate_store_profile("sports-store-789")
    
    if sports_profile:
        print(f"✅ Generated profile for {sports_profile.store_id}:")
        print(f"   Product count: {sports_profile.characteristics.product_count}")
        print(f"   Price range: €{sports_profile.characteristics.price_range[0]:.2f} - €{sports_profile.characteristics.price_range[1]:.2f}")
        print(f"   Average price: €{sports_profile.characteristics.average_price:.2f}")
        print(f"   Confidence score: {sports_profile.confidence_score:.3f}")
        
        print(f"\n   Brand distribution:")
        for brand, count in list(sports_profile.characteristics.brand_distribution.items())[:5]:
            print(f"     {brand}: {count} products")
    else:
        print("⚠️ Failed to generate sports store profile")
    
    # Test 4: Find similar stores
    print("\n4. Testing store similarity detection...")
    if fashion_profile:
        similar_stores = generator.find_similar_stores("fashion-store-123", limit=3)
        
        if similar_stores:
            print(f"✅ Found {len(similar_stores)} similar stores:")
            for i, similarity in enumerate(similar_stores, 1):
                print(f"   {i}. {similarity.store_id_2}")
                print(f"      Overall similarity: {similarity.overall_similarity:.3f}")
                print(f"      Category similarity: {similarity.category_similarity:.3f}")
                print(f"      Price similarity: {similarity.price_similarity:.3f}")
                print(f"      Confidence: {similarity.confidence:.3f}")
        else:
            print("⚠️ No similar stores found (expected if only one store exists)")
    else:
        print("⚠️ Skipping similarity test (no fashion profile available)")
    
    # Test 5: Get existing profile
    print("\n5. Testing profile retrieval...")
    if fashion_profile:
        retrieved_profile = generator.get_store_profile("fashion-store-123")
        
        if retrieved_profile:
            print(f"✅ Retrieved profile for {retrieved_profile.store_id}:")
            print(f"   Version: {retrieved_profile.profile_version}")
            print(f"   Generated: {retrieved_profile.generated_at}")
            print(f"   Last updated: {retrieved_profile.last_updated}")
        else:
            print("⚠️ Failed to retrieve profile")
    else:
        print("⚠️ Skipping retrieval test (no profile available)")
    
    # Test 6: Export profile to JSON
    print("\n6. Testing profile export...")
    if fashion_profile:
        export_path = generator.export_store_profile("fashion-store-123")
        
        if export_path:
            print(f"✅ Exported profile to: {export_path}")
        else:
            print("⚠️ Failed to export profile")
    else:
        print("⚠️ Skipping export test (no profile available)")
    
    # Test 7: Test with different store types
    print("\n7. Testing different store types...")
    store_types = ["budget-fashion", "premium-luxury", "general-store"]
    
    for store_type in store_types:
        profile = generator.generate_store_profile(f"{store_type}-test")
        if profile:
            print(f"✅ {store_type}: {profile.characteristics.product_count} products, €{profile.characteristics.average_price:.2f} avg")
        else:
            print(f"⚠️ Failed to generate {store_type} profile")
    
    print("\n" + "="*50)
    print("✅ Store Profile System test completed!")

if __name__ == "__main__":
    test_store_profiles() 