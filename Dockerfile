# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
# CORRECTED: Assume requirements.txt is at the root of the build context
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and src directory
# CORRECTED: Copy everything from the root of the build context to /app
COPY . .

# *** EXTENSIVE DEBUGGING FOR CLOUD RUN ***
# These commands are excellent for debugging and will now show the correct paths!
RUN echo "=== Current working directory ===" && pwd
RUN echo "=== Listing /app contents ===" && ls -la /app
RUN echo "=== Listing src/ contents ===" && ls -la /app/src/
RUN echo "=== Checking __init__.py exists ===" && test -f /app/src/__init__.py && echo "EXISTS" || echo "MISSING"
RUN echo "=== Content of __init__.py ===" && cat /app/src/__init__.py
RUN echo "=== Checking auth_manager.py exists ===" && test -f /app/src/auth_manager.py && echo "EXISTS" || echo "MISSING"
RUN echo "=== Python version ===" && python --version
RUN echo "=== Python path ===" && python -c "import sys; print('\n'.join(sys.path))"
RUN echo "=== Testing basic Python import ===" && python -c "print('Python working')"
RUN echo "=== Testing src import ===" && python -c "import src; print('src import successful')" || echo "src import FAILED"
RUN echo "=== Testing src.auth_manager import ===" && python -c "import src.auth_manager; print('src.auth_manager import successful')" || echo "src.auth_manager import FAILED"
RUN echo "=== Checking for syntax errors in __init__.py ===" && python -m py_compile src/__init__.py && echo "NO SYNTAX ERRORS" || echo "SYNTAX ERRORS FOUND"
RUN echo "=== Checking for syntax errors in auth_manager.py ===" && python -m py_compile src/auth_manager.py && echo "NO SYNTAX ERRORS" || echo "SYNTAX ERRORS FOUND"
# **********************************************

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=true
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]