#!/usr/bin/env python3
"""
Unit tests for analytics services.
Tests analytics_manager.py and services/analytics_service.py functionality.
"""

import sys
import os
import json
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics_manager import analytics_manager
from services.analytics_service import AnalyticsService
from core.models import SearchAnalytics, PopularSearch, SearchClick


class TestAnalyticsManager:
    """Test analytics manager functionality."""
    
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
        
        # Mock analytics object
        self.mock_analytics = Mock()
        self.mock_analytics.id = 1
        self.mock_analytics.session_id = "test_session_123"
        self.mock_analytics.query = "test query"
        self.mock_analytics.search_type = "ai"
        self.mock_analytics.results_count = 5
        self.mock_analytics.response_time_ms = 150.5
        self.mock_analytics.cache_hit = False
    
    def test_track_search_analytics(self):
        """Test tracking search analytics."""
        print("🧪 Testing Track Search Analytics")
        print("=" * 40)
        
        # Mock session to return analytics object
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.refresh.return_value = None
        
        # Test tracking search
        result = analytics_manager.track_search(
            db=self.mock_session,
            query="test query",
            search_type="ai",
            filters={"price_range": "10-100"},
            results_count=5,
            page=1,
            limit=25,
            response_time_ms=150.5,
            cache_hit=False,
            user_agent="test-agent",
            ip_address="192.168.1.1"
        )
        
        assert result is not None
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        print("✅ Track search analytics tests passed")
    
    def test_track_product_click(self):
        """Test tracking product clicks."""
        print("\n🧪 Testing Track Product Click")
        print("=" * 35)
        
        # Mock search analytics
        mock_search_analytics = Mock()
        mock_search_analytics.id = 1
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_search_analytics
        
        # Test tracking click
        result = analytics_manager.track_product_click(
            db=self.mock_session,
            search_analytics_id=1,
            product_id=123,
            position=3,
            click_time_ms=5000.0,
            user_agent="test-agent",
            ip_address="192.168.1.1"
        )
        
        assert result is True
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        print("✅ Track product click tests passed")
    
    def test_get_popular_searches(self):
        """Test getting popular searches."""
        print("\n🧪 Testing Get Popular Searches")
        print("=" * 40)
        
        # Mock popular searches
        mock_popular_searches = [
            Mock(query="blue shirt", search_count=50, click_count=25),
            Mock(query="red dress", search_count=30, click_count=15),
            Mock(query="black shoes", search_count=20, click_count=10)
        ]
        
        self.mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_popular_searches
        
        # Test getting popular searches
        result = analytics_manager.get_popular_searches_analytics(
            db=self.mock_session,
            limit=10,
            min_searches=1
        )
        
        assert result is not None
        assert "popular_searches" in result
        print("✅ Get popular searches tests passed")
    
    def test_get_performance_analytics(self):
        """Test getting performance analytics."""
        print("\n🧪 Testing Get Performance Analytics")
        print("=" * 45)
        
        # Mock performance data
        mock_performance_data = {
            "total_searches": 1000,
            "avg_response_time": 150.5,
            "cache_hit_rate": 0.75,
            "search_types": {"ai": 600, "basic": 400}
        }
        
        # Mock query results
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 1000
        
        # Test getting performance analytics
        result = analytics_manager.get_performance_analytics(
            db=self.mock_session,
            start_date="2024-01-01",
            end_date="2024-01-31",
            search_type=None
        )
        
        assert result is not None
        print("✅ Get performance analytics tests passed")
    
    def test_cleanup_expired_data(self):
        """Test cleanup of expired data."""
        print("\n🧪 Testing Cleanup Expired Data")
        print("=" * 40)
        
        # Mock cleanup results
        self.mock_session.query.return_value.filter.return_value.delete.return_value = 50
        
        # Test cleanup
        result = analytics_manager.cleanup_expired_data(self.mock_session)
        
        assert result is not None
        assert "search_analytics" in result
        self.mock_session.commit.assert_called()
        print("✅ Cleanup expired data tests passed")
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        print("\n🧪 Testing Cleanup Expired Sessions")
        print("=" * 45)
        
        # Mock cleanup results
        self.mock_session.query.return_value.filter.return_value.delete.return_value = 25
        
        # Test cleanup
        result = analytics_manager.cleanup_expired_sessions(self.mock_session)
        
        assert result == 25
        self.mock_session.commit.assert_called()
        print("✅ Cleanup expired sessions tests passed")


