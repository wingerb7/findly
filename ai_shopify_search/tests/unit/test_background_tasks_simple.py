#!/usr/bin/env python3
"""
Simple tests for background_tasks.py - only testing what actually exists.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from background_tasks import (
    BackgroundTask, BackgroundTaskManager, BackgroundTaskUtils,
    TaskStatus, TaskPriority, background_task, periodic_task
)

class TestBackgroundTask:
    """Test BackgroundTask dataclass."""
    
    def test_background_task_creation(self):
        """Test creating a background task."""
        def test_func():
            return "test"
        
        task = BackgroundTask(
            id="test_123",
            name="test_task",
            func=test_func
        )
        
        assert task.id == "test_123"
        assert task.name == "test_task"
        assert task.func == test_func
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.retry_count == 0
        assert task.max_retries == 3

class TestBackgroundTaskManager:
    """Test BackgroundTaskManager class."""
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test task manager initialization."""
        manager = BackgroundTaskManager(max_workers=5, max_queue_size=100)
        
        assert manager.max_workers == 5
        assert manager.max_queue_size == 100
        assert not manager.running
        assert len(manager.tasks) == 0
        assert len(manager.workers) == 0
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Test starting and stopping the task manager."""
        manager = BackgroundTaskManager(max_workers=2)
        
        # Start manager
        await manager.start()
        assert manager.running
        assert len(manager.workers) == 2
        
        # Stop manager
        await manager.stop()
        assert not manager.running
    
    @pytest.mark.asyncio
    async def test_submit_task(self):
        """Test submitting a task."""
        manager = BackgroundTaskManager(max_workers=1)
        await manager.start()
        
        async def test_func():
            return "success"
        
        task_id = await manager.submit_task(
            name="test_task",
            func=test_func,
            priority=TaskPriority.HIGH
        )
        
        assert task_id in manager.tasks
        assert manager.tasks[task_id].name == "test_task"
        assert manager.tasks[task_id].priority == TaskPriority.HIGH
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_task_status(self):
        """Test getting task status."""
        manager = BackgroundTaskManager(max_workers=1)
        await manager.start()
        
        async def test_func():
            return "success"
        
        task_id = await manager.submit_task("test_task", test_func)
        
        status = await manager.get_task_status(task_id)
        assert status is not None
        assert status["name"] == "test_task"
        assert status["status"] == TaskStatus.PENDING.value
        
        # Test non-existent task
        assert await manager.get_task_status("non_existent") is None
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test canceling a task."""
        manager = BackgroundTaskManager(max_workers=1)
        await manager.start()
        
        async def test_func():
            await asyncio.sleep(10)  # Long running task
        
        task_id = await manager.submit_task("test_task", test_func)
        
        # Cancel the task
        success = await manager.cancel_task(task_id)
        assert success
        
        # Verify task is cancelled
        status = await manager.get_task_status(task_id)
        assert status["status"] == TaskStatus.CANCELLED.value
        
        # Test canceling non-existent task
        assert not await manager.cancel_task("non_existent")
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting manager statistics."""
        manager = BackgroundTaskManager(max_workers=2)
        
        stats = manager.get_stats()
        assert "running" in stats
        assert "max_workers" in stats
        assert "stats" in stats
        assert "task_status_counts" in stats
        assert stats["max_workers"] == 2

class TestBackgroundTaskUtils:
    """Test BackgroundTaskUtils class."""
    
    @pytest.mark.asyncio
    async def test_submit_data_cleanup_task(self):
        """Test submitting data cleanup task."""
        with patch('background_tasks.background_task_manager') as mock_manager:
            mock_manager.submit_task = AsyncMock(return_value="task_123")
            
            task_id = await BackgroundTaskUtils.submit_data_cleanup_task()
            
            assert task_id == "task_123"
            mock_manager.submit_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_cache_warmup_task(self):
        """Test submitting cache warmup task."""
        with patch('background_tasks.background_task_manager') as mock_manager:
            mock_manager.submit_task = AsyncMock(return_value="task_456")
            
            task_id = await BackgroundTaskUtils.submit_cache_warmup_task()
            
            assert task_id == "task_456"
            mock_manager.submit_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_bulk_operation_task(self):
        """Test submitting bulk operation task."""
        with patch('background_tasks.background_task_manager') as mock_manager:
            mock_manager.submit_task = AsyncMock(return_value="task_789")
            
            data = [{"id": 1}, {"id": 2}]
            task_id = await BackgroundTaskUtils.submit_bulk_operation_task("test_op", data)
            
            assert task_id == "task_789"
            mock_manager.submit_task.assert_called_once()

class TestDecorators:
    """Test decorators."""
    
    @pytest.mark.asyncio
    async def test_background_task_decorator(self):
        """Test @background_task decorator."""
        with patch('background_tasks.background_task_manager') as mock_manager:
            mock_manager.submit_task = AsyncMock(return_value="task_123")
            
            @background_task("decorated_task", TaskPriority.HIGH)
            async def test_func(x, y):
                return x + y
            
            result = await test_func(5, 3)
            
            assert result == "task_123"
            mock_manager.submit_task.assert_called_once()
    
    def test_periodic_task_decorator(self):
        """Test @periodic_task decorator."""
        from datetime import timedelta
        
        @periodic_task(timedelta(minutes=5), "test_periodic")
        async def test_func():
            return "periodic"
        
        # Decorator should return a function
        assert callable(test_func)

class TestTaskLifecycle:
    """Test complete task lifecycle."""
    
    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self):
        """Test a complete task lifecycle."""
        manager = BackgroundTaskManager(max_workers=1)
        await manager.start()
        
        # Submit a simple task
        async def simple_task():
            return "completed"
        
        task_id = await manager.submit_task("simple", simple_task)
        
        # Wait a bit for task to complete
        await asyncio.sleep(0.1)
        
        # Check status
        status = await manager.get_task_status(task_id)
        assert status is not None
        
        await manager.stop()

class TestErrorScenarios:
    """Test error scenarios."""
    
    @pytest.mark.asyncio
    async def test_manager_already_running(self):
        """Test starting manager that's already running."""
        manager = BackgroundTaskManager(max_workers=1)
        await manager.start()
        
        # Try to start again
        await manager.start()  # Should not raise error
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_stop_manager_not_running(self):
        """Test stopping manager that's not running."""
        manager = BackgroundTaskManager(max_workers=1)
        
        # Try to stop when not running
        await manager.stop()  # Should not raise error
    
    @pytest.mark.asyncio
    async def test_task_with_empty_name(self):
        """Test submitting task with empty name."""
        manager = BackgroundTaskManager(max_workers=1)
        await manager.start()
        
        async def test_func():
            return "test"
        
        # This should work (empty name is allowed)
        task_id = await manager.submit_task("", test_func)
        assert task_id in manager.tasks
        
        await manager.stop() 