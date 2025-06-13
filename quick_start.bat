@echo off
REM MultiAgentAI21 Quick Start Script for Windows
REM This script helps you quickly deploy and test your Streamlit application

echo 🚀 MultiAgentAI21 Quick Start
echo ==============================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ app.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Check environment variables
echo 🔍 Checking environment variables...
if "%GOOGLE_API_KEY%"=="" (
    echo ⚠️  GOOGLE_API_KEY not set. Please set it in your environment or .env file.
)

if "%GOOGLE_PROJECT_ID%"=="" (
    echo ⚠️  GOOGLE_PROJECT_ID not set. Please set it in your environment or .env file.
)

REM Start the application
echo 🚀 Starting Streamlit application...
echo 📍 Application will be available at: http://localhost:8501
echo 🌐 For Cloudflare integration, configure your domain to proxy to this address
echo.
echo Press Ctrl+C to stop the application
echo.

REM Run Streamlit with correct parameter names
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.enableCORS=true --server.enableXsrfProtection=false --server.headless=true

pause 