#!/usr/bin/env python3
"""
Environment Variable Loader
Robust .env file loading with fallback mechanisms
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_environment_variables():
    """
    Load environment variables with robust fallback mechanisms.
    Tries multiple .env file locations and handles errors gracefully.
    """
    
    # List of possible .env file locations
    env_file_locations = [
        Path.cwd() / '.env',  # Current working directory
        Path(__file__).parent.parent.parent / '.env',  # Project root
        Path.cwd().parent / '.env',  # Parent directory
        Path.home() / '.env',  # User home directory
    ]
    
    loaded = False
    
    for env_file in env_file_locations:
        if env_file.exists():
            try:
                load_dotenv(env_file, override=False)
                logger.info(f"Successfully loaded .env file from: {env_file}")
                loaded = True
                break
            except Exception as e:
                logger.warning(f"Failed to load .env file from {env_file}: {e}")
                continue
    
    if not loaded:
        logger.warning("No .env file found in any expected location")
        logger.info("Searched locations: " + ", ".join(str(loc) for loc in env_file_locations))
    
    # Verify critical environment variables
    critical_vars = ['GOOGLE_API_KEY', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing critical environment variables: {missing_vars}")
        logger.info("Please ensure your .env file contains these variables")
    else:
        logger.info("All critical environment variables are set")
    
    return loaded

def get_api_key(preferred_key='GOOGLE_API_KEY'):
    """
    Get API key with fallback options.
    Tries multiple environment variable names.
    """
    api_key_vars = ['GOOGLE_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY']
    
    # Try preferred key first
    if preferred_key in api_key_vars:
        api_key_vars.remove(preferred_key)
        api_key_vars.insert(0, preferred_key)
    
    for var_name in api_key_vars:
        api_key = os.getenv(var_name)
        if api_key:
            logger.info(f"Using API key from {var_name}")
            return api_key
    
    logger.error("No API key found in environment variables")
    return None

def ensure_env_loaded():
    """
    Ensure environment variables are loaded.
    Call this function before accessing environment variables.
    """
    if not hasattr(ensure_env_loaded, '_loaded'):
        load_environment_variables()
        ensure_env_loaded._loaded = True

# Auto-load when module is imported
ensure_env_loaded()