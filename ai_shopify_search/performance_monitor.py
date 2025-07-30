"""
Performance monitoring service for tracking async operations and database performance.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data class."""
    
    operation_name: str
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Performance monitoring service."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance monitor."""
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "success_count": 0,
            "error_count": 0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "times": deque(maxlen=100)  # Keep last 100 times for percentiles
        })
        self._lock = asyncio.Lock()
    
    async def record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric."""
        async with self._lock:
            self.metrics_history.append(metric)
            
            # Update operation statistics
            stats = self.operation_stats[metric.operation_name]
            stats["count"] += 1
            stats["total_time"] += metric.execution_time
            stats["times"].append(metric.execution_time)
            
            if metric.success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1
            
            stats["min_time"] = min(stats["min_time"], metric.execution_time)
            stats["max_time"] = max(stats["max_time"], metric.execution_time)
    
    async def monitor_async_operation(
        self,
        operation_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Async context manager for monitoring operations."""
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            execution_time = time.time() - start_time
            metric = PerformanceMetrics(
                operation_name=operation_name,
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )
            await self.record_metric(metric)
    
    def monitor_sync_operation(
        self,
        operation_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Decorator for monitoring synchronous operations."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = False
                error_message = None
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    error_message = str(e)
                    raise
                finally:
                    execution_time = time.time() - start_time
                    metric = PerformanceMetrics(
                        operation_name=operation_name,
                        execution_time=execution_time,
                        success=success,
                        error_message=error_message,
                        metadata=metadata or {}
                    )
                    # For sync operations, we'll record metrics in a thread-safe way
                    asyncio.create_task(self.record_metric(metric))
            
            return wrapper
        return decorator
    
    def monitor_async_function(
        self,
        operation_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Decorator for monitoring asynchronous operations."""
        def decorator(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                success = False
                error_message = None
                
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    error_message = str(e)
                    raise
                finally:
                    execution_time = time.time() - start_time
                    metric = PerformanceMetrics(
                        operation_name=operation_name,
                        execution_time=execution_time,
                        success=success,
                        error_message=error_message,
                        metadata=metadata or {}
                    )
                    await self.record_metric(metric)
            
            return wrapper
        return decorator
    
    async def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific operation."""
        async with self._lock:
            if operation_name not in self.operation_stats:
                return {}
            
            stats = self.operation_stats[operation_name]
            times = list(stats["times"])
            
            if not times:
                return {}
            
            return {
                "operation_name": operation_name,
                "total_count": stats["count"],
                "success_count": stats["success_count"],
                "error_count": stats["error_count"],
                "success_rate": stats["success_count"] / stats["count"] if stats["count"] > 0 else 0,
                "total_time": stats["total_time"],
                "average_time": stats["total_time"] / stats["count"] if stats["count"] > 0 else 0,
                "min_time": stats["min_time"] if stats["min_time"] != float('inf') else 0,
                "max_time": stats["max_time"],
                "median_time": statistics.median(times),
                "p95_time": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                "p99_time": statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times)
            }
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations."""
        async with self._lock:
            return {
                operation_name: await self.get_operation_stats(operation_name)
                for operation_name in self.operation_stats.keys()
            }
    
    async def get_slow_operations(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Get operations that are slower than the threshold."""
        slow_operations = []
        
        for operation_name in self.operation_stats.keys():
            stats = await self.get_operation_stats(operation_name)
            if stats.get("average_time", 0) > threshold:
                slow_operations.append(stats)
        
        return sorted(slow_operations, key=lambda x: x.get("average_time", 0), reverse=True)
    
    async def get_error_prone_operations(self, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Get operations with high error rates."""
        error_prone_operations = []
        
        for operation_name in self.operation_stats.keys():
            stats = await self.get_operation_stats(operation_name)
            if stats.get("success_rate", 1.0) < (1.0 - threshold):
                error_prone_operations.append(stats)
        
        return sorted(error_prone_operations, key=lambda x: x.get("success_rate", 1.0))
    
    async def clear_history(self) -> None:
        """Clear performance history."""
        async with self._lock:
            self.metrics_history.clear()
            self.operation_stats.clear()
    
    async def get_recent_metrics(self, limit: int = 100) -> List[PerformanceMetrics]:
        """Get recent performance metrics."""
        async with self._lock:
            return list(self.metrics_history)[-limit:]
    
    async def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external monitoring."""
        async with self._lock:
            return {
                "timestamp": time.time(),
                "total_operations": len(self.metrics_history),
                "operation_stats": dict(self.operation_stats),
                "recent_metrics": [
                    {
                        "operation_name": metric.operation_name,
                        "execution_time": metric.execution_time,
                        "success": metric.success,
                        "error_message": metric.error_message,
                        "metadata": metric.metadata
                    }
                    for metric in list(self.metrics_history)[-50:]  # Last 50 metrics
                ]
            }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience decorators
def monitor_sync(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for monitoring synchronous functions."""
    return performance_monitor.monitor_sync_operation(operation_name, metadata)


def monitor_async(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for monitoring asynchronous functions."""
    return performance_monitor.monitor_async_function(operation_name, metadata)


@asynccontextmanager
async def monitor_operation(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for monitoring operations."""
    async with performance_monitor.monitor_async_operation(operation_name, metadata):
        yield 