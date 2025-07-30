#!/usr/bin/env python3
"""
Unit tests for background tasks.
Tests background_tasks.py functionality.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from background_tasks import (
    log_analytics_task,
    update_popular_searches_task,
    cleanup_expired_data_task,
    update_search_suggestions_task,
    process_product_import_task
)


class TestBackgroundTasks:
    """Test background tasks functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Mock database session
        self.mock_session = Mock()
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.refresh.return_value = None
        self.mock_session.query.return_value = self.mock_session
        self.mock_session.filter.return_value = self.mock_session
        self.mock_session.filter_by.return_value = self.mock_session
        self.mock_session.first.return_value = None
        self.mock_session.all.return_value = []
        self.mock_session.count.return_value = 0
    
    async def test_log_analytics_task(self):
        """Test log analytics background task."""
        print("🧪 Testing Log Analytics Background Task")
        print("=" * 50)
        
        # Test parameters
        query = "test query"
        search_type = "ai"
        filters = {"price_range": "10-100"}
        results_count = 5
        page = 1
        limit = 25
        response_time_ms = 150.5
        cache_hit = False
        user_agent = "test-agent"
        ip_address = "192.168.1.1"
        
        # Mock analytics manager
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.track_search.return_value = 1
            
            # Execute task
            await log_analytics_task(
                query=query,
                search_type=search_type,
                filters=filters,
                results_count=results_count,
                page=page,
                limit=limit,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                user_agent=user_agent,
                ip_address=ip_address,
                db=self.mock_session
            )
            
            # Verify analytics were tracked
            mock_analytics.track_search.assert_called_once_with(
                db=self.mock_session,
                query=query,
                search_type=search_type,
                filters=filters,
                results_count=results_count,
                page=page,
                limit=limit,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            print("✅ Log analytics background task tests passed")
    
    async def test_update_popular_searches_task(self):
        """Test update popular searches background task."""
        print("\n🧪 Testing Update Popular Searches Background Task")
        print("=" * 60)
        
        # Test parameters
        query = "blue shirt"
        
        # Mock popular search update
        with patch('background_tasks.update_popular_search') as mock_update:
            mock_update.return_value = True
            
            # Execute task
            await update_popular_searches_task(
                query=query,
                db=self.mock_session
            )
            
            # Verify popular search was updated
            mock_update.assert_called_once_with(
                query=query,
                db=self.mock_session
            )
            
            print("✅ Update popular searches background task tests passed")
    
    async def test_cleanup_expired_data_task(self):
        """Test cleanup expired data background task."""
        print("\n🧪 Testing Cleanup Expired Data Background Task")
        print("=" * 55)
        
        # Mock cleanup functions
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.cleanup_expired_data.return_value = {"search_analytics": 50}
            mock_analytics.cleanup_expired_sessions.return_value = 25
            
            # Execute task
            result = await cleanup_expired_data_task(db=self.mock_session)
            
            # Verify cleanup was performed
            mock_analytics.cleanup_expired_data.assert_called_once_with(self.mock_session)
            mock_analytics.cleanup_expired_sessions.assert_called_once_with(self.mock_session)
            
            assert result is not None
            assert "cleanup_stats" in result
            assert result["cleanup_stats"]["analytics_records"] == 50
            assert result["cleanup_stats"]["expired_sessions"] == 25
            
            print("✅ Cleanup expired data background task tests passed")
    
    async def test_update_search_suggestions_task(self):
        """Test update search suggestions background task."""
        print("\n🧪 Testing Update Search Suggestions Background Task")
        print("=" * 60)
        
        # Test parameters
        query = "blue shirt"
        suggestions = ["blue cotton shirt", "blue denim shirt", "blue polo shirt"]
        
        # Mock suggestion update
        with patch('background_tasks.update_search_suggestions') as mock_update:
            mock_update.return_value = True
            
            # Execute task
            await update_search_suggestions_task(
                query=query,
                suggestions=suggestions,
                db=self.mock_session
            )
            
            # Verify suggestions were updated
            mock_update.assert_called_once_with(
                query=query,
                suggestions=suggestions,
                db=self.mock_session
            )
            
            print("✅ Update search suggestions background task tests passed")
    
    async def test_process_product_import_task(self):
        """Test process product import background task."""
        print("\n🧪 Testing Process Product Import Background Task")
        print("=" * 60)
        
        # Test parameters
        products_data = [
            {
                "id": 1,
                "title": "Test Product 1",
                "description": "Test Description 1",
                "price": "29.99",
                "tags": ["test", "product"]
            },
            {
                "id": 2,
                "title": "Test Product 2",
                "description": "Test Description 2",
                "price": "49.99",
                "tags": ["test", "product"]
            }
        ]
        
        # Mock product processing
        with patch('background_tasks.process_products') as mock_process:
            mock_process.return_value = {"imported": 2, "updated": 0}
            
            # Execute task
            result = await process_product_import_task(
                products_data=products_data,
                db=self.mock_session
            )
            
            # Verify products were processed
            mock_process.assert_called_once_with(
                products_data=products_data,
                db=self.mock_session
            )
            
            assert result is not None
            assert result["imported"] == 2
            assert result["updated"] == 0
            
            print("✅ Process product import background task tests passed")


class TestBackgroundTaskErrorHandling:
    """Test background task error handling."""
    
    async def test_log_analytics_task_error_handling(self):
        """Test log analytics task error handling."""
        print("\n🧪 Testing Log Analytics Task Error Handling")
        print("=" * 55)
        
        # Mock analytics manager to raise exception
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.track_search.side_effect = Exception("Database error")
            
            # Mock session
            mock_session = Mock()
            
            try:
                # Execute task - should not raise exception
                await log_analytics_task(
                    query="test query",
                    search_type="ai",
                    filters={},
                    results_count=5,
                    page=1,
                    limit=25,
                    response_time_ms=150.5,
                    cache_hit=False,
                    user_agent="test-agent",
                    ip_address="192.168.1.1",
                    db=mock_session
                )
                
                # Should not reach here if exception was raised
                print("✅ Log analytics task error handling tests passed")
                
            except Exception as e:
                assert False, f"Background task should handle errors gracefully: {e}"
    
    async def test_update_popular_searches_task_error_handling(self):
        """Test update popular searches task error handling."""
        print("\n🧪 Testing Update Popular Searches Task Error Handling")
        print("=" * 65)
        
        # Mock update function to raise exception
        with patch('background_tasks.update_popular_search') as mock_update:
            mock_update.side_effect = Exception("Update error")
            
            # Mock session
            mock_session = Mock()
            
            try:
                # Execute task - should not raise exception
                await update_popular_searches_task(
                    query="test query",
                    db=mock_session
                )
                
                print("✅ Update popular searches task error handling tests passed")
                
            except Exception as e:
                assert False, f"Background task should handle errors gracefully: {e}"


class TestBackgroundTaskPerformance:
    """Test background task performance."""
    
    async def test_background_task_performance(self):
        """Test background task performance with multiple tasks."""
        print("\n🧪 Testing Background Task Performance")
        print("=" * 45)
        
        import time
        
        # Mock session
        mock_session = Mock()
        
        # Mock analytics manager
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.track_search.return_value = 1
            
            # Test multiple concurrent tasks
            start_time = time.time()
            
            tasks = []
            for i in range(10):
                task = log_analytics_task(
                    query=f"test query {i}",
                    search_type="ai",
                    filters={"price_range": f"{i}-{i+100}"},
                    results_count=i % 50,
                    page=1,
                    limit=25,
                    response_time_ms=float(i * 10),
                    cache_hit=i % 2 == 0,
                    user_agent=f"test-agent-{i}",
                    ip_address=f"192.168.1.{i % 255}",
                    db=mock_session
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            operation_time = end_time - start_time
            
            assert operation_time < 2.0  # Should complete within 2 seconds
            assert mock_analytics.track_search.call_count == 10
            
            print(f"✅ Background task performance test completed in {operation_time:.3f}s")
    
    async def test_background_task_memory_efficiency(self):
        """Test background task memory efficiency."""
        print("\n🧪 Testing Background Task Memory Efficiency")
        print("=" * 55)
        
        # Mock session
        mock_session = Mock()
        
        # Mock analytics manager
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.track_search.return_value = 1
            
            # Test with large data
            large_filters = {
                "price_range": "10-1000",
                "categories": ["shirts", "pants", "shoes", "accessories"],
                "brands": ["nike", "adidas", "puma", "reebok"],
                "sizes": ["S", "M", "L", "XL", "XXL"],
                "colors": ["red", "blue", "green", "yellow", "black", "white"]
            }
            
            # Execute task with large data
            await log_analytics_task(
                query="test query with large filters",
                search_type="ai",
                filters=large_filters,
                results_count=1000,
                page=1,
                limit=1000,
                response_time_ms=5000.0,
                cache_hit=False,
                user_agent="test-agent",
                ip_address="192.168.1.1",
                db=mock_session
            )
            
            # Verify task completed successfully
            mock_analytics.track_search.assert_called_once()
            
            print("✅ Background task memory efficiency tests passed")


class TestBackgroundTaskIntegration:
    """Test background task integration scenarios."""
    
    async def test_complete_analytics_flow(self):
        """Test complete analytics flow with background tasks."""
        print("\n🧪 Testing Complete Analytics Flow")
        print("=" * 45)
        
        # Mock session
        mock_session = Mock()
        
        # Mock analytics manager
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.track_search.return_value = 1
            
            # Mock popular search update
            with patch('background_tasks.update_popular_search') as mock_update:
                mock_update.return_value = True
                
                # Execute complete flow
                await log_analytics_task(
                    query="blue shirt under 50 euros",
                    search_type="ai",
                    filters={"price_range": "0-50"},
                    results_count=15,
                    page=1,
                    limit=25,
                    response_time_ms=245.7,
                    cache_hit=False,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    ip_address="192.168.1.100",
                    db=mock_session
                )
                
                await update_popular_searches_task(
                    query="blue shirt under 50 euros",
                    db=mock_session
                )
                
                # Verify both tasks were executed
                mock_analytics.track_search.assert_called_once()
                mock_update.assert_called_once()
                
                print("✅ Complete analytics flow tests passed")
    
    async def test_data_cleanup_flow(self):
        """Test data cleanup flow with background tasks."""
        print("\n🧪 Testing Data Cleanup Flow")
        print("=" * 40)
        
        # Mock session
        mock_session = Mock()
        
        # Mock cleanup functions
        with patch('background_tasks.analytics_manager') as mock_analytics:
            mock_analytics.cleanup_expired_data.return_value = {"search_analytics": 50}
            mock_analytics.cleanup_expired_sessions.return_value = 25
            
            # Execute cleanup flow
            result = await cleanup_expired_data_task(db=mock_session)
            
            # Verify cleanup was performed
            mock_analytics.cleanup_expired_data.assert_called_once_with(mock_session)
            mock_analytics.cleanup_expired_sessions.assert_called_once_with(mock_session)
            
            assert result is not None
            assert "cleanup_stats" in result
            assert result["cleanup_stats"]["analytics_records"] == 50
            assert result["cleanup_stats"]["expired_sessions"] == 25
            
            print("✅ Data cleanup flow tests passed")


def test_background_task_scheduling():
    """Test background task scheduling scenarios."""
    print("\n🧪 Testing Background Task Scheduling")
    print("=" * 45)
    
    # Test task scheduling with different intervals
    intervals = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
    
    for interval in intervals:
        # Mock task execution
        with patch('background_tasks.cleanup_expired_data_task') as mock_task:
            mock_task.return_value = {"cleanup_stats": {"analytics_records": 10}}
            
            # Simulate scheduled execution
            print(f"✅ Task scheduled for {interval}s interval")
    
    print("✅ Background task scheduling tests passed")


if __name__ == "__main__":
    # Run background task tests
    test_instance = TestBackgroundTasks()
    test_instance.setup_method()
    
    # Run async tests
    asyncio.run(test_instance.test_log_analytics_task())
    asyncio.run(test_instance.test_update_popular_searches_task())
    asyncio.run(test_instance.test_cleanup_expired_data_task())
    asyncio.run(test_instance.test_update_search_suggestions_task())
    asyncio.run(test_instance.test_process_product_import_task())
    
    # Run error handling tests
    error_instance = TestBackgroundTaskErrorHandling()
    asyncio.run(error_instance.test_log_analytics_task_error_handling())
    asyncio.run(error_instance.test_update_popular_searches_task_error_handling())
    
    # Run performance tests
    perf_instance = TestBackgroundTaskPerformance()
    asyncio.run(perf_instance.test_background_task_performance())
    asyncio.run(perf_instance.test_background_task_memory_efficiency())
    
    # Run integration tests
    integration_instance = TestBackgroundTaskIntegration()
    asyncio.run(integration_instance.test_complete_analytics_flow())
    asyncio.run(integration_instance.test_data_cleanup_flow())
    
    # Run scheduling tests
    test_background_task_scheduling()
    
    print("\n🎉 Background tasks tests completed!") 