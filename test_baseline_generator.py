#!/usr/bin/env python3
"""
Test script for Baseline Generator
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from analysis.baseline_generator import BaselineGenerator

def test_baseline_generator():
    """Test the baseline generator functionality."""
    print("📊 Testing Baseline Generator")
    print("="*50)
    
    # Initialize generator
    generator = BaselineGenerator()
    
    # Test 1: Generate store baselines
    print("\n1. Testing store baseline generation...")
    benchmark = generator.generate_store_baselines("test_store", days_back=30)
    
    if benchmark:
        print(f"✅ Generated baseline for store {benchmark.store_id}:")
        print(f"   Overall baseline: {benchmark.overall_baseline:.3f}")
        print(f"   Performance grade: {benchmark.performance_grade}")
        print(f"   Category baselines: {len(benchmark.category_baselines)}")
        print(f"   Intent baselines: {len(benchmark.intent_baselines)}")
        print(f"   Improvement opportunities: {len(benchmark.improvement_opportunities)}")
        
        # Show category baselines
        if benchmark.category_baselines:
            print("\n   Category Baselines:")
            for category, baseline in benchmark.category_baselines.items():
                print(f"     {category}: {baseline.avg_score:.3f} (confidence: {baseline.confidence:.3f})")
        
        # Show intent baselines
        if benchmark.intent_baselines:
            print("\n   Intent Baselines:")
            for intent_type, baseline in benchmark.intent_baselines.items():
                print(f"     {intent_type}: {baseline.avg_score:.3f} (confidence: {baseline.confidence:.3f})")
        
        # Show improvement opportunities
        if benchmark.improvement_opportunities:
            print("\n   Improvement Opportunities:")
            for i, opportunity in enumerate(benchmark.improvement_opportunities, 1):
                print(f"     {i}. {opportunity}")
    else:
        print("⚠️ No baseline generated (expected if no benchmark data exists)")
    
    # Test 2: Get latest baseline
    print("\n2. Testing latest baseline retrieval...")
    latest_baseline = generator.get_latest_baseline("test_store")
    
    if latest_baseline:
        print(f"✅ Retrieved latest baseline:")
        print(f"   Store ID: {latest_baseline.store_id}")
        print(f"   Overall baseline: {latest_baseline.overall_baseline:.3f}")
        print(f"   Performance grade: {latest_baseline.performance_grade}")
        print(f"   Generated at: {latest_baseline.generated_at}")
    else:
        print("⚠️ No latest baseline found (expected if no baselines exist)")
    
    # Test 3: Export baselines to JSON
    print("\n3. Testing baseline export...")
    if latest_baseline:
        export_path = generator.export_baselines_to_json("test_store")
        if export_path:
            print(f"✅ Exported baselines to: {export_path}")
        else:
            print("⚠️ Failed to export baselines")
    else:
        print("⚠️ Skipping export (no baseline available)")
    
    # Test 4: Test with different store
    print("\n4. Testing with different store...")
    benchmark2 = generator.generate_store_baselines("another_store", days_back=7)
    
    if benchmark2:
        print(f"✅ Generated baseline for another store:")
        print(f"   Overall baseline: {benchmark2.overall_baseline:.3f}")
        print(f"   Performance grade: {benchmark2.performance_grade}")
    else:
        print("⚠️ No baseline for another store (expected)")
    
    print("\n" + "="*50)
    print("✅ Baseline Generator test completed!")

if __name__ == "__main__":
    test_baseline_generator() 