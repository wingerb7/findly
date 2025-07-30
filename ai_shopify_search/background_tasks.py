#!/usr/bin/env python3
"""
Background task management system for async task processing.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import traceback

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class BackgroundTask:
    """Background task definition."""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)

class BackgroundTaskManager:
    """Background task manager with priority queue and monitoring."""
    
    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.tasks: Dict[str, BackgroundTask] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_tasks": 0,
            "running_tasks": 0
        }
    
    async def start(self):
        """Start the background task manager."""
        if self.running:
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Background task manager started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the background task manager."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Background task manager stopped")
    
    async def submit_task(
        self,
        name: str,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        tags: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for background execution.
        
        Args:
            name: Task name
            func: Function to execute
            *args: Function arguments
            priority: Task priority
            timeout: Task timeout in seconds
            max_retries: Maximum retry attempts
            tags: Task tags for categorization
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        task_id = f"{name}_{int(time.time() * 1000)}"
        
        task = BackgroundTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            tags=tags or {}
        )
        
        self.tasks[task_id] = task
        self.stats["total_tasks"] += 1
        self.stats["pending_tasks"] += 1
        
        # Add to priority queue (lower priority number = higher priority)
        priority_value = -priority.value  # Negative for correct ordering
        await self.task_queue.put((priority_value, task_id))
        
        logger.info(f"Task submitted: {task_id} ({name}) with priority {priority.name}")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and details."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.name,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "result": task.result,
            "error": task.error,
            "tags": task.tags
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self.stats["pending_tasks"] -= 1
            logger.info(f"Task cancelled: {task_id}")
            return True
        
        return False
    
    async def _worker(self, worker_name: str):
        """Worker task that processes background tasks."""
        logger.info(f"Worker {worker_name} started")
        
        while self.running:
            # Get task from queue with timeout
            try:
                priority, task_id = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            
            if task_id not in self.tasks:
                continue
            
            task = self.tasks[task_id]
            
            # Skip cancelled tasks
            if task.status == TaskStatus.CANCELLED:
                continue
            
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.stats["pending_tasks"] -= 1
            self.stats["running_tasks"] += 1
            
            logger.info(f"Worker {worker_name} processing task: {task_id}")
            
            # Execute task
            try:
                if asyncio.iscoroutinefunction(task.func):
                    # Async function
                    if task.timeout:
                        result = await asyncio.wait_for(
                            task.func(*task.args, **task.kwargs),
                            timeout=task.timeout
                        )
                    else:
                        result = await task.func(*task.args, **task.kwargs)
                else:
                    # Sync function - run in thread pool
                    loop = asyncio.get_event_loop()
                    if task.timeout:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(
                                self.executor,
                                task.func,
                                *task.args,
                                **task.kwargs
                            ),
                            timeout=task.timeout
                        )
                    else:
                        result = await loop.run_in_executor(
                            self.executor,
                            task.func,
                            *task.args,
                            **task.kwargs
                        )
                
                # Task completed successfully
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                self.stats["completed_tasks"] += 1
                
                logger.info(f"Task completed: {task_id}")
                
            except asyncio.TimeoutError:
                # Task timed out
                task.error = f"Task timed out after {task.timeout} seconds"
                await self._handle_task_failure(task, worker_name)
                
            except Exception as e:
                # Task failed
                task.error = str(e)
                await self._handle_task_failure(task, worker_name)
            
            finally:
                self.stats["running_tasks"] -= 1
                self.task_queue.task_done()
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _handle_task_failure(self, task: BackgroundTask, worker_name: str):
        """Handle task failure with retry logic."""
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Retry task
            logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.error = None
            self.stats["pending_tasks"] += 1
            
            # Add back to queue with lower priority
            priority_value = -task.priority.value - 1  # Lower priority for retries
            await self.task_queue.put((priority_value, task.id))
        else:
            # Max retries exceeded
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.stats["failed_tasks"] += 1
            
            logger.error(f"Task {task.id} failed after {task.max_retries} retries: {task.error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        return {
            "running": self.running,
            "max_workers": self.max_workers,
            "active_workers": len([w for w in self.workers if not w.done()]),
            "queue_size": self.task_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "stats": self.stats.copy(),
            "task_status_counts": self._get_task_status_counts()
        }
    
    def _get_task_status_counts(self) -> Dict[str, int]:
        """Get counts of tasks by status."""
        counts = {status.value: 0 for status in TaskStatus}
        for task in self.tasks.values():
            counts[task.status.value] += 1
        return counts
    
    async def cleanup_completed_tasks(self, max_age: timedelta = timedelta(hours=24)):
        """Clean up old completed tasks to prevent memory issues."""
        cutoff_time = datetime.now() - max_age
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

# Global background task manager instance
background_task_manager = BackgroundTaskManager()

# Background task utilities
class BackgroundTaskUtils:
    """Utility functions for background tasks."""
    
    @staticmethod
    async def submit_data_cleanup_task():
        """Submit a data cleanup task."""
        from services.analytics_service import AnalyticsService
        
        async def cleanup_analytics_data():
            try:
                # This would normally get the database session
                # For now, we'll just log the task
                logger.info("Running analytics data cleanup task")
                await asyncio.sleep(5)  # Simulate work
                logger.info("Analytics data cleanup completed")
            except Exception as e:
                logger.error(f"Analytics data cleanup failed: {e}")
                raise
        
        return await background_task_manager.submit_task(
            name="analytics_cleanup",
            func=cleanup_analytics_data,
            priority=TaskPriority.LOW,
            tags={"type": "maintenance", "component": "analytics"}
        )
    
    @staticmethod
    async def submit_cache_warmup_task():
        """Submit a cache warmup task."""
        async def warmup_cache():
            try:
                logger.info("Running cache warmup task")
                # Simulate cache warmup
                await asyncio.sleep(10)
                logger.info("Cache warmup completed")
            except Exception as e:
                logger.error(f"Cache warmup failed: {e}")
                raise
        
        return await background_task_manager.submit_task(
            name="cache_warmup",
            func=warmup_cache,
            priority=TaskPriority.NORMAL,
            tags={"type": "maintenance", "component": "cache"}
        )
    
    @staticmethod
    async def submit_performance_monitoring_task():
        """Submit a performance monitoring task."""
        from performance_monitor import PerformanceUtils
        
        async def monitor_performance():
            try:
                logger.info("Running performance monitoring task")
                PerformanceUtils.record_memory_usage()
                PerformanceUtils.record_cpu_usage()
                logger.info("Performance monitoring completed")
            except Exception as e:
                logger.error(f"Performance monitoring failed: {e}")
                raise
        
        return await background_task_manager.submit_task(
            name="performance_monitoring",
            func=monitor_performance,
            priority=TaskPriority.NORMAL,
            tags={"type": "monitoring", "component": "performance"}
        )
    
    @staticmethod
    async def submit_bulk_operation_task(operation: str, data: List[Dict[str, Any]]):
        """Submit a bulk operation task."""
        async def execute_bulk_operation():
            try:
                logger.info(f"Running bulk {operation} task with {len(data)} items")
                # Simulate bulk operation
                await asyncio.sleep(len(data) * 0.01)  # 10ms per item
                logger.info(f"Bulk {operation} completed")
            except Exception as e:
                logger.error(f"Bulk {operation} failed: {e}")
                raise
        
        return await background_task_manager.submit_task(
            name=f"bulk_{operation}",
            func=execute_bulk_operation,
            priority=TaskPriority.HIGH,
            tags={"type": "bulk_operation", "operation": operation}
        )

# Background task decorators
def background_task(name: str, priority: TaskPriority = TaskPriority.NORMAL):
    """Decorator to run a function as a background task."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            task_id = await background_task_manager.submit_task(
                name=name,
                func=func,
                *args,
                priority=priority,
                **kwargs
            )
            return task_id
        
        return wrapper
    return decorator

def periodic_task(interval: timedelta, name: str):
    """Decorator to run a function periodically as a background task."""
    def decorator(func):
        async def periodic_wrapper():
            while True:
                try:
                    await func()
                except Exception as e:
                    logger.error(f"Periodic task {name} failed: {e}")
                
                await asyncio.sleep(interval.total_seconds())
        
        return periodic_wrapper
    return decorator

# Initialize background task manager
async def start_background_tasks():
    """Start the background task manager and schedule periodic tasks."""
    await background_task_manager.start()
    
    # Schedule periodic tasks
    @periodic_task(timedelta(hours=1), "data_cleanup")
    async def scheduled_data_cleanup():
        await BackgroundTaskUtils.submit_data_cleanup_task()
    
    @periodic_task(timedelta(minutes=5), "performance_monitoring")
    async def scheduled_performance_monitoring():
        await BackgroundTaskUtils.submit_performance_monitoring_task()
    
    # Start periodic tasks
    asyncio.create_task(scheduled_data_cleanup())
    asyncio.create_task(scheduled_performance_monitoring())
    
    logger.info("Background tasks started")

async def stop_background_tasks():
    """Stop the background task manager."""
    await background_task_manager.stop()
    logger.info("Background tasks stopped") 