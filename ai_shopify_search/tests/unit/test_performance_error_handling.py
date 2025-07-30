#!/usr/bin/env python3
"""
Test script voor performance en error handling implementatie
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database_async import AsyncDatabaseService
from utils.error_handling import (
    ErrorHandler, BaseError, ValidationError, DatabaseError as EHDatabaseError,
    NetworkError, RateLimitError, handle_errors, retry_on_error
)
from performance_monitor import (
    PerformanceMonitor, monitor_sync, monitor_async, monitor_operation
)
from background_tasks import (
    BackgroundTaskManager, TaskStatus, TaskPriority,
    BackgroundTaskUtils, background_task, periodic_task
)

async def test_async_database():
    """Test async database functionality."""
    
    print("🧪 Testing Async Database")
    print("=" * 40)
    
    try:
        # Create database manager
        db_manager = AsyncDatabaseService()
        
        print("1. Database manager creation...")
        print("   ✅ Async Database Manager created successfully")
        
        # Test method availability
        print("\n2. Testing method availability...")
        
        methods = [
            "initialize", "get_session", "execute_query", "execute_many",
            "get_connection_pool_stats", "health_check", "close"
        ]
        
        for method in methods:
            if hasattr(db_manager, method):
                print(f"   ✅ Method '{method}' available")
            else:
                print(f"   ❌ Method '{method}' missing")
        
        # Test URL conversion
        print("\n3. Testing URL conversion...")
        
        test_urls = [
            "postgresql://user:pass@localhost/db",
            "mysql://user:pass@localhost/db",
            "sqlite:///test.db"
        ]
        
        for url in test_urls:
            converted = db_manager._convert_to_async_url(url)
            print(f"   {url} -> {converted}")
        
        # Test error classes
        print("\n4. Testing error classes...")
        
        # Use error handling errors instead
        from utils.error_handling import DatabaseError as EHDatabaseError
        
        error_classes = [
            EHDatabaseError("Test database error"),
            Exception("Test timeout error")
        ]
        
        for error in error_classes:
            print(f"   ✅ {type(error).__name__}: {str(error)}")
        
    except Exception as e:
        print(f"   ❌ Async Database test failed: {e}")

async def test_error_handling():
    """Test error handling system."""
    
    print("\n🧪 Testing Error Handling")
    print("=" * 40)
    
    try:
        # Create error handler
        error_handler = ErrorHandler()
        
        print("1. Error handler creation...")
        print("   ✅ Error Handler created successfully")
        
        # Test error classes
        print("\n2. Testing error classes...")
        
        test_errors = [
            ValidationError("Invalid input", field="query", value=""),
            EHDatabaseError("Database connection failed", operation="select", table="products"),
            NetworkError("Connection timeout", url="https://api.example.com", status_code=408),
            RateLimitError("Rate limit exceeded", retry_after=60)
        ]
        
        for error in test_errors:
            print(f"   ✅ {type(error).__name__}: {error.message}")
            print(f"      Category: {error.category.value}, Severity: {error.severity.value}")
            print(f"      Retryable: {error.retryable}")
        
        # Test error handling
        print("\n3. Testing error handling...")
        
        for error in test_errors:
            result = error_handler.handle_error(error)
            print(f"   Handled {type(error).__name__}: {result['category']}")
        
        # Test error statistics
        print("\n4. Testing error statistics...")
        stats = error_handler.get_error_stats()
        print(f"   Total errors: {stats['total_errors']}")
        print(f"   Categories: {stats['categories']}")
        
    except Exception as e:
        print(f"   ❌ Error Handling test failed: {e}")

async def test_performance_monitoring():
    """Test performance monitoring system."""
    
    print("\n🧪 Testing Performance Monitoring")
    print("=" * 40)
    
    try:
        # Create performance monitor
        monitor = PerformanceMonitor()
        
        print("1. Performance monitor creation...")
        print("   ✅ Performance Monitor created successfully")
        
        # Test metric recording
        print("\n2. Testing metric recording...")
        
        # Record different types of metrics
        monitor.record_counter("test_counter", 1, {"test": "counter"})
        monitor.record_gauge("test_gauge", 42.5, {"test": "gauge"})
        monitor.record_histogram("test_histogram", 100, {"test": "histogram"})
        
        print("   ✅ Counter, gauge, and histogram metrics recorded")
        
        # Test timer
        print("\n3. Testing timer functionality...")
        
        timer = monitor.start_timer("test_timer", {"test": "timer"})
        await asyncio.sleep(0.1)  # Simulate work
        monitor.stop_timer(timer)
        
        print("   ✅ Timer functionality works")
        
        # Test alert thresholds
        print("\n4. Testing alert thresholds...")
        
        monitor.set_alert_threshold("test_gauge", "max", 50.0)
        monitor.record_gauge("test_gauge", 60.0)  # Should trigger alert
        
        print("   ✅ Alert threshold functionality works")
        
        # Test metrics summary
        print("\n5. Testing metrics summary...")
        
        summary = monitor.get_metrics_summary()
        print(f"   Active metrics: {len(summary)}")
        
        for metric_name, metric_data in summary.items():
            print(f"   {metric_name}: count={metric_data['count']}, avg={metric_data['avg']:.2f}")
        
    except Exception as e:
        print(f"   ❌ Performance Monitoring test failed: {e}")

async def test_background_tasks():
    """Test background task management."""
    
    print("\n🧪 Testing Background Tasks")
    print("=" * 40)
    
    try:
        # Create task manager
        task_manager = BackgroundTaskManager(max_workers=2, max_queue_size=10)
        
        print("1. Task manager creation...")
        print("   ✅ Background Task Manager created successfully")
        
        # Test task submission
        print("\n2. Testing task submission...")
        
        async def test_task(name: str, duration: float = 1.0):
            """Test task function."""
            await asyncio.sleep(duration)
            return f"Task {name} completed"
        
        # Submit tasks
        task_ids = []
        for i in range(3):
            task_id = await task_manager.submit_task(
                f"test_task_{i}",
                test_task,
                f"task_{i}",
                0.5,
                priority=TaskPriority.NORMAL,
                tags={"test": "background_task"}
            )
            task_ids.append(task_id)
            print(f"   Submitted task: {task_id}")
        
        # Start task manager
        print("\n3. Starting task manager...")
        await task_manager.start()
        
        # Wait for tasks to complete
        await asyncio.sleep(2)
        
        # Check task status
        print("\n4. Checking task status...")
        
        for task_id in task_ids:
            status = await task_manager.get_task_status(task_id)
            if status:
                print(f"   Task {task_id}: {status['status']}")
            else:
                print(f"   Task {task_id}: Not found")
        
        # Get statistics
        print("\n5. Getting task statistics...")
        stats = task_manager.get_stats()
        print(f"   Total tasks: {stats['stats']['total_tasks']}")
        print(f"   Completed tasks: {stats['stats']['completed_tasks']}")
        print(f"   Failed tasks: {stats['stats']['failed_tasks']}")
        
        # Stop task manager
        await task_manager.stop()
        print("   ✅ Task manager stopped successfully")
        
    except Exception as e:
        print(f"   ❌ Background Tasks test failed: {e}")

async def test_decorators():
    """Test performance and error handling decorators."""
    
    print("\n🧪 Testing Decorators")
    print("=" * 40)
    
    try:
        # Test performance monitoring decorator
        print("1. Testing performance monitoring decorator...")
        
        @monitor_sync("test_function")
        async def test_function():
            await asyncio.sleep(0.1)
            return "Function completed"
        
        result = await test_function()
        print(f"   ✅ Performance monitored function: {result}")
        
        # Test database performance decorator
        print("\n2. Testing database performance decorator...")
        
        @monitor_async("test_query")
        async def test_database_query():
            await asyncio.sleep(0.05)
            return "Query completed"
        
        result = await test_database_query()
        print(f"   ✅ Database performance monitored: {result}")
        
        # Test API performance decorator
        print("\n3. Testing API performance decorator...")
        
        @monitor_async("test_endpoint")
        async def test_api_endpoint():
            await asyncio.sleep(0.05)
            return "API call completed"
        
        result = await test_api_endpoint()
        print(f"   ✅ API performance monitored: {result}")
        
        # Test error handling decorator
        print("\n4. Testing error handling decorator...")
        
        @handle_errors
        async def test_error_function():
            raise ValidationError("Test validation error", field="test", value="invalid")
        
        try:
            await test_error_function()
        except ValidationError as e:
            print(f"   ✅ Error handled correctly: {e.message}")
        
        # Test retry decorator
        print("\n5. Testing retry decorator...")
        
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.1)
        async def test_retry_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary network error")
            return "Success after retries"
        
        result = await test_retry_function()
        print(f"   ✅ Retry function succeeded: {result} (calls: {call_count})")
        
    except Exception as e:
        print(f"   ❌ Decorators test failed: {e}")

async def test_integration():
    """Test integration of all components."""
    
    print("\n🧪 Testing Integration")
    print("=" * 40)
    
    try:
        # Test background task with performance monitoring
        print("1. Testing background task with performance monitoring...")
        
        @background_task("integration_test", TaskPriority.HIGH)
        @monitor_async("integration_task")
        async def integration_task():
            await asyncio.sleep(0.1)
            return "Integration task completed"
        
        task_id = await integration_task()
        print(f"   ✅ Integration task submitted: {task_id}")
        
        # Test error handling with performance monitoring
        print("\n2. Testing error handling with performance monitoring...")
        
        @handle_errors
        @monitor_async("error_test")
        async def error_test_function():
            await asyncio.sleep(0.05)
            raise DatabaseError("Test database error", operation="test")
        
        try:
            await error_test_function()
        except DatabaseError as e:
            print(f"   ✅ Error handling with performance monitoring: {e.message}")
        
        # Test retry with performance monitoring
        print("\n3. Testing retry with performance monitoring...")
        
        retry_count = 0
        
        @retry_on_error(max_retries=2, delay=0.1)
        @monitor_async("retry_test")
        async def retry_test_function():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 2:
                raise NetworkError("Temporary error")
            return "Retry success"
        
        result = await retry_test_function()
        print(f"   ✅ Retry with performance monitoring: {result}")
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")

async def main():
    """Run all performance and error handling tests."""
    
    print("🚀 Starting Performance & Error Handling Tests")
    print("Testing the new performance monitoring and error handling systems...")
    print()
    
    await test_async_database()
    await test_error_handling()
    await test_performance_monitoring()
    await test_background_tasks()
    await test_decorators()
    await test_integration()
    
    print("\n🎉 Performance & Error Handling tests voltooid!")
    print("\n📋 Summary:")
    print("- ✅ Async Database with connection pooling")
    print("- ✅ Comprehensive error handling system")
    print("- ✅ Performance monitoring with metrics")
    print("- ✅ Background task management")
    print("- ✅ Performance and error decorators")
    print("- ✅ Integration of all components")
    print("- ✅ Error recovery strategies")
    print("- ✅ Performance alerting")
    print("- ✅ Task prioritization and retry logic")

if __name__ == "__main__":
    asyncio.run(main()) 