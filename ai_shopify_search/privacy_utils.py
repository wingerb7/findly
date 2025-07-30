#!/usr/bin/env python3
"""
Privacy utilities for GDPR compliance and data anonymization.
"""

import re
import time
import secrets
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def anonymize_ip(ip_address: str) -> Optional[str]:
    """
    Anonymize IP address for GDPR compliance.
    
    Args:
        ip_address: Raw IP address string
        
    Returns:
        Anonymized IP address (first 2 octets only) or None if invalid
        
    Example:
        >>> anonymize_ip("192.168.1.100")
        "192.168.*.*"
        >>> anonymize_ip("2001:db8::1")
        "2001:db8:*:*"
    """
    if not ip_address or not ip_address.strip():
        return None
    
    ip_address = ip_address.strip()
    
    # Handle IPv4 addresses
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
        parts = ip_address.split('.')
        if len(parts) == 4:
            try:
                # Validate each octet
                octets = [int(part) for part in parts]
                if all(0 <= octet <= 255 for octet in octets):
                    return f"{parts[0]}.{parts[1]}.*.*"
            except ValueError:
                logger.warning(f"Invalid IPv4 address format: {ip_address}")
                return None
    
    # Handle IPv6 addresses
    elif ':' in ip_address:
        # Extract first 4 segments for IPv6
        parts = ip_address.split(':')
        if len(parts) >= 4:
            return f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:*:*"
        else:
            return f"{parts[0]}:*:*"
    
    # Handle localhost and special addresses
    elif ip_address.lower() in ['localhost', '127.0.0.1', '::1']:
        return "127.0.0.*"
    
    logger.warning(f"Could not anonymize IP address: {ip_address}")
    return None

def sanitize_user_agent(user_agent: str) -> Optional[str]:
    """
    Sanitize user agent string to extract only relevant browser/OS information.
    
    Args:
        user_agent: Raw user agent string
        
    Returns:
        Sanitized user agent string or None if invalid
        
    Example:
        >>> sanitize_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        "Chrome/Windows"
    """
    if not user_agent or not user_agent.strip():
        return None
    
    user_agent = user_agent.strip()
    
    try:
        # Extract browser information
        browser_patterns = [
            r'(Chrome|Firefox|Safari|Edge|Opera)/[\d.]+',
            r'MSIE [\d.]+',
            r'Trident/[\d.]+'
        ]
        
        browser = "Unknown"
        for pattern in browser_patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                browser = match.group(1) if match.group(1) else "IE"
                break
        
        # Extract operating system information
        os_patterns = [
            r'\((Windows NT [\d.]+|Windows [\d.]+)',
            r'\((Macintosh|Mac OS X)',
            r'\((Linux|Ubuntu|Debian|CentOS)',
            r'\((iPhone|iPad|iPod)',
            r'\((Android)',
            r'\((X11; Linux)'
        ]
        
        os_info = "Unknown"
        for pattern in os_patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                os_match = match.group(1)
                if 'Windows NT' in os_match or 'Windows' in os_match:
                    os_info = "Windows"
                elif 'Macintosh' in os_match or 'Mac OS X' in os_match:
                    os_info = "Mac"
                elif 'Linux' in os_match or 'Ubuntu' in os_match or 'Debian' in os_match or 'CentOS' in os_match:
                    os_info = "Linux"
                elif 'iPhone' in os_match or 'iPad' in os_match or 'iPod' in os_match:
                    os_info = "iOS"
                elif 'Android' in os_match:
                    os_info = "Android"
                break
        
        return f"{browser}/{os_info}"
        
    except Exception as e:
        logger.warning(f"Error sanitizing user agent '{user_agent}': {e}")
        return "Unknown/Unknown"

def generate_session_id() -> str:
    """
    Generate a temporary session ID with timestamp for GDPR compliance.
    
    Returns:
        Session ID with timestamp prefix
        
    Example:
        >>> generate_session_id()
        "1703123456_abc123def456"
    """
    timestamp = int(time.time())
    random_part = secrets.token_urlsafe(8)
    return f"{timestamp}_{random_part}"

def is_session_expired(session_id: str, expiry_hours: int = 24) -> bool:
    """
    Check if a session ID has expired.
    
    Args:
        session_id: Session ID to check
        expiry_hours: Hours after which session expires
        
    Returns:
        True if session has expired, False otherwise
        
    Example:
        >>> is_session_expired("1703123456_abc123def456", 24)
        False
    """
    try:
        if not session_id or '_' not in session_id:
            return True
        
        timestamp_str = session_id.split('_')[0]
        timestamp = int(timestamp_str)
        current_time = int(time.time())
        
        return (current_time - timestamp) > (expiry_hours * 3600)
        
    except (ValueError, IndexError) as e:
        logger.warning(f"Error checking session expiration for '{session_id}': {e}")
        return True

def sanitize_log_data(data: str, max_length: int = 50) -> str:
    """
    Sanitize data for logging to prevent sensitive information exposure.
    
    Args:
        data: Data to sanitize
        max_length: Maximum length of sanitized data
        
    Returns:
        Sanitized data safe for logging
        
    Example:
        >>> sanitize_log_data("sensitive@email.com", 20)
        "sensitive@email.com"
        >>> sanitize_log_data("very long sensitive data that should be truncated", 20)
        "very long sensitive..."
    """
    if not data:
        return "None"
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(data))
    
    # Truncate if too long
    if len(sanitized) > max_length:
        return sanitized[:max_length] + "..."
    
    return sanitized

class DataRetentionManager:
    """Manager for data retention policies and cleanup."""
    
    def __init__(self, default_retention_days: int = 90):
        self.default_retention_days = default_retention_days
    
    def get_retention_date(self, days: Optional[int] = None) -> datetime:
        """
        Get the cutoff date for data retention.
        
        Args:
            days: Number of days to retain data (uses default if None)
            
        Returns:
            Cutoff date for data retention
        """
        retention_days = days or self.default_retention_days
        return datetime.now() - timedelta(days=retention_days)
    
    def should_cleanup_data(self, created_at: datetime, days: Optional[int] = None) -> bool:
        """
        Check if data should be cleaned up based on retention policy.
        
        Args:
            created_at: When the data was created
            days: Retention period in days (uses default if None)
            
        Returns:
            True if data should be cleaned up
        """
        cutoff_date = self.get_retention_date(days)
        return created_at < cutoff_date
    
    def get_cleanup_query_filters(self, days: Optional[int] = None) -> dict:
        """
        Get filters for cleanup queries.
        
        Args:
            days: Retention period in days (uses default if None)
            
        Returns:
            Dictionary with cleanup filters
        """
        cutoff_date = self.get_retention_date(days)
        return {
            "created_at__lt": cutoff_date
        }

# Configuration for privacy settings
PRIVACY_CONFIG = {
    "ip_anonymization": True,
    "user_agent_sanitization": True,
    "session_expiry_hours": 24,
    "log_sanitization": True,
    "default_retention_days": 90,
    "analytics_retention_days": 365,
    "search_analytics_retention_days": 180
} 