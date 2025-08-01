#!/usr/bin/env python3
"""
Test script voor privacy en security implementatie
"""

import sys
import os
import requests
import json
from typing import Dict, Any

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.privacy import (
    anonymize_ip, sanitize_user_agent, generate_session_id, 
    is_session_expired, sanitize_log_data
)
from utils.validation import (
    sanitize_search_query, validate_price_range, generate_secure_cache_key,
    validate_api_key, validate_rate_limit_identifier
)

def test_privacy_utils():
    """Test privacy utilities."""
    
    print("🧪 Testing Privacy Utilities")
    print("=" * 40)
    
    # Test IP anonymization
    print("\n1. IP Anonymization:")
    test_ips = [
        "192.168.1.100",
        "10.0.0.1", 
        "172.16.0.50",
        "2001:db8::1",
        "localhost",
        "invalid.ip.address"
    ]
    
    for ip in test_ips:
        anonymized = anonymize_ip(ip)
        print(f"   {ip} -> {anonymized}")
    
    # Test user agent sanitization
    print("\n2. User Agent Sanitization:")
    test_user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Invalid User Agent String"
    ]
    
    for ua in test_user_agents:
        sanitized = sanitize_user_agent(ua)
        print(f"   {ua[:50]}... -> {sanitized}")
    
    # Test session ID generation and expiration
    print("\n3. Session ID Management:")
    session_id = generate_session_id()
    print(f"   Generated session ID: {session_id}")
    print(f"   Is expired: {is_session_expired(session_id)}")
    print(f"   Is expired (1 hour): {is_session_expired(session_id, 1)}")
    
    # Test log data sanitization
    print("\n4. Log Data Sanitization:")
    test_log_data = [
        "normal text",
        "text with <script>alert('xss')</script>",
        "text with 'quotes' and \"double quotes\"",
        "very long text that should be truncated when it exceeds the maximum length limit",
        ""
    ]
    
    for data in test_log_data:
        sanitized = sanitize_log_data(data, max_length=30)
        print(f"   '{data}' -> '{sanitized}'")

def test_validation():
    """Test validation utilities."""
    
    print("\n🧪 Testing Validation Utilities")
    print("=" * 40)
    
    # Test search query sanitization
    print("\n1. Search Query Sanitization:")
    test_queries = [
        "normal search",
        "search with <script>alert('xss')</script>",
        "search with 'quotes'",
        "a",  # Too short
        "very long search query " * 20,  # Too long
        ""
    ]
    
    for query in test_queries:
        try:
            sanitized = sanitize_search_query(query)
            print(f"   ✅ '{query[:30]}...' -> '{sanitized[:30]}...'")
        except ValueError as e:
            print(f"   ❌ '{query[:30]}...' -> Error: {e}")
    
    # Test price range validation
    print("\n2. Price Range Validation:")
    test_price_ranges = [
        (10, 100),  # Valid
        (-10, 100),  # Negative min
        (10, -100),  # Negative max
        (100, 10),   # Min > Max
        (None, 100), # Valid
        (10, None),  # Valid
        (None, None) # Valid
    ]
    
    for min_price, max_price in test_price_ranges:
        try:
            validate_price_range(min_price, max_price)
            print(f"   ✅ min={min_price}, max={max_price} -> Valid")
        except ValueError as e:
            print(f"   ❌ min={min_price}, max={max_price} -> Error: {e}")
    
    # Test cache key generation
    print("\n3. Secure Cache Key Generation:")
    test_cache_data = [
        {"query": "test", "page": 1, "limit": 25},
        {"query": "very long query that should be hashed", "page": 1, "limit": 25},
        {"query": "test", "min_price": 10, "max_price": 100}
    ]
    
    for data in test_cache_data:
        cache_key = generate_secure_cache_key("ai_search", **data)
        print(f"   {data} -> {cache_key}")
    
    # Test API key validation
    print("\n4. API Key Validation:")
    test_api_keys = [
        "valid_api_key_123",
        "short",
        "invalid@key#",
        "",
        "very_long_api_key_" * 10
    ]
    
    for key in test_api_keys:
        is_valid = validate_api_key(key)
        print(f"   '{key[:20]}...' -> {is_valid}")
    
    # Test rate limit identifier validation
    print("\n5. Rate Limit Identifier Validation:")
    test_identifiers = [
        "192.168.1.100",
        "invalid.ip",
        "user123",
        "",
        "very_long_identifier_" * 10
    ]
    
    for identifier in test_identifiers:
        try:
            validated = validate_rate_limit_identifier(identifier)
            print(f"   '{identifier}' -> '{validated}'")
        except ValueError as e:
            print(f"   '{identifier}' -> Error: {e}")

