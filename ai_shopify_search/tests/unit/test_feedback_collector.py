"""
Test script for Feedback Collector
Tests feedback collection, analysis, and API functionality.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feedback.feedback_collector import (
    FeedbackCollector, FeedbackData, FeedbackType, FeedbackCategory
)

async def test_feedback_collector():
    """Test the feedback collector functionality"""
    print("🧪 Testing Feedback Collector...")
    
    # Initialize feedback collector
    feedback_collector = FeedbackCollector()
    
    # Test 1: Submit sample feedback
    print("\n1️⃣ Testing feedback submission...")
    
    sample_feedback = [
        FeedbackData(
            feedback_id="",
            query_id="test_query_1",
            search_query="zwarte schoenen",
            feedback_type=FeedbackType.NEGATIVE,
            feedback_category=FeedbackCategory.PRICE,
            feedback_text="Te duur voor wat je krijgt",
            user_rating=2,
            suggested_improvement="Meer betaalbare opties tonen",
            metadata={"user_type": "new_customer"}
        ),
        FeedbackData(
            feedback_id="",
            query_id="test_query_2", 
            search_query="winter jas",
            feedback_type=FeedbackType.POSITIVE,
            feedback_category=FeedbackCategory.RELEVANCE,
            feedback_text="Perfecte resultaten gevonden",
            user_rating=5,
            suggested_improvement="Meer van dit soort resultaten",
            metadata={"user_type": "returning_customer"}
        ),
        FeedbackData(
            feedback_id="",
            query_id="test_query_3",
            search_query="sportieve kleding",
            feedback_type=FeedbackType.NEUTRAL,
            feedback_category=FeedbackCategory.SPEED,
            feedback_text="Zoeken duurde lang",
            user_rating=3,
            suggested_improvement="Snellere zoekresultaten",
            metadata={"user_type": "mobile_user"}
        )
    ]
    
    for feedback in sample_feedback:
        success = feedback_collector.collect_feedback(feedback)
        print(f"   ✅ Feedback submitted: {feedback.feedback_id} - {success}")
    
    # Test 2: Get feedback by query
    print("\n2️⃣ Testing feedback retrieval...")
    
    query_feedback = feedback_collector.get_feedback_by_query("test_query_1")
    print(f"   📊 Found {len(query_feedback)} feedback entries for test_query_1")
    
    for feedback in query_feedback:
        print(f"      - {feedback.feedback_type.value}: {feedback.feedback_text}")
    
    # Test 3: Analyze feedback
    print("\n3️⃣ Testing feedback analysis...")
    
    analysis = feedback_collector.analyze_feedback(days=30)
    print(f"   📈 Total feedback: {analysis.total_feedback}")
    print(f"   😊 Positive ratio: {analysis.positive_ratio:.2%}")
    print(f"   😞 Negative ratio: {analysis.negative_ratio:.2%}")
    print(f"   ⭐ Average rating: {analysis.avg_rating:.1f}/5")
    print(f"   🎯 Satisfaction score: {analysis.satisfaction_score:.2f}")
    
    print(f"   📋 Top categories:")
    for category in analysis.top_categories:
        print(f"      - {category['category']}: {category['count']} ({category['percentage']:.1f}%)")
    
    # Test 4: Get recommendations
    print("\n4️⃣ Testing improvement recommendations...")
    
    recommendations = feedback_collector.get_improvement_recommendations()
    print(f"   💡 Generated {len(recommendations)} recommendations:")
    for rec in recommendations:
        print(f"      - {rec}")
    
    # Test 5: Export report
    print("\n5️⃣ Testing report export...")
    
    report = feedback_collector.export_feedback_report(days=30)
    print(f"   📄 Report generated with {len(report)} sections")
    print(f"   📊 Summary: {report['summary']['total_feedback']} feedback entries")
    
    print("\n✅ Feedback Collector tests completed successfully!")

async def test_feedback_api():
    """Test the feedback API endpoints"""
    print("\n🌐 Testing Feedback API endpoints...")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("\n1️⃣ Testing health check...")
        try:
            async with session.get(f"{base_url}/api/feedback/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Health check passed: {data['status']}")
                else:
                    print(f"   ❌ Health check failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        # Test 2: Get categories
        print("\n2️⃣ Testing categories endpoint...")
        try:
            async with session.get(f"{base_url}/api/feedback/categories") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Categories retrieved: {len(data['feedback_types'])} types, {len(data['feedback_categories'])} categories")
                else:
                    print(f"   ❌ Categories failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Categories error: {e}")
        
        # Test 3: Submit feedback via API
        print("\n3️⃣ Testing feedback submission...")
        feedback_payload = {
            "query_id": "api_test_query",
            "search_query": "test query via API",
            "feedback_type": "positive",
            "feedback_category": "relevance",
            "feedback_text": "Great search results via API test",
            "user_rating": 5,
            "suggested_improvement": "Keep up the good work",
            "metadata": {"test": True, "source": "api_test"}
        }
        
        try:
            async with session.post(
                f"{base_url}/api/feedback/submit",
                json=feedback_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Feedback submitted via API: {data['feedback_id']}")
                else:
                    print(f"   ❌ Feedback submission failed: {response.status}")
                    error_text = await response.text()
                    print(f"      Error: {error_text}")
        except Exception as e:
            print(f"   ❌ Feedback submission error: {e}")
        
        # Test 4: Get analysis
        print("\n4️⃣ Testing analysis endpoint...")
        try:
            async with session.get(f"{base_url}/api/feedback/analysis?days=30") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Analysis retrieved: {data['total_feedback']} feedback entries")
                    print(f"      Satisfaction score: {data['satisfaction_score']:.2f}")
                else:
                    print(f"   ❌ Analysis failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
        
        # Test 5: Get stats
        print("\n5️⃣ Testing stats endpoint...")
        try:
            async with session.get(f"{base_url}/api/feedback/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Stats retrieved: {data['last_30_days']['total_feedback']} feedback entries")
                else:
                    print(f"   ❌ Stats failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Stats error: {e}")
    
    print("\n✅ Feedback API tests completed!")

async def main():
    """Run all feedback tests"""
    print("🚀 Starting Feedback Collector Tests")
    print("=" * 50)
    
    # Test core functionality
    await test_feedback_collector()
    
    # Test API endpoints (if server is running)
    print("\n" + "=" * 50)
    print("⚠️  Note: API tests require the FastAPI server to be running on localhost:8000")
    print("   Start the server with: uvicorn ai_shopify_search.main:app --reload")
    
    try:
        await test_feedback_api()
    except Exception as e:
        print(f"\n❌ API tests skipped (server not running): {e}")
        print("   This is expected if the server is not running")
    
    print("\n" + "=" * 50)
    print("🎉 All Feedback Collector tests completed!")
    print("\n📋 Next steps:")
    print("   1. Start the FastAPI server to test API endpoints")
    print("   2. Submit real feedback via the API")
    print("   3. Monitor feedback analysis and recommendations")
    print("   4. Integrate with the main search system")

if __name__ == "__main__":
    asyncio.run(main()) 