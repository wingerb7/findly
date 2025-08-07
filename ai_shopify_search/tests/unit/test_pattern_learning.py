#!/usr/bin/env python3
"""
Test script for Pattern Learning System with Memory Management
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ai_shopify_search.analysis.pattern_learning import PatternLearningSystem

def test_pattern_learning():
    """Test the pattern learning system functionality."""
    print("🤖 Testing Pattern Learning System")
    print("="*50)
    
    # Initialize system
    system = PatternLearningSystem()
    
    # Test 1: Pattern analysis and learning
    print("\n1. Testing pattern analysis and learning...")
    suggestions = system.analyze_and_learn_patterns("test_store", days_back=30)
    
    if suggestions:
        print(f"✅ Generated {len(suggestions)} improvement suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion.suggestion_type}")
            print(f"      Description: {suggestion.description}")
            print(f"      Target: {suggestion.target_category}")
            print(f"      Expected improvement: {suggestion.expected_improvement:.3f}")
            print(f"      Priority: {suggestion.priority}")
            print(f"      Effort: {suggestion.estimated_effort}")
    else:
        print("⚠️ No suggestions generated (expected if no benchmark data exists)")
    
    # Test 2: Memory management - cleanup old data
    print("\n2. Testing memory management - cleanup...")
    cleanup_results = system.cleanup_old_data()
    
    if cleanup_results:
        print(f"✅ Cleanup completed:")
        total_cleaned = 0
        for table, count in cleanup_results.items():
            print(f"   {table}: {count} records cleaned")
            total_cleaned += count
        
        if total_cleaned > 0:
            print(f"   Total records cleaned: {total_cleaned}")
        else:
            print("   No old records found to clean (database is fresh)")
    else:
        print("⚠️ No cleanup performed (no policies or tables found)")
    
    # Test 3: Memory usage statistics
    print("\n3. Testing memory usage statistics...")
    memory_stats = system.get_memory_usage_stats()
    
    if memory_stats:
        print(f"✅ Memory usage statistics:")
        for table, stats in memory_stats.items():
            print(f"   {table}:")
            print(f"     Total records: {stats.get('total_records', 0)}")
            print(f"     Retention days: {stats.get('retention_days', 0)}")
            print(f"     Last cleanup: {stats.get('last_cleanup', 'Never')}")
            print(f"     Total cleaned: {stats.get('total_cleaned', 0)}")
    else:
        print("⚠️ No memory stats available (no tables found)")
    
    # Test 4: Storage optimization
    print("\n4. Testing storage optimization...")
    optimization_result = system.optimize_storage()
    
    if optimization_result.get("optimization_completed"):
        print(f"✅ Storage optimization completed:")
        print(f"   Initial pages: {optimization_result.get('initial_pages', 0)}")
        print(f"   Final pages: {optimization_result.get('final_pages', 0)}")
        print(f"   Space reclaimed: {optimization_result.get('space_reclaimed', 0)} pages")
    else:
        print("⚠️ Storage optimization failed or not needed")
    
    # Test 5: Export pattern analysis report
    print("\n5. Testing pattern analysis report export...")
    report_path = system.export_pattern_analysis_report("test_store")
    
    if report_path:
        print(f"✅ Pattern analysis report exported to: {report_path}")
    else:
        print("⚠️ Failed to export pattern analysis report")
    
    # Test 6: Memory policies overview
    print("\n6. Testing memory policies overview...")
    print("✅ Memory management policies:")
    for policy_name, policy in system.memory_policies.items():
        print(f"   {policy_name}:")
        print(f"     Table: {policy.table_name}")
        print(f"     Retention: {policy.retention_days} days")
        print(f"     Condition: {policy.cleanup_condition}")
        print(f"     Last cleanup: {policy.last_cleanup}")
        print(f"     Total cleaned: {policy.records_cleaned}")
    
    print("\n" + "="*50)
    print("✅ Pattern Learning System test completed!")

if __name__ == "__main__":
    test_pattern_learning() 