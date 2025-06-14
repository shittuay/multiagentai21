"""Configuration settings for the multi-agent system."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Cloud settings
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID', 'multiagentai21')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'multiagentai21-key.json')

# Database settings
FIRESTORE_COLLECTIONS = {
    'chats': 'chats',
    'sessions': 'sessions',
    'agents': 'agents',
    'analytics': 'analytics'
}

# Agent settings
AGENT_SETTINGS: Dict[str, Dict[str, Any]] = {
    'content_creation_and_generation': {
        'model': 'gemini-1.5-pro',
        'max_tokens': 2048,
        'temperature': 0.7,
        'top_p': 0.9,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    },
    'data_analysis_and_insights': {
        'model': 'gemini-1.5-pro',
        'max_tokens': 4096,
        'temperature': 0.3,
        'top_p': 0.9,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    },
    'customer_service_and_engagement': {
        'model': 'gemini-1.5-pro',
        'max_tokens': 1024,
        'temperature': 0.7,
        'top_p': 0.9,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    },
    'automation_of_complex_processes': {
        'model': 'gemini-1.5-pro',
        'max_tokens': 2048,
        'temperature': 0.5,
        'top_p': 0.9,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    }
}

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv('LOG_FILE', 'multiagentai21.log')

# Session settings
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour in seconds
MAX_SESSION_LENGTH = int(os.getenv('MAX_SESSION_LENGTH', '50'))  # Maximum interactions per session

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))  # Requests per minute
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # Window in seconds

# Content settings
MAX_CONTENT_LENGTH = {
    'blog_post': 2000,
    'social_media': 280,
    'article': 3000,
    'email': 500
}

# Error messages
ERROR_MESSAGES = {
    'model_not_initialized': 'Model not initialized. Please check your API credentials.',
    'invalid_request': 'Invalid request format or content.',
    'rate_limit_exceeded': 'Rate limit exceeded. Please try again later.',
    'session_expired': 'Session has expired. Please start a new session.',
    'database_error': 'Database operation failed. Please try again.',
    'authentication_error': 'Authentication failed. Please check your credentials.'
}

def get_agent_settings(agent_type: str) -> Dict[str, Any]:
    """Get settings for a specific agent type.
    
    Args:
        agent_type: Type of agent to get settings for
        
    Returns:
        Dictionary containing agent settings
    """
    return AGENT_SETTINGS.get(agent_type, AGENT_SETTINGS['content_creation_and_generation'])

def validate_settings() -> bool:
    """Validate that all required settings are present.
    
    Returns:
        True if all required settings are present, False otherwise
    """
    required_settings = [
        'GOOGLE_API_KEY',
        'GOOGLE_PROJECT_ID',
        'GOOGLE_APPLICATION_CREDENTIALS'
    ]
    
    missing_settings = [setting for setting in required_settings 
                       if not os.getenv(setting)]
    
    if missing_settings:
        print(f"Missing required settings: {', '.join(missing_settings)}")
        return False
    
    return True 