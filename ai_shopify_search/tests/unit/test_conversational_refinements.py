"""
Test script for Conversational Refinements Agent
Tests refinement generation with various search contexts and scenarios.
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_shopify_search.features.refinement_agent import (
    ConversationalRefinementAgent, RefinementContext, RefinementType, RefinementPriority
)

def test_refinement_agent():
    """Test the conversational refinement agent"""
    print("🧪 Testing Conversational Refinements Agent...")
    
    # Initialize agent
    agent = ConversationalRefinementAgent()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Price-sensitive user",
            "context": RefinementContext(
                search_query="goedkope zwarte schoenen",
                result_count=15,
                avg_price=75.0,
                price_range={"min": 25.0, "max": 150.0},
                categories=["Schoenen", "Casual"],
                brands=["Nike", "Adidas", "Puma"],
                colors=["Zwart", "Wit", "Grijs"],
                materials=["Leder", "Canvas", "Synthetisch"]
            )
        },
        {
            "name": "Brand-conscious user",
            "context": RefinementContext(
                search_query="exclusieve designer jas",
                result_count=8,
                avg_price=250.0,
                price_range={"min": 150.0, "max": 500.0},
                categories=["Jassen", "Outerwear"],
                brands=["Tommy Hilfiger", "Calvin Klein", "Ralph Lauren"],
                colors=["Zwart", "Blauw", "Beige"],
                materials=["Wol", "Katoen", "Polyester"]
            )
        },
        {
            "name": "Style-focused user",
            "context": RefinementContext(
                search_query="trendy streetwear kleding",
                result_count=25,
                avg_price=45.0,
                price_range={"min": 15.0, "max": 120.0},
                categories=["T-shirts", "Hoodies", "Broeken"],
                brands=["H&M", "Zara", "Pull&Bear"],
                colors=["Zwart", "Wit", "Grijs", "Blauw", "Rood"],
                materials=["Katoen", "Polyester", "Elastaan"]
            )
        },
        {
            "name": "Occasion-specific user",
            "context": RefinementContext(
                search_query="elegante bruiloft jurk",
                result_count=12,
                avg_price=180.0,
                price_range={"min": 80.0, "max": 350.0},
                categories=["Jurk", "Formeel"],
                brands=["Vero Moda", "Only", "Selected"],
                colors=["Wit", "Beige", "Roze", "Blauw"],
                materials=["Zijde", "Kant", "Chiffon"]
            )
        },
        {
            "name": "Budget-conscious user",
            "context": RefinementContext(
                search_query="duur premium horloge",
                result_count=6,
                avg_price=450.0,
                price_range={"min": 200.0, "max": 800.0},
                categories=["Horloges", "Accessoires"],
                brands=["Casio", "Seiko", "Citizen"],
                colors=["Zilver", "Goud", "Zwart"],
                materials=["Staal", "Leer", "Silicone"]
            )
        }
    ]
    
    print(f"\n📊 Testing {len(test_scenarios)} scenarios...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}️⃣ Testing: {scenario['name']}")
        print(f"   Query: '{scenario['context'].search_query}'")
        print(f"   Results: {scenario['context'].result_count}, Avg Price: €{scenario['context'].avg_price}")
        
        # Generate refinements
        response = agent.generate_refinements(scenario['context'])
        
        print(f"   🎯 Confidence Score: {response.confidence_score:.2f}")
        print(f"   📋 Generated {response.total_refinements} refinements:")
        
        for j, refinement in enumerate(response.refinements, 1):
            print(f"      {j}. [{refinement.type.value.upper()}] {refinement.title}")
            print(f"         Description: {refinement.description}")
            print(f"         Confidence: {refinement.confidence:.2f}, Priority: {refinement.priority.value}")
            if refinement.metadata:
                print(f"         Metadata: {refinement.metadata}")
        
        # Show primary refinement
        if response.primary_refinement:
            print(f"   ⭐ Primary: {response.primary_refinement.title}")
        
        # Show behavior analysis
        if response.metadata and "behavior_analysis" in response.metadata:
            behavior = response.metadata["behavior_analysis"]
            print(f"   🧠 Behavior Analysis:")
            for behavior_type, score in behavior.items():
                if score > 0.3:  # Only show significant behaviors
                    print(f"      - {behavior_type}: {score:.2f}")
    
    # Test statistics
    print(f"\n📈 Agent Statistics:")
    stats = agent.get_refinement_statistics()
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    print("\n✅ Conversational Refinements tests completed successfully!")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🔍 Testing Edge Cases...")
    
    agent = ConversationalRefinementAgent()
    
    # Test 1: Empty results
    print("\n1️⃣ Testing empty results...")
    empty_context = RefinementContext(
        search_query="nonexistent product",
        result_count=0,
        avg_price=0.0,
        price_range={"min": 0.0, "max": 0.0},
        categories=[],
        brands=[],
        colors=[],
        materials=[]
    )
    
    response = agent.generate_refinements(empty_context)
    print(f"   Generated {response.total_refinements} fallback refinements")
    print(f"   Confidence: {response.confidence_score:.2f}")
    
    # Test 2: Very expensive items
    print("\n2️⃣ Testing expensive items...")
    expensive_context = RefinementContext(
        search_query="luxe designer tas",
        result_count=3,
        avg_price=1200.0,
        price_range={"min": 800.0, "max": 2000.0},
        categories=["Tassen", "Luxe"],
        brands=["Louis Vuitton", "Gucci", "Prada"],
        colors=["Bruin", "Zwart", "Beige"],
        materials=["Leder", "Canvas", "Synthetisch"]
    )
    
    response = agent.generate_refinements(expensive_context)
    print(f"   Generated {response.total_refinements} refinements")
    print(f"   Primary: {response.primary_refinement.title if response.primary_refinement else 'None'}")
    
    # Test 3: Very specific query
    print("\n3️⃣ Testing specific query...")
    specific_context = RefinementContext(
        search_query="rode lederen schoenen maat 42",
        result_count=2,
        avg_price=85.0,
        price_range={"min": 65.0, "max": 105.0},
        categories=["Schoenen"],
        brands=["Clarks"],
        colors=["Rood"],
        materials=["Leder"]
    )
    
    response = agent.generate_refinements(specific_context)
    print(f"   Generated {response.total_refinements} refinements")
    print(f"   Confidence: {response.confidence_score:.2f}")
    
    print("\n✅ Edge case tests completed!")

def test_refinement_types():
    """Test different refinement types"""
    print("\n🎯 Testing Refinement Types...")
    
    agent = ConversationalRefinementAgent()
    
    # Test each refinement type
    refinement_types = [
        ("Price refinements", "goedkope schoenen", {"avg_price": 100.0}),
        ("Style refinements", "trendy kleding", {"categories": ["T-shirts", "Broeken"]}),
        ("Brand refinements", "nike schoenen", {"brands": ["Nike", "Adidas"]}),
        ("Color refinements", "zwarte kleding", {"colors": ["Zwart", "Grijs"]}),
        ("Category refinements", "schoenen", {"categories": ["Schoenen", "Sneakers"]}),
        ("Occasion refinements", "bruiloft jurk", {"categories": ["Jurk", "Formeel"]})
    ]
    
    for refinement_type, query, context_data in refinement_types:
        print(f"\n🔍 Testing {refinement_type}...")
        
        context = RefinementContext(
            search_query=query,
            result_count=10,
            avg_price=context_data.get("avg_price", 50.0),
            price_range={"min": 20.0, "max": 100.0},
            categories=context_data.get("categories", ["Algemeen"]),
            brands=context_data.get("brands", ["Merk"]),
            colors=context_data.get("colors", ["Zwart"]),
            materials=["Katoen"]
        )
        
        response = agent.generate_refinements(context)
        
        # Check if the expected refinement type is present
        refinement_types_found = [r.type.value for r in response.refinements]
        print(f"   Query: '{query}'")
        print(f"   Found types: {refinement_types_found}")
        print(f"   Total refinements: {response.total_refinements}")
    
    print("\n✅ Refinement type tests completed!")

def main():
    """Run all refinement tests"""
    print("🚀 Starting Conversational Refinements Tests")
    print("=" * 60)
    
    # Test core functionality
    test_refinement_agent()
    
    # Test edge cases
    test_edge_cases()
    
    # Test refinement types
    test_refinement_types()
    
    print("\n" + "=" * 60)
    print("🎉 All Conversational Refinements tests completed!")
    print("\n📋 Next steps:")
    print("   1. Integrate with the main search API")
    print("   2. Add refinement suggestions to search responses")
    print("   3. Implement refinement action handlers")
    print("   4. Test with real user interactions")
    print("   5. Monitor refinement effectiveness")

if __name__ == "__main__":
    main() 