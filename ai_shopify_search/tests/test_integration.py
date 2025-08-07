#!/usr/bin/env python3
"""
Integration tests for Findly AI Search API.
Converted from test_system.py to pytest format.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime
import httpx
from unittest.mock import Mock, patch

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30  # seconds


class TestFindlyIntegration:
    """Integration test suite for Findly AI Search API."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.base_url = BASE_URL
        self.session = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.test_results = []
        
        yield
        
        # Cleanup
        asyncio.create_task(self.session.aclose())
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        try:
            response = await self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
                assert data.get('status') == 'healthy'
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}")
                assert False, f"Health check failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_product_search(self):
        """Test AI-powered product search."""
        try:
            payload = {
                "query": "rode schoenen euro",
                "page": 1,
                "limit": 10,
                "similarity_threshold": 0.7
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/products/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get("results", []))
                self.log_test("Product Search", True, f"Results: {results_count} items")
                assert "results" in data
                assert "pagination" in data
            else:
                self.log_test("Product Search", False, f"Status: {response.status_code}")
                assert False, f"Product search failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Product Search", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_autocomplete(self):
        """Test autocomplete functionality."""
        try:
            response = await self.session.get(
                f"{self.base_url}/api/products/autocomplete",
                params={"query": "schoe", "limit": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestions_count = len(data.get("suggestions", []))
                self.log_test("Autocomplete", True, f"Suggestions: {suggestions_count}")
                assert "suggestions" in data
            else:
                self.log_test("Autocomplete", False, f"Status: {response.status_code}")
                assert False, f"Autocomplete failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Autocomplete", False, f"Error: {e}")
            raise
    

    
    @pytest.mark.asyncio
    async def test_ai_learning_health(self):
        """Test AI learning health check."""
        try:
            response = await self.session.get(f"{self.base_url}/api/ai-learning/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("AI Learning Health", True, f"Status: {data.get('status', 'unknown')}")
                assert "status" in data
            else:
                self.log_test("AI Learning Health", False, f"Status: {response.status_code}")
                assert False, f"AI learning health failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("AI Learning Health", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_transfer_learning(self):
        """Test transfer learning functionality."""
        try:
            payload = {
                "target_store_id": "test_store_123",
                "limit": 3
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/ai-learning/transfer-learning/similar-stores",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                similar_stores_count = len(data.get("similar_stores", []))
                self.log_test("Transfer Learning", True, f"Similar stores: {similar_stores_count}")
                assert "similar_stores" in data
            else:
                self.log_test("Transfer Learning", False, f"Status: {response.status_code}")
                assert False, f"Transfer learning failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Transfer Learning", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_knowledge_base(self):
        """Test knowledge base functionality."""
        try:
            payload = {
                "store_id": "test",
                "action": "build"
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/ai-learning/knowledge-base/build",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Knowledge Base", True, "Knowledge base built")
                assert "result" in data
            else:
                self.log_test("Knowledge Base", False, f"Status: {response.status_code}")
                assert False, f"Knowledge base failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Knowledge Base", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_benchmark_health(self):
        """Test benchmark health check."""
        try:
            response = await self.session.get(f"{self.base_url}/api/benchmark/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Benchmark Health", True, f"Status: {data.get('status', 'unknown')}")
                assert "status" in data
            else:
                self.log_test("Benchmark Health", False, f"Status: {response.status_code}")
                assert False, f"Benchmark health failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Benchmark Health", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_benchmark_metrics(self):
        """Test benchmark metrics endpoint."""
        try:
            response = await self.session.get(f"{self.base_url}/api/benchmark/metrics")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Benchmark Metrics", True, "Metrics retrieved")
                assert isinstance(data, dict)
            else:
                self.log_test("Benchmark Metrics", False, f"Status: {response.status_code}")
                assert False, f"Benchmark metrics failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Benchmark Metrics", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_feedback_submission(self):
        """Test feedback submission."""
        try:
            payload = {
                "query": "rode schoenen",
                "result_count": 10,
                "user_satisfaction": 5,
                "feedback_text": "Perfecte resultaten!"
            }
            
            response = await self.session.post(
                f"{self.base_url}/api/feedback/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Feedback Submission", True, "Feedback submitted")
                assert data.get("status") == "success"
            else:
                self.log_test("Feedback Submission", False, f"Status: {response.status_code}")
                assert False, f"Feedback submission failed with status {response.status_code}"
                
        except Exception as e:
            self.log_test("Feedback Submission", False, f"Error: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting by making many requests."""
        try:
            # Make multiple requests quickly
            responses = []
            for i in range(5):
                response = await self.session.post(
                    f"{self.base_url}/api/products/search",
                    json={"query": f"test query {i}", "page": 1, "limit": 1},
                    headers={"Content-Type": "application/json"}
                )
                responses.append(response.status_code)
            
            # Check if rate limiting is working
            if 429 in responses:
                self.log_test("Rate Limiting", True, "Rate limiting active")
            else:
                self.log_test("Rate Limiting", True, "All requests successful")
            
            # All requests should be successful or rate limited
            assert all(status in [200, 429] for status in responses)
                
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Error: {e}")
            raise
    
    def test_summary(self):
        """Generate test summary."""
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📊 Test Summary")
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "passed": passed,
                    "failed": total - passed,
                    "total": total,
                    "success_rate": success_rate
                },
                "results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        assert success_rate >= 80, f"Test success rate {success_rate:.1f}% is below 80% threshold"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 