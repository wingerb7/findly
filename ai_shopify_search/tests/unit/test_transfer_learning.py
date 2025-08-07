#!/usr/bin/env python3
"""
Test script for Transfer Learning Engine
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ai_shopify_search.features.transfer_learning import TransferLearningEngine

def test_transfer_learning():
    """Test the transfer learning engine functionality."""
    print("🚀 Testing Transfer Learning Engine")
    print("="*50)
    
    # Initialize engine
    engine = TransferLearningEngine()
    
    # Test 1: Find similar stores
    print("\n1. Testing store similarity detection...")
    similar_stores = engine.find_similar_stores("test_store", limit=3)
    
    if similar_stores:
        print(f"✅ Found {len(similar_stores)} similar stores:")
        for i, store_sim in enumerate(similar_stores, 1):
            print(f"   {i}. Store {store_sim.store_id_2} - Similarity: {store_sim.similarity_score:.3f}")
            print(f"      Confidence: {store_sim.confidence:.3f}")
            print(f"      Factors: {list(store_sim.similarity_factors.keys())}")
    else:
        print("⚠️ No similar stores found (expected if no store profiles exist)")
    
    # Test 2: Generate transfer recommendations
    print("\n2. Testing transfer recommendations...")
    recommendations = engine.generate_transfer_recommendations("test_store")
    
    if recommendations:
        print(f"✅ Generated {len(recommendations)} transfer recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec.pattern_type}")
            print(f"      Description: {rec.pattern_description}")
            print(f"      Expected improvement: {rec.expected_improvement:.3f}")
            print(f"      Confidence: {rec.confidence:.3f}")
            print(f"      Risk level: {rec.risk_level}")
            print(f"      Source stores: {rec.source_stores}")
    else:
        print("⚠️ No transfer recommendations generated (expected if no similar stores)")
    
    # Test 3: Apply recommendations
    if recommendations:
        print("\n3. Testing recommendation application...")
        results = engine.apply_transfer_recommendations("test_store", recommendations)
        
        print(f"✅ Applied {len(results['applied_recommendations'])} recommendations:")
        for applied in results['applied_recommendations']:
            print(f"   - {applied['pattern_type']}: {applied['expected_improvement']:.3f} improvement")
        
        if results['skipped_recommendations']:
            print(f"⚠️ Skipped {len(results['skipped_recommendations'])} recommendations:")
            for skipped in results['skipped_recommendations']:
                print(f"   - {skipped['pattern_type']}: {skipped['reason']}")
    else:
        print("3. Skipping recommendation application (no recommendations available)")
    
    # Test 4: Get transfer history
    print("\n4. Testing transfer history...")
    history = engine.get_transfer_history("test_store")
    
    if history:
        print(f"✅ Found {len(history)} transfer applications:")
        for i, entry in enumerate(history, 1):
            print(f"   {i}. {entry['pattern_type']} - Applied: {entry['applied_at']}")
            print(f"      Expected improvement: {entry['expected_improvement']:.3f}")
            print(f"      Risk level: {entry['risk_level']}")
    else:
        print("⚠️ No transfer history found (expected for new stores)")
    
    print("\n" + "="*50)
    print("✅ Transfer Learning Engine test completed!")

if __name__ == "__main__":
    test_transfer_learning() 