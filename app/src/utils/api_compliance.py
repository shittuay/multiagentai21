#!/usr/bin/env python3
"""
API Compliance and Rate Limiting Module
Ensures compliance with Google Cloud API Terms of Service and Acceptable Use Policy
"""

import time
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import re

logger = logging.getLogger(__name__)

@dataclass
class APIUsageMetrics:
    """Track API usage metrics for compliance monitoring."""
    requests_per_minute: int = 0
    requests_per_hour: int = 0
    requests_per_day: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    quota_exceeded_count: int = 0
    last_request_time: Optional[datetime] = None
    daily_reset_time: datetime = None

class ComplianceValidator:
    """Validates requests for policy compliance."""
    
    # Prohibited content patterns (basic implementation)
    PROHIBITED_PATTERNS = [
        # Hate speech indicators
        r'\b(?:hate|nazi|terrorist|kill|murder|bomb|weapon)\b',
        # Personal information patterns
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{16}\b',  # Credit card
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email (basic)
        # Malicious intent
        r'\b(?:hack|exploit|vulnerability|malware|virus)\b',
    ]
    
    @classmethod
    def validate_content(cls, content: str) -> tuple[bool, List[str]]:
        """
        Validate content for policy compliance.
        Returns (is_compliant, violations_found)
        """
        violations = []
        content_lower = content.lower()
        
        for pattern in cls.PROHIBITED_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                violations.append(f"Potential prohibited content detected: {pattern}")
        
        # Additional checks
        if len(content) > 50000:  # Very long requests might be suspicious
            violations.append("Request content exceeds recommended length")
        
        is_compliant = len(violations) == 0
        return is_compliant, violations

