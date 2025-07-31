#!/usr/bin/env python3
"""
Simple tests for metrics.py - only testing what actually exists.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from metrics import (
    MetricsCollector, metrics_collector,
    SEARCH_REQUESTS_TOTAL, SEARCH_RESPONSE_TIME, SEARCH_RESULTS_COUNT,
    CACHE_HIT_RATIO, ACTIVE_CONNECTIONS, REDIS_CONNECTIONS
)

class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        assert collector.search_metrics is not None
    
    def test_record_search_request_success(self):
        """Test successful search request recording."""
        collector = MetricsCollector()
        
        with patch('metrics.SEARCH_REQUESTS_TOTAL') as mock_counter:
            with patch('metrics.SEARCH_RESPONSE_TIME') as mock_histogram:
                with patch('metrics.SEARCH_RESULTS_COUNT') as mock_results:
                    with patch('metrics.CACHE_HIT_RATIO') as mock_cache:
                        with patch('metrics.logger') as mock_logger:
                            collector.record_search_request(
                                search_type="ai",
                                cache_hit=True,
                                response_time=0.5,
                                results_count=25
                            )
            
            # Verify metrics were called
            mock_counter.labels.assert_called_once_with(search_type="ai", cache_hit="True")
            mock_counter.labels().inc.assert_called_once()
            
            mock_histogram.labels.assert_called_once_with(search_type="ai")
            mock_histogram.labels().observe.assert_called_once_with(0.5)
            
            mock_results.labels.assert_called_once_with(search_type="ai")
            mock_results.labels().observe.assert_called_once_with(25)
            
            mock_cache.labels.assert_called_once_with(search_type="ai")
            mock_cache.labels().set.assert_called_once_with(1.0)
    
    def test_record_search_request_cache_miss(self):
        """Test search request recording with cache miss."""
        collector = MetricsCollector()
        
        with patch('metrics.SEARCH_REQUESTS_TOTAL') as mock_counter:
            with patch('metrics.SEARCH_RESPONSE_TIME') as mock_histogram:
                with patch('metrics.SEARCH_RESULTS_COUNT') as mock_results:
                    with patch('metrics.CACHE_HIT_RATIO') as mock_cache:
                        with patch('metrics.logger') as mock_logger:
                            collector.record_search_request(
                                search_type="basic",
                                cache_hit=False,
                                response_time=1.2,
                                results_count=50
                            )
            
            # Verify cache miss metrics
            mock_counter.labels.assert_called_once_with(search_type="basic", cache_hit="False")
            mock_cache.labels().set.assert_called_once_with(0.0)
    
    def test_record_search_request_error(self):
        """Test search request recording with error."""
        collector = MetricsCollector()
        
        with patch('metrics.SEARCH_REQUESTS_TOTAL') as mock_counter:
            mock_counter.labels.side_effect = Exception("Metrics error")
            with patch('metrics.logger') as mock_logger:
                # Should not raise exception
                collector.record_search_request(
                    search_type="ai",
                    cache_hit=True,
                    response_time=0.5,
                    results_count=25
                )
            
            # Should log error
            mock_logger.error.assert_called_once()
    
    def test_record_database_connections_success(self):
        """Test successful database connections recording."""
        collector = MetricsCollector()
        
        with patch('metrics.ACTIVE_CONNECTIONS') as mock_gauge:
            with patch('metrics.logger') as mock_logger:
                collector.record_database_connections(10)
            
            mock_gauge.set.assert_called_once_with(10)
    
    def test_record_database_connections_error(self):
        """Test database connections recording with error."""
        collector = MetricsCollector()
        
        with patch('metrics.ACTIVE_CONNECTIONS') as mock_gauge:
            mock_gauge.set.side_effect = Exception("Gauge error")
            with patch('metrics.logger') as mock_logger:
                # Should not raise exception
                collector.record_database_connections(5)
            
            # Should log error
            mock_logger.error.assert_called_once()
    
    def test_record_redis_connections_success(self):
        """Test successful Redis connections recording."""
        collector = MetricsCollector()
        
        with patch('metrics.REDIS_CONNECTIONS') as mock_gauge:
            with patch('metrics.logger') as mock_logger:
                collector.record_redis_connections(3)
            
            mock_gauge.set.assert_called_once_with(3)
    
    def test_record_redis_connections_error(self):
        """Test Redis connections recording with error."""
        collector = MetricsCollector()
        
        with patch('metrics.REDIS_CONNECTIONS') as mock_gauge:
            mock_gauge.set.side_effect = Exception("Gauge error")
            with patch('metrics.logger') as mock_logger:
                # Should not raise exception
                collector.record_redis_connections(2)
            
            # Should log error
            mock_logger.error.assert_called_once()
    
    def test_get_metrics_success(self):
        """Test successful metrics generation."""
        collector = MetricsCollector()
        
        with patch('metrics.generate_latest') as mock_generate:
            mock_generate.return_value = "test_metrics_data"
            with patch('metrics.logger') as mock_logger:
                result = collector.get_metrics()
            
            assert result == "test_metrics_data"
            mock_generate.assert_called_once()
    
    def test_get_metrics_error(self):
        """Test metrics generation with error."""
        collector = MetricsCollector()
        
        with patch('metrics.generate_latest') as mock_generate:
            mock_generate.side_effect = Exception("Generation error")
            with patch('metrics.logger') as mock_logger:
                result = collector.get_metrics()
            
            assert result == ""
            mock_logger.error.assert_called_once()

class TestGlobalMetricsCollector:
    """Test global metrics collector instance."""
    
    def test_global_metrics_collector_exists(self):
        """Test that global metrics collector instance exists."""
        assert metrics_collector is not None
        assert isinstance(metrics_collector, MetricsCollector)
    
    def test_global_metrics_collector_methods(self):
        """Test that global metrics collector has required methods."""
        assert hasattr(metrics_collector, 'record_search_request')
        assert hasattr(metrics_collector, 'record_database_connections')
        assert hasattr(metrics_collector, 'record_redis_connections')
        assert hasattr(metrics_collector, 'get_metrics')

class TestPrometheusMetrics:
    """Test Prometheus metrics objects."""
    
    def test_search_requests_total_metric(self):
        """Test SEARCH_REQUESTS_TOTAL metric."""
        assert SEARCH_REQUESTS_TOTAL is not None
        assert hasattr(SEARCH_REQUESTS_TOTAL, 'labels')
        assert hasattr(SEARCH_REQUESTS_TOTAL, 'inc')
    
    def test_search_response_time_metric(self):
        """Test SEARCH_RESPONSE_TIME metric."""
        assert SEARCH_RESPONSE_TIME is not None
        assert hasattr(SEARCH_RESPONSE_TIME, 'labels')
        assert hasattr(SEARCH_RESPONSE_TIME, 'observe')
    
    def test_search_results_count_metric(self):
        """Test SEARCH_RESULTS_COUNT metric."""
        assert SEARCH_RESULTS_COUNT is not None
        assert hasattr(SEARCH_RESULTS_COUNT, 'labels')
        assert hasattr(SEARCH_RESULTS_COUNT, 'observe')
    
    def test_cache_hit_ratio_metric(self):
        """Test CACHE_HIT_RATIO metric."""
        assert CACHE_HIT_RATIO is not None
        assert hasattr(CACHE_HIT_RATIO, 'labels')
        assert hasattr(CACHE_HIT_RATIO, 'set')
    
    def test_active_connections_metric(self):
        """Test ACTIVE_CONNECTIONS metric."""
        assert ACTIVE_CONNECTIONS is not None
        assert hasattr(ACTIVE_CONNECTIONS, 'set')
    
    def test_redis_connections_metric(self):
        """Test REDIS_CONNECTIONS metric."""
        assert REDIS_CONNECTIONS is not None
        assert hasattr(REDIS_CONNECTIONS, 'set')

class TestMetricsCollectorIntegration:
    """Test integration scenarios for MetricsCollector."""
    
    def test_complete_metrics_workflow(self):
        """Test complete metrics workflow."""
        collector = MetricsCollector()
        
        with patch('metrics.SEARCH_REQUESTS_TOTAL') as mock_counter:
            with patch('metrics.SEARCH_RESPONSE_TIME') as mock_histogram:
                with patch('metrics.SEARCH_RESULTS_COUNT') as mock_results:
                    with patch('metrics.CACHE_HIT_RATIO') as mock_cache:
                        with patch('metrics.ACTIVE_CONNECTIONS') as mock_db:
                            with patch('metrics.REDIS_CONNECTIONS') as mock_redis:
                                with patch('metrics.logger') as mock_logger:
                                    # Record search request
                                    collector.record_search_request(
                                        search_type="ai",
                                        cache_hit=True,
                                        response_time=0.3,
                                        results_count=15
                                    )
                                    
                                    # Record connections
                                    collector.record_database_connections(5)
                                    collector.record_redis_connections(2)
                                    
                                    # Get metrics
                                    with patch('metrics.generate_latest', return_value="metrics_data"):
                                        result = collector.get_metrics()
                                    
                                    assert result == "metrics_data"
    
    def test_multiple_search_types(self):
        """Test metrics with multiple search types."""
        collector = MetricsCollector()
        
        with patch('metrics.SEARCH_REQUESTS_TOTAL') as mock_counter:
            with patch('metrics.SEARCH_RESPONSE_TIME') as mock_histogram:
                with patch('metrics.SEARCH_RESULTS_COUNT') as mock_results:
                    with patch('metrics.CACHE_HIT_RATIO') as mock_cache:
                        with patch('metrics.logger') as mock_logger:
                            # AI search
                            collector.record_search_request(
                                search_type="ai",
                                cache_hit=True,
                                response_time=0.5,
                                results_count=25
                            )
                            
                            # Basic search
                            collector.record_search_request(
                                search_type="basic",
                                cache_hit=False,
                                response_time=0.1,
                                results_count=10
                            )
                            
                            # Faceted search
                            collector.record_search_request(
                                search_type="faceted",
                                cache_hit=True,
                                response_time=0.8,
                                results_count=100
                            )
                            
                            # Verify different search types were recorded
                            assert mock_counter.labels.call_count == 3
                            assert mock_histogram.labels.call_count == 3
                            assert mock_results.labels.call_count == 3
                            assert mock_cache.labels.call_count == 3
    
    def test_metrics_with_extreme_values(self):
        """Test metrics with extreme values."""
        collector = MetricsCollector()
        
        with patch('metrics.SEARCH_REQUESTS_TOTAL') as mock_counter:
            with patch('metrics.SEARCH_RESPONSE_TIME') as mock_histogram:
                with patch('metrics.SEARCH_RESULTS_COUNT') as mock_results:
                    with patch('metrics.CACHE_HIT_RATIO') as mock_cache:
                        with patch('metrics.logger') as mock_logger:
                            # Very fast response
                            collector.record_search_request(
                                search_type="basic",
                                cache_hit=True,
                                response_time=0.001,
                                results_count=1
                            )
                            
                            # Very slow response
                            collector.record_search_request(
                                search_type="ai",
                                cache_hit=False,
                                response_time=10.0,
                                results_count=10000
                            )
                            
                            # Zero results
                            collector.record_search_request(
                                search_type="faceted",
                                cache_hit=False,
                                response_time=0.5,
                                results_count=0
                            )
                            
                            # Verify all were recorded
                            assert mock_counter.labels.call_count == 3
                            assert mock_histogram.labels.call_count == 3  # 1 histogram per call
    
    def test_connection_metrics_edge_cases(self):
        """Test connection metrics with edge cases."""
        collector = MetricsCollector()
        
        with patch('metrics.ACTIVE_CONNECTIONS') as mock_db:
            with patch('metrics.REDIS_CONNECTIONS') as mock_redis:
                with patch('metrics.logger') as mock_logger:
                    # Zero connections
                    collector.record_database_connections(0)
                    collector.record_redis_connections(0)
                    
                    # Many connections
                    collector.record_database_connections(1000)
                    collector.record_redis_connections(500)
                    
                    # Verify calls
                    assert mock_db.set.call_count == 2
                    assert mock_redis.set.call_count == 2 