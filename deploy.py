#!/usr/bin/env python3
"""
Deployment script for MultiAgentCodingAI21 Streamlit application
Configured for Cloudflare integration
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'GOOGLE_API_KEY',
        'GOOGLE_PROJECT_ID',
        'GOOGLE_APPLICATION_CREDENTIALS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your environment or .env file")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

def install_dependencies():
    """Install required dependencies."""
    try:
        logger.info("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def run_streamlit():
    """Run the Streamlit application."""
    try:
        logger.info("🚀 Starting Streamlit application...")
        logger.info("📍 Application will be available at: http://localhost:8501")
        logger.info("🌐 For Cloudflare integration, configure your domain to proxy to this address")
        
        # Run Streamlit with the app - using correct parameter names
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.enableCORS=true",
            "--server.enableXsrfProtection=false",
            "--server.headless=true"
        ])
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start Streamlit: {e}")

def main():
    """Main deployment function."""
    logger.info("🚀 MultiAgentCodingAI21 Deployment Script")
    logger.info("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        logger.error("❌ app.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main() 