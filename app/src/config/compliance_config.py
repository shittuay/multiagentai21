#!/usr/bin/env python3
"""
Compliance Configuration for MultiAgentAI21
Centralized settings for API usage limits and policy compliance
"""

import os
from typing import Dict, Any

class ComplianceConfig:
    """Centralized compliance configuration."""
    
    # CONSERVATIVE API LIMITS (adjust based on your quota)
    # These are set very conservatively to prevent violations
    DEFAULT_LIMITS = {
        # Rate limiting (very conservative)
        "requests_per_minute": int(os.getenv("API_REQUESTS_PER_MINUTE", "5")),  # Very low
        "requests_per_hour": int(os.getenv("API_REQUESTS_PER_HOUR", "50")),
        "requests_per_day": int(os.getenv("API_REQUESTS_PER_DAY", "200")),
        "min_request_interval": float(os.getenv("API_MIN_INTERVAL", "12.0")),  # 12 seconds between requests
        
        # Content limits
        "max_content_length": int(os.getenv("MAX_CONTENT_LENGTH", "8000")),  # Conservative content size
        "max_prompt_length": int(os.getenv("MAX_PROMPT_LENGTH", "4000")),
        
        # Retry policies
        "max_retries": int(os.getenv("API_MAX_RETRIES", "2")),  # Limited retries
        "retry_base_delay": float(os.getenv("API_RETRY_DELAY", "30.0")),  # 30 second base delay
        "retry_max_delay": float(os.getenv("API_MAX_RETRY_DELAY", "300.0")),  # Max 5 minutes
        
        # Monitoring
        "enable_usage_logging": os.getenv("ENABLE_USAGE_LOGGING", "true").lower() == "true",
        "log_level": os.getenv("COMPLIANCE_LOG_LEVEL", "INFO"),
        
        # Safety features
        "enable_content_filtering": os.getenv("ENABLE_CONTENT_FILTERING", "true").lower() == "true",
        "enable_rate_limiting": os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
        "enable_quota_monitoring": os.getenv("ENABLE_QUOTA_MONITORING", "true").lower() == "true",
    }
    
    # PRODUCTION LIMITS (for when you get higher quota)
    PRODUCTION_LIMITS = {
        "requests_per_minute": 20,
        "requests_per_hour": 200,
        "requests_per_day": 2000,
        "min_request_interval": 3.0,
        "max_content_length": 32000,
        "max_prompt_length": 16000,
    }
    
    # DEVELOPMENT LIMITS (even more conservative)
    DEVELOPMENT_LIMITS = {
        "requests_per_minute": 2,
        "requests_per_hour": 20,
        "requests_per_day": 100,
        "min_request_interval": 30.0,  # 30 seconds between requests
        "max_content_length": 4000,
        "max_prompt_length": 2000,
    }
    
    @classmethod
    def get_limits(cls, environment: str = None) -> Dict[str, Any]:
        """
        Get appropriate limits based on environment.
        
        Args:
            environment: 'development', 'production', or None for default
        """
        if environment == "development":
            return {**cls.DEFAULT_LIMITS, **cls.DEVELOPMENT_LIMITS}
        elif environment == "production":
            return {**cls.DEFAULT_LIMITS, **cls.PRODUCTION_LIMITS}
        else:
            return cls.DEFAULT_LIMITS.copy()
    
    @classmethod
    def get_compliance_settings(cls) -> Dict[str, Any]:
        """Get all compliance-related settings."""
        return {
            "api_limits": cls.get_limits(),
            "prohibited_content_patterns": [
                # Personal information
                r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
                r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
                
                # Potentially harmful content
                r'\b(?:password|secret|key|token|credential)\s*[:=]\s*\S+',  # Credentials
                r'\b(?:hack|exploit|vulnerability|malware|virus|trojan)\b',  # Malicious terms
                r'\b(?:bomb|weapon|kill|murder|terrorist)\b',  # Violent content
                
                # Spam indicators
                r'\b(?:free\s+money|get\s+rich|guaranteed\s+income)\b',
                r'\b(?:click\s+here|act\s+now|limited\s+time)\b',
            ],
            "content_validation": {
                "max_length": cls.DEFAULT_LIMITS["max_content_length"],
                "min_length": 1,
                "required_encoding": "utf-8",
                "prohibited_file_types": [".exe", ".bat", ".cmd", ".sh", ".ps1"],
            },
            "monitoring": {
                "track_usage": True,
                "log_violations": True,
                "alert_on_quota_limit": True,
                "quota_warning_threshold": 0.8,  # Alert at 80% of quota
            },
            "error_handling": {
                "graceful_degradation": True,
                "fallback_responses": True,
                "max_consecutive_failures": 5,
            }
        }

# Environment detection
def get_environment() -> str:
    """Detect current environment."""
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "")).lower()
    if env in ["prod", "production"]:
        return "production"
    elif env in ["dev", "development", "local"]:
        return "development"
    else:
        return "default"

# Global configuration instance
COMPLIANCE_CONFIG = ComplianceConfig.get_compliance_settings()
CURRENT_ENVIRONMENT = get_environment()
API_LIMITS = ComplianceConfig.get_limits(CURRENT_ENVIRONMENT)