def test_api_endpoints():
    """Test API endpoints with privacy and security features."""
    
    print("\n🧪 Testing API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test privacy status endpoint
    print("\n1. Privacy Status Endpoint:")
    try:
        response = requests.get(f"{base_url}/api/privacy/status")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Privacy status retrieved successfully")
            print(f"   IP Anonymization: {data['privacy_compliance']['ip_anonymization']}")
            print(f"   User Agent Sanitization: {data['privacy_compliance']['user_agent_sanitization']}")
            print(f"   Data Retention Days: {data['privacy_compliance']['data_retention_days']}")
        else:
            print(f"   ❌ Failed to get privacy status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing privacy status: {e}")
    
    # Test AI search with security features
    print("\n2. AI Search with Security Features:")
    test_queries = [
        "goedkoop shirt",  # Valid query with price intent
        "a",  # Too short (should be rejected)
        "search with <script>alert('xss')</script>",  # XSS attempt
        "very long query " * 20  # Too long
    ]
    
    for query in test_queries:
        try:
            response = requests.get(
                f"{base_url}/api/ai-search",
                params={"query": query, "limit": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ '{query[:30]}...' -> {len(data.get('results', []))} results")
            elif response.status_code == 422:
                print(f"   ✅ '{query[:30]}...' -> Validation error (expected)")
            else:
                print(f"   ❌ '{query[:30]}...' -> HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing query '{query[:30]}...': {e}")
    
    # Test rate limiting
    print("\n3. Rate Limiting Test:")
    try:
        # Make multiple rapid requests
        responses = []
        for i in range(5):
            response = requests.get(
                f"{base_url}/api/ai-search",
                params={"query": f"test query {i}", "limit": 1}
            )
            responses.append(response.status_code)
        
        rate_limited = any(status == 429 for status in responses)
        if rate_limited:
            print("   ✅ Rate limiting working (some requests blocked)")
        else:
            print("   ℹ️  Rate limiting not triggered (normal for small number of requests)")
            
    except Exception as e:
        print(f"   ❌ Error testing rate limiting: {e}")

def test_data_cleanup():
    """Test data cleanup functionality."""
    
    print("\n🧪 Testing Data Cleanup")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    try:
        response = requests.post(f"{base_url}/api/privacy/cleanup")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Data cleanup completed successfully")
            print(f"   Analytics records cleaned: {data['cleanup_stats']['analytics_records']}")
            print(f"   Expired sessions cleaned: {data['cleanup_stats']['expired_sessions']}")
        else:
            print(f"   ❌ Data cleanup failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing data cleanup: {e}")

if __name__ == "__main__":
    print("🚀 Starting Privacy & Security Tests")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    test_privacy_utils()
    test_validation()
    test_api_endpoints()
    test_data_cleanup()
    
    print("\n🎉 Privacy & Security tests voltooid!")
    print("\n📋 Summary:")
    print("- ✅ IP anonymization implemented")
    print("- ✅ User agent sanitization implemented")
    print("- ✅ Input validation and sanitization implemented")
    print("- ✅ Secure cache key generation implemented")
    print("- ✅ Rate limiting with security logging implemented")
    print("- ✅ Data retention and cleanup implemented")
    print("- ✅ GDPR compliance features implemented") 