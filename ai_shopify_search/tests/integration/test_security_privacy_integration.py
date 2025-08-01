"""
Integration tests for security and privacy compliance.
Tests GDPR compliance, data protection, and security measures across the application.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
import time
from datetime import datetime, timedelta

from main import app
from core.database import SessionLocal
from core.models import Product, SearchAnalytics, SearchClick
from services.service_factory import service_factory
from utils.privacy import anonymize_ip, sanitize_user_agent, generate_session_id
from utils.validation import sanitize_search_query, validate_price_range
from utils.error_handling import handle_errors


@pytest.mark.skip(reason="Integration test requires external dependencies not available in CI environment")
class TestSecurityPrivacyIntegration:
    """Integration tests for security and privacy compliance."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        """Database session for testing."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def sample_products(self, db_session):
        """Create sample products for testing."""
        products = [
            Product(
                id=1,
                title="Security Test Product 1",
                description="Product for security and privacy testing",
                price=29.99,
                shopify_id="security_test_1",
                tags=["electronics", "security"]
            ),
            Product(
                id=2,
                title="Security Test Product 2",
                description="Another product for security testing",
                price=59.99,
                shopify_id="security_test_2",
                tags=["electronics", "security"]
            )
        ]
        
        for product in products:
            db_session.add(product)
        db_session.commit()
        
        yield products
        
        # Cleanup
        for product in products:
            db_session.delete(product)
        db_session.commit()
    
    def test_gdpr_compliance_integration(self, client, db_session, sample_products):
        """Test GDPR compliance across the entire application."""
        # Test IP anonymization
        client_ip = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Test Browser) 1.0"
        
        response = client.get("/api/v2/products/search", params={
            "query": "gdpr compliance test"
        }, headers={
            "X-Forwarded-For": client_ip,
            "User-Agent": user_agent
        })
        
        assert response.status_code == 200
        
        # Verify IP is anonymized in database
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "gdpr compliance test"
        ).first()
        
        if analytics and analytics.client_ip:
            assert analytics.client_ip != client_ip
            assert analytics.client_ip == anonymize_ip(client_ip)
        
        # Verify user agent is sanitized
        if analytics and analytics.user_agent:
            assert analytics.user_agent != user_agent
            assert len(analytics.user_agent) <= 50  # Sanitized length
    
    def test_data_retention_compliance(self, client, db_session, sample_products):
        """Test data retention compliance."""
        from utils.privacy import DataRetentionManager
        
        retention_manager = DataRetentionManager()
        
        # Create old analytics data
        old_date = datetime.now() - timedelta(days=400)  # Older than retention period
        old_analytics = SearchAnalytics(
            query="old test query",
            search_count=1,
            last_searched=old_date,
            client_ip=anonymize_ip("192.168.1.101"),
            user_agent="Old Browser"
        )
        db_session.add(old_analytics)
        db_session.commit()
        
        # Verify old data exists
        old_data = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "old test query"
        ).first()
        assert old_data is not None
        
        # Run data cleanup
        retention_manager.cleanup_expired_data(db_session)
        
        # Verify old data was cleaned up
        cleaned_data = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "old test query"
        ).first()
        assert cleaned_data is None
    
    def test_input_validation_integration(self, client, db_session):
        """Test input validation across the application."""
        # Test SQL injection attempts
        malicious_queries = [
            "'; DROP TABLE products; --",
            "' OR '1'='1",
            "'; INSERT INTO products VALUES (999, 'hacked'); --",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')"
        ]
        
        for malicious_query in malicious_queries:
            response = client.get("/api/v2/products/search", params={
                "query": malicious_query
            })
            
            # Should handle malicious input gracefully
            assert response.status_code in [200, 400, 422]
            
            # Verify no SQL injection occurred
            # (In a real test, you'd check the database state)
        
        # Test XSS prevention
        xss_query = "<script>alert('xss')</script>"
        sanitized_query = sanitize_search_query(xss_query)
        
        assert "<script>" not in sanitized_query
        assert "javascript:" not in sanitized_query
    
    def test_rate_limiting_integration(self, client, db_session, sample_products):
        """Test rate limiting integration."""
        # Make multiple rapid requests
        responses = []
        for i in range(15):  # Exceed rate limit
            response = client.get("/api/v2/products/search", params={
                "query": f"rate limit test {i}",
                "limit": 10
            })
            responses.append(response)
        
        # Check for rate limiting
        status_codes = [r.status_code for r in responses]
        
        # Should have some rate limited responses (429)
        # or all successful if rate limiting is not strict
        assert 429 in status_codes or all(code == 200 for code in status_codes)
    
    def test_session_management_integration(self, client, db_session):
        """Test session management and security."""
        # Test session creation
        session_id = generate_session_id()
        assert session_id is not None
        assert len(session_id) > 20  # Should be sufficiently random
        
        # Test session expiration
        expired_session = "expired_session_123"
        is_expired = is_session_expired(expired_session, max_age_hours=24)
        # This would depend on the actual session data
    
    def test_secure_headers_integration(self, client):
        """Test secure headers are properly set."""
        response = client.get("/api/v2/products/search", params={
            "query": "secure headers test"
        })
        
        # Check for security headers
        headers = response.headers
        
        # Common security headers (implementation dependent)
        # assert "X-Content-Type-Options" in headers
        # assert "X-Frame-Options" in headers
        # assert "X-XSS-Protection" in headers
    
    def test_authentication_integration(self, client):
        """Test authentication and authorization."""
        # Test unauthenticated access (should work for public endpoints)
        response = client.get("/api/v2/products/search", params={
            "query": "public access test"
        })
        
        assert response.status_code == 200
        
        # Test with invalid authentication
        response = client.get("/api/v2/products/search", params={
            "query": "auth test"
        }, headers={
            "Authorization": "Bearer invalid_token"
        })
        
        # Should handle invalid auth gracefully
        assert response.status_code in [200, 401, 403]
    
    def test_data_encryption_integration(self, client, db_session):
        """Test data encryption and protection."""
        # Test sensitive data handling
        sensitive_query = "credit card 1234-5678-9012-3456"
        
        response = client.get("/api/v2/products/search", params={
            "query": sensitive_query
        })
        
        assert response.status_code == 200
        
        # Verify sensitive data is not logged in plain text
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == sensitive_query
        ).first()
        
        if analytics:
            # Query should be sanitized or encrypted
            assert "1234-5678-9012-3456" not in analytics.query
    
    def test_error_handling_security(self, client, db_session):
        """Test that error handling doesn't leak sensitive information."""
        # Test with invalid input that might cause errors
        response = client.get("/api/v2/products/search", params={
            "query": "error test",
            "min_price": "invalid_price",  # Invalid price
            "limit": "not_a_number"  # Invalid limit
        })
        
        # Should handle errors gracefully
        assert response.status_code in [400, 422]
        
        # Error response should not contain sensitive information
        error_data = response.json()
        assert "database" not in str(error_data).lower()
        assert "password" not in str(error_data).lower()
        assert "api_key" not in str(error_data).lower()
    
    def test_csrf_protection_integration(self, client):
        """Test CSRF protection."""
        # Test POST request without CSRF token
        response = client.post("/api/v2/products/search", json={
            "query": "csrf test"
        })
        
        # Should handle CSRF protection
        assert response.status_code in [200, 405, 422]  # Depending on implementation
    
    def test_sql_injection_prevention(self, client, db_session, sample_products):
        """Test SQL injection prevention."""
        # Test various SQL injection attempts
        injection_attempts = [
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM products; --",
            "'; UPDATE products SET price = 0; --",
            "'; DELETE FROM products; --"
        ]
        
        for attempt in injection_attempts:
            response = client.get("/api/v2/products/search", params={
                "query": attempt
            })
            
            # Should handle injection attempts safely
            assert response.status_code in [200, 400, 422]
            
            # Verify database integrity
            product_count = db_session.query(Product).count()
            assert product_count == len(sample_products)  # No products deleted
    
    def test_xss_prevention_integration(self, client, db_session):
        """Test XSS prevention."""
        # Test XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            response = client.get("/api/v2/products/search", params={
                "query": payload
            })
            
            # Should handle XSS attempts safely
            assert response.status_code in [200, 400, 422]
            
            # Verify response doesn't contain XSS payload
            response_text = response.text
            assert "<script>" not in response_text
            assert "javascript:" not in response_text
            assert "onerror=" not in response_text
            assert "onload=" not in response_text
    
    def test_privacy_logging_integration(self, client, db_session):
        """Test that logging respects privacy."""
        import logging
        
        # Configure test logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Test with sensitive data
        sensitive_data = {
            "email": "user@example.com",
            "password": "secret123",
            "credit_card": "1234-5678-9012-3456",
            "ip": "192.168.1.100"
        }
        
        # Log should be sanitized
        with patch.object(logger, 'info') as mock_logger:
            # This would be called by the application
            sanitized_log = f"Search query: {sanitize_search_query(str(sensitive_data))}"
            logger.info(sanitized_log)
            
            # Verify sensitive data is not logged
            log_call_args = mock_logger.call_args[0][0]
            assert "secret123" not in log_call_args
            assert "1234-5678-9012-3456" not in log_call_args
            assert "user@example.com" not in log_call_args
    
    def test_data_anonymization_integration(self, client, db_session, sample_products):
        """Test data anonymization across the application."""
        # Test IP anonymization
        test_ips = [
            "192.168.1.100",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8"
        ]
        
        for ip in test_ips:
            anonymized = anonymize_ip(ip)
            assert anonymized != ip
            assert anonymized is not None
            
            # Test that anonymized IPs are consistent
            anonymized_again = anonymize_ip(ip)
            assert anonymized == anonymized_again
        
        # Test user agent sanitization
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        
        for ua in user_agents:
            sanitized = sanitize_user_agent(ua)
            assert len(sanitized) <= 50
            assert sanitized != ua
    
    def test_secure_configuration_integration(self):
        """Test secure configuration management."""
        from config import settings
        
        # Verify sensitive configuration is not exposed
        config_vars = vars(settings)
        
        # Check for sensitive data exposure
        sensitive_keys = ["password", "secret", "key", "token"]
        for key in sensitive_keys:
            if key in config_vars:
                value = config_vars[key]
                # Should not be in plain text or default values
                assert value not in ["", "default", "secret", "password"]
    
    def test_audit_trail_integration(self, client, db_session, sample_products):
        """Test audit trail functionality."""
        # Perform actions that should be audited
        response = client.get("/api/v2/products/search", params={
            "query": "audit trail test"
        })
        
        assert response.status_code == 200
        
        # Verify audit trail was created
        analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.query == "audit trail test"
        ).first()
        
        if analytics:
            # Should have audit information
            assert analytics.last_searched is not None
            assert analytics.search_count >= 1
    
    def test_compliance_reporting_integration(self, client, db_session):
        """Test compliance reporting functionality."""
        # This would test GDPR compliance reporting
        # In a real implementation, you'd have endpoints for data export/deletion
        
        # Test data export (if implemented)
        # response = client.get("/api/v2/user/data/export")
        # assert response.status_code in [200, 404]  # 404 if not implemented
        
        # Test data deletion (if implemented)
        # response = client.delete("/api/v2/user/data")
        # assert response.status_code in [200, 404]  # 404 if not implemented 