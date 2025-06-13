#!/bin/bash

# MultiAgentAI21 Quick Start Script
# This script helps you quickly deploy and test your Streamlit application

echo "🚀 MultiAgentAI21 Quick Start"
echo "=============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set. Please set it in your environment or .env file."
fi

if [ -z "$GOOGLE_PROJECT_ID" ]; then
    echo "⚠️  GOOGLE_PROJECT_ID not set. Please set it in your environment or .env file."
fi

# Start the application
echo "🚀 Starting Streamlit application..."
echo "📍 Application will be available at: http://localhost:8501"
echo "🌐 For Cloudflare integration, configure your domain to proxy to this address"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Run Streamlit with correct parameter names
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.enableCORS=true --server.enableXsrfProtection=false --server.headless=true 