class TestAnalyticsService:
    """Test analytics service functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.analytics_service = AnalyticsService()
        
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
    
    async def test_track_search(self):
        """Test async track search functionality."""
        print("\n🧪 Testing Async Track Search")
        print("=" * 35)
        
        # Mock analytics object
        mock_analytics = Mock()
        mock_analytics.id = 1
        
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.refresh.return_value = None
        
        # Test tracking search
        result = await self.analytics_service.track_search(
            db=self.mock_session,
            query="test query",
            search_type="ai",
            filters={"price_range": "10-100"},
            results_count=5,
            page=1,
            limit=25,
            response_time_ms=150.5,
            cache_hit=False,
            user_agent="test-agent",
            ip_address="192.168.1.1"
        )
        
        assert result == 1
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        print("✅ Async track search tests passed")
    
    async def test_track_click(self):
        """Test async track click functionality."""
        print("\n🧪 Testing Async Track Click")
        print("=" * 35)
        
        # Mock search analytics
        mock_search_analytics = Mock()
        mock_search_analytics.id = 1
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_search_analytics
        
        # Test tracking click
        result = await self.analytics_service.track_click(
            db=self.mock_session,
            search_analytics_id=1,
            product_id=123,
            position=3,
            user_agent="test-agent",
            ip_address="192.168.1.1"
        )
        
        assert result is True
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        print("✅ Async track click tests passed")
    
    async def test_get_popular_searches(self):
        """Test async get popular searches functionality."""
        print("\n🧪 Testing Async Get Popular Searches")
        print("=" * 45)
        
        # Mock popular searches
        mock_popular_searches = [
            Mock(query="blue shirt", search_count=50, click_count=25),
            Mock(query="red dress", search_count=30, click_count=15)
        ]
        
        self.mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_popular_searches
        
        # Test getting popular searches
        result = await self.analytics_service.get_popular_searches(
            db=self.mock_session,
            limit=10,
            min_searches=1,
            days=30
        )
        
        assert result is not None
        assert "popular_searches" in result
        print("✅ Async get popular searches tests passed")
    
    async def test_get_search_performance(self):
        """Test async get search performance functionality."""
        print("\n🧪 Testing Async Get Search Performance")
        print("=" * 50)
        
        # Mock performance data
        self.mock_session.query.return_value.filter.return_value.all.return_value = []
        self.mock_session.query.return_value.filter.return_value.count.return_value = 1000
        
        # Test getting performance data
        result = await self.analytics_service.get_search_performance(
            db=self.mock_session,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            search_type=None
        )
        
        assert result is not None
        assert "total_searches" in result
        print("✅ Async get search performance tests passed")
    
    async def test_cleanup_expired_data(self):
        """Test async cleanup expired data functionality."""
        print("\n🧪 Testing Async Cleanup Expired Data")
        print("=" * 50)
        
        # Mock cleanup results
        self.mock_session.query.return_value.filter.return_value.delete.return_value = 50
        
        # Test cleanup
        result = await self.analytics_service.cleanup_expired_data(self.mock_session)
        
        assert result is not None
        assert "search_analytics" in result
        self.mock_session.commit.assert_called()
        print("✅ Async cleanup expired data tests passed")
    
    async def test_cleanup_expired_sessions(self):
        """Test async cleanup expired sessions functionality."""
        print("\n🧪 Testing Async Cleanup Expired Sessions")
        print("=" * 55)
        
        # Mock cleanup results
        self.mock_session.query.return_value.filter.return_value.delete.return_value = 25
        
        # Test cleanup
        result = await self.analytics_service.cleanup_expired_sessions(self.mock_session)
        
        assert result == 25
        self.mock_session.commit.assert_called()
        print("✅ Async cleanup expired sessions tests passed")


class TestAnalyticsPrivacy:
    """Test analytics privacy compliance."""
    
    def test_ip_anonymization(self):
        """Test IP address anonymization in analytics."""
        print("\n🧪 Testing Analytics IP Anonymization")
        print("=" * 45)
        
        analytics_service = AnalyticsService()
        
        # Test with real IP addresses
        test_ips = [
            "192.168.1.100",
            "10.0.0.1",
            "172.16.0.50",
            "2001:db8::1"
        ]
        
        for ip in test_ips:
            # Mock session
            mock_session = Mock()
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            
            # Track search with IP
            analytics_service.track_search(
                db=mock_session,
                query="test query",
                search_type="ai",
                filters={},
                results_count=5,
                page=1,
                limit=25,
                response_time_ms=150.5,
                cache_hit=False,
                user_agent="test-agent",
                ip_address=ip
            )
            
            # Verify IP was anonymized in the call
            call_args = mock_session.add.call_args[0][0]
            assert call_args.ip_address != ip  # Should be anonymized
            assert call_args.ip_address is not None  # Should not be None
            
            print(f"✅ IP {ip} was properly anonymized")
    
    def test_user_agent_sanitization(self):
        """Test user agent sanitization in analytics."""
        print("\n🧪 Testing Analytics User Agent Sanitization")
        print("=" * 55)
        
        analytics_service = AnalyticsService()
        
        # Test with various user agents
        test_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15"
        ]
        
        for ua in test_user_agents:
            # Mock session
            mock_session = Mock()
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            
            # Track search with user agent
            analytics_service.track_search(
                db=mock_session,
                query="test query",
                search_type="ai",
                filters={},
                results_count=5,
                page=1,
                limit=25,
                response_time_ms=150.5,
                cache_hit=False,
                user_agent=ua,
                ip_address="192.168.1.1"
            )
            
            # Verify user agent was sanitized
            call_args = mock_session.add.call_args[0][0]
            assert call_args.user_agent != ua  # Should be sanitized
            assert call_args.user_agent is not None  # Should not be None
            assert len(call_args.user_agent) <= 100  # Should be truncated
            
            print(f"✅ User agent was properly sanitized")


class TestAnalyticsPerformance:
    """Test analytics performance scenarios."""
    
    def test_bulk_analytics_tracking(self):
        """Test bulk analytics tracking performance."""
        print("\n🧪 Testing Bulk Analytics Tracking Performance")
        print("=" * 60)
        
        analytics_service = AnalyticsService()
        
        # Mock session
        mock_session = Mock()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Test bulk tracking
        import time
        start_time = time.time()
        
        for i in range(100):
            analytics_service.track_search(
                db=mock_session,
                query=f"test query {i}",
                search_type="ai",
                filters={"price_range": f"{i}-{i+100}"},
                results_count=i % 50,
                page=1,
                limit=25,
                response_time_ms=float(i * 10),
                cache_hit=i % 2 == 0,
                user_agent=f"test-agent-{i}",
                ip_address=f"192.168.1.{i % 255}"
            )
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        assert operation_time < 5.0  # Should complete within 5 seconds
        assert mock_session.add.call_count == 100
        
        print(f"✅ Bulk analytics tracking completed in {operation_time:.3f}s")
    
    def test_analytics_data_retention(self):
        """Test analytics data retention policies."""
        print("\n🧪 Testing Analytics Data Retention")
        print("=" * 45)
        
        analytics_service = AnalyticsService()
        
        # Mock session
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.delete.return_value = 50
        
        # Test data retention cleanup
        result = analytics_service.cleanup_expired_data(mock_session)
        
        assert result is not None
        assert "search_analytics" in result
        assert result["search_analytics"] == 50
        
        print("✅ Analytics data retention tests passed")


def test_analytics_integration():
    """Test analytics integration with real scenarios."""
    print("\n🧪 Testing Analytics Integration")
    print("=" * 40)
    
    # Test complete analytics flow
    analytics_service = AnalyticsService()
    
    # Mock session
    mock_session = Mock()
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None
    mock_session.query.return_value = mock_session
    mock_session.filter.return_value = mock_session
    mock_session.filter_by.return_value = mock_session
    mock_session.first.return_value = None
    mock_session.all.return_value = []
    mock_session.count.return_value = 0
    
    # 1. Track search
    search_id = analytics_service.track_search(
        db=mock_session,
        query="blue shirt under 50 euros",
        search_type="ai",
        filters={"price_range": "0-50"},
        results_count=15,
        page=1,
        limit=25,
        response_time_ms=245.7,
        cache_hit=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="192.168.1.100"
    )
    
    assert search_id is not None
    
    # 2. Track click
    click_result = analytics_service.track_click(
        db=mock_session,
        search_analytics_id=search_id,
        product_id=123,
        position=3,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="192.168.1.100"
    )
    
    assert click_result is True
    
    # 3. Verify analytics were tracked
    assert mock_session.add.call_count == 2  # One search, one click
    assert mock_session.commit.call_count == 2
    
    print("✅ Analytics integration tests passed")


if __name__ == "__main__":
    # Run analytics manager tests
    test_instance = TestAnalyticsManager()
    test_instance.setup_method()
    
    test_instance.test_track_search_analytics()
    test_instance.test_track_product_click()
    test_instance.test_get_popular_searches()
    test_instance.test_get_performance_analytics()
    test_instance.test_cleanup_expired_data()
    test_instance.test_cleanup_expired_sessions()
    
    # Run integration tests
    test_analytics_integration()
    
    print("\n🎉 Analytics services tests completed!") 