class APIRateLimiter:
    """
    Implements comprehensive rate limiting and compliance monitoring
    for Google Cloud Gemini API usage.
    """
    
    def __init__(self, 
                 requests_per_minute: int = 10,  # Conservative limit
                 requests_per_hour: int = 100,
                 requests_per_day: int = 1000,
                 min_request_interval: float = 6.0,  # 6 seconds between requests
                 enable_compliance_check: bool = True):
        """
        Initialize rate limiter with conservative defaults.
        
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour  
            requests_per_day: Max requests per day
            min_request_interval: Minimum seconds between requests
            enable_compliance_check: Enable content validation
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.min_request_interval = min_request_interval
        self.enable_compliance_check = enable_compliance_check
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Usage tracking
        self.usage_metrics = APIUsageMetrics()
        self.usage_metrics.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Time-based request tracking
        self.minute_requests = deque()
        self.hour_requests = deque()
        self.day_requests = deque()
        
        # Last request timestamp
        self.last_request_time = 0.0
        
        # Compliance tracking
        self.compliance_violations = []
        self.blocked_requests = 0
        
        logger.info(f"API Rate Limiter initialized: {requests_per_minute}/min, {requests_per_hour}/hour, {requests_per_day}/day")
    
    def can_make_request(self, content: str = "") -> tuple[bool, str]:
        """
        Check if a request can be made based on rate limits and compliance.
        
        Returns:
            (can_proceed, reason_if_blocked)
        """
        with self._lock:
            now = time.time()
            dt_now = datetime.now()
            
            # Check minimum interval between requests
            if now - self.last_request_time < self.min_request_interval:
                remaining = self.min_request_interval - (now - self.last_request_time)
                return False, f"Rate limit: Wait {remaining:.1f}s before next request"
            
            # Clean old entries
            self._cleanup_old_entries(dt_now)
            
            # Check per-minute limit
            if len(self.minute_requests) >= self.requests_per_minute:
                return False, f"Rate limit: Exceeded {self.requests_per_minute} requests per minute"
            
            # Check per-hour limit
            if len(self.hour_requests) >= self.requests_per_hour:
                return False, f"Rate limit: Exceeded {self.requests_per_hour} requests per hour"
            
            # Check per-day limit
            if len(self.day_requests) >= self.requests_per_day:
                return False, f"Rate limit: Exceeded {self.requests_per_day} requests per day"
            
            # Content compliance check
            if self.enable_compliance_check and content:
                is_compliant, violations = ComplianceValidator.validate_content(content)
                if not is_compliant:
                    self.compliance_violations.extend(violations)
                    self.blocked_requests += 1
                    logger.warning(f"Request blocked for compliance violations: {violations}")
                    return False, f"Content compliance violation: {'; '.join(violations)}"
            
            return True, "Request approved"
    
    def record_request(self, success: bool = True, quota_exceeded: bool = False):
        """Record a request for rate limiting tracking."""
        with self._lock:
            now = time.time()
            dt_now = datetime.now()
            
            # Update last request time
            self.last_request_time = now
            self.usage_metrics.last_request_time = dt_now
            
            # Add to tracking queues
            self.minute_requests.append(dt_now)
            self.hour_requests.append(dt_now)
            self.day_requests.append(dt_now)
            
            # Update metrics
            self.usage_metrics.total_requests += 1
            if not success:
                self.usage_metrics.failed_requests += 1
            if quota_exceeded:
                self.usage_metrics.quota_exceeded_count += 1
            
            # Clean old entries
            self._cleanup_old_entries(dt_now)
            
            # Update current period counters
            self.usage_metrics.requests_per_minute = len(self.minute_requests)
            self.usage_metrics.requests_per_hour = len(self.hour_requests)
            self.usage_metrics.requests_per_day = len(self.day_requests)
            
            logger.debug(f"Request recorded: {self.usage_metrics.requests_per_minute}/min, {self.usage_metrics.requests_per_hour}/hour, {self.usage_metrics.requests_per_day}/day")
    
    def _cleanup_old_entries(self, now: datetime):
        """Remove old entries from tracking queues."""
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Clean minute requests
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()
        
        # Clean hour requests
        while self.hour_requests and self.hour_requests[0] < hour_ago:
            self.hour_requests.popleft()
        
        # Clean day requests
        while self.day_requests and self.day_requests[0] < day_ago:
            self.day_requests.popleft()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        with self._lock:
            now = datetime.now()
            self._cleanup_old_entries(now)
            
            return {
                "current_usage": {
                    "requests_per_minute": len(self.minute_requests),
                    "requests_per_hour": len(self.hour_requests), 
                    "requests_per_day": len(self.day_requests),
                },
                "limits": {
                    "requests_per_minute": self.requests_per_minute,
                    "requests_per_hour": self.requests_per_hour,
                    "requests_per_day": self.requests_per_day,
                    "min_interval_seconds": self.min_request_interval
                },
                "totals": asdict(self.usage_metrics),
                "compliance": {
                    "violations_detected": len(self.compliance_violations),
                    "requests_blocked": self.blocked_requests,
                    "recent_violations": self.compliance_violations[-10:] if self.compliance_violations else []
                }
            }
    
    def wait_if_needed(self, content: str = "") -> bool:
        """
        Wait if needed to comply with rate limits, then return if request can proceed.
        
        Returns:
            True if request can proceed, False if blocked for compliance
        """
        max_wait_time = 300  # Maximum 5 minutes wait
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            can_proceed, reason = self.can_make_request(content)
            
            if can_proceed:
                return True
            
            # If it's a compliance violation, don't wait
            if "compliance violation" in reason.lower():
                logger.error(f"Request permanently blocked: {reason}")
                return False
            
            # Extract wait time from reason if it's a rate limit
            if "Wait" in reason:
                try:
                    wait_time = float(reason.split("Wait ")[1].split("s")[0])
                    wait_time = min(wait_time + 1, 30)  # Max 30 second wait per iteration
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s: {reason}")
                    time.sleep(wait_time)
                    continue
                except:
                    pass
            
            # Default wait for other rate limits
            logger.info(f"Rate limit reached, waiting 30s: {reason}")
            time.sleep(30)
        
        logger.error(f"Max wait time exceeded, request blocked")
        return False
    
    def reset_daily_counters(self):
        """Reset daily counters (called at midnight)."""
        with self._lock:
            now = datetime.now()
            if now >= self.usage_metrics.daily_reset_time:
                self.day_requests.clear()
                self.usage_metrics.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                logger.info("Daily API usage counters reset")

# Global rate limiter instance
_global_rate_limiter: Optional[APIRateLimiter] = None

def get_rate_limiter() -> APIRateLimiter:
    """Get or create the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = APIRateLimiter()
    return _global_rate_limiter

def configure_rate_limiter(requests_per_minute: int = 10,
                          requests_per_hour: int = 100,
                          requests_per_day: int = 1000,
                          min_request_interval: float = 6.0):
    """Configure the global rate limiter with custom settings."""
    global _global_rate_limiter
    _global_rate_limiter = APIRateLimiter(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        requests_per_day=requests_per_day,
        min_request_interval=min_request_interval
    )
    logger.info(f"Rate limiter configured: {requests_per_minute}/min, {requests_per_hour}/hour, {requests_per_day}/day")